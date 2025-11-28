

"""
Memory Manager
Implements hybrid short-term (sliding window) and long-term (progressive summary) memory.
Passes conversation history only when continuation is detected.
"""
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages conversational memory with sliding window and summarization."""

    def __init__(self, short_term_window: int = 3):
        """
        Initialize memory manager.
        
        Args:
            short_term_window: Number of recent messages to keep (default: 3 to save tokens)
        """
        self.short_term_window = short_term_window
        self.long_term_summary = ""

    def get_short_term_context(self, chat_history: List[Any]) -> List[Any]:
        """
        Get the most recent N messages for immediate context.

        Args:
            chat_history: Full chat history

        Returns:
            Last N messages (sliding window)
        """
        if not chat_history:
            return []

        # Get last N messages
        recent_messages = chat_history[-self.short_term_window:]
        logger.info(f"[MEMORY] Short-term: {len(recent_messages)} messages")
        return recent_messages

    def format_for_llm(
        self,
        chat_history: List[Any],
        is_continuation: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Format chat history for LLM consumption.
        CRITICAL: Only returns history if continuation is detected, otherwise returns None.
        
        Args:
            chat_history: List of messages (Message objects or dicts)
            is_continuation: Whether user asked for more detail
        
        Returns:
            List of dicts formatted for Gemini API, or None if not continuation
        """
        # ✅ FIX: Only pass history for continuation queries
        if not is_continuation:
            logger.info("[MEMORY] Not a continuation - returning None to save tokens")
            return None

        if not chat_history:
            return None

        formatted_messages = []

        for msg in chat_history:
            # Handle both Pydantic models and dicts
            if hasattr(msg, "role") and hasattr(msg, "content"):
                role = msg.role
                content = msg.content
            elif isinstance(msg, dict):
                role = msg.get("role", "human")
                content = msg.get("content", "")
            else:
                logger.warning(f"[MEMORY] Skipping invalid message format: {type(msg)}")
                continue

            # Map roles to Gemini-compatible format
            if role == "human":
                gemini_role = "user"
            elif role == "ai":
                gemini_role = "model"
            else:
                gemini_role = "user"

            # Handle structured AI responses (dict content)
            if isinstance(content, dict):
                # Try both snake_case and camelCase for key_points
                answer = content.get("answer", "")
                key_points = content.get("key_points") or content.get("keyPoints", [])
                
                if key_points:
                    content = f"{answer}\n\nKey Points:\n" + "\n".join(f"• {kp}" for kp in key_points)
                else:
                    content = answer
            
            # Ensure content is string
            content = str(content)

            formatted_messages.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

        logger.info(f"[MEMORY] Formatted {len(formatted_messages)} messages for continuation context")
        return formatted_messages

    def should_summarize(self, chat_history: List[Any]) -> bool:
        """
        Determine if conversation history should be summarized.
        Currently a placeholder for future implementation.

        Args:
            chat_history: Full chat history

        Returns:
            True if summarization needed
        """
        total_chars = 0
        for msg in chat_history:
            if hasattr(msg, "content"):
                total_chars += len(str(msg.content))
            elif isinstance(msg, dict):
                total_chars += len(str(msg.get("content", "")))

        estimated_tokens = total_chars // 2
        threshold = 2000
        should_summarize = estimated_tokens > threshold

        if should_summarize:
            logger.info(f"[MEMORY] History exceeds {threshold} tokens, summarization recommended")

        return should_summarize

    def get_progressive_summary(self) -> str:
        """
        Get long-term memory summary.
        Currently returns a placeholder; future implementation would use LLM.
        """
        if self.long_term_summary:
            logger.info("[MEMORY] Returning existing long-term summary")
            return self.long_term_summary
        return ""

















# """
# Memory Manager
# Implements hybrid short-term (sliding window) and long-term (progressive summary) memory.
# Passes conversation history only when continuation is detected.
# """
# import logging
# from typing import List, Dict, Any, Optional

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class MemoryManager:
#     """Manages conversational memory with sliding window and summarization."""

