# GROK RAG_ENGINE
"""
RAG Engine - Core Orchestration
Integrates intent detection, retrieval, prompt construction, and LLM generation.
Now tracks presentation context for continuation queries.
"""
import logging
from typing import List, Dict, Any
import os
from Backend.models import Message
from Backend.rag_retriever import RAGRetriever
from Backend.prompt_builder import PromptBuilder
from Backend.llm_client import GeminiClient
from Backend.memory_manager import MemoryManager
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG orchestrator with presentation awareness and continuation tracking."""
    
    def __init__(self):
        """Initialize all RAG components."""
        try:
            self.retriever = RAGRetriever()
            self.prompt_builder = PromptBuilder()
            self.llm_client = GeminiClient()
            self.memory_manager = MemoryManager(short_term_window=3)
            
            # Track last presentation context for continuations
            self.last_presentation_keywords = None
            
            logger.info("[RAG_ENGINE] ✅ All components initialized")
        except Exception as e:
            logger.error(f"[RAG_ENGINE_ERR] Initialization failed: {e}")
            raise
    
    def process_query(
        self,
        query: str,
        chat_history: List[Message]
    ) -> Dict[str, Any]:
        """
        Main processing pipeline with presentation-aware logic.
        
        Args:
            query: Current user query
            chat_history: Full conversation history
        
        Returns:
            Dict with 'answer' (str) and 'type' (str)
        """
        try:
            # Step 1: Intent Detection (now integrated in PromptBuilder)
            logger.info(f"[RAG_ENGINE] Step 1: Intent Detection")
            intent = self.prompt_builder.detect_intent(query, chat_history)
            logger.info(f"[RAG_ENGINE] Intent: {intent['intent_type']}, Continuation: {intent['is_continuation']}")
            
            # Step 2: Handle Greeting
            if intent['is_greeting']:
                logger.info("[RAG_ENGINE] Greeting detected")
                self.last_presentation_keywords = None  # Reset context
                return {
                    "answer": self.prompt_builder.build_greeting_response(),
                    "type": "greeting"
                }
            
            # Step 2.5: Handle Farewell (new addition based on integrated intent)
            if intent.get('is_farewell', False):
                logger.info("[RAG_ENGINE] Farewell detected")
                self.last_presentation_keywords = None  # Reset context
                return {
                    "answer": self.prompt_builder.build_farewell_response(),
                    "type": "text"
                }
            
            # Step 3: Memory Management
            logger.info(f"[RAG_ENGINE] Step 2: Memory Management")
            short_term_history = self.memory_manager.get_short_term_context(chat_history)
            formatted_history = self.memory_manager.format_for_llm(
                short_term_history,
                is_continuation=intent['is_continuation']
            )
            
            if formatted_history:
                logger.info(f"[RAG_ENGINE] Passing {len(formatted_history)} messages to LLM")
            else:
                logger.info(f"[RAG_ENGINE] No history passed (saving tokens)")
            
            # Step 4: RAG Retrieval
            logger.info(f"[RAG_ENGINE] Step 3: RAG Retrieval")
            
            # If continuation and we have presentation context, use keyword filtering
            presentation_keywords = None
            if intent['is_continuation'] and self.last_presentation_keywords:
                logger.info("[RAG_ENGINE] Continuation detected - using presentation keywords for filtering")
                presentation_keywords = self.last_presentation_keywords
            
            retrieval_result = self.retriever.retrieve(
                query,
                presentation_keywords=presentation_keywords
            )
            
            has_context = retrieval_result["score_threshold_met"] and len(retrieval_result["chunks"]) > 0
            is_presentation = retrieval_result.get("is_presentation", False)
            
            logger.info(f"[RAG_ENGINE] Retrieved {len(retrieval_result['chunks'])} chunks, threshold met: {has_context}, presentation: {is_presentation}")
            
            # Update presentation context tracking
            if is_presentation and retrieval_result["provenance"]:
                # Extract keywords from presentation document for future continuations
                # (This would require fetching the full doc, simplified here)
                self.last_presentation_keywords = None  # Placeholder - implement if needed
            elif not intent['is_continuation']:
                # Reset if not continuation
                self.last_presentation_keywords = None
            
            # Step 5: Prompt Construction
            logger.info(f"[RAG_ENGINE] Step 4: Prompt Construction")
            system_prompt = self.prompt_builder.build_system_prompt(
                intent,
                has_context,
                is_presentation
            )
            user_prompt = self.prompt_builder.build_user_prompt(
                query=query,
                context_chunks=retrieval_result["chunks"],
                intent=intent,
                is_presentation=is_presentation
            )
            
            # Step 6: LLM Generation
            logger.info(f"[RAG_ENGINE] Step 5: LLM Generation")
            llm_response = self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                chat_history=formatted_history
            )
            
            if not llm_response["success"]:
                logger.error(f"[RAG_ENGINE_ERR] LLM generation failed: {llm_response['error']}")
                return {
                    "answer": "⚠️ I encountered an issue processing your question. Please try again.",
                    "type": "text"
                }
            
            raw_answer = llm_response["response"]
            raw_answer = self._validate_and_fix_response(raw_answer, has_context)
            
            # Step 7: Response Classification
            logger.info(f"[RAG_ENGINE] Step 6: Response Classification")
            response_type = self._classify_response(raw_answer, has_context, is_presentation)
            logger.info(f"[RAG_ENGINE] Response type: {response_type}")
            
            return {
                "answer": raw_answer,
                "type": response_type
            }
        
        except Exception as e:
            logger.error(f"[RAG_ENGINE_ERR] Pipeline failure: {e}", exc_info=True)
            return {
                "answer": "⚠️ An unexpected error occurred. Please try your question again.",
                "type": "text"
            }
    
    def _classify_response(self, response: str, has_context: bool, is_presentation: bool) -> str:
        """Classify response type for frontend rendering."""
        
        # Check for out-of-scope (starts with warning emoji OR contains specialization statement)
        if response.startswith("⚠") or "I specialize in AI and Machine Learning topics" in response:
            return "decline"
        
        # Check for "I don't have" (knowledge gaps)
        if "I don't have" in response or "I don't know" in response:
            return "decline"
        
        # Check for structured format (HTML or markdown)
        if ("<strong>Answer:</strong>" in response or "**Answer:**" in response) and \
        ("<strong>Key Points:</strong>" in response or "**Key Points:**" in response):
            return "structured"
        
        return "text"

    def _validate_and_fix_response(self, response: str, has_context: bool) -> str:
        """
        Validate response has proper structure, fix if needed.
        
        Args:
            response: Raw LLM response
            has_context: Whether query had context
        
        Returns:
            Fixed response with proper structure
        """
        # If no context (decline message), Key Points not required
        if not has_context:
            return response
        
        # Check if Key Points section exists
        if "<strong>Key Points:</strong>" in response:
            return response
        
        logger.warning("[RAG_ENGINE] Response missing Key Points section")
        
        # If missing Key Points, add basic structure
        if response.endswith("</p>"):
            response += "\n\n<strong>Key Points:</strong>\n<ul>\n"
            response += "<li><strong>Summary:</strong> Key concepts explained above</li>\n"
            response += "</ul>"
        
        return response
    
    def cleanup(self):
        """Close all persistent connections."""
        try:
            self.retriever.mongo_client.close()
            logger.info("[RAG_ENGINE] ✅ Cleanup complete")
        except Exception as e:
            logger.error(f"[RAG_ENGINE] Cleanup error: {e}")
