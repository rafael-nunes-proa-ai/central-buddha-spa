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
    from store.database import delete_session
    
    message = req.message
    conversation_id = req.conversation_id
    
    # Sessão separada com prefixo para isolamento
    session_id = f"central_{conversation_id}"
    
    # Comando manual de encerramento - Detecta palavras e deleta sessão
    if message and isinstance(message, str) and message.lower() in ["sair", "encerrar"]:
        print("=" * 80)
        print("🔴 FINALIZAR_SESSAO - PALAVRA DE ENCERRAMENTO DETECTADA")
        print(f"Conversation ID: {conversation_id}")
        print(f"Session ID (com prefixo): {session_id}")
        print(f"Mensagem recebida: {message}")
        print("=" * 80)
        
        # Verifica se sessão existe antes de deletar
        session_antes = get_session(session_id)
        if session_antes:
            print(f"📊 Sessão encontrada no banco:")
            print(f"   - Agente atual: {session_antes[1]}")
            print(f"   - Última atualização: {session_antes[3]}")
        else:
            print("⚠️  Sessão não encontrada no banco (pode já ter sido deletada)")
        
        print("🗑️  Deletando sessão do banco de dados...")
        delete_session(session_id)
        
        # Verifica se sessão foi realmente deletada
        session_depois = get_session(session_id)
        if session_depois is None:
            print("✅ CONFIRMADO: Sessão deletada com sucesso do banco de dados")
        else:
            print("❌ ERRO: Sessão ainda existe no banco após delete_session()")
            print(f"   Dados da sessão: {session_depois}")
        
        print("🚩 Flag finalizar_sessao: TRUE")
        print("📤 Retornando resposta de despedida para React Flow")
        print("=" * 80)
        return {
            "response": "Obrigado por entrar em contato com a Buddha Spa! 😊\n\nVolte sempre que precisar! 🙏",
            "finalizar_sessao": True  # Flag para React Flow encerrar
        }
    
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
    
    # Verifica se sessão foi deletada (encerramento via tool)
    session_after = get_session(session_id)
    
    if session_after is None:
        print("🔴 Sessão foi deletada (encerramento). Retornando resposta final.")
        print("=" * 80)
        add_messages(session_id, result.new_messages())
        
        output_text = result.data if hasattr(result, 'data') and result.data else result.output
        output_text = str(output_text)
        
        print("✅ BOT CENTRAL - RESPOSTA (ENCERRAMENTO):")
        print(output_text)
        print("=" * 80)
        return {"response": output_text}
    
    # Salva novas mensagens
    add_messages(session_id, result.new_messages())
    
    # IMPORTANTE: Recarrega contexto do banco pois as tools podem ter atualizado via update_context
    session_updated = get_session(session_id)
    context_from_db = session_updated[2] if session_updated else {}
    
    if isinstance(context_from_db, str):
        try:
            context_from_db = json.loads(context_from_db) if context_from_db else {}
        except:
            context_from_db = {}
    
    print("=" * 80)
    print("🔄 DEBUG: Contexto RECARREGADO do banco após agent")
    print(f"unidades_multiplas no banco: {context_from_db.get('unidades_multiplas')}")
    print(f"Length: {len(context_from_db.get('unidades_multiplas')) if context_from_db.get('unidades_multiplas') else 0}")
    print("=" * 80)
    
    # Mescla deps (que pode ter sido atualizado pelo agent) com contexto do banco (atualizado pelas tools)
    context_updated = {
        "cep_informado": context_from_db.get('cep_informado') or deps.cep_informado,
        "bairro_informado": context_from_db.get('bairro_informado') or deps.bairro_informado,
        "cidade_informada": context_from_db.get('cidade_informada') or deps.cidade_informada,
        "estado_informado": context_from_db.get('estado_informado') or deps.estado_informado,
        "latitude_usuario": context_from_db.get('latitude_usuario') or deps.latitude_usuario,
        "longitude_usuario": context_from_db.get('longitude_usuario') or deps.longitude_usuario,
        "unidade_encontrada": context_from_db.get('unidade_encontrada') or deps.unidade_encontrada,
        "unidades_multiplas": context_from_db.get('unidades_multiplas') or deps.unidades_multiplas,  # Prioriza banco
        "tentativas_agendamento": deps.tentativas_agendamento,
        "quer_reagendar": deps.quer_reagendar,
        "quer_info_reagendamento": deps.quer_info_reagendamento,
        "precisa_contato_unidade": deps.precisa_contato_unidade,
        "nome_unidade_reagendamento": deps.nome_unidade_reagendamento,
        "contexto_cancelamento": deps.contexto_cancelamento,
        "steps": deps.steps,
        "assuntos": deps.assuntos,
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
