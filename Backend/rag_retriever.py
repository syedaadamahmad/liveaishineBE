# """
# RAG Retriever
# Performs semantic search with metadata filtering and context ranking.
# """
# import logging
# from typing import List, Dict, Any, Optional
# from Backend.embedding_client import BedrockEmbeddingClient
# from Backend.mongodb_client import MongoDBClient

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class RAGRetriever:
#     """Semantic retrieval with metadata filtering and ranking."""
    
#     def __init__(self):
#         self.embedding_client = BedrockEmbeddingClient()
#         self.mongo_client = MongoDBClient()
#         self.similarity_threshold = 0.65  # ✅ LOWERED from 0.75 for better recall
#         self.max_results = 5
    
#     def retrieve(
#         self,
#         query: str,
#         metadata_filters: Optional[Dict[str, Any]] = None
#     ) -> Dict[str, Any]:
#         """
#         Retrieve relevant context for a query.
        
#         Args:
#             query: User query string
#             metadata_filters: Optional filters (e.g., {"module_name": "module1_kb"})
        
#         Returns:
#             Dict with 'chunks', 'provenance', 'score_threshold_met'
#         """
#         try:
#             logger.info(f"[RETRIEVE] Query: {query}")
#             query_embedding = self.embedding_client.generate_embedding(query)
            
#             if not query_embedding:
#                 logger.error("[RETRIEVE_ERR] Failed to generate query embedding")
#                 return {
#                     "chunks": [],
#                     "provenance": [],
#                     "score_threshold_met": False
#                 }
            
#             results = self.mongo_client.vector_search(
#                 query_embedding=query_embedding,
#                 limit=self.max_results,
#                 similarity_threshold=self.similarity_threshold,
#                 metadata_filters=metadata_filters
#             )
            
#             if not results:
#                 logger.warning(f"[RETRIEVE] No results above threshold {self.similarity_threshold}")
#                 return {
#                     "chunks": [],
#                     "provenance": [],
#                     "score_threshold_met": False
#                 }
            
#             chunks = []
#             provenance = []
            
#             for idx, doc in enumerate(results):
#                 # ✅ CRITICAL FIX: Use full 'content' field if available
#                 content = doc.get('content', '') or doc.get('summary', '')
                
#                 if not content:
#                     logger.warning(f"[RETRIEVE] Document {idx+1} has no content or summary")
#                     continue
                
#                 # Format chunk with rich context
#                 chunk_text = f"Topic: {doc.get('topic', 'N/A')}\n"
#                 chunk_text += f"Category: {doc.get('category', 'N/A')}\n"
#                 chunk_text += f"Level: {doc.get('level', 'N/A')}\n\n"
#                 chunk_text += f"Content:\n{content}"
                
#                 chunks.append(chunk_text)
#                 provenance.append({
#                     "doc_id": str(doc.get('_id', '')),
#                     "topic": doc.get('topic', 'N/A'),
#                     "score": round(doc.get('score', 0.0), 3),
#                     "module": doc.get('module_name', 'N/A')
#                 })
            
#             logger.info(f"[RETRIEVE_OK] Retrieved {len(chunks)} chunks")
#             logger.info(f"[RETRIEVE_DEBUG] Scores: {[p['score'] for p in provenance]}")
#             logger.info(f"[RETRIEVE_DEBUG] Topics: {[p['topic'] for p in provenance]}")
            
#             return {
#                 "chunks": chunks,
#                 "provenance": provenance,
#                 "score_threshold_met": True
#             }
            
#         except Exception as e:
#             logger.error(f"[RETRIEVE_ERR] {e}", exc_info=True)
#             return {
#                 "chunks": [],
#                 "provenance": [],
#                 "score_threshold_met": False
#             }





































# """
# RAG Retriever
# Performs semantic search with presentation-aware prioritization and keyword filtering.
# """
# import logging
# from typing import List, Dict, Any, Optional
# from Backend.embedding_client import BedrockEmbeddingClient
# from Backend.mongodb_client import MongoDBClient

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class RAGRetriever:
#     """Semantic retrieval with presentation awareness and KB filtering."""
    
#     def __init__(self):
#         self.embedding_client = BedrockEmbeddingClient()
#         self.mongo_client = MongoDBClient()
#         self.similarity_threshold = 0.65
#         self.max_results = 5
    
#     def retrieve(
#         self,
#         query: str,
#         metadata_filters: Optional[Dict[str, Any]] = None,
#         presentation_keywords: Optional[List[str]] = None
#     ) -> Dict[str, Any]:
#         """
#         Retrieve relevant context with presentation-aware logic.
        
