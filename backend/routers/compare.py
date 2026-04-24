from fastapi import APIRouter, HTTPException
import time
import numpy as np

from schemas.query import QueryRequest
from schemas.ticket import TicketResponse
from schemas.comparison import (
    RAGResponse, LLMResponse, MLPredictionResponse,
    LLMPredictionResponse, ComparisonResponse
)
from utils.embedding import embedding_model
from utils.logger import logger

router = APIRouter(prefix="/compare", tags=["compare"])

@router.post("/full", response_model=ComparisonResponse)
async def full_comparison(request: QueryRequest):
    """
    Complete comparison of all four systems:
    1. RAG (LLM + retrieved context)
    2. Non-RAG (LLM alone)
    3. ML predictor
    4. LLM zero-shot predictor
    """
    try:
        # Ensure all models are loaded
        if embedding_model.model is None:
            embedding_model.load()
        if groq_client.client is None:
            groq_client.initialize()
        if ml_model.model is None:
            try:
                ml_model.load()
            except FileNotFoundError:
                logger.warning("ML model not loaded - skipping ML prediction")
                ml_model.model = None

        query_start = time.time()

        # ========== 1. RAG PATH ==========
        rag_start = time.time()
        query_embedding = embedding_model.encode_single(request.query)
        similar_tickets = weaviate_client.search_similar(
            query_embedding,
            top_k=request.top_k
        )
        retrieval_time = (time.time() - rag_start) * 1000

        if similar_tickets:
            context = "\n\n".join([
                f"[Ticket {i+1}] {t['text']} (Priority: {t['label']})"
                for i, t in enumerate(similar_tickets)
            ])
        else:
            context = "No similar tickets found."

        rag_answer, rag_gen_latency = groq_client.generate_with_context(request.query, context)
        rag_total_time = (time.time() - rag_start) * 1000
        rag_prompt_tokens = len(request.query.split()) + len(context.split())
        rag_cost = groq_client.estimate_cost(rag_prompt_tokens, len(rag_answer.split()))

        rag_response = RAGResponse(
            answer=rag_answer,
            retrieved_tickets=similar_tickets,
            latency_ms=rag_total_time,
            cost_usd=rag_cost,
            context_used=context[:200] + "..." if len(context) > 200 else context
        )

        # ========== 2. NON-RAG LLM ==========
        llm_start = time.time()
        llm_answer, llm_gen_latency = groq_client.generate_without_context(request.query)
        llm_total_time = (time.time() - llm_start) * 1000
        llm_prompt_tokens = len(request.query.split())
        llm_cost = groq_client.estimate_cost(llm_prompt_tokens, len(llm_answer.split()))

        llm_response = LLMResponse(
            answer=llm_answer,
            latency_ms=llm_total_time,
            cost_usd=llm_cost
        )

        # ========== 3. ML PREDICTION ==========
        ml_start = time.time()
        if ml_model.model is not None:
            clean_text = preprocessor.clean_text(request.query)
            features = preprocessor.extract_features(pd.Series({
                'clean_text': clean_text,
                'created_at': None
            }))
            ml_label, ml_confidence = ml_model.predict_single(features)
        else:
            ml_label, ml_confidence = "N/A", 0.0
            features = {}

        ml_time = (time.time() - ml_start) * 1000

        ml_response = MLPredictionResponse(
            priority=ml_label,
            confidence=ml_confidence,
            latency_ms=ml_time,
            features_used=features,
            top_features=sorted(features.items(), key=lambda x: abs(x[1]), reverse=True)[:5] if features else None
        )

        # ========== 4. LLM ZERO-SHOT PRIORITY ==========
        llm_priority_start = time.time()
        llm_priority_label, llm_priority_conf, llm_priority_lat = groq_client.predict_priority(
            request.query,
            use_context=False
        )
        llm_priority_total = (time.time() - llm_priority_start) * 1000
        llm_priority_cost = groq_client.estimate_cost(len(request.query.split()), 10)

        llm_priority_response = LLMPredictionResponse(
            priority=llm_priority_label,
            confidence=llm_priority_conf,
            latency_ms=llm_priority_total,
            cost_usd=llm_priority_cost
        )

        # ========== AGGREGATED METRICS ==========
        total_time = (time.time() - query_start) * 1000

        aggregated = {
            "total_time_ms": total_time,
            "cost_breakdown": {
                "rag_usd": rag_cost,
                "llm_usd": llm_cost,
                "ml_usd": 0.0,  # ML is free
                "llm_priority_usd": llm_priority_cost,
                "total_usd": rag_cost + llm_cost + llm_priority_cost
            },
            "latency_breakdown_ms": {
                "retrieval": retrieval_time,
                "rag_generation": rag_gen_latency,
                "llm_generation": llm_gen_latency,
                "ml_inference": ml_time,
                "llm_priority": llm_priority_total
            },
            "retrieved_count": len(similar_tickets),
            "avg_similarity": float(np.mean([t['similarity'] for t in similar_tickets])) if similar_tickets else 0.0
        }

        # Log full query
        query_logger.log_query({
            "timestamp": time.time(),
            "query": request.query,
            "rag_answer": rag_answer,
            "llm_answer": llm_answer,
            "ml_priority": ml_label,
            "llm_priority": llm_priority_label,
            "similarity_scores": [t['similarity'] for t in similar_tickets],
            "metrics": aggregated
        })

        logger.info(f"Full comparison completed in {total_time:.2f}ms")

        return ComparisonResponse(
            query=request.query,
            rag=rag_response,
            llm_only=llm_response,
            ml=ml_response,
            llm_priority=llm_priority_response,
            aggregated_metrics=aggregated
        )

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
