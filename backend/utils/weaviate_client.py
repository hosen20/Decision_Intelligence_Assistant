import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import MetadataQuery
from typing import List, Dict, Optional
import numpy as np

from config import settings
from utils.logger import logger

class WeaviateClient:
    """Client for Weaviate vector database operations"""

    def __init__(self):
        self.client = None
        self.class_name = settings.weaviate_class_name

    def connect(self):
        """Establish connection to Weaviate"""
        try:
            self.client = weaviate.connect_to_custom(
                http_host=settings.weaviate_url.replace("http://", "").replace("https://", "").split(":")[0],
                http_port=settings.weaviate_http_port,
                http_secure=False,
                grpc_host=settings.weaviate_url.replace("http://", "").replace("https://", "").split(":")[0],
                grpc_port=settings.weaviate_grpc_port,
                grpc_secure=False,
            )
            logger.info("Connected to Weaviate successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            return False

    def create_schema(self):
        """Create schema for SupportTicket class"""
        try:
            # Delete existing class if it exists
            if self.client.collections.exists(self.class_name):
                self.client.collections.delete(self.class_name)
                logger.info(f"Deleted existing collection: {self.class_name}")

            # Create collection
            collection = self.client.collections.create(
                name=self.class_name,
                properties=[
                    Property(name="tweet_id", data_type=DataType.TEXT),
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="author_id", data_type=DataType.TEXT),
                    Property(name="created_at", data_type=DataType.TEXT),
                    Property(name="label", data_type=DataType.TEXT),  # priority label
                    Property(name="is_urgent", data_type=DataType.BOOL),
                    Property(name="features", data_type=DataType.OBJECT),  # engineered features
                    Property(name="inbound", data_type=DataType.BOOL),
                ],
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric="cosine",
                    ef=128,
                    ef_construction=128,
                    max_connections=64
                )
            )
            logger.info(f"Created collection: {self.class_name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise

    def add_ticket(self, ticket_data: Dict, embedding: np.ndarray):
        """Add a single ticket with embedding to Weaviate"""
        try:
            collection = self.client.collections.get(self.class_name)
            collection.data.insert(
                properties={
                    "tweet_id": ticket_data["tweet_id"],
                    "text": ticket_data["text"],
                    "author_id": ticket_data.get("author_id", ""),
                    "created_at": ticket_data.get("created_at", ""),
                    "label": ticket_data.get("label", ""),
                    "is_urgent": ticket_data.get("is_urgent", False),
                    "features": ticket_data.get("features", {}),
                    "inbound": ticket_data.get("inbound", True),
                },
                vector=embedding.tolist()
            )
            logger.debug(f"Added ticket: {ticket_data['tweet_id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to add ticket: {e}")
            return False

    def add_tickets_batch(self, tickets: List[Dict], embeddings: List[np.ndarray]):
        """Add multiple tickets in batch"""
        try:
            collection = self.client.collections.get(self.class_name)
            with collection.batch.dynamic() as batch:
                for ticket, embedding in zip(tickets, embeddings):
                    batch.add_object(
                        properties={
                            "tweet_id": ticket["tweet_id"],
                            "text": ticket["text"],
                            "author_id": ticket.get("author_id", ""),
                            "created_at": ticket.get("created_at", ""),
                            "label": ticket.get("label", ""),
                            "is_urgent": ticket.get("is_urgent", False),
                            "features": ticket.get("features", {}),
                            "inbound": ticket.get("inbound", True),
                        },
                        vector=embedding.tolist()
                    )
            logger.info(f"Added {len(tickets)} tickets in batch")
            return True
        except Exception as e:
            logger.error(f"Failed to add tickets batch: {e}")
            return False

    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5):
        """Search for similar tickets"""
        try:
            collection = self.client.collections.get(self.class_name)
            results = collection.query.near_vector(
                near_vector=query_embedding.tolist(),
                limit=top_k,
                return_metadata=MetadataQuery(distance=True),
                return_properties=["tweet_id", "text", "label", "is_urgent", "features"]
            )

            tickets = []
            for obj in results.objects:
                ticket = {
                    "tweet_id": obj.properties.get("tweet_id", ""),
                    "text": obj.properties.get("text", ""),
                    "label": obj.properties.get("label", ""),
                    "is_urgent": obj.properties.get("is_urgent", False),
                    "features": obj.properties.get("features", {}),
                    "similarity": 1 - obj.metadata.distance  # cosine distance to similarity
                }
                tickets.append(ticket)

            logger.info(f"Retrieved {len(tickets)} similar tickets")
            return tickets
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_all_tickets(self):
        """Get all tickets (for debugging/analysis)"""
        try:
            collection = self.client.collections.get(self.class_name)
            results = collection.query.fetch_objects(
                limit=10000,
                return_properties=["tweet_id", "text", "label", "is_urgent"]
            )
            return [obj.properties for obj in results.objects]
        except Exception as e:
            logger.error(f"Failed to fetch tickets: {e}")
            return []

    def count_tickets(self):
        """Count total tickets in database"""
        try:
            collection = self.client.collections.get(self.class_name)
            return collection.aggregate.over_all(total_count=True).total_count
        except Exception as e:
            logger.error(f"Failed to count tickets: {e}")
            return 0

    def delete_ticket(self, tweet_id: str):
        """Delete a ticket by ID"""
        try:
            collection = self.client.collections.get(self.class_name)
            collection.data.delete_by_id(tweet_id)
            logger.info(f"Deleted ticket: {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete ticket: {e}")
            return False

    def clear_all(self):
        """Clear all data"""
        try:
            if self.client.collections.exists(self.class_name):
                self.client.collections.delete(self.class_name)
                logger.info(f"Cleared collection: {self.class_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False

    def disconnect(self):
        """Close connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Weaviate")

# Global client instance
weaviate_client = WeaviateClient()
