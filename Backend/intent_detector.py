"""
Intent Detector - Hybrid Regex + Semantic Fallback
Handles greetings and continuation via deterministic patterns.
Falls back to Gemini for ambiguous cases.
"""
import re
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentDetector:
    """Detects user intent patterns from chat messages."""
    
    # Continuation patterns
    CONTINUATION_PATTERNS = [
    r'\btell\s+me\s+more\b',
    r'\belaborate\b',
    r'\bgo\s+deeper\b',
    r'\bexpand\b',
    r'\bmore\s+detail',
    r'\bcontinue\b',
    r'\bkeep\s+going\b',
    r'\bwhat\s+else\b',
    r'\bexplain\s+further\b',
    r'\bgo\s+on\b',
    r'^\s*and\s*\??\s*$',  # "and?"
    r'^\s*more\s*\??\s*$',  # "more?"
    r'^\s*continue\s*\??\s*$',  # "continue?"
    r'\btell\s+me\s+about',
    r'\bgive\s+me\s+more',
    r'\bcan\s+you\s+elaborate'
    ]
    
    # Simple greeting detection via regex (keeps it fast)
    GREETING_PATTERNS = [
        r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo)\s*[!.,]?\s*$'
    ]
    
    def __init__(self, use_semantic_fallback: bool = False):
        """
        Initialize intent detector.
        
        Args:
            use_semantic_fallback: If True, uses Gemini for ambiguous cases (costs tokens)
        """
        self.continuation_regex = re.compile('|'.join(self.CONTINUATION_PATTERNS), re.IGNORECASE)
        self.greeting_regex = re.compile('|'.join(self.GREETING_PATTERNS), re.IGNORECASE)
        self.use_semantic_fallback = use_semantic_fallback
        
        if use_semantic_fallback:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.semantic_model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("[INTENT] Semantic fallback enabled (uses Gemini tokens)")
            else:
                self.use_semantic_fallback = False
                logger.warning("[INTENT] Semantic fallback disabled - no API key")
    
    def detect(self, message: str, chat_history: list = None) -> Dict[str, Any]:
        """
        Detect intent from user message.
        
        Args:
            message: Current user message
            chat_history: Previous messages (for context)
        
        Returns:
            Dict with 'intent_type', 'is_continuation', 'is_greeting', 'confidence'
        """
        if not message or not message.strip():
            logger.warning("[INTENT] Empty message")
            return {
                "intent_type": "query",
                "is_continuation": False,
                "is_greeting": False,
                "confidence": 0.0
            }
        
        message = message.strip()
        
        # 1. Check for greeting (fast regex)
        is_greeting = bool(self.greeting_regex.match(message))
        if is_greeting:
            logger.info("[INTENT] Greeting detected (regex)")
            return {
                "intent_type": "greeting",
                "is_continuation": False,
                "is_greeting": True,
                "confidence": 1.0
            }
        
        # 2. Check for continuation cues (fast regex)
        is_continuation = bool(self.continuation_regex.search(message))
        if is_continuation:
            logger.info("[INTENT] Continuation detected (regex)")
            return {
                "intent_type": "continuation",
                "is_continuation": True,
                "is_greeting": False,
                "confidence": 1.0
            }
        
        # 3. Semantic fallback for ambiguous short messages (optional)
        if self.use_semantic_fallback and len(message.split()) <= 3:
            semantic_intent = self._semantic_detect(message, chat_history)
            if semantic_intent:
                return semantic_intent
        
        # 4. Default: standard query
        logger.info("[INTENT] Standard query")
        return {
            "intent_type": "query",
            "is_continuation": False,
            "is_greeting": False,
            "confidence": 1.0
        }
    
    def _semantic_detect(self, message: str, chat_history: list) -> Optional[Dict[str, Any]]:
        """
        Semantic intent detection using Gemini (fallback only).
        Used for ambiguous short messages like "more?", "and?", "continue?".
        
        Args:
            message: User message
            chat_history: Conversation context
        
        Returns:
            Intent dict or None if classification fails
        """
        try:
            # Get last assistant message for context
            last_ai_message = ""
            if chat_history:
                for msg in reversed(chat_history):
                    if hasattr(msg, 'role') and msg.role == 'ai':
                        last_ai_message = str(msg.content)[:200]  # First 200 chars
                        break
            
            prompt = f"""Classify this user message into ONE intent:
1. greeting - User is saying hello/hi
2. continuation - User wants more detail about the previous topic
3. query - User is asking a new question

Previous AI message: "{last_ai_message}"
User message: "{message}"

Respond with ONLY the intent name (greeting, continuation, or query)."""

            response = self.semantic_model.generate_content(prompt)
            intent_type = response.text.strip().lower()
            
            if intent_type in ['greeting', 'continuation', 'query']:
                logger.info(f"[INTENT] Semantic classification: {intent_type}")
                return {
                    "intent_type": intent_type,
                    "is_continuation": intent_type == "continuation",
                    "is_greeting": intent_type == "greeting",
                    "confidence": 0.8  # Lower confidence for semantic
                }
        except Exception as e:
            logger.warning(f"[INTENT] Semantic fallback failed: {e}")
        
        return None




