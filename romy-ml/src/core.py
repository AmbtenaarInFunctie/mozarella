import os
import glob
import json
from typing import List, Dict, Any

from embeddings import EmbeddingModel
from faiss_vectordb import FaissVectorDB
from dotenv import load_dotenv
from model import Model

class Core:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.faiss_vectordb = FaissVectorDB.load(os.getcwd() + "/data/vectordb")
        self.model = Model("openrouter", "anthropic/claude-3.5-sonnet")

    def get_passages(self) -> List[Dict[str, Any]]:
        """Get all passages from spider JSON files"""
        spider_files = glob.glob(os.path.join(os.getcwd(), "data", "spider*.json"))
        if not spider_files:
            return []
        
        all_data = []
        for file_path in spider_files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data.extend(data if isinstance(data, list) else [data])

        passages = []
        for idx, item in enumerate(all_data):
            if item.get("content") and "metadata" in item:
                passages.append({
                    "id": idx,
                    "text": item["content"],
                    "meta": {
                        "metadata:original_url": item["metadata"]["original_url"],
                        "metadata:domain": item["metadata"]["domain"],
                        "metadata:title": item["metadata"]["title"],
                        "metadata:description": item["metadata"]["description"]
                    }
                })
        
        return passages

    async def process_query(self, query: str, user_id: str) -> Any:
        """Process user query and return AI response"""
        query_embeddings = await self.embedding_model.embed_text(query)
        support_docs = self.faiss_vectordb.search(query_embeddings, k=10)
        return await self.model.run(query, support_docs, user_id)
    
    def get_conversation_history(self, user_id: str) -> list[dict[str, str]]:
        """Get conversation history for a specific user/thread ID"""
        return self.model.get_conversation_history(user_id)
