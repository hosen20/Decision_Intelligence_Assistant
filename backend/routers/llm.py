from fastapi import APIRouter, HTTPException
from typing import Optional
import time

from schemas import QueryRequest, LLMResponse, LLMPredictionResponse
from utils.groq_client import groq_client
from utils.logger import logger, query_logger
from utils.weaviate_client import weaviate_client
from config import settings

router = APIRouter(prefix="/llm", tags=["llm"])

@router.post("/generate", response_model=LLMResponse)
async def llm_generate(request: QueryRequest):
    """Generate answer using LLM without RAG (pure LLM)"""
    try:
        start_time = time.time()

        if groq_client.client is None:
            groq_client.initialize()

        answer, llm_latency = groq_client.generate_without_context(request.query)
        total_time = (time.time() - start_time) * 1000

        # Estimate cost
        prompt_tokens = len(request.query.split())
        completion_tokens = len(answer.split())
        cost = groq_client.estimate_cost(prompt_tokens, completion_tokens)

        # Log
        query_logger.log_query({
            "query": request.query,
            "llm_answer": answer,
            "llm_latency_ms": total_time,
            "llm_cost": cost
        })

        logger.info(f"LLM generation completed: {total_time:.2f}ms, cost: ${cost:.6f}")

        return LLMResponse(
            answer=answer,
            latency_ms=total_time,
            cost_usd=cost
        )

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/priority", response_model=LLMPredictionResponse)
async def llm_priority(
    text: str,
    use_context: bool = False,
    top_k: int = 3
):
    """Predict ticket priority using LLM zero-shot"""
    try:
        start_time = time.time()

        if groq_client.client is None:
            groq_client.initialize()

        # Optionally include retrieved context
        context = ""
        if use_context:
            from backend.utils.embedding import embedding_model
            if embedding_model.model is None:
                embedding_model.load()
            embedding = embedding_model.encode_single(text)
            similar = weaviate_client.search_similar(embedding, top_k=top_k)
            context = "\n\n".join([t['text'] for t in similar])

        label, confidence, llm_latency = groq_client.predict_priority(text, context)
        total_time = (time.time() - start_time) * 1000

        # Estimate cost
        prompt_tokens = len(text.split()) + (len(context.split()) if context else 0)
        cost = groq_client.estimate_cost(prompt_tokens, 10)  # small output

        logger.info(f"LLM priority prediction: {label}, confidence: {confidence:.2f}, latency: {total_time:.2f}ms")

        return LLMPredictionResponse(
            priority=label,
            confidence=confidence,
            latency_ms=total_time,
            cost_usd=cost
        )

    except Exception as e:
        logger.error(f"LLM priority prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
