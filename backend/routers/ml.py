from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List
import time
import pandas as pd
import numpy as np

from schemas import MLPredictionResponse
from utils.ml_model import ml_model
from utils.preprocess import preprocessor
from utils.logger import logger, query_logger
from config import settings

router = APIRouter(prefix="/ml", tags=["ml"])

from utils.weaviate_client import weaviate_client

def load_tickets_into_preprocessor():
    tickets = weaviate_client.get_all_tickets()  # however you fetch them
    if tickets:
        df = preprocessor.prepare_dataframe(tickets)
        preprocessor.df = df
        logger.info(f"Loaded {len(df)} tickets into preprocessor")
    else:
        logger.warning("No tickets found in database")


@router.post("/train")
async def train_model(model_type: str = "random_forest", tune: bool = False):
    """Train the ML model on currently loaded data"""
    try:
        if preprocessor.df is None or len(preprocessor.df) == 0:
            load_tickets_into_preprocessor()
            #raise HTTPException(
             #   status_code=400,
              #  detail="No data loaded. Please ingest tickets first or load dataset."
            #)

        start_time = time.time()

        results = ml_model.train(preprocessor.df, model_type=model_type, tune_hyperparams=tune)

        training_time = (time.time() - start_time) * 1000

        # Save model
        ml_model.save()

        logger.info(f"Model training completed in {training_time:.2f}ms")

        return {
            "success": True,
            "training_time_ms": training_time,
            "model_type": model_type,
            "metrics": results['val_metrics'],
            "feature_importance": results.get('feature_importance', {}),
            "best_params": results.get('best_params')
        }

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=MLPredictionResponse)
async def predict_priority(text: str):
    """Predict priority for a single text using trained ML model"""
    try:
        start_time = time.time()

        # Check if model is loaded
        if ml_model.model is None:
            # Try to load from disk
            try:
                ml_model.load()
            except FileNotFoundError:
                raise HTTPException(
                    status_code=400,
                    detail="Model not trained. Please train the model first via /ml/train endpoint."
                )

        # Extract features from text
        clean_text = preprocessor.clean_text(text)
        features = preprocessor.extract_features(pd.Series({
            'clean_text': clean_text,
            'created_at': None
        }))

        # Predict
        label, confidence = ml_model.predict_single(features)

        inference_time = (time.time() - start_time) * 1000

        logger.info(f"ML prediction: {label}, confidence: {confidence:.2f}, time: {inference_time:.2f}ms")

        # Get feature importance
        feature_importance = None
        if ml_model.feature_importance:
            # Sort features by absolute value and get top 5
            sorted_features = sorted(
                features.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]
            feature_importance = sorted_features

        return MLPredictionResponse(
            priority=label,
            confidence=confidence,
            latency_ms=inference_time,
            features_used=features,
            top_features=feature_importance
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-batch")
async def predict_batch(texts: List[str]):
    """Predict priority for multiple texts"""
    try:
        if ml_model.model is None:
            try:
                ml_model.load()
            except FileNotFoundError:
                raise HTTPException(
                    status_code=400,
                    detail="Model not trained"
                )

        start_time = time.time()

        # Clean and extract features
        clean_texts = [preprocessor.clean_text(t) for t in texts]
        features_list = []
        for text in clean_texts:
            features = preprocessor.extract_features(pd.Series({
                'clean_text': text,
                'created_at': None
            }))
            features_list.append(features)

        # Create dataframe
        df = pd.DataFrame(features_list)

        # Predict
        predictions, probabilities = ml_model.predict(df)

        inference_time = (time.time() - start_time) * 1000

        results = []
        for text, pred, prob in zip(texts, predictions, probabilities):
            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "priority": "urgent" if pred == 1 else "normal",
                "confidence": float(prob)
            })

        return {
            "predictions": results,
            "total_time_ms": inference_time,
            "avg_time_per_ticket_ms": inference_time / len(texts)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_model_metrics():
    """Get model performance metrics"""
    try:
        if ml_model.model is None:
            try:
                ml_model.load()
            except FileNotFoundError:
                return {"message": "No model trained yet"}

        return {
            "model_type": ml_model.model_type,
            "feature_importance": ml_model.feature_importance,
            "metrics": ml_model.evaluate(preprocessor.df) if preprocessor.df is not None else None
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feature-importance")
async def get_feature_importance():
    """Get feature importance from trained model"""
    try:
        if ml_model.model is None:
            try:
                ml_model.load()
            except FileNotFoundError:
                return {"message": "No model trained yet"}

        return {
            "feature_importance": ml_model.feature_importance,
            "top_features": sorted(
                ml_model.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10] if ml_model.feature_importance else []
        }
    except Exception as e:
        logger.error(f"Failed to get feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
