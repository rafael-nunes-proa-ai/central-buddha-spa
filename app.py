import time
from datetime import datetime
import json
import os
import logging
import re
import uvicorn
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agents.agent_new import voucher_agent, moderator_agent, cadastro_agent, agendamento_agent
#from store.db import add_messages, delete_session, get_messages, check_sessions, update_context
from dataclasses import dataclass
from fastapi.middleware.cors import CORSMiddleware
from security.auth import verificar_api_key
from typing import List, Dict, Any, Optional, Union
#from store import db
from fastapi.encoders import jsonable_encoder
import threading
from services.users import get_user
from agents.agent_new import voucher_agent, moderator_agent, cadastro_agent, agendamento_agent, cancelamento_agent, reagendamento_agent


def _validar_campos_cadastro(user_data: dict) -> tuple:
    """
    Valida se todos os campos obrigatórios do cadastro estão preenchidos e válidos.
    
    Returns:
        tuple: (cadastro_completo: bool, campos_faltantes: list)
    """
    campos_obrigatorios = {
        "nome": user_data.get("nome"),
        "cpf": user_data.get("cpf"),
        "celular": user_data.get("celular"),
        "email": user_data.get("email"),
        "dtNascimento": user_data.get("dtNascimento"),
        "genero": user_data.get("sexo")  # API retorna "sexo"
    }
    
    campos_faltantes = []
    
    for campo, valor in campos_obrigatorios.items():
        # Verifica se está vazio, None, ou inválido
        if not valor or str(valor).strip() == "":
            campos_faltantes.append(campo)
        # Valida dtNascimento específico (0000-00-00 é inválido)
        elif campo == "dtNascimento" and str(valor) in ["0000-00-00", "00/00/0000", ""]:
            campos_faltantes.append(campo)
    
    cadastro_completo = len(campos_faltantes) == 0
    
    return cadastro_completo, campos_faltantes
# from store.db_neobpo import add_messages_neobpo, get_messages_neobpo, delete_session_neobpo
# from store.db_porto_seguro import add_messages_porto_seguro, get_messages_porto_seguro, delete_session_porto_seguro
from tools.tool_neobpo import consultar_boletos_em_aberto_service, consultar_cliente_service, criar_protocolo_2_via_cartao, enviar_boletos_em_aberto_por_email, limpar_chamados
from tools.tool_neobpo import chamados_db, base_clientes, get_chamados_db
import re
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from typing import Optional
from store.database import cleanup_sessions
from agents.deps import MyDeps
import logfire
from store.database import (
    ensure_session,
    get_session,
    get_messages,
    add_messages,
    update_context,
    update_current_agent,
)

