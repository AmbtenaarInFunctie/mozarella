import json
import os
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import faiss
from structures import SearchResult
from embeddings import EmbeddingModel
from dotenv import load_dotenv

load_dotenv()

class FaissVectorDB:
    """
    Lightweight FAISS-backed vector store.

    Stores embeddings in a FAISS index and keeps in-memory mappings for
    document ids and metadata. Supports cosine similarity (default) or L2.
    """

    def __init__(
        self,
        dim: int,
        metric: str = "cosine",
    ) -> None:
        if dim <= 0:
            raise ValueError("dim must be > 0")
        metric_normalized = metric.lower().strip()
        if metric_normalized not in {"cosine", "l2"}:
            raise ValueError("metric must be one of: 'cosine', 'l2'")

        self.dim: int = dim
        self.metric: str = metric_normalized

        if self.metric == "cosine":
            base_index = faiss.IndexFlatIP(self.dim)
            self._index: faiss.Index = faiss.IndexIDMap(base_index)
        else:
            base_index = faiss.IndexFlatL2(self.dim)
            self._index = faiss.IndexIDMap(base_index)

        self._next_internal_id: int = 0
        self._internal_id_to_external_id: Dict[int, str] = {}
        self._external_id_to_internal_id: Dict[str, int] = {}
        self._metadata_by_internal_id: Dict[int, Dict[str, Any]] = {}
        self._content_by_internal_id: Dict[int, str] = {}

    @staticmethod
    def _as_float32(matrix: np.ndarray) -> np.ndarray:
        if matrix.dtype != np.float32:
            matrix = matrix.astype(np.float32, copy=False)
        return np.ascontiguousarray(matrix)

    def _normalize_inplace(self, matrix: np.ndarray) -> None:
        if self.metric != "cosine":
            return
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        matrix /= norms

    def _ensure_2d(self, vecs: Union[np.ndarray, Sequence[float]]) -> np.ndarray:
        if isinstance(vecs, np.ndarray):
            arr = vecs
        else:
            arr = np.array(vecs, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] != self.dim:
            raise ValueError(f"Expected embedding dim {self.dim}, got {arr.shape[1]}")
        return arr

    def _allocate_internal_ids(self, count: int) -> np.ndarray:
        start = self._next_internal_id
        end = start + count
        ids = np.arange(start, end, dtype=np.int64)
        self._next_internal_id = end
        return ids

    def add_embeddings(
        self,
        embeddings: Union[np.ndarray, Sequence[Sequence[float]]],
        ids: Sequence[str],
        contents: Optional[Sequence[Optional[str]]] = None,
        metadatas: Optional[Sequence[Optional[Dict[str, Any]]]] = None,
        allow_upsert: bool = False,
    ) -> None:
        """
        Add embeddings to the vector database.
        
        Args:
            embeddings: Array of embeddings, shape (n, dim)
            ids: List of unique IDs for each embedding
            contents: Optional list of text content for each embedding
            metadatas: Optional list of metadata dicts for each embedding
            allow_upsert: If True, allows updating existing IDs
        """
        arr = self._ensure_2d(np.asarray(embeddings, dtype=np.float32))
        if arr.shape[0] != len(ids):
            raise ValueError("embeddings rows must match number of ids")
        if arr.shape[1] != self.dim:
            raise ValueError(f"embeddings must have dimension {self.dim}")

        arr = self._as_float32(arr)
        self._normalize_inplace(arr)

        if contents is None:
            contents = [None] * len(ids)
        if len(contents) != len(ids):
            raise ValueError("contents length must match ids length")

        if metadatas is None:
            metadatas = [None] * len(ids)
        if len(metadatas) != len(ids):
            raise ValueError("metadatas length must match ids length")

        internal_ids: List[int] = []
        for external_id in ids:
            if external_id in self._external_id_to_internal_id:
                if not allow_upsert:
                    raise ValueError(f"Duplicate id '{external_id}' detected")
                internal_id = self._external_id_to_internal_id[external_id]
            else:
                internal_id = int(self._allocate_internal_ids(1)[0])
                self._external_id_to_internal_id[external_id] = internal_id
                self._internal_id_to_external_id[internal_id] = external_id
            internal_ids.append(internal_id)

        id_array = np.array(internal_ids, dtype=np.int64)

        for i, internal_id in enumerate(internal_ids):
            # Store content
            content = contents[i] if contents is not None else None
            self._content_by_internal_id[internal_id] = content or ""
            
            # Store metadata
            meta = metadatas[i] if metadatas is not None else None
            if meta is None:
                meta = {}
            self._metadata_by_internal_id[internal_id] = meta

        # IndexIDMap always supports add_with_ids
        self._index.add_with_ids(arr, id_array)

    def search(
        self,
        query_embeddings: Union[np.ndarray, Sequence[Sequence[float]], Sequence[float]],
        k: int = 5,
    ) -> List[List[SearchResult]]:
        queries = self._ensure_2d(np.asarray(query_embeddings, dtype=np.float32))
        queries = self._as_float32(queries)
        self._normalize_inplace(queries)

        if k <= 0:
            raise ValueError("k must be > 0")
        if self._index.ntotal == 0:
            return [[] for _ in range(queries.shape[0])]

        distances, indices = self._index.search(queries, min(k, self._index.ntotal))

        results: List[List[SearchResult]] = []
        for row_dist, row_idx in zip(distances, indices):
            row: List[SearchResult] = []
            for d, idx in zip(row_dist.tolist(), row_idx.tolist()):
                if idx == -1:
                    continue
                external_id = self._internal_id_to_external_id.get(idx)
                if external_id is None:
                    continue
                if self.metric == "cosine":
                    score = float(d)
                else:
                    score = float(-d)
                content = self._content_by_internal_id.get(idx)
                meta = self._metadata_by_internal_id.get(idx)
                row.append(SearchResult(id=external_id, score=score, content=content, metadata=meta))
            results.append(row)
        return results

    def save(self, directory: str) -> None:
        if not directory:
            raise ValueError("directory path must be provided")
        os.makedirs(directory, exist_ok=True)
        index_path = os.path.join(directory, "index.faiss")
        meta_path = os.path.join(directory, "meta.json")

        faiss.write_index(self._index, index_path)

        meta_payload = {
            "dim": self.dim,
            "metric": self.metric,
            "next_internal_id": self._next_internal_id,
            "internal_to_external": {str(k): v for k, v in self._internal_id_to_external_id.items()},
            "external_to_internal": self._external_id_to_internal_id,
            "content_by_internal": {str(k): v for k, v in self._content_by_internal_id.items()},
            "metadata_by_internal": {str(k): v for k, v in self._metadata_by_internal_id.items()},
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f)

    @classmethod
    def load(cls, directory: str) -> "FaissVectorDB":
        if not directory:
            raise ValueError("directory path must be provided")
        index_path = os.path.join(directory, "index.faiss")
        meta_path = os.path.join(directory, "meta.json")
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("index.faiss or meta.json not found in directory")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta_payload = json.load(f)

        instance = cls(dim=int(meta_payload["dim"]), metric=str(meta_payload["metric"]))
        instance._index = faiss.read_index(index_path)
        instance._next_internal_id = int(meta_payload.get("next_internal_id", 0))

        internal_to_external = {int(k): v for k, v in meta_payload.get("internal_to_external", {}).items()}
        external_to_internal = {str(k): int(v) for k, v in meta_payload.get("external_to_internal", {}).items()}
        content_by_internal = {int(k): v for k, v in meta_payload.get("content_by_internal", {}).items()}
        metadata_by_internal = {int(k): v for k, v in meta_payload.get("metadata_by_internal", {}).items()}

        instance._internal_id_to_external_id = internal_to_external
        instance._external_id_to_internal_id = external_to_internal
        instance._content_by_internal_id = content_by_internal
        instance._metadata_by_internal_id = metadata_by_internal

        return instance

