"""
LangChain Gemini Client
Wraps Google Gemini 2.5 Flash with LangChain's ChatGoogleGenerativeAI interface.
"""
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_langchain_gemini_client() -> ChatGoogleGenerativeAI:
    """
    Create LangChain-compatible Gemini 2.5 Flash client.
    
    Returns:
        ChatGoogleGenerativeAI instance configured for educational content
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("[LANGCHAIN_GEMINI] GOOGLE_API_KEY not set")
    
    # Configure safety settings (permissive for educational content)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    # Create LangChain Gemini client
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.75,  # Balanced creativity and grounding
        top_p=0.95,
        top_k=40,
        max_output_tokens=4096,  # Increased to reduce truncation
        safety_settings=safety_settings,
        convert_system_message_to_human=True  # Gemini requires system as first user message
    )
    
    logger.info("[LANGCHAIN_GEMINI] ✅ Initialized Gemini 2.5 Flash via LangChain")
    logger.info("[LANGCHAIN_GEMINI] Config: temp=0.75, max_tokens=4096")
    
    return llm
