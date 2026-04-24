from fastapi import APIRouter, HTTPException
from typing import List, Optional
import time

from schemas import QueryRequest, RAGResponse, TicketResponse
from utils.weaviate_client import weaviate_client
from utils.embedding import embedding_model
from utils.groq_client import groq_client
from utils.logger import logger, query_logger
from config import settings

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/query", response_model=RAGResponse)
async def rag_query(request: QueryRequest):
    """Query the RAG system: retrieve similar tickets and generate answer"""
    try:
        start_total = time.time()

        # Ensure models are loaded
        if embedding_model.model is None:
            embedding_model.load()
        if groq_client.client is None:
            groq_client.initialize()

        # Generate query embedding
        query_embedding = embedding_model.encode_single(request.query)

        # Retrieve similar tickets
        retrieval_start = time.time()
        similar_tickets = weaviate_client.search_similar(
            query_embedding,
            top_k=request.top_k
        )
        retrieval_time = (time.time() - retrieval_start) * 1000

        if not similar_tickets:
            logger.warning("No similar tickets found")
            # Still generate answer without context
            context = "No similar past tickets found."
        else:
            # Build context string
            context_parts = []
            for i, ticket in enumerate(similar_tickets, 1):
                context_parts.append(f"[Ticket {i}] {ticket['text']} (Priority: {ticket['label']})")
            context = "\n\n".join(context_parts)

        # Generate answer with context
        answer_start = time.time()
        answer, llm_latency = groq_client.generate_with_context(request.query, context)
        generation_time = (time.time() - answer_start) * 1000

        total_time = (time.time() - start_total) * 1000

        # Estimate cost (approximate token count)
        prompt_tokens = len(request.query.split()) + len(context.split())
        completion_tokens = len(answer.split())
        cost = groq_client.estimate_cost(prompt_tokens, completion_tokens)

        # Build response
        response = RAGResponse(
            answer=answer,
            retrieved_tickets=[
                TicketResponse(**t) for t in similar_tickets
            ],
            latency_ms=total_time,
            cost_usd=cost,
            context_used=context[:500] + "..." if len(context) > 500 else context
        )

        # Log the query
        query_logger.log_query({
            "timestamp": time.time(),
            "query": request.query,
            "use_rag": request.use_rag,
            "retrieved_tickets": [t['tweet_id'] for t in similar_tickets],
            "similarity_scores": [t['similarity'] for t in similar_tickets],
            "rag_answer": answer,
            "rag_latency_ms": total_time,
            "rag_cost": cost,
            "generation_latency_ms": llm_latency
        })

        logger.info(f"RAG query completed: {total_time:.2f}ms, {len(similar_tickets)} tickets retrieved")
        return response

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{query}")
async def get_similar_tickets(query: str, top_k: int = 5):
    """Get similar tickets without generation"""
    try:
        if embedding_model.model is None:
            embedding_model.load()

        query_embedding = embedding_model.encode_single(query)
        similar_tickets = weaviate_client.search_similar(query_embedding, top_k=top_k)

        return {
            "query": query,
            "similar_tickets": similar_tickets
        }
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