load_dotenv()
app = FastAPI()


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
class SessionData(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    current_agent: str
    context: Dict[str, Any]
    last_updated: datetime
    
class ChatRequest(BaseModel):
    conversation_id: str
    message: Union[str, dict, Any]
    phone: Optional[str] = Field(default=None)
    
class UserRequest(BaseModel):
    cpf: str
    
class EnviarBoletosRequest(BaseModel):
    id_cliente: str
    boletos_ids: List[str]

AGENTS = {
    "voucher_agent": voucher_agent,
    "cadastro_agent": cadastro_agent,
    "agendamento_agent": agendamento_agent,
    "cancelamento_agent": cancelamento_agent,
    "reagendamento_agent": reagendamento_agent
}

# =========================
# Main Chat Endpoint
# =========================

@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/chat")
async def post_chat(req: ChatRequest, api_key: str = Depends(verificar_api_key)):

    message = req.message

    if message.lower() in ["sair", "encerrar"]:
        return {"response": "Obrigado por entrar em contato com a Buddha Spa! \nVolte sempre! 😃"}

    # garante que sessão existe
    ensure_session(req.conversation_id)

    # busca dados da sessão
    session = get_session(req.conversation_id)

    print("DEBUG SESSION:", session)

    context = session[2] or {}

    if isinstance(context, str):
        context = context.strip()
        if context == "" or context.lower() == "none":
            context = {}
        else:
            try:
                context = json.loads(context)
            except Exception:
                context = {}

    current_agent = session[1]

    print("DEBUG CURRENT_AGENT:", current_agent)
    print("DEBUG TYPE:", type(current_agent))

    # defesa: se vier tupla tipo ('agendamento_agent',)
    if isinstance(current_agent, (list, tuple)):
        current_agent = current_agent[0] if current_agent else None

    # defesa: se vier None/vazio
    if not current_agent:
        current_agent = "voucher_agent"

    # telefone - CONSULTA AUTOMÁTICA DE CADASTRO
    celular = context.get("celular")

    if req.phone is not None and celular is None:

        user = get_user(req.phone)

        if "erro" not in user:
            # Valida se cadastro está completo
            cadastro_completo, campos_faltantes = _validar_campos_cadastro(user)

            data = {
                "codigo_usuario": user.get("codigo"),
                "nome": user.get("nome"),
                "cpf": user.get("cpf"),
                "celular": user.get("celular"),
                "email": user.get("email"),
                "dtNascimento": user.get("dtNascimento"),
                "genero": user.get("sexo"),
                "cadastro_completo": cadastro_completo,
                "campos_faltantes": campos_faltantes if not cadastro_completo else []
            }

            update_context(req.conversation_id, data)

            context.update(data)
            celular = user.get("celular")
    
    # CONSULTA AUTOMÁTICA DE CADASTRO (se estiver no cadastro_agent e tiver phone)
    if current_agent == "cadastro_agent" and req.phone is not None and not context.get("cadastro_completo"):
        print("=" * 80)
        print(" CONSULTA AUTOMÁTICA DE CADASTRO")
        print(f"Phone recebido: {req.phone}")
        print("=" * 80)
        
        # Se ainda não consultou, consulta agora
        if not context.get("codigo_usuario"):
            user = get_user(req.phone)
            if "erro" not in user:
                # Valida se cadastro está completo
                cadastro_completo, campos_faltantes = _validar_campos_cadastro(user)
                
                data = {
                    "codigo_usuario": user.get("codigo"),
                    "nome": user.get("nome"),
                    "cpf": user.get("cpf"),
                    "celular": user.get("celular"),
                    "email": user.get("email"),
                    "dtNascimento": user.get("dtNascimento"),
                    "genero": user.get("sexo"),
                    "cadastro_completo": cadastro_completo,
                    "campos_faltantes": campos_faltantes if not cadastro_completo else []
                }
                update_context(req.conversation_id, data)
                context.update(data)
                
                if cadastro_completo:
                    print(f"✅ Cadastro encontrado e COMPLETO: {user.get('nome')}")
                else:
                    print(f"⚠️ Cadastro encontrado mas INCOMPLETO: {user.get('nome')}")
                    print(f"   Campos faltantes: {campos_faltantes}")
            else:
                print("⚠️ Cadastro não encontrado, usuário precisará criar novo")

    # histórico de mensagens
    history = get_messages(req.conversation_id)

    # agente atual
    agent = AGENTS.get(current_agent)

    if not agent:
        raise HTTPException(status_code=400, detail=f"Agente '{current_agent}' não encontrado.")

    context.setdefault("session_id", req.conversation_id)
    deps = MyDeps(**context)
    print("DEBUG /chat - conversation_id:", req.conversation_id)
    print("DEBUG /chat - message:", req.message)
    print("DEBUG /chat - context_atual:", context)
    print("DEBUG /chat - agent_escolhido:", current_agent)
    print("=" * 80)
    print("🔍 DEBUG - HISTÓRICO ANTES DO RUN:")
    print(f"Quantidade de mensagens no histórico: {len(history)}")
    if history:
        print(f"  Última mensagem: {history[-1] if history else 'Nenhuma'}")
    print("=" * 80)
    
    result = await agent.run(
        req.message,
        message_history=history,
        deps=deps
    )
    
    print("=" * 80)
    print("🔍 DEBUG - RESULT DETALHADO:")
    print(f"  result.output: {result.output}")
    print(f"  hasattr(result, 'data'): {hasattr(result, 'data')}")
    if hasattr(result, 'data'):
        print(f"  result.data: {result.data}")
    print(f"  new_messages count: {len(result.new_messages())}")
    for i, msg in enumerate(result.new_messages()):
        print(f"  new_message[{i}]: kind={msg.kind if hasattr(msg, 'kind') else 'N/A'}")
    print("=" * 80)
    
    # 🔥 Detecta transição de agente (tool ir_para_cadastro retorna "")
    # Verifica se houve mudança de agente durante esta execução
    session_after = get_session(req.conversation_id)
    
    # Se sessão foi deletada (ex: encerrar_atendimento), retorna resposta final
    if session_after is None:
        print("🔴 DEBUG - Sessão foi deletada (encerramento). Retornando resposta final.")
        print("=" * 80)
        add_messages(req.conversation_id, result.new_messages())
        
        print("📤 DEBUG - OUTPUT FINAL ENVIADO AO USUÁRIO:", result.output)
        print("=" * 80)
        print("✅ DEBUG - RESPOSTA RETORNADA PELA API:", result.output)
        print("=" * 80)
        return {"response": result.output}
    
    new_agent = session_after[1]
    
    if isinstance(new_agent, (list, tuple)):
        new_agent = new_agent[0] if new_agent else None
    
    agent_changed = (current_agent != new_agent)
    
    if agent_changed:
        print(f"🔄 DEBUG - TRANSIÇÃO DETECTADA: {current_agent} → {new_agent}")
        print("� DEBUG - Executando novo agente imediatamente...")
        print("=" * 80)
        
        # Salva as mensagens da transição
        add_messages(req.conversation_id, result.new_messages())
        
        # Executa o novo agente com a mesma mensagem do usuário
        new_agent_instance = AGENTS.get(new_agent)
        if not new_agent_instance:
            print(f"❌ ERRO: Agente '{new_agent}' não encontrado!")
            return {"response": ""}
        
        # Atualiza contexto e histórico
        session_new = get_session(req.conversation_id)
        context_new = session_new[2] or {}
        if isinstance(context_new, str):
            context_new = context_new.strip()
            if context_new == "" or context_new.lower() == "none":
                context_new = {}
            else:
                try:
                    context_new = json.loads(context_new)
                except Exception:
                    context_new = {}
        
        context_new.setdefault("session_id", req.conversation_id)
        deps_new = MyDeps(**context_new)
        history_new = get_messages(req.conversation_id)
        
        print(f"🔄 DEBUG - Executando {new_agent} com histórico de {len(history_new)} mensagens")
        
        # Executa o novo agente
        result_new = await new_agent_instance.run(
            req.message,
            message_history=history_new,
            deps=deps_new
        )
        
        # Salva as novas mensagens
        add_messages(req.conversation_id, result_new.new_messages())
        
        # 🔥 LÓGICA DE CADASTRO AUTOMÁTICO EM CÓDIGO
        if new_agent == "cadastro_agent":
            from tools.cadastro_automatico import _processar_cadastro_automatico
            resultado_cadastro = _processar_cadastro_automatico(req.conversation_id, history_new)
            if resultado_cadastro:
                output_new = resultado_cadastro
            else:
                output_new = result_new.data if hasattr(result_new, 'data') and result_new.data else result_new.output
                output_new = str(output_new)
        else:
            output_new = result_new.data if hasattr(result_new, 'data') and result_new.data else result_new.output
            output_new = str(output_new)
        
        print(f"✅ DEBUG - Resposta do novo agente: {output_new}")
        print("=" * 80)
        
        return {"response": output_new}
    
    # Tenta pegar result.data primeiro (pode conter resultado de tools), senão usa result.output
    try:
        output_text = result.data if hasattr(result, 'data') and result.data else result.output
        output_text = str(output_text)
    except:
        output_text = str(result.output)
    
    print("📤 DEBUG - OUTPUT FINAL ENVIADO AO USUÁRIO:", output_text)
    print("=" * 80)
    
    add_messages(req.conversation_id, result.new_messages())
    
    # 🔥 LÓGICA DE CADASTRO AUTOMÁTICO EM CÓDIGO
    if current_agent == "cadastro_agent":
        from tools.cadastro_automatico import _processar_cadastro_automatico
        resultado_cadastro = _processar_cadastro_automatico(req.conversation_id, history + result.new_messages())
        if resultado_cadastro:
            output_text = resultado_cadastro

    print("✅ DEBUG - RESPOSTA RETORNADA PELA API:", output_text)
    print("=" * 80)
    return {"response": output_text}


# @app.post("/neobpo/chat")
# async def neobpo_post_chat(req: ChatRequest, api_key: str = Depends(verificar_api_key)):
#     message = req.message
#     if message.lower() == "sair" or message.lower() == "encerrar":
#         delete_session_neobpo(req.conversation_id)
#         return {"response": "Obrigado por entrar em contato com o Ouribank! \nVolte sempre 😃!"}

#     conversations = get_messages_neobpo(req.conversation_id)

#     history = conversations.get("messages", [])
    
#     # Obtém o agente atual com base na sessão
#     current_agent = conversations.get("current_agent", None)

#     agent = AGENTS.get(current_agent)
#     if not agent:
#         raise HTTPException(status_code=400, detail=f"Agente '{current_agent}' não encontrado.")
#     deps_dict = conversations.get("context", {})
#     deps = NeobpoDeps(**deps_dict)

#     result = await agent.run(req.message, message_history=history, deps=deps)

#     add_messages_neobpo(req.conversation_id, result.new_messages())

#     return {"response": result.output}


def clean_result(result) -> dict:
    """
    Remove as instruções do retorno do agente, mantendo apenas dados relevantes.
    Adiciona campo 'transfer_call' se houver solicitação de transferência para humano.
    """
    clean_data = {}
    
    # Output principal
    try:
        output_text = result.data if hasattr(result, 'data') else result.output
        output_text = str(output_text)
    except:
        output_text = str(result)

    # Verifica se há comando de transferência
    transfer_tag = "@transferir_humano"
    transfer_call = False
    if transfer_tag in output_text:
        output_text = output_text.replace(transfer_tag, "").strip()
        transfer_call = True

    clean_data["output"] = output_text
    clean_data["transfer_call"] = transfer_call  # null por padrão se não houver

    # Tenta adicionar informações extras se disponíveis
    try:
        if hasattr(result, '_state') and hasattr(result._state, 'usage'):
            usage = result._state.usage
            clean_data["usage"] = {
                "total_tokens": getattr(usage, 'total_tokens', 0),
                "request_tokens": getattr(usage, 'request_tokens', 0),
                "response_tokens": getattr(usage, 'response_tokens', 0),
            }
    except:
        pass  # Ignora se não conseguir acessar usage
    
    return clean_data


#
#Security
#
# 🔒 Palavras e padrões suspeitos
SQL_KEYWORDS = [
    "select", "insert", "update", "delete", "drop", "alter", "truncate", "union", "exec", "create", "replace",
]
CODE_PATTERNS = [
    # JS specifics
    r"\bconsole\.log\s*\(",      # console.log(...)
    r"\bdocument\.\w+",         # document.xxx
    r"\bwindow\.\w+",           # window.xxx
    r"\bfetch\s*\(",            # fetch(...)
    r"\baxios\.\w+",            # axios.get/post...
    r"\bimport\s+[\w\{\}\*\s,]+from\b",  # import ... from ...
    r"\brequire\s*\(",          # require(...)
    r"\bexport\s+(default|const|function|class)\b",
    r"\bconst\s+\w+\s*=",       # const name =
    r"\blet\s+\w+\s*=",         # let name =
    r"\bvar\s+\w+\s*=",         # var name =
    r"=>",                      # arrow functions

    # Generic function/class/def patterns (Python/JS/other)
    r"\bdef\s+\w+\s*\(",        # def func(
    r"\bclass\s+\w+",           # class Name
    r"[A-Za-z_]\w*\s*\([^)]{0,200}\)\s*;?",  # name(args) optional semicolon - heuristic

    # Dangerous builtins / calls
    r"\beval\s*\(", 
    r"\bexec\s*\(",
    r"os\.system\s*\(",
    r"subprocess\.",
    r"popen\s*\(",
    
    # HTML/script injection
    r"<script.*?>",
    r"```.*?```",               # fenced code blocks (markdown)
]
PROMPT_INJECTION_PATTERNS = [
    # Inglês
    r"ignore\s+your\s+previous\s+instructions",
    r"forget\s+all\s+previous\s+rules",
    r"system\s+prompt",
    r"act\s+as\s+an\s+assistant",
    r"you\s+are\s+no\s+longer\s+chatgpt",
    r"disregard\s+all\s+prior\s+context",
    r"override\s+the\s+system",
    r"developer\s+mode",
    
    # Português
    r"ignore\s+suas\s+instruções\s+anteriores",
    r"esqueça\s+todas\s+as\s+regras\s+anteriores",
    r"prompt\s+do\s+sistema",
    r"aja\s+como\s+um\s+assistente",
    r"você\s+não\s+é\s+mais\s+um\s+assistente",
    r"desconsidere\s+as\s+instruções\s+anteriores",
    r"mude\s+seu\s+comportamento",
    r"modifique\s+suas\s+regras",
    r"finja\s+ser\s+um\s+usuário",
    r"ative\s+modo\s+desenvolvedor",
    r"prompt",
]
# ---- listas para temas não relacionados
POLITICS_WORDS = [
    # English
    "election", "vote", "voting", "president", "government", "congress", "senate", "politician", "party", "impeach",
    # Português
    "eleição", "voto", "votar", "presidente", "governo", "congresso", "senador", "partido", "impeachment", "candidato",
    # (nomes de políticos podem ser adicionados conforme necessário)
]

VIOLENCE_WORDS = [
    # English
    "kill", "murder", "shoot", "stab", "bomb", "explode", "attack", "torture",
    # Português
    "matar", "morte", "assassinar", "atacar", "bomba", "explodir", "tortura", "esfaquear",
]

PROFANITY_WORDS = [
    # English
    "fuck", "shit", "bitch", "damn",
    # Português (palavrões comuns) -- se preferir, pode ofuscar
    "porra", "merda", "caralho", "pqp",
]




# ---- já existentes (exemplos)
SQL_KEYWORDS = [
    "select", "insert", "update", "delete", "drop", "alter", "truncate", "union", "exec", "create", "replace",
]

CODE_PATTERNS = [
    r"\bconsole\.log\s*\(",
    r"\bdocument\.\w+",
    r"\bwindow\.\w+",
    r"\bfetch\s*\(",
    r"\baxios\.\w+",
    r"\bimport\s+[\w\{\}\*\s,]+from\b",
    r"\brequire\s*\(",
    r"\bexport\s+(default|const|function|class)\b",
    r"\bconst\s+\w+\s*=",
    r"\blet\s+\w+\s*=",
    r"\bvar\s+\w+\s*=",
    r"=>",
    r"\bdef\s+\w+\s*\(",
    r"\bclass\s+\w+",
    r"[A-Za-z_]\w*\s*\([^)]{0,200}\)\s*;?",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"os\.system\s*\(",
    r"subprocess\.",
    r"popen\s*\(",
    r"<script.*?>",
    r"```.*?```",
]

PROMPT_INJECTION_PATTERNS = [
    # Inglês
    r"ignore\s+your\s+previous\s+instructions",
    r"forget\s+all\s+previous\s+rules",
    r"system\s+prompt",
    r"act\s+as\s+an\s+assistant",
    r"you\s+are\s+no\s+longer\s+chatgpt",
    r"disregard\s+all\s+prior\s+context",
    r"override\s+the\s+system",
    r"developer\s+mode",
    # Português
    r"ignore\s+suas\s+instruções\s+anteriores",
    r"esqueça\s+todas\s+as\s+regras\s+anteriores",
    r"prompt\s+do\s+sistema",
    r"aja\s+como\s+um\s+assistente",
    r"você\s+não\s+é\s+mais\s+um\s+assistente",
    r"desconsidere\s+as\s+instruções\s+anteriores",
    r"mude\s+seu\s+comportamento",
    r"modifique\s+suas\s+regras",
    r"finja\s+ser\s+um\s+usuário",
    r"ative\s+modo\s+desenvolvedor",
]

# ---- listas para temas não relacionados
POLITICS_WORDS = [
    # English
    "election", "vote", "voting", "president", "government", "congress", "senate", "politician", "party", "impeach", "Obama", "Trump", "Biden",
    # Português
    "eleição", "voto", "votar", "presidente", "governo", "congresso", "senador", "partido", "impeachment", "candidato", "Lula", "Bolsonaro",
    # (nomes de políticos podem ser adicionados conforme necessário)
]

VIOLENCE_WORDS = [
    # English
    "kill", "murder", "shoot", "stab", "bomb", "explode", "attack", "torture",
    # Português
    "matar", "morte", "assassinar", "atacar", "bomba", "explodir", "tortura", "esfaquear",
]

PROFANITY_WORDS = [
    # English
    "fuck", "shit", "bitch", "damn",
    # Português (palavrões comuns) -- se preferir, pode ofuscar
    "porra", "merda", "caralho", "pqp",
]

def contains_word_from_list(text: str, words: list) -> bool:
    """Procura qualquer palavra da lista no texto (word-boundary)."""
    for w in words:
        if re.search(r"\b" + re.escape(w) + r"\b", text, flags=re.IGNORECASE):
            return True
    return False

def is_malicious_message(msg: str) -> bool:
    """Verifica se o texto contém SQL, código ou prompt injection."""
    if not isinstance(msg, str):
        return False

    text = msg.strip()
    lower = text.lower()

    # 1) SQL keywords (palavra isolada)
    for kw in SQL_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            return True

    # 2) Código / padrões perigosos
    for pattern in CODE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            return True

    # 3) Prompt injection (ing e pt)
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            return True

    return False

def categorize_unrelated_themes(msg: str) -> Optional[str]:
    """
    Retorna:
      - "politics" se detectar termos relacionados a política,
      - "violence" se detectar violência,
      - "profanity" se detectar palavrões,
      - None se nenhum tema for detectado.
    """
    if not isinstance(msg, str):
        return None
    text = msg.strip()
    lower = text.lower()

    if contains_word_from_list(lower, VIOLENCE_WORDS):
        return "violence"
    if contains_word_from_list(lower, PROFANITY_WORDS):
        return "profanity"
    if contains_word_from_list(lower, POLITICS_WORDS):
        return "politics"
    return None


# @app.post("/porto_seguro/chat")
# async def porto_seguro_post_chat(request: Request, api_key: str = Depends(verificar_api_key)):
#     start_time = time.time()
#     start_dt = datetime.now()
    
#     try:
#         body = await request.json()
#     except Exception:
#         return JSONResponse(
#             status_code=200,
#             content={"output": "Corpo da requisição inválido ou ausente.", "transfer_call": False}
#         )

#     # 🔹 Se o corpo vier como string JSON, tenta fazer o parse
#     if isinstance(body, str):
#         try:
#             body = json.loads(body)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=200, detail="Formato JSON inválido.")

#     # 🔹 Validação manual dos campos obrigatórios
#     conversation_id = body.get("conversation_id")
#     message = body.get("message")
    
#     phone = body.get("phone", None)

#     if not conversation_id:
#         raise HTTPException(status_code=200, detail="Campo 'conversation_id' é obrigatório.")
#     if message is None:
#         raise HTTPException(status_code=200, detail="Campo 'message' é obrigatório.")

#     # 1) validação de código / SQL / prompt injection
#     if isinstance(message, str) and is_malicious_message(message):
#         # log.warning(...)  # sugiro logar IP, conversation_id e trecho da mensagem aqui
#         return JSONResponse(
#             status_code=200,
#             content={"output": "🚫 Operação não permitida: não aceitamos trechos de código, comandos SQL ou instruções de sistema.", "transfer_call": False, "reason": "malicious prompt"}
#         )

#     # 2) validação de temas não relacionados (política, violência, profanidade)
#     theme = categorize_unrelated_themes(message)
#     if theme == "politics":
#         return JSONResponse(
#             status_code=200,
#             content={"output": "🔒 Não discutimos temas políticos por aqui. Por favor, pergunte sobre serviços e atendimento.", "transfer_call": False, "reason": "politics"}
#         )
#     if theme == "violence":
#         return JSONResponse(
#             status_code=200,
#             content={"output": "🔒 Conteúdo violento não é permitido. Se você estiver em risco, procure ajuda local imediatamente.", "transfer_call": False, "reason": "violence"}
#         )
#     if theme == "profanity":
#         return JSONResponse(
#             status_code=200,
#             content={"output": "🔒 Evite o uso de linguagem ofensiva. Mantenha a conversa respeitosa, por favor.", "transfer_call": False, "reason": "profanity"}
#         )


#     # 🔹 Caso o usuário queira encerrar o chat
#     if isinstance(message, str) and message.lower() in ["sair", "encerrar"]:
#         delete_session_porto_seguro(conversation_id)
#         return {"output": "Obrigado por entrar em contato com Porto Seguro! \nVolte sempre 😃!"}

#     # 🔹 Busca o histórico da conversa
#     conversations = get_messages_porto_seguro(conversation_id)
#     history = conversations.get("messages", [])

#     # 🔹 Obtém o agente atual
#     current_agent = conversations.get("current_agent", None)
#     agent = AGENTS.get(current_agent)
#     if not agent:
#         raise HTTPException(status_code=400, detail=f"Agente '{current_agent}' não encontrado.")

#     deps_dict = conversations.get("context", {})
#     deps = PortoSeguroDeps(**deps_dict)

#     # 🔹 Executa o agente
#     result = await agent.run(message, message_history=history, deps=deps)
#     add_messages_porto_seguro(conversation_id, result.new_messages())

#     # 🔹 Limpa o resultado e retorna
#     result_clean = clean_result(result)
#     end_time = time.time()
#     end_dt = datetime.now()
#     elapsed = end_time - start_time
#     result_clean["start_dt"] = start_dt
#     result_clean["end_dt"] = end_dt
#     result_clean["response_time_seconds"] = round(elapsed, 3)
#     return result_clean



@app.post("/usuario")
def buscar_usuario(req: UserRequest, api_key: str = Depends(verificar_api_key)):
    cpf = req.cpf
    cliente_info = base_clientes.get(cpf)

    if not cliente_info:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return cliente_info

@app.post("/protocolos_por_usuario")
def protocolos_por_usuario(
    data: dict = Body(...),
    api_key: str = Depends(verificar_api_key)
):
    usuario_id = data.get("usuario_id")

    if not usuario_id:
        raise HTTPException(status_code=400, detail="Campo 'usuario_id' é obrigatório")

    # Recupera toda a base de protocolos
    protocolos = get_chamados_db()  # Esperado: {1: [...], 2: [...]}

    # Filtra apenas os protocolos do usuário
    protocolos_usuario = []
    for user_id, lista in protocolos.items():
        if user_id == usuario_id:
            # Se a lista estiver com strings (JSON serializado), converta:
            for p in lista:
                if isinstance(p, str):
                    try:
                        p = json.loads(p)  # converte JSON string para dict
                    except:
                        pass
                protocolos_usuario.append(p)

    return jsonable_encoder(protocolos_usuario)

@app.post("/adicionar_protocolo")
async def adicionar_protocolo(
    data: dict = Body(...),
    api_key: str = Depends(verificar_api_key)
):
    required_fields = ["usuario_id", "cpf", "descricao"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Campo '{field}' é obrigatório")

    # Adiciona o novo protocolo à base de dados
    response = await criar_protocolo_2_via_cartao(
        usuario_id=data["usuario_id"],
        cpf=data["cpf"],
        descricao=data["descricao"]
    )
    # Se for string JSON, converte para dicionário
    return json.loads(response) if isinstance(response, str) else response
    


@app.get("/protocolos")
def get_protocolos(api_key: str = Depends(verificar_api_key)):    
    return jsonable_encoder(chamados_db)


@app.get("/limpar_chamados")
def limpar_todos_chamados(api_key: str = Depends(verificar_api_key)):
    try:
        limpar_chamados()
        return {"status": "success", "message": "Todos os chamados foram removidos."}
    except Exception as e:
        logging.error(f"Erro ao limpar chamados: {e}")
        raise HTTPException(status_code=500, detail="Erro ao limpar chamados.")

@app.get("/clientes/{cpf}")
def consultar_cliente(cpf: str):
    resultado = consultar_cliente_service(cpf)

    if resultado["status"] == "nao_encontrado":
        raise HTTPException(
            status_code=404,
            detail=resultado["message"]
        )

    return resultado

@app.get("/boletos/{user_id}")
def consultar_boletos(user_id: str):
    resultado = consultar_boletos_em_aberto_service(user_id)

    if resultado["status"] == "sem_boletos":
        raise HTTPException(
            status_code=404,
            detail=resultado["message"]
        )

    return resultado

@app.post("/boletos/enviar-email")
def enviar_boletos(request: EnviarBoletosRequest):
    resultado = enviar_boletos_em_aberto_por_email(
        request.id_cliente,
        request.boletos_ids
    )

    if resultado["status"] == "erro":
        raise HTTPException(
            status_code=400,
            detail=resultado["message"]
        )

    return resultado

if __name__ == "__main__":
    try:
        session_check_thread = threading.Thread(target=cleanup_sessions, daemon=True)
        session_check_thread.start()
        port = int(os.getenv("PORT", 8080))
        workers = int(os.getenv("WORKERS", 1))
        reload = bool(os.getenv("RELOAD", False) == True)
        print(f"Starting server on port {port} with {workers} workers and reload={reload}")

        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            workers=workers if not os.getenv("RELOAD") else 1,
            log_level="info",
            proxy_headers=True,
            timeout_keep_alive=30,
            reload=bool(os.getenv("RELOAD")),
        )
    except Exception as e:
        logging.error(f"Erro ao iniciar o servidor: {e}")
        raise