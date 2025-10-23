"""
FastAPI Backend para Solverde Chatbot
Fornece API REST com suporte a Server-Sent Events (SSE) para streaming
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
import os
import sys
import glob

# Adicionar diretório pai ao path para importar o chatbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solverde_chatbot_enhanced import SolverdeChatbot
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="Solverde Chatbot API",
    description="API REST com streaming para o assistente virtual Solverde.pt",
    version="2.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar chatbot
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada no ambiente!")

# Configurações do chatbot (podem ser ajustadas via env vars)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "8"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

chatbot = SolverdeChatbot(
    openai_api_key=OPENAI_API_KEY,
    persist_directory="./chroma_db",
    embedding_model=EMBEDDING_MODEL,
    llm_model=LLM_MODEL,
    temperature=TEMPERATURE,
    max_context_messages=MAX_CONTEXT_MESSAGES,
    retrieval_top_k=RETRIEVAL_TOP_K
)

# Carregar FAQs se database está vazia
FAQ_DIR = os.getenv("FAQ_DIR", "../docs/ajuda/")
if chatbot.collection.count() == 0:
    print(f"📁 A carregar FAQs de {FAQ_DIR}...")
    
    # Load all .md files in the directory
    faq_files = glob.glob(os.path.join(FAQ_DIR, "*.md"))
    
    if not faq_files:
        print(f"⚠️  Nenhum ficheiro .md encontrado em {FAQ_DIR}")
    else:
        total_loaded = 0
        for faq_file in sorted(faq_files):
            print(f"  📄 A carregar: {os.path.basename(faq_file)}")
            try:
                chatbot.load_faqs_from_file(faq_file)
                total_loaded += 1
            except Exception as e:
                print(f"  ❌ Erro ao carregar {faq_file}: {e}")
        
        print(f"✅ {total_loaded} ficheiros carregados com sucesso!")


# Modelos Pydantic para requests
class ChatRequest(BaseModel):
    session_id: str
    message: str


class SessionRequest(BaseModel):
    session_id: str


# Endpoints
@app.get("/")
async def root():
    """Health check básico"""
    return {
        "message": "Solverde Chatbot API v2.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Verificação detalhada de saúde do sistema"""
    return {
        "status": "healthy",
        "faq_count": chatbot.collection.count(),
        "embedding_model": chatbot.embedding_model,
        "llm_model": chatbot.llm_model,
        "active_sessions": len(chatbot.conversations)
    }


@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint para chat com streaming via Server-Sent Events

    Params:
        session_id: ID único da sessão de conversa
        message: Mensagem do utilizador

    Returns:
        StreamingResponse com eventos SSE
    """
    async def event_generator():
        try:
            async for chunk in chatbot.chat_stream(request.session_id, request.message):
                # Formato SSE
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"

                # Small delay para não sobrecarregar o cliente
                await asyncio.sleep(0.01)

        except Exception as e:
            error_data = json.dumps({
                "type": "error",
                "content": f"Erro no servidor: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/api/chat")
async def chat_no_stream(request: ChatRequest):
    """
    Endpoint para chat sem streaming (fallback)

    Params:
        session_id: ID único da sessão
        message: Mensagem do utilizador

    Returns:
        Resposta completa do chatbot
    """
    try:
        response = chatbot.chat(request.session_id, request.message)
        return {
            "session_id": request.session_id,
            "response": response,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/clear")
async def clear_session(request: SessionRequest):
    """
    Limpa o histórico de uma sessão

    Params:
        session_id: ID da sessão a limpar
    """
    chatbot.clear_conversation(request.session_id)
    return {
        "status": "cleared",
        "session_id": request.session_id
    }


@app.get("/api/sessions/{session_id}/history")
async def get_history(session_id: str):
    """
    Obtém o histórico de conversa de uma sessão

    Params:
        session_id: ID da sessão
    """
    history = chatbot.get_conversation_history(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "message_count": len(history)
    }


@app.post("/api/sessions/{session_id}/export")
async def export_session(session_id: str):
    """
    Exporta a conversa de uma sessão para JSON

    Params:
        session_id: ID da sessão
    """
    history = chatbot.get_conversation_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou vazia")

    return {
        "session_id": session_id,
        "history": history,
        "export_format": "json"
    }


@app.get("/api/stats")
async def get_stats():
    """
    Estatísticas gerais do sistema
    """
    return {
        "total_faqs": chatbot.collection.count(),
        "active_sessions": len(chatbot.conversations),
        "embedding_model": chatbot.embedding_model,
        "llm_model": chatbot.llm_model,
        "temperature": chatbot.temperature,
        "max_context_messages": chatbot.max_context_messages,
        "retrieval_top_k": chatbot.retrieval_top_k
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
