"""
Gemini LLM Client
Interface for Google Gemini 2.5 Flash with structured response handling.
"""
import os
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini 2.5 Flash client."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("[GEMINI_ERR] GOOGLE_API_KEY not set")
        
        genai.configure(api_key=self.api_key)
        
        # Configure generation settings
        self.generation_config = {
            "temperature": 0.75,  # Balanced creativity and grounding
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Safety settings (permissive for educational content)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        logger.info("[GEMINI_OK] Initialized Gemini 2.5 Flash with temperature=0.75")
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from Gemini.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query with context
            chat_history: Previous conversation messages (formatted for Gemini)
        
        Returns:
            Dict with 'response', 'success', 'error'
        """
        try:
            # Build the full prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Start chat session if history provided
            if chat_history and len(chat_history) > 0:
                chat = self.model.start_chat(history=chat_history)
                response = chat.send_message(full_prompt)
            else:
                response = self.model.generate_content(full_prompt)
            
            if not response or not response.text:
                logger.error("[GEMINI_ERR] Empty response from model")
                return {
                    "response": "I'm having trouble generating a response. Please try again.",
                    "success": False,
                    "error": "Empty response"
                }
            
            logger.info(f"[GEMINI_OK] Generated {len(response.text)} chars")
            return {
                "response": response.text,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"[GEMINI_ERR] {e}")
            return {
                "response": "⚠️ I encountered an error processing your request. Please try again.",
                "success": False,
                "error": str(e)
            }
    
    def parse_structured_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse structured response into answer and key points.
        Expected format:
        Answer: <text>
        
        Key Points:
        • Point 1
        • Point 2
        
        Args:
            raw_response: Raw text from LLM
        
        Returns:
            Dict with 'answer', 'key_points'
        """
        # Split by "Key Points:" marker
        parts = raw_response.split("**Key Points:**")
        
        if len(parts) == 2:
            answer_part = parts[0].strip()
            key_points_part = parts[1].strip()
            
            # Extract answer (remove "**Answer:**" if present)
            answer = answer_part.replace("**Answer:**", "").strip()
            
            # Parse key points
            key_points = []
            for line in key_points_part.split('\n'):
                line = line.strip()
                # Remove bullet markers
                line = line.lstrip('•-*').strip()
                if line:
                    key_points.append(line)
            
            return {
                "answer": answer,
                "key_points": key_points
            }
        else:
            # No structured format detected, return as-is
            return {
                "answer": raw_response.strip(),
                "key_points": []
            }






















# """
# Gemini LLM Client
# Interface for Google Gemini 2.5 Flash with structured response handling.
# CRITICAL FIX: Handles optional chat_history (None when not continuation).
# """
# import os
# import logging
# from typing import Dict, Any, List, Optional
# import google.generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold
# from dotenv import load_dotenv

# load_dotenv()

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class GeminiClient:
#     """Google Gemini 2.5 Flash client."""
    
#     def __init__(self):
#         self.api_key = os.getenv("GOOGLE_API_KEY")
#         if not self.api_key:
#             raise ValueError("[GEMINI_ERR] GOOGLE_API_KEY not set")
        
#         genai.configure(api_key=self.api_key)
        
#         # Configure generation settings
#         self.generation_config = {
#             "temperature": 0.75,
#             "top_p": 0.95,
#             "top_k": 40,
#             "max_output_tokens": 2048,
#         }
        
#         # Safety settings (permissive for educational content)
#         self.safety_settings = {
#             HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
#         }
        
#         self.model = genai.GenerativeModel(
#             model_name='gemini-2.5-flash',
#             generation_config=self.generation_config,
#             safety_settings=self.safety_settings
#         )
        
#         logger.info("[GEMINI_OK] Initialized Gemini 2.5 Flash with temperature=0.75")
    
#     def generate_response(
#         self,
#         system_prompt: str,
#         user_prompt: str,
#         chat_history: Optional[List[Dict[str, Any]]] = None
#     ) -> Dict[str, Any]:
#         """
#         Generate response from Gemini.
        
#         Args:
#             system_prompt: System instructions
#             user_prompt: User query with context
#             chat_history: Previous conversation messages (None if not continuation)
        
#         Returns:
#             Dict with 'response', 'success', 'error'
#         """
#         try:
#             # Build the full prompt
#             full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
#             # ✅ FIX: Only start chat session if history provided
#             if chat_history and len(chat_history) > 0:
#                 logger.info(f"[GEMINI] Using chat history with {len(chat_history)} messages")
#                 chat = self.model.start_chat(history=chat_history)
#                 response = chat.send_message(full_prompt)
#             else:
#                 logger.info("[GEMINI] No chat history - using stateless generation (saves tokens)")
#                 response = self.model.generate_content(full_prompt)
            
#             if not response or not response.text:
#                 logger.error("[GEMINI_ERR] Empty response from model")
#                 return {
#                     "response": "I'm having trouble generating a response. Please try again.",
#                     "success": False,
#                     "error": "Empty response"
#                 }
            
#             logger.info(f"[GEMINI_OK] Generated {len(response.text)} chars")
#             return {
#                 "response": response.text,
#                 "success": True,
#                 "error": None
#             }
            
#         except Exception as e:
#             logger.error(f"[GEMINI_ERR] {e}")
#             return {
#                 "response": "⚠️ I encountered an error processing your request. Please try again.",
#                 "success": False,
#                 "error": str(e)
#             }












# """
# Gemini LLM Client
# Interface for Google Gemini 2.5 Flash with structured response handling.
# CRITICAL FIX: Adds Windows-compatible timeout handling.
# """
# import os
# import logging
# from typing import Dict, Any, List, Optional
# import google.generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold
# from dotenv import load_dotenv
# from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# load_dotenv()

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class GeminiClient:
#     """Google Gemini 2.5 Flash client with timeout protection."""
    
#     def __init__(self):
#         self.api_key = os.getenv("GOOGLE_API_KEY")
#         if not self.api_key:
#             raise ValueError("[GEMINI_ERR] GOOGLE_API_KEY not set")
        
#         genai.configure(api_key=self.api_key)
        
#         # Configure generation settings
#         self.generation_config = {
#             "temperature": 0.75,  # Balanced creativity and grounding
#             "top_p": 0.95,
#             "top_k": 40,
#             "max_output_tokens": 2048,
#         }
        
#         # Safety settings (permissive for educational content)
#         self.safety_settings = {
#             HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
#             HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
#         }
        
#         self.model = genai.GenerativeModel(
#             model_name='gemini-2.5-flash',
#             generation_config=self.generation_config,
#             safety_settings=self.safety_settings
#         )
        
#         # Thread pool for timeout handling (Windows-compatible)
#         self.executor = ThreadPoolExecutor(max_workers=2)
        
#         logger.info("[GEMINI_OK] Initialized Gemini 2.5 Flash with temperature=0.75")
    
#     def _generate_with_timeout(
#         self,
#         full_prompt: str,
#         chat_history: Optional[List[Dict[str, Any]]] = None,
#         timeout: int = 30
#     ) -> str:
#         """
#         Generate response with timeout using ThreadPoolExecutor.
#         This is Windows-compatible (signal.alarm doesn't work on Windows).
        
#         Args:
#             full_prompt: Combined system + user prompt
#             chat_history: Optional conversation history
#             timeout: Timeout in seconds
            
#         Returns:
#             Generated response text
            
#         Raises:
#             TimeoutError: If generation exceeds timeout
#         """
#         def _generate():
#             """Inner function to run in thread."""
#             try:
#                 if chat_history and len(chat_history) > 0:
#                     logger.info(f"[GEMINI] Using chat history with {len(chat_history)} messages")
#                     chat = self.model.start_chat(history=chat_history)
#                     response = chat.send_message(full_prompt)
#                 else:
#                     logger.info("[GEMINI] No chat history - using stateless generation (saves tokens)")
#                     response = self.model.generate_content(full_prompt)
                
#                 if not response or not response.text:
#                     return None
                    
#                 return response.text
#             except Exception as e:
#                 logger.error(f"[GEMINI_THREAD_ERR] {e}")
#                 raise
        
#         try:
#             # Submit to thread pool with timeout
#             future = self.executor.submit(_generate)
#             result = future.result(timeout=timeout)
            
#             if result is None:
#                 raise ValueError("Empty response from Gemini")
                
#             return result
            
#         except FuturesTimeoutError:
#             logger.error(f"[GEMINI_TIMEOUT] Request exceeded {timeout}s")
#             raise TimeoutError(f"Gemini API call exceeded {timeout} seconds")
#         except Exception as e:
#             logger.error(f"[GEMINI_THREAD_ERR] {e}")
#             raise
    
#     def generate_response(
#         self,
#         system_prompt: str,
#         user_prompt: str,
#         chat_history: Optional[List[Dict[str, Any]]] = None
#     ) -> Dict[str, Any]:
#         """
#         Generate response from Gemini with timeout protection.
        
#         Args:
#             system_prompt: System instructions
#             user_prompt: User query with context
#             chat_history: Previous conversation messages (None if not continuation)
        
#         Returns:
#             Dict with 'response', 'success', 'error'
#         """
#         try:
#             # Build the full prompt
#             full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
#             # Log prompt size for debugging
#             prompt_chars = len(full_prompt)
#             estimated_tokens = prompt_chars // 4  # Rough estimate: 1 token ≈ 4 chars
#             logger.info(f"[GEMINI] Prompt size: {prompt_chars} chars (~{estimated_tokens} tokens)")
            
#             # Generate with 30-second timeout
#             response_text = self._generate_with_timeout(
#                 full_prompt,
#                 chat_history,
#                 timeout=30
#             )
            
#             if not response_text or not response_text.strip():
#                 logger.error("[GEMINI_ERR] Empty response from model")
#                 return {
#                     "response": "I'm having trouble generating a response. Please try again.",
#                     "success": False,
#                     "error": "Empty response"
#                 }
            
#             logger.info(f"[GEMINI_OK] Generated {len(response_text)} chars")
#             return {
#                 "response": response_text,
#                 "success": True,
#                 "error": None
#             }
            
#         except TimeoutError as e:
#             logger.error(f"[GEMINI_TIMEOUT] {e}")
#             return {
#                 "response": "⚠️ Response generation timed out. Please try a shorter question or try again.",
#                 "success": False,
#                 "error": "Timeout after 30 seconds"
#             }
#         except Exception as e:
#             logger.error(f"[GEMINI_ERR] Unexpected error: {e}", exc_info=True)
#             return {
#                 "response": "⚠️ I encountered an error processing your request. Please try again.",
#                 "success": False,
#                 "error": str(e)
#             }
    
#     def __del__(self):
#         """Cleanup executor on deletion."""
#         if hasattr(self, 'executor'):
#             self.executor.shutdown(wait=False)