from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from utils.logger import logger
from utils.weaviate_client import weaviate_client
from utils.embedding import embedding_model
from utils.groq_client import groq_client

# Import routers
from routers import tickets, rag, llm, ml, compare

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Decision Intelligence Assistant...")

    # Connect to Weaviate
    connected = weaviate_client.connect()
    if not connected:
        logger.error("Failed to connect to Weaviate")
        # Continue anyway, might be used for direct file loading

    # Load embedding model
    try:
        embedding_model.load()
        logger.info("Embedding model loaded")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")

    # Initialize GROQ client
    try:
        groq_client.initialize()
        logger.info("GROQ client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize GROQ: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    weaviate_client.disconnect()

app = FastAPI(
    title="Decision Intelligence Assistant API",
    description="API for comparing RAG, LLM, ML, and zero-shot priority predictions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets.router)
app.include_router(rag.router)
app.include_router(llm.router)
app.include_router(ml.router)
app.include_router(compare.router)

@app.get("/")
async def root():
    return {"message": "Decision Intelligence Assistant API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "weaviate_connected": weaviate_client.client is not None,
        "model_loaded": embedding_model.model is not None,
        "groq_initialized": groq_client.client is not None
    }

# For direct execution (development only)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
