from pydantic import BaseModel, Field
from typing import Optional
from typing import List
from schemas.ticket import TicketIngestRequest

class BatchIngestRequest(BaseModel):
    """Request to ingest multiple tickets"""
    tickets: List[TicketIngestRequest] = Field(..., description="List of tickets to ingest")


class QueryRequest(BaseModel):
    """User query request"""
    query: str = Field(..., description="User's question")
    use_rag: bool = Field(True, description="Whether to use RAG or not")
    top_k: int = Field(5, ge=1, le=10, description="Number of retrieved tickets")

class TicketIngestRequest(BaseModel):
    """Request to ingest a single ticket"""
    tweet_id: str = Field(..., description="Unique identifier for the tweet")
    text: str = Field(..., description="Raw tweet text")
    author_id: Optional[str] = Field(None, description="Author ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    inbound: bool = Field(True, description="Whether this is an inbound tweet")

class BatchIngestRequest(BaseModel):
    """Request to ingest multiple tickets"""
    #tickets: list = Field(..., description="List of tickets to ingest")
    tickets: List[TicketIngestRequest] = Field(..., description="List of tickets to ingest")