#     def __init__(self, short_term_window: int = 3):
#         """
#         Initialize memory manager.
        
#         Args:
#             short_term_window: Number of recent messages to keep (default: 3 to save tokens)
#         """
#         self.short_term_window = short_term_window
#         self.long_term_summary = ""

#     def get_short_term_context(self, chat_history: List[Any]) -> List[Any]:
#         """
#         Get the most recent N messages for immediate context.

#         Args:
#             chat_history: Full chat history

#         Returns:
#             Last N messages (sliding window)
#         """
#         if not chat_history:
#             return []

#         # Get last N messages
#         recent_messages = chat_history[-self.short_term_window:]
#         logger.info(f"[MEMORY] Short-term: {len(recent_messages)} messages")
#         return recent_messages

#     def format_for_llm(
#         self,
#         chat_history: List[Any],
#         is_continuation: bool = False
#     ) -> Optional[List[Dict[str, Any]]]:
#         """
#         Format chat history for LLM consumption.
#         CRITICAL: Only returns history if continuation is detected, otherwise returns None.
        
#         Args:
#             chat_history: List of messages (Message objects or dicts)
#             is_continuation: Whether user asked for more detail
        
#         Returns:
#             List of dicts formatted for Gemini API, or None if not continuation
#         """
#         # ✅ FIX: Only pass history for continuation queries
#         if not is_continuation:
#             logger.info("[MEMORY] Not a continuation - returning None to save tokens")
#             return None

#         if not chat_history:
#             return None

#         formatted_messages = []

#         for msg in chat_history:
#             # Handle both Pydantic models and dicts
#             if hasattr(msg, "role") and hasattr(msg, "content"):
#                 role = msg.role
#                 content = msg.content
#             elif isinstance(msg, dict):
#                 role = msg.get("role", "human")
#                 content = msg.get("content", "")
#             else:
#                 logger.warning(f"[MEMORY] Skipping invalid message format: {type(msg)}")
#                 continue

#             # Map roles to Gemini-compatible format
#             if role == "human":
#                 gemini_role = "user"
#             elif role == "ai":
#                 gemini_role = "model"
#             else:
#                 gemini_role = "user"

#             # Handle structured AI responses (dict content)
#             if isinstance(content, dict):
#                 # Try both snake_case and camelCase for key_points
#                 answer = content.get("answer", "")
#                 key_points = content.get("key_points") or content.get("keyPoints", [])
                
#                 if key_points:
#                     content = f"{answer}\n\nKey Points:\n" + "\n".join(f"• {kp}" for kp in key_points)
#                 else:
#                     content = answer
            
#             # Ensure content is string
#             content = str(content)

#             formatted_messages.append({
#                 "role": gemini_role,
#                 "parts": [{"text": content}]
#             })

#         logger.info(f"[MEMORY] Formatted {len(formatted_messages)} messages for continuation context")
#         return formatted_messages

#     def should_summarize(self, chat_history: List[Any]) -> bool:
#         """
#         Determine if conversation history should be summarized.
#         Currently a placeholder for future implementation.

#         Args:
#             chat_history: Full chat history

#         Returns:
#             True if summarization needed
#         """
#         total_chars = 0
#         for msg in chat_history:
#             if hasattr(msg, "content"):
#                 total_chars += len(str(msg.content))
#             elif isinstance(msg, dict):
#                 total_chars += len(str(msg.get("content", "")))

#         estimated_tokens = total_chars // 4
#         threshold = 2000
#         should_summarize = estimated_tokens > threshold

#         if should_summarize:
#             logger.info(f"[MEMORY] History exceeds {threshold} tokens, summarization recommended")

#         return should_summarize

#     def get_progressive_summary(self) -> str:
#         """
#         Get long-term memory summary.
#         Currently returns a placeholder; future implementation would use LLM.
#         """
#         if self.long_term_summary:
#             logger.info("[MEMORY] Returning existing long-term summary")
#             return self.long_term_summary
#         return ""
