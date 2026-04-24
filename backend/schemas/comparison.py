from pydantic import BaseModel
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime

class RAGResponse(BaseModel):
    """RAG-generated answer"""
    answer: str
    retrieved_tickets: List
    latency_ms: float
    cost_usd: float
    context_used: str

class LLMResponse(BaseModel):
    """Pure LLM response without RAG"""
    answer: str
    latency_ms: float
    cost_usd: float

class MLPredictionResponse(BaseModel):
    """ML model prediction"""
    priority: str  # "urgent" or "normal"
    confidence: float
    latency_ms: float
    features_used: Optional[Dict[str, float]] = None
    top_features: Optional[List[Tuple[str, float]]] = None

class LLMPredictionResponse(BaseModel):
    """LLM zero-shot prediction"""
    priority: str
    confidence: float
    latency_ms: float
    cost_usd: float

class ComparisonResponse(BaseModel):
    """Full comparison of all four outputs"""
    query: str
    rag: RAGResponse
    llm_only: LLMResponse
    ml: MLPredictionResponse
    llm_priority: LLMPredictionResponse
    aggregated_metrics: Dict[str, Any]

class LogEntry(BaseModel):
    """Structured log entry for a query"""
    timestamp: datetime
    query: str
    retrieved_tickets: List[str]
    rag_answer: str
    llm_answer: str
    ml_prediction: str
    llm_priority_prediction: str
    rag_latency_ms: float
    llm_latency_ms: float
    ml_latency_ms: float
    llm_priority_latency_ms: float
    rag_cost: float
    llm_cost: float
    llm_priority_cost: float
    similarity_scores: List[float]

class HealthResponse(BaseModel):
    status: str
    weaviate_connected: bool
    model_loaded: bool

class TicketIngestResponse(BaseModel):
    """Response after ingesting a ticket"""
    success: bool
    ticket_id: str
    message: str