if __name__ == "__main__":
    # Example usage - uncomment to test building the database
    # from core import Core
    # core = Core()
    # passages = core.get_passages()
    
    # embedding_model = EmbeddingModel()
    # embeddings = embedding_model.embed_batch([passage["meta"]["metadata:title"] for passage in passages])
    # ids = [str(id) for id in range(len(passages))]
    # contents = [passage["text"] for passage in passages]
    # metadatas = [passage["meta"] for passage in passages]
    
    # vectordb = FaissVectorDB(dim=3072, metric="cosine")
    # vectordb.add_embeddings(embeddings, ids, contents=contents, metadatas=metadatas)
    # vectordb.save(os.getcwd() + "/data/vectordb")
    
    # Search example
    embedding_model = EmbeddingModel()
    vectordb = FaissVectorDB.load(os.getcwd() + "/data/vectordb")

    query_embeddings = embedding_model.embed_text("wat is phishing")
    results = vectordb.search(query_embeddings, k=5)
    
    # Display results with content
    for i, result_set in enumerate(results):
        print(f"\n=== Query {i+1} Results ===")
        for j, result in enumerate(result_set):
            print(f"\n{j+1}. ID: {result.id}")
            print(f"   Score: {result.score:.4f}")
            if result.metadata:
                print(f"   Title: {result.metadata.get('metadata:title', 'N/A')}")
                print(f"   Description: {result.metadata.get('metadata:description', 'N/A')}")
                print(f"   URL: {result.metadata.get('metadata:original_url', 'N/A')}")
            if result.content:
                print(f"   Content Preview: {result.content[:200]}...")  # First 200 chars
