import os
from typing import List, Union, Optional
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class EmbeddingModel:
    """
    OpenAI text-embedding-3-large wrapper for generating embeddings.
    
    This model supports:
    - Single text embedding
    - Batch text embedding
    - Configurable dimensions (default: 3072)
    - Returns numpy arrays compatible with FaissVectorDB
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        dimensions: Optional[int] = None,
    ):
        """
        Initialize the embedding model.
        
        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY env var.
            model: OpenAI embedding model name. Default: text-embedding-3-large
            dimensions: Optional dimension reduction. Default: None (uses 3072 for text-embedding-3-large)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY env var")
        
        self.model = model
        self.dimensions = dimensions
        self.client = OpenAI(api_key=self.api_key)
        
        # Set default dimensions based on model
        if self.dimensions is None:
            if "text-embedding-3-large" in self.model:
                self.dimensions = 3072
            elif "text-embedding-3-small" in self.model:
                self.dimensions = 1536
            elif "text-embedding-ada-002" in self.model:
                self.dimensions = 1536
            else:
                self.dimensions = 1536  # fallback
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array of shape (dimensions,)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model,
                dimensions=self.dimensions
            )
            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of input texts to embed
            batch_size: Maximum number of texts per API call (OpenAI limit is 2048)
            
        Returns:
            numpy array of shape (len(texts), dimensions)
        """
        if not texts:
            raise ValueError("texts list cannot be empty")
        
        if any(not text or not text.strip() for text in texts):
            raise ValueError("All texts must be non-empty")
        
        all_embeddings = []
        
        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model,
                    dimensions=self.dimensions
                )
                
                # Extract embeddings in the correct order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                raise RuntimeError(f"Failed to generate embeddings for batch {i//batch_size}: {str(e)}")
        
        return np.array(all_embeddings, dtype=np.float32)
    
    def __call__(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Convenience method to embed text(s).
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            numpy array with embeddings
        """
        if isinstance(text, str):
            return self.embed_text(text)
        elif isinstance(text, list):
            return self.embed_batch(text)
        else:
            raise TypeError("text must be str or List[str]")
    
    def get_dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self.dimensions
    
    def __str__(self):
        return f"EmbeddingModel(model={self.model}, dimensions={self.dimensions})"
    
    def __repr__(self):
        return f"EmbeddingModel(model='{self.model}', dimensions={self.dimensions})"


if __name__ == "__main__":
    # Example usage
    embedder = EmbeddingModel()
    
    # Single text embedding
    text = "This is a test sentence for embedding."
    embedding = embedder.embed_text(text)
    print(f"Single embedding shape: {embedding.shape}")
    
    # Batch embedding
    texts = [
        "First document to embed.",
        "Second document to embed.",
        "Third document to embed."
    ]
    embeddings = embedder.embed_batch(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")
    
    # Using __call__ interface
    single_result = embedder("Another test text")
    batch_result = embedder(["Text 1", "Text 2"])
    print(f"Call single shape: {single_result.shape}")
    print(f"Call batch shape: {batch_result.shape}")