#         Args:
#             query: User query string
#             metadata_filters: Optional filters
#             presentation_keywords: If provided, filter KB results by these keywords
        
#         Returns:
#             Dict with 'chunks', 'provenance', 'score_threshold_met', 'is_presentation'
#         """
#         try:
#             logger.info(f"[RETRIEVE] Query: {query}")
#             query_embedding = self.embedding_client.generate_embedding(query)
            
#             if not query_embedding:
#                 logger.error("[RETRIEVE_ERR] Failed to generate query embedding")
#                 return self._empty_result()
            
#             # First, try to find presentation match
#             presentation_results = self.mongo_client.vector_search(
#                 query_embedding=query_embedding,
#                 limit=2,
#                 similarity_threshold=0.70,  # Higher threshold for presentation
#                 metadata_filters={"source": "presentation"}
#             )
            
#             # If strong presentation match found
#             if presentation_results and presentation_results[0].get('score', 0) >= 0.75:
#                 logger.info(f"[RETRIEVE] Strong presentation match: {presentation_results[0].get('topic')}")
#                 return self._format_results(presentation_results[:1], is_presentation=True)
            
#             # Otherwise, search knowledge base
#             kb_filters = metadata_filters or {}
#             kb_filters["source"] = "knowledge_base"
            
#             # If presentation_keywords provided, add keyword filtering
#             if presentation_keywords:
#                 logger.info(f"[RETRIEVE] Filtering KB by presentation keywords: {presentation_keywords[:3]}...")
#                 kb_results = self._search_with_keyword_filter(
#                     query_embedding,
#                     presentation_keywords,
#                     kb_filters
#                 )
#             else:
#                 kb_results = self.mongo_client.vector_search(
#                     query_embedding=query_embedding,
#                     limit=self.max_results,
#                     similarity_threshold=self.similarity_threshold,
#                     metadata_filters=kb_filters
#                 )
            
#             if not kb_results:
#                 logger.warning(f"[RETRIEVE] No KB results above threshold {self.similarity_threshold}")
#                 return self._empty_result()
            
#             return self._format_results(kb_results, is_presentation=False)
            
#         except Exception as e:
#             logger.error(f"[RETRIEVE_ERR] {e}", exc_info=True)
#             return self._empty_result()
    
#     def _search_with_keyword_filter(
#         self,
#         query_embedding: List[float],
#         keywords: List[str],
#         base_filters: Dict[str, Any]
#     ) -> List[Dict[str, Any]]:
#         """
#         Search KB with keyword filtering for presentation-guided retrieval.
#         Uses semantic similarity as fallback if keyword match fails.
#         """
#         # Try keyword match first
#         keyword_filter = base_filters.copy()
#         keyword_filter["keywords"] = {"$in": keywords}
        
#         results = self.mongo_client.vector_search(
#             query_embedding=query_embedding,
#             limit=self.max_results,
#             similarity_threshold=self.similarity_threshold,
#             metadata_filters=keyword_filter
#         )
        
#         if results:
#             logger.info(f"[RETRIEVE] Found {len(results)} results with keyword matching")
#             return results
        
#         # Fallback: semantic search only
#         logger.info("[RETRIEVE] No keyword match, falling back to semantic search")
#         return self.mongo_client.vector_search(
#             query_embedding=query_embedding,
#             limit=self.max_results,
#             similarity_threshold=self.similarity_threshold,
#             metadata_filters=base_filters
#         )
    
#     def _format_results(self, results: List[Dict[str, Any]], is_presentation: bool) -> Dict[str, Any]:
#         """Format retrieval results into standard structure."""
#         chunks = []
#         provenance = []
        
#         for idx, doc in enumerate(results):
#             # Handle presentation documents
#             if is_presentation:
#                 presentation_data = doc.get('presentation_data', {})
#                 chunk_text = self._format_presentation_chunk(doc, presentation_data)
#             else:
#                 # Use full content if available, else summary
#                 content = doc.get('content', '') or doc.get('summary', '')
#                 chunk_text = f"Topic: {doc.get('topic', 'N/A')}\n"
#                 chunk_text += f"Category: {doc.get('category', 'N/A')}\n"
#                 chunk_text += f"Level: {doc.get('level', 'N/A')}\n\n"
#                 chunk_text += f"Content:\n{content}"
            
