# """
# FastAPI Backend for AI Shine Tutor RAG Chatbot
# Orchestrates RAG pipeline with intent detection, retrieval, and LLM generation.
# """
# import os
# import logging
# from typing import List
# from contextlib import asynccontextmanager
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from Backend.models import ChatRequest, ChatResponse
# from Backend.rag_engine import RAGEngine

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# logger = logging.getLogger(__name__)

# # Global RAG engine instance
# rag_engine = None


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan manager - initializes and cleans up resources."""
#     global rag_engine
    
#     logger.info("[STARTUP] Initializing RAG Engine...")
#     try:
#         rag_engine = RAGEngine()
#         logger.info("[STARTUP] ✅ RAG Engine ready")
#     except Exception as e:
#         logger.error(f"[STARTUP] ❌ Failed to initialize RAG Engine: {e}")
#         raise
    
#     yield
    
#     # Cleanup
#     logger.info("[SHUTDOWN] Closing connections...")
#     if rag_engine:
#         rag_engine.cleanup()
#     logger.info("[SHUTDOWN] ✅ Shutdown complete")


# # Initialize FastAPI app
# app = FastAPI(
#     title="AI Shine Tutor API",
#     description="RAG-powered AI/ML tutor chatbot with domain-specific knowledge",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Update for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/")
# async def root():
#     """Health check endpoint."""
#     return {
#         "status": "online",
#         "service": "AI Shine Tutor API",
#         "version": "1.0.0"
#     }


# @app.get("/health")
# async def health_check():
#     """Detailed health check with component status."""
#     health_status = {
#         "api": "healthy",
#         "rag_engine": "healthy" if rag_engine else "unavailable",
#         "components": {}
#     }
    
#     if rag_engine:
#         try:
#             # Test MongoDB connection
#             rag_engine.retriever.mongo_client.client.admin.command('ping')
#             health_status["components"]["mongodb"] = "connected"
#         except Exception as e:
#             health_status["components"]["mongodb"] = f"error: {str(e)}"
#             health_status["rag_engine"] = "degraded"
        
#         health_status["components"]["llm"] = "ready"
#         health_status["components"]["embeddings"] = "ready"
    
#     return health_status


# @app.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     """
#     Main chat endpoint for AI Shine Tutor.
    
#     Request Body:
#         - chat_history: List of messages with role ("human"/"ai") and content
    
#     Response:
#         - answer: Generated response text
#         - type: Response type ("greeting"/"text"/"structured"/"decline")
#     """
#     if not rag_engine:
#         logger.error("[CHAT_ERR] RAG engine not initialized")
#         raise HTTPException(status_code=503, detail="RAG engine unavailable")
    
#     try:
#         # Validate input
#         if not request.chat_history:
#             logger.warning("[CHAT] Empty chat history received")
#             return ChatResponse(
#                 answer="👋 Hello! I'm **AI Shine**, your AI/ML tutor. How can I help you today?",
#                 type="greeting"
#             )
        
#         # Extract current user query
#         current_query = None
#         for msg in reversed(request.chat_history):
#             if msg.role == "human":
#                 current_query = msg.content
#                 break
        
#         if not current_query:
#             logger.warning("[CHAT] No user message found")
#             raise HTTPException(status_code=400, detail="No user message in chat history")
        
#         logger.info(f"[CHAT] Processing query: {current_query[:100]}...")
        
#         # Process through RAG engine
#         response = rag_engine.process_query(
#             query=current_query,
#             chat_history=request.chat_history
#         )
        
#         logger.info(f"[CHAT_OK] Response type: {response['type']}")
        
#         return ChatResponse(
#             answer=response["answer"],
#             type=response["type"]
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[CHAT_ERR] Unexpected error: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail="Internal server error. Please try again."
#         )


# if __name__ == "__main__":
#     import uvicorn
    
#     port = int(os.getenv("PORT", 8000))
    
#     logger.info(f"[STARTUP] Starting AI Shine Tutor API on port {port}")
    
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=port,
#         # reload=True,  # Disable in production
#         log_level="info"
#     )
# # ```

# # ---

# # ## Key Design Decisions

# # ### 1. **Lifespan Management**
# # - Uses FastAPI's `@asynccontextmanager` to initialize RAG engine once at startup
# # - Ensures graceful shutdown and resource cleanup
# # - Prevents re-initialization on every request

# # ### 2. **Single `/chat` Endpoint**
# # - Accepts `chat_history` array (not individual messages)
# # - Returns structured response with `answer` and `type`
# # - Type indicates frontend rendering strategy: `"greeting"`, `"text"`, `"structured"`, or `"decline"`

# # ### 3. **Error Handling Strategy**
# # ```
# # ┌─────────────────┬──────────────────────────────────┐
# # │ Failure Type    │ Response                         │
# # ├─────────────────┼──────────────────────────────────┤
# # │ Empty history   │ Default greeting (200 OK)        │
# # │ No user message │ 400 Bad Request                  │
# # │ RAG unavailable │ 503 Service Unavailable          │
# # │ Unexpected      │ 500 Internal Server Error        │
# # └─────────────────┴──────────────────────────────────┘






























# post-presentation.json main.py
# """
# FastAPI Backend for AI Shine Tutor RAG Chatbot
# Unified RAG pipeline - presentation.json now handled within RAG engine.
# """
# import os
# import logging
# from contextlib import asynccontextmanager
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from Backend.models import ChatRequest, ChatResponse
# from Backend.rag_engine import RAGEngine

# load_dotenv()

# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# logger = logging.getLogger(__name__)

# rag_engine = None


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan manager."""
#     global rag_engine
    
#     logger.info("[STARTUP] Initializing RAG Engine...")
#     try:
#         rag_engine = RAGEngine()
#         logger.info("[STARTUP] ✅ RAG Engine ready")
#     except Exception as e:
#         logger.error(f"[STARTUP] ❌ Failed to initialize RAG Engine: {e}")
#         raise
    
#     yield
    
#     logger.info("[SHUTDOWN] Closing connections...")
#     if rag_engine:
#         rag_engine.cleanup()
#     logger.info("[SHUTDOWN] ✅ Shutdown complete")


# app = FastAPI(
#     title="AI Shine Tutor API",
#     description="RAG-powered AI/ML tutor with domain-specific knowledge",
#     version="1.0.0",
#     lifespan=lifespan
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/")
# async def root():
#     return {
#         "status": "online",
#         "service": "AI Shine Tutor API",
#         "version": "1.0.0"
#     }


# @app.get("/health")
# async def health_check():
#     health_status = {
#         "api": "healthy",
#         "rag_engine": "healthy" if rag_engine else "unavailable",
#         "components": {}
#     }
    
#     if rag_engine:
#         try:
#             rag_engine.retriever.mongo_client.client.admin.command('ping')
#             health_status["components"]["mongodb"] = "connected"
#         except Exception as e:
#             health_status["components"]["mongodb"] = f"error: {str(e)}"
#             health_status["rag_engine"] = "degraded"
        
#         health_status["components"]["llm"] = "ready"
#         health_status["components"]["embeddings"] = "ready"
    
#     return health_status


# @app.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     """Main chat endpoint - unified RAG handles both KB and presentation."""
#     if not rag_engine:
#         logger.error("[CHAT_ERR] RAG engine not initialized")
#         raise HTTPException(status_code=503, detail="RAG engine unavailable")
    
#     try:
#         if not request.chat_history:
#             logger.warning("[CHAT] Empty chat history")
#             return ChatResponse(
#                 answer="👋 Hello! I'm **AI Shine**, your AI/ML tutor. How can I help you today?",
#                 type="greeting"
#             )
        
#         current_query = None
#         for msg in reversed(request.chat_history):
#             if msg.role == "human":
#                 current_query = msg.content
#                 break
        
#         if not current_query:
#             raise HTTPException(status_code=400, detail="No user message")
        
#         logger.info(f"[CHAT] Processing: {current_query[:100]}...")
        
#         response = rag_engine.process_query(
#             query=current_query,
#             chat_history=request.chat_history
#         )
        
#         logger.info(f"[CHAT_OK] Response type: {response['type']}")
        
#         return ChatResponse(
#             answer=response["answer"],
#             type=response["type"]
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[CHAT_ERR] Unexpected error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal server error")


# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.getenv("PORT", 8000))
#     logger.info(f"[STARTUP] Starting AI Shine Tutor API on port {port}")
#     uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")




































"""
FastAPI Backend for AI Shine Tutor RAG Chatbot
Unified RAG pipeline - presentation.json now handled within RAG engine.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from Backend.models import ChatRequest, ChatResponse
from Backend.rag_engine import RAGEngine

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

rag_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global rag_engine
    
    logger.info("[STARTUP] Initializing RAG Engine...")
    try:
        rag_engine = RAGEngine()
        logger.info("[STARTUP] ✅ RAG Engine ready")
    except Exception as e:
        logger.error(f"[STARTUP] ❌ Failed to initialize RAG Engine: {e}")
        raise
    
    yield
    
    logger.info("[SHUTDOWN] Closing connections...")
    if rag_engine:
        rag_engine.cleanup()
    logger.info("[SHUTDOWN] ✅ Shutdown complete")


app = FastAPI(
    title="AI Shine Tutor API",
    description="RAG-powered AI/ML tutor with domain-specific knowledge",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "AI Shine Tutor API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    health_status = {
        "api": "healthy",
        "rag_engine": "healthy" if rag_engine else "unavailable",
        "components": {}
    }
    
    if rag_engine:
        try:
            rag_engine.retriever.mongo_client.client.admin.command('ping')
            health_status["components"]["mongodb"] = "connected"
        except Exception as e:
            health_status["components"]["mongodb"] = f"error: {str(e)}"
            health_status["rag_engine"] = "degraded"
        
        health_status["components"]["llm"] = "ready"
        health_status["components"]["embeddings"] = "ready"
    
    return health_status


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - unified RAG handles both KB and presentation."""
    if not rag_engine:
        logger.error("[CHAT_ERR] RAG engine not initialized")
        raise HTTPException(status_code=503, detail="RAG engine unavailable")
    
    try:
        if not request.chat_history:
            logger.warning("[CHAT] Empty chat history")
            return ChatResponse(
                answer="👋 Hello! I'm **AI Shine**, your AI/ML tutor. How can I help you today?",
                type="greeting"
            )
        
        current_query = None
        for msg in reversed(request.chat_history):
            if msg.role == "human":
                current_query = msg.content
                break
        
        if not current_query:
            raise HTTPException(status_code=400, detail="No user message")
        
        logger.info(f"[CHAT] Processing: {current_query[:100]}...")
        
        response = rag_engine.process_query(
            query=current_query,
            chat_history=request.chat_history
        )
        
        logger.info(f"[CHAT_OK] Response type: {response['type']}")
        
        return ChatResponse(
            answer=response["answer"],
            type=response["type"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAT_ERR] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
