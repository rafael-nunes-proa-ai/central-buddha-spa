"""
Bot Central - API para informações de contato e geolocalização
Aplicação independente do projeto principal
"""

import json
import os
import re
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Union, Any

from agents.agent_central import central_agent, duvidas_agent
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

# Lock para evitar processamento duplicado
processing_locks = {}


def format_whatsapp(text: str) -> str:
    """
    Formata texto para WhatsApp removendo formatação incorreta.
    - Substitui **texto** por *texto* (asterisco duplo para simples)
    - Remove traços separadores ---
    """
    # Substitui **texto** por *texto*
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    
    # Remove linhas com apenas traços (separadores)
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    
    return text.strip()

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
async def post_chat_central(req: ChatRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verificar_api_key)):
    """
    Endpoint do Bot Central - Informações de Contato e Geolocalização
    Bot independente para fornecer contatos das unidades e encontrar unidade mais próxima
    """
    from store.database import delete_session
    
    message = req.message
    conversation_id = req.conversation_id
    
    # Sessão separada com prefixo para isolamento
    session_id = f"central_{conversation_id}"
    
    # 🔒 PROTEÇÃO CONTRA PROCESSAMENTO DUPLICADO
    if session_id in processing_locks:
        print(f"⚠️  BLOQUEADO: Mensagem já está sendo processada para session_id={session_id}")
        raise HTTPException(status_code=429, detail="Mensagem já está sendo processada")
    
    processing_locks[session_id] = True
    
    try:
        # Comando manual de encerramento - Detecta palavras e deleta sessão
        if message and isinstance(message, str) and message.lower() in ["sair", "encerrar"]:
            print("=" * 80)
            print("🔴 ENCERRAMENTO MANUAL - Palavra detectada")
            print(f"Session ID: {session_id}")
            print("=" * 80)
            
            delete_session(session_id)
            
            print("✅ Sessão deletada")
            print("🚩 Flag finalizar_sessao: TRUE")
            print("=" * 80)
            return {
                "response": "Obrigado por entrar em contato com a Buddha Spa! 😊\n\nVolte sempre que precisar! 🙏",
                "finalizar_sessao": True
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
        
        # PROTEÇÃO: Se transbordo já foi ativado, retorna imediatamente SEM processar
        if context.get('transbordo') == True:
            print("=" * 80)
            print("⚠️  TRANSBORDO JÁ ATIVADO - Retornando sem processar")
            print("🚩 Flag transbordo: TRUE")
            print("🗑️  Sessão será deletada após retorno")
            print("=" * 80)
            # Deleta sessão em background APÓS retornar
            background_tasks.add_task(delete_session, session_id)
            return {
                "response": "",
                "transbordo": True
            }
        
        # Cria deps com contexto
        context.setdefault("session_id", session_id)
        context.setdefault("agente_atual", "central_agent")  # Default
        deps = MyDeps(**context)
        
        # Determina qual agente usar
        agente_atual = context.get("agente_atual", "central_agent")
        
        print(f"🤖 Current Agent: {agente_atual}")
        print(f"📊 Histórico: {len(history)} mensagens")
        
        # Seleciona o agente correto
        if agente_atual == "duvidas_agent":
            agent = duvidas_agent
        else:
            agent = central_agent
        
        # Executa o agente selecionado
        result = await agent.run(
            message,
            message_history=history,
            deps=deps
        )
        
        print(f"📝 Novas mensagens geradas: {len(result.new_messages())}")
        
        # Verifica se houve transição de agente
        session_after_run = get_session(session_id)
        if session_after_run:
            context_after = session_after_run[2]
            if isinstance(context_after, str):
                try:
                    context_after = json.loads(context_after) if context_after else {}
                except:
                    context_after = {}
            
            novo_agente = context_after.get("agente_atual", "central_agent")
            
            # Se mudou de agente (transição detectada)
            if novo_agente != agente_atual:
                # Verifica se a resposta é apenas o emoji de transição
                try:
                    output_temp = result.data if hasattr(result, 'data') and result.data else result.output
                    output_temp = str(output_temp).strip()
                except:
                    output_temp = ""
                
                # Se for transição silenciosa (emoji 🔄), reprocessa
                if output_temp == "🔄":
                    print("=" * 80)
                    print(f"🔄 TRANSIÇÃO SILENCIOSA DETECTADA: {agente_atual} → {novo_agente}")
                    print("🔄 Reprocessando mensagem com novo agente...")
                    print("=" * 80)
                    
                    # NÃO salva as mensagens da transição (para não poluir histórico)
                    # Apenas recarrega histórico atual
                    history = get_messages(session_id)
                    
                    # Seleciona novo agente
                    if novo_agente == "duvidas_agent":
                        agent = duvidas_agent
                    else:
                        agent = central_agent
                    
                    # Recarrega deps com contexto atualizado
                    context_after.setdefault("session_id", session_id)
                    deps = MyDeps(**context_after)
                    
                    # Reprocessa a MESMA mensagem com o novo agente
                    result = await agent.run(
                        message,
                        message_history=history,
                        deps=deps
                    )
                    
                    print(f"📝 Novas mensagens após reprocessamento: {len(result.new_messages())}")
        
        # VERIFICA TRANSBORDO PRIMEIRO (antes de verificar sessão deletada)
        if deps.transbordo:
            print("=" * 80)
            print("🔴 TRANSBORDO ATIVADO")
            print("🚩 Flag transbordo: TRUE")
            print("�️  Sessão será deletada após retorno")
            print("=" * 80)
            
            # Deleta sessão em background APÓS retornar
            background_tasks.add_task(delete_session, session_id)
            
            return {
                "response": "",
                "transbordo": True
            }
        
        # Verifica se sessão foi deletada (encerramento via tool)
        session_after = get_session(session_id)
        
        if session_after is None:
            print("🔴 Sessão foi deletada (encerramento via tool). Retornando resposta final.")
            print("🚩 Flag finalizar_sessao: TRUE")
            print("=" * 80)
            add_messages(session_id, result.new_messages())
            
            output_text = result.data if hasattr(result, 'data') and result.data else result.output
            output_text = str(output_text)
            output_text = format_whatsapp(output_text)
            
            print("✅ BOT CENTRAL - RESPOSTA (ENCERRAMENTO):")
            print(output_text)
            print("=" * 80)
            return {
                "response": output_text,
                "finalizar_sessao": True  # Flag para React Flow encerrar
            }
        
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
            "opcoes_faq": context_from_db.get('opcoes_faq') or deps.opcoes_faq,  # FAQ
            "agente_atual": context_from_db.get('agente_atual') or deps.agente_atual,  # Roteamento
            "transbordo": deps.transbordo,  # Transbordo para atendimento humano
        }
        update_context(session_id, context_updated)
        
        # Extrai resposta
        try:
            output_text = result.data if hasattr(result, 'data') and result.data else result.output
            output_text = str(output_text)
            output_text = format_whatsapp(output_text)
        except:
            output_text = str(result.output)
            output_text = format_whatsapp(output_text)
        
        print("=" * 80)
        print("✅ BOT CENTRAL - RESPOSTA:")
        print(output_text)
        print("=" * 80)
        
        # Monta resposta com transbordo se ativado
        response_data = {"response": output_text}
        if deps.transbordo:
            response_data["transbordo"] = True
            print("🔄 TRANSBORDO ATIVADO - Transferindo para atendimento humano")
        
        return response_data
    
    finally:
        # 🔓 Libera o lock
        if session_id in processing_locks:
            del processing_locks[session_id]


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
