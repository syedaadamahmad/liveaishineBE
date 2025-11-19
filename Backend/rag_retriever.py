"""
RAG Retriever
Performs semantic search with presentation-aware prioritization and keyword filtering.
COMPLETE VERSION - Every line included, nothing omitted.
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
        """Initialize retriever with embedding client and MongoDB connection."""
        self.embedding_client = BedrockEmbeddingClient()
        self.mongo_client = MongoDBClient()
        self.similarity_threshold = 0.55  # Lowered from 0.65 for better recall
        self.max_results = 5
        logger.info(f"[RAG_RETRIEVER] Initialized with threshold={self.similarity_threshold}")
    
    def retrieve(
        self,
        query: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        presentation_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context with presentation-aware logic.
        CRITICAL FIX: Always searches BOTH collections, returns best match.
        Allows free topic switching between presentation and KB.
        
        Args:
            query: User query string
            metadata_filters: Optional filters (e.g., {"module_name": "module1_kb"})
            presentation_keywords: If provided, filter KB results by these keywords (optional)
        
        Returns:
            Dict with:
                - chunks: List[str] - Retrieved text chunks
                - provenance: List[Dict] - Source metadata with scores
                - score_threshold_met: bool - Whether threshold was met
                - is_presentation: bool - Whether result is from presentation
        """
        try:
            logger.info(f"[RETRIEVE] Query: {query}")
            
            # Generate query embedding using AWS Bedrock
            query_embedding = self.embedding_client.generate_embedding(query)
            
            if not query_embedding:
                logger.error("[RETRIEVE_ERR] Failed to generate query embedding")
                return self._empty_result()
            
            # Step 1: Search presentation collection with higher threshold
            logger.info("[RETRIEVE] Step 1: Searching presentation collection")
            presentation_results = self.mongo_client.vector_search(
                query_embedding=query_embedding,
                limit=2,  # Only get top 2 presentation matches
                similarity_threshold=0.70,  # Higher threshold for presentation
                metadata_filters={"source": "presentation"}
            )
            
            # Step 2: Search knowledge base collection
            logger.info("[RETRIEVE] Step 2: Searching knowledge base collection")
            kb_filters = metadata_filters or {}
            kb_filters["source"] = "knowledge_base"
            
            # If presentation_keywords provided, add keyword filtering (for continuations)
            if presentation_keywords:
                logger.info(f"[RETRIEVE] Filtering KB by presentation keywords: {presentation_keywords[:3]}...")
                kb_results = self._search_with_keyword_filter(
                    query_embedding,
                    presentation_keywords,
                    kb_filters
                )
            else:
                # Standard semantic search
                kb_results = self.mongo_client.vector_search(
                    query_embedding=query_embedding,
                    limit=self.max_results,
                    similarity_threshold=self.similarity_threshold,
                    metadata_filters=kb_filters
                )
            
            # Step 3: Decision logic - best match wins, allows free topic switching
            pres_score = presentation_results[0].get('score', 0) if presentation_results else 0
            kb_score = kb_results[0].get('score', 0) if kb_results else 0
            
            logger.info(f"[RETRIEVE] Scores - Presentation: {pres_score:.3f}, KB: {kb_score:.3f}")
            
            # Decision tree:
            # 1. Very strong presentation match (>0.80) → Use presentation exclusively
            if pres_score > 0.80:
                logger.info(f"[RETRIEVE] ✅ Strong presentation match: {presentation_results[0].get('topic')}")
                return self._format_results(presentation_results[:1], is_presentation=True)
            
            # 2. KB has better or equal score → Use KB (allows topic switching)
            if kb_score >= pres_score and kb_results:
                logger.info(f"[RETRIEVE] ✅ KB match wins: {kb_results[0].get('topic')} (score: {kb_score:.3f})")
                # Return top 3 KB results for richer context
                return self._format_results(kb_results[:3], is_presentation=False)
            
            # 3. Presentation has better score but not strong enough for exclusive
            elif presentation_results:
                logger.info(f"[RETRIEVE] ✅ Presentation match: {presentation_results[0].get('topic')} (score: {pres_score:.3f})")
                return self._format_results(presentation_results[:1], is_presentation=True)
            
            # 4. No results above threshold
            else:
                logger.warning(f"[RETRIEVE] ❌ No results above threshold {self.similarity_threshold}")
                return self._empty_result()
            
        except Exception as e:
            logger.error(f"[RETRIEVE_ERR] Unexpected error: {e}", exc_info=True)
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
        
        Args:
            query_embedding: Query embedding vector
            keywords: Keywords to filter by
            base_filters: Base metadata filters
        
        Returns:
            List of matching documents
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
        
        # Fallback: semantic search only (no keyword filter)
        logger.info("[RETRIEVE] No keyword match, falling back to semantic search")
        return self.mongo_client.vector_search(
            query_embedding=query_embedding,
            limit=self.max_results,
            similarity_threshold=self.similarity_threshold,
            metadata_filters=base_filters
        )
    
    def _format_results(
        self,
        results: List[Dict[str, Any]],
        is_presentation: bool
    ) -> Dict[str, Any]:
        """
        Format retrieval results into standard structure.
        
        Args:
            results: List of MongoDB documents
            is_presentation: Whether results are from presentation collection
        
        Returns:
            Formatted result dict with chunks and provenance
        """
        chunks = []
        provenance = []
        
        for idx, doc in enumerate(results):
            # Handle presentation documents
            if is_presentation:
                presentation_data = doc.get('presentation_data', {})
                chunk_text = self._format_presentation_chunk(doc, presentation_data)
            else:
                # Handle KB documents - use full content if available, else summary
                content = doc.get('content', '') or doc.get('summary', '')
                
                if not content:
                    logger.warning(f"[RETRIEVE] Document {idx+1} has no content or summary")
                    continue
                
                # Format KB chunk with metadata
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
        logger.info(f"[RETRIEVE_DEBUG] Topics: {[p['topic'] for p in provenance]}")
        
        return {
            "chunks": chunks,
            "provenance": provenance,
            "score_threshold_met": True,
            "is_presentation": is_presentation
        }
    
    def _format_presentation_chunk(
        self,
        doc: Dict[str, Any],
        data: Dict[str, Any]
    ) -> str:
        """
        Format presentation data into readable chunk.
        
        Args:
            doc: MongoDB document
            data: presentation_data field from document
        
        Returns:
            Formatted string with presentation content
        """
        parts = [
            f"Topic: {doc.get('topic', 'N/A')}",
            "Category: Workshop Presentation",
            ""
        ]
        
        # Add introduction if present
        if 'intro' in data:
            parts.append(f"Introduction: {data['intro']}")
            parts.append("")
        
        # Add description if present
        if 'description' in data:
            parts.append(f"Description: {data['description']}")
            parts.append("")
        
        # Add key features
        if 'features' in data:
            parts.append("Key Features:")
            for feature in data['features']:
                title = feature.get('title', '')
                description = feature.get('description', '')
                if title and description:
                    parts.append(f"- {title}: {description}")
            parts.append("")
        
        # Add activities
        if 'activities' in data:
            parts.append("Activities:")
            for activity in data['activities']:
                title = activity.get('title', '')
                description = activity.get('description', '')
                if title and description:
                    parts.append(f"- {title}: {description}")
            parts.append("")
        
        # Add career opportunities (limit to first 3)
        if 'careers' in data:
            parts.append("Career Opportunities:")
            for career in data['careers']:  # ✅ REMOVED [:3] limit
                title = career.get('title', '')
                description = career.get('description', '')
                example = career.get('example', '')
                if title and description:
                    career_text = f"- {title}: {description}"
                    if example:
                        career_text += f" Example: {example}"
                    parts.append(career_text)
            parts.append("")
        
        # Add key benefits if present
        if 'keyBenefits' in data:
            parts.append("Key Benefits:")
            for benefit in data['keyBenefits']:
                parts.append(f"- {benefit}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _empty_result(self) -> Dict[str, Any]:
        """
        Return empty result structure when no results found.
        
        Returns:
            Empty result dict
        """
        return {
            "chunks": [],
            "provenance": [],
            "score_threshold_met": False,
            "is_presentation": False
        }
