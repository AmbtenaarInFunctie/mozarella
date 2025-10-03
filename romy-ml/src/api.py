from fastapi import FastAPI, Header
from pydantic import BaseModel
import uvicorn
from typing import Optional
from structures import QueryRequest, QueryResponse
from dotenv import load_dotenv

from core import Core

load_dotenv()

app = FastAPI(title="Hackwerk 2025 API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Hackwerk 2025 API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, x_user_id: Optional[str] = Header(default="default")):
    core = Core()

    result = await core.process_query(request.query, x_user_id)

    # Extract citations from the ModelResponse
    citations = None
    if hasattr(result, 'citations') and result.citations:
        citations = [citation.model_dump() for citation in result.citations]

    return QueryResponse(
        response={
            "content": result.content,
            "citations": citations
        },
        status="success"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
