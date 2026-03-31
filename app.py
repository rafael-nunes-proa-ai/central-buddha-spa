"""
Bot Central - API para informações de contato e geolocalização
Aplicação independente do projeto principal
"""

import json
import os
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, Any

from agents.agent_central import central_agent
from agents.deps import MyDeps
from security.auth import verificar_api_key
from store.database import (
    ensure_session,
    get_session,
    get_messages,
    add_messages,
    update_context,
)

load_dotenv()

app = FastAPI(title="Bot Central - Buddha Spa")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Models
# =========================
class ChatRequest(BaseModel):
    conversation_id: str
    message: Union[str, dict, Any]

# =========================
# Endpoints
# =========================

@app.get("/")
async def read_root():
    return {"message": "Bot Central - Buddha Spa API", "status": "online"}


@app.post("/chat-central")
async def post_chat_central(req: ChatRequest, api_key: str = Depends(verificar_api_key)):
    """
    Endpoint do Bot Central - Informações de Contato e Geolocalização
    Bot independente para fornecer contatos das unidades e encontrar unidade mais próxima
    """
    message = req.message
    conversation_id = req.conversation_id
    
    # Sessão separada com prefixo para isolamento
    session_id = f"central_{conversation_id}"
    
    print("=" * 80)
    print("🏢 BOT CENTRAL - NOVA MENSAGEM")
    print(f"Session ID: {session_id}")
    print(f"Mensagem: {message}")
    print("=" * 80)
    
    # Garante que a sessão existe
    ensure_session(session_id)
    
    # Busca histórico de mensagens
    history = get_messages(session_id)
    
    # Busca contexto atual
    session = get_session(session_id)
    context = session[2] if session else {}
    
    if isinstance(context, str):
        try:
            context = json.loads(context) if context else {}
        except:
            context = {}
    
    # Cria deps com contexto
    context.setdefault("session_id", session_id)
    deps = MyDeps(**context)
    
    print(f"🤖 Executando agent com {len(history)} mensagens no histórico")
    
    # Executa central_agent
    result = await central_agent.run(
        message,
        message_history=history,
        deps=deps
    )
    
    print(f"📝 Novas mensagens geradas: {len(result.new_messages())}")
    
    # Salva novas mensagens
    add_messages(session_id, result.new_messages())
    
    # Extrai contexto atualizado do deps e salva no banco
    context_updated = {
        "cep_informado": deps.cep_informado,
        "bairro_informado": deps.bairro_informado,
        "cidade_informada": deps.cidade_informada,
        "estado_informado": deps.estado_informado,
        "latitude_usuario": deps.latitude_usuario,
        "longitude_usuario": deps.longitude_usuario,
        "unidade_encontrada": deps.unidade_encontrada,
        "tentativas_agendamento": deps.tentativas_agendamento,
        "quer_reagendar": deps.quer_reagendar,
        "quer_info_reagendamento": deps.quer_info_reagendamento,
        "precisa_contato_unidade": deps.precisa_contato_unidade,
        "nome_unidade_reagendamento": deps.nome_unidade_reagendamento,
        "steps": deps.steps,
    }
    update_context(session_id, context_updated)
    
    # Extrai resposta
    try:
        output_text = result.data if hasattr(result, 'data') and result.data else result.output
        output_text = str(output_text)
    except:
        output_text = str(result.output)
    
    print("=" * 80)
    print("✅ BOT CENTRAL - RESPOSTA:")
    print(output_text)
    print("=" * 80)
    
    return {"response": output_text}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"🚀 Iniciando Bot Central na porta {port}")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info",
        proxy_headers=True,
        timeout_keep_alive=30,
    )
