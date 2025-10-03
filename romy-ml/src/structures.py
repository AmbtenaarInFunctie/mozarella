from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    """Represents a citation to a support document"""
    document_id: str  # URL or unique identifier of the document
    document_title: str  # Title of the source document
    document_original_url: str  # Original URL of the source document
    document_domain: str  # Domain of the source document
    document_number: int  # The support document number (1, 2, 3, etc.)
    relevance_score: Optional[float] = None

class ModelResponse(BaseModel):
    """Model response with content and citations to source documents"""
    content: str
    citations: List[Citation] = Field(default_factory=list)
    
@dataclass
class SearchResult:
    id: str
    score: float
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: Any
    citations: Optional[List[Dict[str, Any]]] = None
    status: str = "success"