#             chunks.append(chunk_text)
#             provenance.append({
#                 "doc_id": str(doc.get('_id', '')),
#                 "topic": doc.get('topic', 'N/A'),
#                 "score": round(doc.get('score', 0.0), 3),
#                 "source": doc.get('source', 'N/A')
#             })
        
#         logger.info(f"[RETRIEVE_OK] Retrieved {len(chunks)} chunks (Presentation: {is_presentation})")
#         logger.info(f"[RETRIEVE_DEBUG] Scores: {[p['score'] for p in provenance]}")
        
#         return {
#             "chunks": chunks,
#             "provenance": provenance,
#             "score_threshold_met": True,
#             "is_presentation": is_presentation
#         }
    
#     def _format_presentation_chunk(self, doc: Dict[str, Any], data: Dict[str, Any]) -> str:
#         """Format presentation data into readable chunk."""
#         parts = [f"Topic: {doc.get('topic', 'N/A')}", "Category: Workshop Presentation", ""]
        
#         if 'intro' in data:
#             parts.append(f"Introduction: {data['intro']}")
        
#         if 'features' in data:
#             parts.append("\nKey Features:")
#             for feature in data['features']:
#                 parts.append(f"- {feature['title']}: {feature['description']}")
        
#         if 'activities' in data:
#             parts.append("\nActivities:")
#             for activity in data['activities']:
#                 parts.append(f"- {activity.get('title', '')}: {activity.get('description', '')}")
        
#         if 'careers' in data:
#             parts.append("\nCareer Opportunities:")
#             for career in data['careers'][:3]:  # Limit to first 3
#                 parts.append(f"- {career['title']}: {career['description']}")
        
#         return "\n".join(parts)
    
#     def _empty_result(self) -> Dict[str, Any]:
#         """Return empty result structure."""
#         return {
#             "chunks": [],
#             "provenance": [],
#             "score_threshold_met": False,
#             "is_presentation": False
#         }





































