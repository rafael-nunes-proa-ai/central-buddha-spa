from datetime import datetime, timedelta
from pydantic_ai.messages import ModelMessage
from fastapi.encoders import jsonable_encoder
import time

# Simulando o banco de dados em memória
conversations_db = {}

# Função para inserir uma nova sessão
def insert_session(session_id: str):
    conversations_db[session_id] = {
        "session_id": session_id,
        "messages": [],
        "current_agent": "neobpo_agent",
        "context": {
            "session_id": session_id,
            "nome": None,
            "cpf": None,
            "celular": None,
            "email": None,
            "protocolos": []
            },
        "last_updated": datetime.now()
    }

def get_messages_neobpo(session_id: str) -> list[ModelMessage]:
    if session_id not in conversations_db:
        insert_session(session_id)
    return conversations_db[session_id]

def add_messages_neobpo(session_id: str, new_msgs: list[ModelMessage]):
    if session_id not in conversations_db:
        insert_session(session_id)
    conversations_db[session_id]["messages"].extend(new_msgs)
    conversations_db[session_id]["last_updated"] = datetime.now()
    
def get_current_agent(session_id: str) -> str:    
    return conversations_db[session_id]["current_agent"]

def update_current_agent(session_id: str, agent_name: str):
    conversations_db[session_id]["current_agent"] = agent_name
    conversations_db[session_id]["last_updated"] = datetime.now()
    
def update_context(session_id: str, data: dict):
    conversations_db[session_id]["context"].update(data)
    conversations_db[session_id]["last_updated"] = datetime.now()
    
# Função para deletar uma sessão
def delete_session_neobpo(session_id):
    if session_id in conversations_db:
        del conversations_db[session_id]
    else:
        print(f"Sessão {session_id} não encontrada!")

# Função para visualizar uma sessão
def get_session(session_id):
    return conversations_db.get(session_id, f"Sessão {session_id} não encontrada!")

def get_all_sessions():
    return list(conversations_db.values())

def check_sessions():
    while True:
        try:
            current_time = datetime.now()
            sessions_to_delete = []

            for session_id, data in list(conversations_db.items()):
                last_updated = data.get("last_updated")
                if last_updated and (current_time - last_updated) >= timedelta(minutes=5):
                    print(f"[CLEANUP] Session {session_id} last updated over 5 minutes ago → will be deleted.")
                    sessions_to_delete.append(session_id)

            if sessions_to_delete:
                for session_id in sessions_to_delete:
                    del conversations_db[session_id]
                    print(f"[CLEANUP] Session {session_id} deleted.")
            else:
                print("[CLEANUP] No sessions to delete this cycle.")

            time.sleep(300)  # checa a cada 5 min
        except Exception as e:
            print(f"[CLEANUP] Error while checking sessions: {e}")
            time.sleep(300)