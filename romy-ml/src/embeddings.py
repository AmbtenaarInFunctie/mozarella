import os
from typing import List, Optional, Dict
import numpy as np
from openai import AsyncOpenAI
from hashlib import md5

class EmbeddingModel:
    """Async OpenAI text-embedding-3-large wrapper with caching"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        dimensions: Optional[int] = None,
        enable_cache: bool = True,
    ):
        self.model = model
        self.enable_cache = enable_cache
        self._cache: Dict[str, np.ndarray] = {}
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        
        if dimensions:
            self.dimensions = dimensions
        elif "3-large" in model:
            self.dimensions = 3072
        else:
            self.dimensions = 1536
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text with caching"""
        if self.enable_cache:
            cache_key = md5(text.encode()).hexdigest()
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        response = await self.client.embeddings.create(
            input=[text],
            model=self.model,
            dimensions=self.dimensions
        )
        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        
        if self.enable_cache:
            self._cache[cache_key] = embedding
        
        return embedding
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """Generate embeddings for multiple texts in batches with caching"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_to_embed = []
            batch_indices = []
            batch_results = [None] * len(batch)
            
            # Check cache
            for j, text in enumerate(batch):
                if self.enable_cache:
                    cache_key = md5(text.encode()).hexdigest()
                    if cache_key in self._cache:
                        batch_results[j] = self._cache[cache_key]
                        continue
                
                batch_to_embed.append(text)
                batch_indices.append(j)
            
            # API call for uncached texts
            if batch_to_embed:
                response = await self.client.embeddings.create(
                    input=batch_to_embed,
                    model=self.model,
                    dimensions=self.dimensions
                )
                
                for idx, (text, item) in enumerate(zip(batch_to_embed, response.data)):
                    embedding = np.array(item.embedding, dtype=np.float32)
                    batch_results[batch_indices[idx]] = embedding
                    
                    if self.enable_cache:
                        self._cache[md5(text.encode()).hexdigest()] = embedding
            
            all_embeddings.extend(batch_results)
        
        return np.array(all_embeddings, dtype=np.float32)
    
    def clear_cache(self):
        """Clear embedding cache"""
        self._cache.clear()
    
    def __str__(self):
        return f"EmbeddingModel({self.model}, {self.dimensions}D)"