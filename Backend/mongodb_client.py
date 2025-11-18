# """
# MongoDB Atlas Vector Search Client
# Handles connection pooling, vector search, and metadata filtering.
# """
# import os
# import logging
# from typing import List, Dict, Any, Optional
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure, OperationFailure
# from dotenv import load_dotenv

# # Force load .env
# load_dotenv(override=True)

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class MongoDBClient:
#     """MongoDB Atlas Vector Search client with connection pooling."""
    
#     def __init__(self):
#         # Explicit .env loading
#         load_dotenv(override=True)
        
#         self.uri = os.getenv("MONGO_DB_URI")
#         self.db_name = os.getenv("DB_NAME")
#         self.collection_name = "module_vectors"
        
#         # Validate required env vars
#         if not self.uri:
#             raise ValueError("[MONGO_ERR] MONGO_DB_URI not set in environment")
        
#         if not self.db_name:
#             raise ValueError("[MONGO_ERR] DB_NAME not set in environment")
        
#         logger.info(f"[MONGO_INIT] Connecting to database: {self.db_name}")
        
#         try:
#             self.client = MongoClient(
#                 self.uri,
#                 maxPoolSize=10,
#                 minPoolSize=2,
#                 serverSelectionTimeoutMS=5000,
#             )
#             self.client.admin.command('ping')
#             self.db = self.client[self.db_name]
#             self.collection = self.db[self.collection_name]
#             logger.info(f"[MONGO_OK] Connected to {self.db_name}.{self.collection_name}")
#         except ConnectionFailure as e:
#             logger.error(f"[MONGO_ERR] Connection failed: {e}")
#             raise
    
#     def vector_search(
#         self,
#         query_embedding: List[float],
#         limit: int = 5,
#         similarity_threshold: float = 0.65,
#         metadata_filters: Optional[Dict[str, Any]] = None
#     ) -> List[Dict[str, Any]]:
#         """
#         Perform vector similarity search with optional metadata filtering.
        
#         Args:
#             query_embedding: 1024-dim embedding vector
#             limit: Max results to return
#             similarity_threshold: Minimum cosine similarity score
#             metadata_filters: Optional dict of metadata filters
        
#         Returns:
#             List of documents with score >= threshold, sorted by relevance
#         """
#         try:
#             # Build aggregation pipeline
#             pipeline = [
#                 {
#                     "$vectorSearch": {
#                         "index": "vector_index",
#                         "path": "embedding",
#                         "queryVector": query_embedding,
#                         "numCandidates": limit * 20,
#                         "limit": limit
#                     }
#                 },
#                 {
#                     "$addFields": {
#                         "score": {"$meta": "vectorSearchScore"}
#                     }
#                 },
#                 {
#                     "$match": {
#                         "score": {"$gte": similarity_threshold}
#                     }
#                 }
#             ]
            
#             # Add metadata filters if provided
#             if metadata_filters:
#                 pipeline.append({"$match": metadata_filters})
            
#             # Project fields
#             pipeline.append({
#                 "$project": {
#                     "_id": 1,
#                     "topic": 1,
#                     "category": 1,
#                     "level": 1,
#                     "summary": 1,
#                     "content": 1,
#                     "keywords": 1,
#                     "module_name": 1,
#                     "source": 1,
#                     "presentation_data": 1,
#                     "score": 1
#                 }
#             })
            
#             results = list(self.collection.aggregate(pipeline))
            
#             logger.info(f"[VECTOR_SEARCH] Retrieved {len(results)} chunks above threshold {similarity_threshold}")
#             if results:
#                 logger.info(f"[VECTOR_SEARCH_DEBUG] Top result: {results[0].get('topic', 'N/A')} (score: {results[0].get('score', 0)})")
#                 logger.info(f"[VECTOR_SEARCH_DEBUG] Source: {results[0].get('source', 'N/A')}")
            
#             return results
            
#         except OperationFailure as e:
#             logger.error(f"[VECTOR_SEARCH_ERR] {e}")
#             return []
#         except Exception as e:
#             logger.error(f"[VECTOR_SEARCH_ERR] Unexpected error: {e}", exc_info=True)
#             return []
    
