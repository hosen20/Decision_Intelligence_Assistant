import os
from groq import Groq
from typing import Dict, Optional, Tuple
import time

from config import settings
from utils.logger import logger

class GroqClient:
    """Client for GROQ API for LLM inference"""

    def __init__(self):
        self.client = None
        self.model = settings.groq_model

    def initialize(self):
        """Initialize GROQ client"""
        try:
            self.client = Groq(api_key=settings.groq_api_key)
            logger.info("GROQ client initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GROQ client: {e}")
            return False

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Tuple[str, float]:
        """Generate text completion, returns (response, latency_ms)"""
        start_time = time.time()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            latency = (time.time() - start_time) * 1000

            response = completion.choices[0].message.content
            logger.debug(f"GROQ generation latency: {latency:.2f}ms")
            return response, latency
        except Exception as e:
            logger.error(f"GROQ generation failed: {e}")
            raise

    def generate_with_context(self, query: str, context: str, system_prompt: str = None) -> Tuple[str, float]:
        """Generate answer using RAG context"""
        prompt = f"""You are a helpful customer support assistant.

Use the following context from past support tickets to answer the user's question.
If the context doesn't contain relevant information, say so and provide a general helpful response.

Context from past tickets:
{context}

User question: {query}

Please provide a clear, helpful, and concise answer:"""

        return self.generate(prompt, max_tokens=512, temperature=0.7)

    def generate_without_context(self, query: str) -> Tuple[str, float]:
        """Generate answer using LLM alone (no RAG)"""
        prompt = f"""You are a helpful customer support assistant.

User question: {query}

Please provide a clear, helpful, and concise answer:"""

        return self.generate(prompt, max_tokens=512, temperature=0.7)

    def predict_priority(self, text: str, context: str = "") -> Tuple[str, float, float]:
        """Predict priority (urgent/normal) for a ticket, returns (label, confidence, latency_ms)"""
        start_time = time.time()

        if context:
            prompt = f"""Given a customer support ticket and similar past cases, determine if this ticket is URGENT or NORMAL priority.

Ticket: {text}

Similar past tickets for context:
{context}

Consider factors like:
- Urgency keywords (refund, cancel, broken, emergency, help, etc.)
- Strong negative sentiment
- Excessive punctuation or ALL-CAPS
- Time sensitivity (billing issues, service outages, security concerns)

Respond with only one word: URGENT or NORMAL"""
        else:
            prompt = f"""Given a customer support ticket, determine if it is URGENT or NORMAL priority.

Ticket: {text}

Consider factors like:
- Urgency keywords (refund, cancel, broken, emergency, help, etc.)
- Strong negative sentiment
- Excessive punctuation or ALL-CAPS
- Time sensitivity (billing issues, service outages, security concerns)

Respond with only one word: URGENT or NORMAL"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0  # Low temperature for consistent classification
            )
            latency = (time.time() - start_time) * 1000

            response = completion.choices[0].message.content.strip().upper()

            # Parse response
            if "URGENT" in response:
                label = "urgent"
                confidence = 0.9  # High confidence for clear LLM response
            elif "NORMAL" in response:
                label = "normal"
                confidence = 0.9
            else:
                # Ambiguous response
                label = "normal"
                confidence = 0.5

            logger.debug(f"GROQ priority prediction: {label}, confidence: {confidence:.2f}, latency: {latency:.2f}ms")
            return label, confidence, latency
        except Exception as e:
            logger.error(f"GROQ priority prediction failed: {e}")
            return "normal", 0.0, (time.time() - start_time) * 1000

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on GROQ pricing (adjust rates as needed)"""
        # GROQ pricing (approximate, check current rates)
        # Llama 3.3 70B: ~$0.00059 per 1K input tokens, ~$0.00079 per 1K output tokens
        input_cost = (prompt_tokens / 1000) * 0.00059
        output_cost = (completion_tokens / 1000) * 0.00079
        return input_cost + output_cost

# Global GROQ client instance
groq_client = GroqClient()
