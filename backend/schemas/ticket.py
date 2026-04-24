from pydantic import BaseModel, Field
from typing import Optional, Dict

class TicketBase(BaseModel):
    tweet_id: str
    text: str
    author_id: Optional[str] = None
    created_at: Optional[str] = None
    is_urgent: bool = False
    label: Optional[str] = None
    features: Optional[Dict[str, float]] = None
    inbound: bool = True

class TicketCreate(TicketBase):
    pass

class TicketIngestRequest(BaseModel):
    tweet_id: str
    text: str
    author_id: Optional[str] = None
    created_at: Optional[str] = None
    inbound: bool = True

class TicketIngestResponse(BaseModel):
    success: bool
    ticket_id: Optional[str] = None
    message: Optional[str] = None

class TicketResponse(TicketBase):
    similarity: Optional[float] = None

    class Config:
        from_attributes = True

