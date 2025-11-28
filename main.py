"""
FastAPI Backend for AI Shine Tutor RAG Chatbot
Now supports both original (regex-based) and LangChain-powered RAG engines.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from Backend.models import ChatRequest, ChatResponse
from Backend.rag_engine import RAGEngine
from Backend.langchain_rag_engine import LangChainRAGEngine

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

rag_engine = None
langchain_rag_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global rag_engine, langchain_rag_engine
    
    logger.info("[STARTUP] Initializing RAG Engines...")
    
    # Initialize original RAG engine (backup)
    try:
        rag_engine = RAGEngine()
        logger.info("[STARTUP] ✅ Original RAG Engine ready")
    except Exception as e:
        logger.error(f"[STARTUP] ❌ Failed to initialize original RAG Engine: {e}")
        # Don't raise - allow LangChain to work even if original fails
    
    # Initialize LangChain RAG engine
    try:
        langchain_rag_engine = LangChainRAGEngine()
        logger.info("[STARTUP] ✅ LangChain RAG Engine ready")
    except Exception as e:
        logger.error(f"[STARTUP] ❌ Failed to initialize LangChain RAG Engine: {e}")
        # If LangChain fails but original works, we can still serve requests
        if not rag_engine:
            raise  # Both engines failed, can't serve
    
    yield
    
    logger.info("[SHUTDOWN] Closing connections...")
    if rag_engine:
        rag_engine.cleanup()
    if langchain_rag_engine:
        langchain_rag_engine.cleanup()
    logger.info("[SHUTDOWN] ✅ Shutdown complete")


app = FastAPI(
    title="AI Shine Tutor API",
    description="RAG-powered AI/ML tutor with domain-specific knowledge",
    version="2.0.0",  # Bumped for LangChain integration
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
        "version": "2.0.0",
        "engines": {
            "original": "available" if rag_engine else "unavailable",
            "langchain": "available" if langchain_rag_engine else "unavailable"
        }
    }


@app.get("/health")
async def health_check():
    health_status = {
        "api": "healthy",
        "engines": {
            "original": "healthy" if rag_engine else "unavailable",
            "langchain": "healthy" if langchain_rag_engine else "unavailable"
        },
        "components": {}
    }
    
    # Check original engine
    if rag_engine:
        try:
            rag_engine.retriever.mongo_client.client.admin.command('ping')
            health_status["components"]["mongodb_original"] = "connected"
        except Exception as e:
            health_status["components"]["mongodb_original"] = f"error: {str(e)}"
            health_status["engines"]["original"] = "degraded"
    
    # Check LangChain engine
    if langchain_rag_engine:
        health_status["components"]["llm_langchain"] = "ready"
        health_status["components"]["memory_langchain"] = "ready"
    
    return health_status


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Original chat endpoint (regex-based RAG engine).
    Kept as backup during LangChain testing.
    """
    if not rag_engine:
        logger.error("[CHAT_ERR] Original RAG engine not initialized")
        raise HTTPException(status_code=503, detail="Original RAG engine unavailable")
    
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
        
        logger.info(f"[CHAT] Processing (original): {current_query[:100]}...")
        
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


@app.post("/chat-v2", response_model=ChatResponse)
async def chat_langchain(request: ChatRequest):
    """
    LangChain-powered chat endpoint.
    Features:
    - Automatic conversation understanding (no regex)
    - ConversationSummaryMemory (85% token savings)
    - Fixes "be descriptive" bug
    - Natural continuation handling
    """
    if not langchain_rag_engine:
        logger.error("[CHAT_V2_ERR] LangChain RAG engine not initialized")
        raise HTTPException(status_code=503, detail="LangChain RAG engine unavailable")
    
    try:
        if not request.chat_history:
            logger.warning("[CHAT_V2] Empty chat history")
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
        
        logger.info(f"[CHAT_V2] Processing (LangChain): {current_query[:100]}...")
        
        response = langchain_rag_engine.process_query(
            query=current_query,
            chat_history=request.chat_history
        )
        
        logger.info(f"[CHAT_V2_OK] Response type: {response['type']}")
        
        return ChatResponse(
            answer=response["answer"],
            type=response["type"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAT_V2_ERR] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ✅ CORRECT for Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))  # Render uses 10000 as default
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1  # Single worker for free tier
    )











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


# # ✅ CORRECT for Render
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.getenv("PORT", 10000))  # Render uses 10000 as default
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=port,
#         log_level="info",
#         workers=1  # Single worker for free tier
#     )