"""
RAG Retriever
Performs semantic search with presentation-aware prioritization and keyword filtering.
FIXED: Always searches both collections, returns best match.
"""
import logging
from typing import List, Dict, Any, Optional
from Backend.embedding_client import BedrockEmbeddingClient
from Backend.mongodb_client import MongoDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGRetriever:
    """Semantic retrieval with presentation awareness and KB filtering."""
    
    def __init__(self):
        self.embedding_client = BedrockEmbeddingClient()
        self.mongo_client = MongoDBClient()
        self.similarity_threshold = 0.55
        self.max_results = 5
    
    def retrieve(
        self,
        query: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        presentation_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context with presentation-aware logic.
        CRITICAL FIX: Always searches BOTH collections, returns best match.
        
        Args:
            query: User query string
            metadata_filters: Optional filters
            presentation_keywords: If provided, filter KB results by these keywords
        
        Returns:
            Dict with 'chunks', 'provenance', 'score_threshold_met', 'is_presentation'
        """
        try:
            logger.info(f"[RETRIEVE] Query: {query}")
            query_embedding = self.embedding_client.generate_embedding(query)
            
            if not query_embedding:
                logger.error("[RETRIEVE_ERR] Failed to generate query embedding")
                return self._empty_result()
            
            # Step 1: Search presentation collection
            presentation_results = self.mongo_client.vector_search(
                query_embedding=query_embedding,
                limit=2,
                similarity_threshold=0.70,  # Higher threshold for presentation
                metadata_filters={"source": "presentation"}
            )
            
            # Step 2: Search knowledge base collection
            kb_filters = metadata_filters or {}
            kb_filters["source"] = "knowledge_base"
            
            # If presentation_keywords provided, add keyword filtering
            if presentation_keywords:
                logger.info(f"[RETRIEVE] Filtering KB by presentation keywords: {presentation_keywords[:3]}...")
                kb_results = self._search_with_keyword_filter(
                    query_embedding,
                    presentation_keywords,
                    kb_filters
                )
            else:
                kb_results = self.mongo_client.vector_search(
                    query_embedding=query_embedding,
                    limit=self.max_results,
                    similarity_threshold=self.similarity_threshold,
                    metadata_filters=kb_filters
                )
            
            # Step 3: Decision logic - return best match
            pres_score = presentation_results[0].get('score', 0) if presentation_results else 0
            kb_score = kb_results[0].get('score', 0) if kb_results else 0
            
            logger.info(f"[RETRIEVE] Scores - Presentation: {pres_score:.3f}, KB: {kb_score:.3f}")
            
            # If presentation score is very strong (>0.80), use it exclusively
            if pres_score > 0.80:
                logger.info(f"[RETRIEVE] ✅ Strong presentation match: {presentation_results[0].get('topic')}")
                return self._format_results(presentation_results[:1], is_presentation=True)
            
            # Otherwise, use whichever has better score
            if kb_score >= pres_score and kb_results:
                logger.info(f"[RETRIEVE] ✅ KB match wins: {kb_results[0].get('topic')} (score: {kb_score:.3f})")
                # Return top 3 KB results for richer context
                return self._format_results(kb_results[:3], is_presentation=False)
            elif presentation_results:
                logger.info(f"[RETRIEVE] ✅ Presentation match: {presentation_results[0].get('topic')} (score: {pres_score:.3f})")
                return self._format_results(presentation_results[:1], is_presentation=True)
            else:
                logger.warning(f"[RETRIEVE] ❌ No results above threshold {self.similarity_threshold}")
                return self._empty_result()
            
        except Exception as e:
            logger.error(f"[RETRIEVE_ERR] {e}", exc_info=True)
            return self._empty_result()
    
    def _search_with_keyword_filter(
        self,
        query_embedding: List[float],
        keywords: List[str],
        base_filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search KB with keyword filtering for presentation-guided retrieval.
        Uses semantic similarity as fallback if keyword match fails.
        """
        # Try keyword match first
        keyword_filter = base_filters.copy()
        keyword_filter["keywords"] = {"$in": keywords}
        
        results = self.mongo_client.vector_search(
            query_embedding=query_embedding,
            limit=self.max_results,
            similarity_threshold=self.similarity_threshold,
            metadata_filters=keyword_filter
        )
        
        if results:
            logger.info(f"[RETRIEVE] Found {len(results)} results with keyword matching")
            return results
        
        # Fallback: semantic search only
        logger.info("[RETRIEVE] No keyword match, falling back to semantic search")
        return self.mongo_client.vector_search(
            query_embedding=query_embedding,
            limit=self.max_results,
            similarity_threshold=self.similarity_threshold,
            metadata_filters=base_filters
        )
    
    def _format_results(self, results: List[Dict[str, Any]], is_presentation: bool) -> Dict[str, Any]:
        """Format retrieval results into standard structure."""
        chunks = []
        provenance = []
        
        for idx, doc in enumerate(results):
            # Handle presentation documents
            if is_presentation:
                presentation_data = doc.get('presentation_data', {})
                chunk_text = self._format_presentation_chunk(doc, presentation_data)
            else:
                # Use full content if available, else summary
                content = doc.get('content', '') or doc.get('summary', '')
                chunk_text = f"Topic: {doc.get('topic', 'N/A')}\n"
                chunk_text += f"Category: {doc.get('category', 'N/A')}\n"
                chunk_text += f"Level: {doc.get('level', 'N/A')}\n\n"
                chunk_text += f"Content:\n{content}"
            
            chunks.append(chunk_text)
            provenance.append({
                "doc_id": str(doc.get('_id', '')),
                "topic": doc.get('topic', 'N/A'),
                "score": round(doc.get('score', 0.0), 3),
                "source": doc.get('source', 'N/A')
            })
        
        logger.info(f"[RETRIEVE_OK] Retrieved {len(chunks)} chunks (Presentation: {is_presentation})")
        logger.info(f"[RETRIEVE_DEBUG] Scores: {[p['score'] for p in provenance]}")
        
        return {
            "chunks": chunks,
            "provenance": provenance,
            "score_threshold_met": True,
            "is_presentation": is_presentation
        }
    
    def _format_presentation_chunk(self, doc: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Format presentation data into readable chunk."""
        parts = [f"Topic: {doc.get('topic', 'N/A')}", "Category: Workshop Presentation", ""]
        
        if 'intro' in data:
            parts.append(f"Introduction: {data['intro']}")
        
        if 'features' in data:
            parts.append("\nKey Features:")
            for feature in data['features']:
                parts.append(f"- {feature['title']}: {feature['description']}")
        
        if 'activities' in data:
            parts.append("\nActivities:")
            for activity in data['activities']:
                parts.append(f"- {activity.get('title', '')}: {activity.get('description', '')}")
        
        if 'careers' in data:
            parts.append("\nCareer Opportunities:")
            for career in data['careers'][:3]:  # Limit to first 3
                parts.append(f"- {career['title']}: {career['description']}")
        
        return "\n".join(parts)
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            "chunks": [],
            "provenance": [],
            "score_threshold_met": False,
            "is_presentation": False
        }







































# """
# RAG Retriever
# Performs semantic search with presentation-aware prioritization and keyword filtering.
# FIXED: Shows ALL careers (not just 3) and supports forced KB search for continuations.
# """
# import logging
# from typing import List, Dict, Any, Optional
# from Backend.embedding_client import BedrockEmbeddingClient
# from Backend.mongodb_client import MongoDBClient

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class RAGRetriever:
#     """Semantic retrieval with presentation awareness and KB filtering."""
    
#     def __init__(self):
#         self.embedding_client = BedrockEmbeddingClient()
#         self.mongo_client = MongoDBClient()
#         self.similarity_threshold = 0.55
#         self.max_results = 5
    
#     def retrieve(
#         self,
#         query: str,
#         metadata_filters: Optional[Dict[str, Any]] = None,
#         presentation_keywords: Optional[List[str]] = None,
#         force_kb_search: bool = False
#     ) -> Dict[str, Any]:
#         """
#         Retrieve relevant context with presentation-aware logic.
#         CRITICAL FIX: Always searches BOTH collections, returns best match.
        
#         Args:
#             query: User query string
#             metadata_filters: Optional filters
#             presentation_keywords: If provided, filter KB results by these keywords
#             force_kb_search: If True, prioritize KB results (for continuation queries)
        
#         Returns:
#             Dict with 'chunks', 'provenance', 'score_threshold_met', 'is_presentation'
#         """
#         try:
#             logger.info(f"[RETRIEVE] Query: {query}, Force KB: {force_kb_search}")
#             query_embedding = self.embedding_client.generate_embedding(query)
            
#             if not query_embedding:
#                 logger.error("[RETRIEVE_ERR] Failed to generate query embedding")
#                 return self._empty_result()
            
#             # Step 1: Search presentation collection
#             presentation_results = self.mongo_client.vector_search(
#                 query_embedding=query_embedding,
#                 limit=2,
#                 similarity_threshold=0.70,  # Higher threshold for presentation
#                 metadata_filters={"source": "presentation"}
#             )
            
#             # Step 2: Search knowledge base collection
#             kb_filters = metadata_filters or {}
#             kb_filters["source"] = "knowledge_base"
            
#             # If presentation_keywords provided, add keyword filtering
#             if presentation_keywords:
#                 logger.info(f"[RETRIEVE] Filtering KB by presentation keywords: {presentation_keywords[:3]}...")
#                 kb_results = self._search_with_keyword_filter(
#                     query_embedding,
#                     presentation_keywords,
#                     kb_filters
#                 )
#             else:
#                 kb_results = self.mongo_client.vector_search(
#                     query_embedding=query_embedding,
#                     limit=self.max_results,
#                     similarity_threshold=self.similarity_threshold,
#                     metadata_filters=kb_filters
#                 )
            
#             # Step 3: Decision logic - return best match
#             pres_score = presentation_results[0].get('score', 0) if presentation_results else 0
#             kb_score = kb_results[0].get('score', 0) if kb_results else 0
            
#             logger.info(f"[RETRIEVE] Scores - Presentation: {pres_score:.3f}, KB: {kb_score:.3f}")
            
#             # CRITICAL FIX: If force_kb_search, prioritize KB even if presentation score is higher
#             if force_kb_search and kb_results:
#                 logger.info(f"[RETRIEVE] ✅ Forced KB search for continuation: {kb_results[0].get('topic')} (score: {kb_score:.3f})")
#                 return self._format_results(kb_results[:3], is_presentation=False)
            
#             # If presentation score is very strong (>0.80), use it exclusively
#             if pres_score > 0.80:
#                 logger.info(f"[RETRIEVE] ✅ Strong presentation match: {presentation_results[0].get('topic')}")
#                 return self._format_results(presentation_results[:1], is_presentation=True)
            
#             # Otherwise, use whichever has better score
#             if kb_score >= pres_score and kb_results:
#                 logger.info(f"[RETRIEVE] ✅ KB match wins: {kb_results[0].get('topic')} (score: {kb_score:.3f})")
#                 # Return top 3 KB results for richer context
#                 return self._format_results(kb_results[:3], is_presentation=False)
#             elif presentation_results:
#                 logger.info(f"[RETRIEVE] ✅ Presentation match: {presentation_results[0].get('topic')} (score: {pres_score:.3f})")
#                 return self._format_results(presentation_results[:1], is_presentation=True)
#             else:
#                 logger.warning(f"[RETRIEVE] ❌ No results above threshold {self.similarity_threshold}")
#                 return self._empty_result()
            
#         except Exception as e:
#             logger.error(f"[RETRIEVE_ERR] {e}", exc_info=True)
#             return self._empty_result()
    
#     def _search_with_keyword_filter(
#         self,
#         query_embedding: List[float],
#         keywords: List[str],
#         base_filters: Dict[str, Any]
#     ) -> List[Dict[str, Any]]:
#         """
#         Search KB with keyword filtering for presentation-guided retrieval.
#         Uses semantic similarity as fallback if keyword match fails.
#         """
#         # Try keyword match first
#         keyword_filter = base_filters.copy()
#         keyword_filter["keywords"] = {"$in": keywords}
        
#         results = self.mongo_client.vector_search(
#             query_embedding=query_embedding,
#             limit=self.max_results,
#             similarity_threshold=self.similarity_threshold,
#             metadata_filters=keyword_filter
#         )
        
#         if results:
#             logger.info(f"[RETRIEVE] Found {len(results)} results with keyword matching")
#             return results
        
#         # Fallback: semantic search only
#         logger.info("[RETRIEVE] No keyword match, falling back to semantic search")
#         return self.mongo_client.vector_search(
#             query_embedding=query_embedding,
#             limit=self.max_results,
#             similarity_threshold=self.similarity_threshold,
#             metadata_filters=base_filters
#         )
    
#     def _format_results(self, results: List[Dict[str, Any]], is_presentation: bool) -> Dict[str, Any]:
#         """Format retrieval results into standard structure."""
#         chunks = []
#         provenance = []
        
#         for idx, doc in enumerate(results):
#             # Handle presentation documents
#             if is_presentation:
#                 presentation_data = doc.get('presentation_data', {})
#                 chunk_text = self._format_presentation_chunk(doc, presentation_data)
#             else:
#                 # Use full content if available, else summary
#                 content = doc.get('content', '') or doc.get('summary', '')
#                 chunk_text = f"Topic: {doc.get('topic', 'N/A')}\n"
#                 chunk_text += f"Category: {doc.get('category', 'N/A')}\n"
#                 chunk_text += f"Level: {doc.get('level', 'N/A')}\n\n"
#                 chunk_text += f"Content:\n{content}"
            
#             chunks.append(chunk_text)
#             provenance.append({
#                 "doc_id": str(doc.get('_id', '')),
#                 "topic": doc.get('topic', 'N/A'),
#                 "score": round(doc.get('score', 0.0), 3),
#                 "source": doc.get('source', 'N/A')
#             })
        
#         logger.info(f"[RETRIEVE_OK] Retrieved {len(chunks)} chunks (Presentation: {is_presentation})")
#         logger.info(f"[RETRIEVE_DEBUG] Scores: {[p['score'] for p in provenance]}")
        
#         return {
#             "chunks": chunks,
#             "provenance": provenance,
#             "score_threshold_met": True,
#             "is_presentation": is_presentation
#         }
    
#     def _format_presentation_chunk(self, doc: Dict[str, Any], data: Dict[str, Any]) -> str:
#         """
#         Format presentation data into readable chunk.
#         CRITICAL FIX: Shows ALL careers, not just first 3.
#         """
#         parts = [f"Topic: {doc.get('topic', 'N/A')}", "Category: Workshop Presentation", ""]
        
#         if 'intro' in data:
#             parts.append(f"Introduction: {data['intro']}")
        
#         if 'features' in data:
#             parts.append("\nKey Features:")
#             for feature in data['features']:
#                 parts.append(f"- {feature['title']}: {feature['description']}")
        
#         if 'activities' in data:
#             parts.append("\nActivities:")
#             for activity in data['activities']:
#                 parts.append(f"- {activity.get('title', '')}: {activity.get('description', '')}")
        
#         if 'careers' in data:
#             parts.append("\nCareer Opportunities:")
#             # CRITICAL FIX: Show ALL careers, not just [:3]
#             for career in data['careers']:  # ← REMOVED [:3] LIMIT
#                 parts.append(f"- {career['title']}: {career['description']}")
#                 if 'example' in career:
#                     parts.append(f"  Example: {career['example']}")
        
#         return "\n".join(parts)
    
#     def _empty_result(self) -> Dict[str, Any]:
#         """Return empty result structure."""
#         return {
#             "chunks": [],
#             "provenance": [],
#             "score_threshold_met": False,
#             "is_presentation": False
#         }