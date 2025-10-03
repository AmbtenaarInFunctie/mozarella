from fastapi import FastAPI, Header
import uvicorn
from typing import Optional
from structures import QueryRequest, QueryResponse, ConversationHistoryResponse, Message
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from core import Core

load_dotenv()

core = Core()

app = FastAPI(title="Hackwerk 2025 API", version="1.0.0")

origins = [
    "http://localhost:3000/",
    "http://127.0.0.1:3000/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[""],   # This is key — it tells FastAPI to respond to OPTIONS too
    allow_headers=[""],
)

@app.get("/")
async def root():
    return {"message": "Hackwerk 2025 API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, x_user_id: Optional[str] = Header(default="default")):

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

@app.get("/history/{user_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(x_user_id: str):
    """
    Get conversation history for a specific user/thread ID.
    
    The history is stored in-memory and contains up to the last 10 messages
    for each user (5 user messages and 5 assistant responses).
    Citations are included in assistant messages when available.
    """
    history = core.get_conversation_history(x_user_id)
    
    # Convert history to Message objects, including citations if present
    messages = []
    for msg in history:
        message_data = {
            "role": msg["role"],
            "content": msg["content"]
        }
        if "citations" in msg and msg["citations"]:
            # Convert citation dicts back to Citation objects
            from structures import Citation
            message_data["citations"] = [Citation(**citation) for citation in msg["citations"]]
        messages.append(Message(**message_data))
    
    return ConversationHistoryResponse(
        user_id=user_id,
        messages=messages,
        total_messages=len(messages),
        status="success"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
