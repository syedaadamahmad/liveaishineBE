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