#     def insert_documents(self, documents: List[Dict[str, Any]]) -> bool:
#         """Bulk insert documents with embeddings."""
#         try:
#             if not documents:
#                 logger.warning("[INSERT] No documents to insert")
#                 return False
            
#             result = self.collection.insert_many(documents, ordered=False)
#             logger.info(f"[INSERT_OK] Inserted {len(result.inserted_ids)} documents")
#             return True
            
#         except Exception as e:
#             logger.error(f"[INSERT_ERR] {e}")
#             return False
    
#     def close(self):
#         """Close MongoDB connection."""
#         if self.client:
#             self.client.close()
#             logger.info("[MONGO_CLOSE] Connection closed")




























"""
MongoDB Atlas Vector Search Client
Handles connection pooling, vector search, and metadata filtering.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Force load .env
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB Atlas Vector Search client with connection pooling."""
    
    def __init__(self):
        # Explicit .env loading
        load_dotenv(override=True)
        
        self.uri = os.getenv("MONGO_DB_URI")
        self.db_name = os.getenv("DB_NAME")
        self.collection_name = "module_vectors"
        
        # Validate required env vars
        if not self.uri:
            raise ValueError("[MONGO_ERR] MONGO_DB_URI not set in environment")
        
        if not self.db_name:
            raise ValueError("[MONGO_ERR] DB_NAME not set in environment")
        
        logger.info(f"[MONGO_INIT] Connecting to database: {self.db_name}")
        
        try:
            self.client = MongoClient(
                self.uri,
                maxPoolSize=10,
                minPoolSize=2,
                serverSelectionTimeoutMS=5000,
            )
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"[MONGO_OK] Connected to {self.db_name}.{self.collection_name}")
        except ConnectionFailure as e:
            logger.error(f"[MONGO_ERR] Connection failed: {e}")
            raise
    
    def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.65,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search with optional metadata filtering.
        
        Args:
            query_embedding: 1024-dim embedding vector
            limit: Max results to return
            similarity_threshold: Minimum cosine similarity score
            metadata_filters: Optional dict of metadata filters
        
        Returns:
            List of documents with score >= threshold, sorted by relevance
        """
        try:
            # Build aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 20,
                        "limit": limit
                    }
                },
                {
                    "$addFields": {
                        "score": {"$meta": "vectorSearchScore"}
                    }
                },
                {
                    "$match": {
                        "score": {"$gte": similarity_threshold}
                    }
                }
            ]
            
            # Add metadata filters if provided
            if metadata_filters:
                pipeline.append({"$match": metadata_filters})
            
            # Project fields
            pipeline.append({
                "$project": {
                    "_id": 1,
                    "topic": 1,
                    "category": 1,
                    "level": 1,
                    "summary": 1,
                    "content": 1,
                    "keywords": 1,
                    "module_name": 1,
                    "source": 1,
                    "presentation_data": 1,
                    "score": 1
                }
            })
            
            results = list(self.collection.aggregate(pipeline))
            
            logger.info(f"[VECTOR_SEARCH] Retrieved {len(results)} chunks above threshold {similarity_threshold}")
            if results:
                logger.info(f"[VECTOR_SEARCH_DEBUG] Top result: {results[0].get('topic', 'N/A')} (score: {results[0].get('score', 0)})")
                logger.info(f"[VECTOR_SEARCH_DEBUG] Source: {results[0].get('source', 'N/A')}")
            
            return results
            
        except OperationFailure as e:
            logger.error(f"[VECTOR_SEARCH_ERR] {e}")
            return []
        except Exception as e:
            logger.error(f"[VECTOR_SEARCH_ERR] Unexpected error: {e}", exc_info=True)
            return []
    
    def insert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk insert documents with embeddings."""
        try:
            if not documents:
                logger.warning("[INSERT] No documents to insert")
                return False
            
            result = self.collection.insert_many(documents, ordered=False)
            logger.info(f"[INSERT_OK] Inserted {len(result.inserted_ids)} documents")
            return True
            
        except Exception as e:
            logger.error(f"[INSERT_ERR] {e}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("[MONGO_CLOSE] Connection closed")