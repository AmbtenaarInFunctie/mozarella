import os
import glob
import json
import asyncio

from embeddings import EmbeddingModel
from faiss_vectordb import FaissVectorDB
from dotenv import load_dotenv
from model import Model

load_dotenv()

class Core:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.faiss_vectordb = FaissVectorDB.load(os.getcwd() + "/data/vectordb")
        self.model = Model("openai", "gpt-5")

    def get_passages(self):
        
        spider_files = glob.glob(os.getcwd() + "/data/spider*.json")
        raw_data = None
        
        for file_path in spider_files:
            with open(file_path, "r") as f:
                data = json.load(f)
                raw_data = data
                f.close()

        passage_lst = [{
            "id": idx,
            "text": item["content"],
            "meta": {
                "metadata:original_url": item["metadata"]["original_url"],
                "metadata:domain": item["metadata"]["domain"],
                "metadata:title": item["metadata"]["title"],
                "metadata:description": item["metadata"]["description"]
            }
        } for idx, item in enumerate(data) if item.get("content") is not None]
        
        return passage_lst

    async def process_query(self, query: str, user_id: str):
        query_embeddings = self.embedding_model.embed_text(query)
        support_docs = self.faiss_vectordb.search(query_embeddings, k=5)
        response = await self.model.run(query, support_docs, user_id) 
        print(response)
        return response

if __name__ == "__main__":

    core = Core()
    asyncio.run(core.process_query("wat is phishing", "123"))