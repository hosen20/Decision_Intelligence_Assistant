from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import torch

from config import settings
from utils.logger import logger

class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model"""

    def __init__(self):
        self.model = None
        self.model_name = settings.embedding_model
        self.dimension = 384  # Default for all-MiniLM-L6-v2

    def load(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
            return True
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return False

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """Encode text(s) to embedding vector(s)"""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            raise

    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text string"""
        return self.encode(text)[0]

    def get_dimension(self) -> int:
        """Return embedding dimension"""
        return self.dimension

# Global embedding model instance
embedding_model = EmbeddingModel()
