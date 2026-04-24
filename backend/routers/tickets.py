from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import time
import pandas as pd

from utils.weaviate_client import weaviate_client
from utils.embedding import embedding_model
from utils.preprocess import preprocessor
from utils.logger import logger, query_logger
from schemas.ticket import TicketIngestRequest, TicketIngestResponse, TicketResponse
from schemas.query import BatchIngestRequest

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("/ingest", response_model=TicketIngestResponse)
async def ingest_ticket(request: TicketIngestRequest):
    """Ingest a single ticket into the vector database"""
    try:
        # Load models if not loaded
        if embedding_model.model is None:
            embedding_model.load()

        # Clean text
        clean_text = preprocessor.clean_text(request.text)

        # Extract features
        features = preprocessor.extract_features(pd.Series({
            'clean_text': clean_text,
            'created_at': request.created_at
        }))

        # Apply labeling
        is_urgent = preprocessor.labeling_function(pd.Series({
            'clean_text': clean_text
        })) if preprocessor.labeling_function else 0

        # Generate embedding
        embedding = embedding_model.encode_single(clean_text)

        # Prepare ticket data
        ticket_data = {
            "tweet_id": request.tweet_id,
            "text": clean_text,
            "author_id": request.author_id or "",
            "created_at": request.created_at or "",
            "label": "urgent" if is_urgent else "normal",
            "is_urgent": bool(is_urgent),
            "features": features,
            "inbound": request.inbound
        }

        # Store in Weaviate
        success = weaviate_client.add_ticket(ticket_data, embedding)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store ticket")

        return TicketIngestResponse(
            success=True,
            ticket_id=request.tweet_id,
            message="Ticket ingested successfully"
        )

    except Exception as e:
        logger.error(f"Ticket ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest-batch", response_model=dict)
async def ingest_batch(request: BatchIngestRequest):
    """Ingest multiple tickets in batch"""
    try:
        if embedding_model.model is None:
            embedding_model.load()

        clean_texts = [preprocessor.clean_text(t.text) for t in request.tickets]

        # Generate embeddings in batch
        embeddings = embedding_model.encode(clean_texts)

        # Extract features and labels
        tickets_data = []
        for ticket, clean_text, embedding in zip(request.tickets, clean_texts, embeddings):
            features = preprocessor.extract_features(pd.Series({
                'clean_text': clean_text,
                'created_at': ticket.created_at
            }))

            is_urgent = preprocessor.labeling_function(pd.Series({
                'clean_text': clean_text
            })) if preprocessor.labeling_function else 0

            tickets_data.append({
                "tweet_id": ticket.tweet_id,
                "text": clean_text,
                "author_id": ticket.author_id or "",
                "created_at": ticket.created_at or "",
                "label": "urgent" if is_urgent else "normal",
                "is_urgent": bool(is_urgent),
                "features": features,
                "inbound": ticket.inbound
            })

        # Store in Weaviate
        success = weaviate_client.add_tickets_batch(tickets_data, embeddings)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store batch")

        return {
            "success": True,
            "count": len(request.tickets),
            "message": f"Successfully ingested {len(request.tickets)} tickets"
        }

    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count")
async def get_ticket_count():
    """Get total number of tickets in database"""
    try:
        count = weaviate_client.count_tickets()
        return {"count": count}
    except Exception as e:
        logger.error(f"Failed to get count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all")
async def get_all_tickets(limit: int = 100):
    """Get all tickets (debug endpoint)"""
    try:
        tickets = weaviate_client.get_all_tickets()
        return {"tickets": tickets[:limit]}
    except Exception as e:
        logger.error(f"Failed to get tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_all_tickets():
    """Clear all tickets from database"""
    try:
        success = weaviate_client.clear_all()
        return {"success": success, "message": "Database cleared"}
    except Exception as e:
        logger.error(f"Failed to clear: {e}")
        raise HTTPException(status_code=500, detail=str(e))
