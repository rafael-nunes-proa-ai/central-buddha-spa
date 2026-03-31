import os
from typing import Any, Dict, List
from pydantic_ai.tools import Tool
import uuid
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime, timedelta
import random

base_boletos = {
        "1": [
            {
                "id_boleto": "1",
                "nome_boleto": "Cartão Ouribank Visa Gold",
                "data_vencimento": "2025-05-10",
                "valor_fatura": "R$ 350,45"
            },
            {
                "id_boleto": "2",
                "nome_boleto": "Financiamento Ouribank Imobiliário",
                "data_vencimento": "2025-01-15",
                "valor_fatura": "R$ 1.560,90"
            }
        ],
        "3": [
            {
                "id_boleto": "1",
                "nome_boleto": "Cartão Ouribank Visa Gold",
                "data_vencimento": "2025-05-10",
                "valor_fatura": "R$ 350,45"
            },
            {
                "id_boleto": "2",
                "nome_boleto": "Financiamento Imobiliário",
                "data_vencimento": "2025-01-15",
                "valor_fatura": "R$ 1.560,90"
            }
        ]
    }

    # Base simulada de clientes

# Base simulada de clientes
base_clientes = {
    "35996699885": {
        "id": "1",
        "nome": "Rodrigo Santos Moraes",
        "cpf": "35996699885",
        "celular": "+5511957423808",
        "email": "rodrigo-smoraes@hotmail.com",
        "endereco": "Rua Cardeal, 83 - São Paulo/SP"
    },
    "98765432100": {
        "id": "2",
        "nome": "Maria Oliveira",
        "cpf": "98765432100",
        "celular": "(21) 99876-5432",
        "email": "maria_oliveira@hotmail.com",
        "endereco": "Avenida Central, 456 - Rio de Janeiro/RJ"
    },
    "58433844032": {
        "id": "3",
        "nome": "Sergio Gama",
        "cpf": "58433844032",
        "celular": "(11) 94581-7571",
        "email": "Sergio.Gama@tdsynnex.com",
        "endereco": "Av. Giovanni Gronchi 2557 - São Paulo/SP"
    }
    
}

chamados_db = {}

def limpar_chamados():
    """.
    Remove todos os protocolos de todos os usuários
    """
    chamados_db.clear()
    return True

def get_chamados_db():
    """Retorna a base de dados completa de chamados/protocolos"""
    return chamados_db  

def consultar_cliente_service(cpf: str) -> dict:
    """
    Consulta informações do cliente na base de dados Neobpo.
    """
    cliente_info = base_clientes.get(cpf)

    if not cliente_info:
        return {
            "status": "nao_encontrado",
            "message": "Usuário não encontrado"
        }

    return {
        "status": "sucesso",
        "data": cliente_info
    }

@Tool
def consultar_cliente(cpf: str) -> str:
    """
    Consulta informações do cliente na base de dados Neobpo.
    """
    resultado = consultar_cliente_service(cpf)
    return json.dumps(resultado, ensure_ascii=False)


def consultar_boletos_em_aberto_service(user_id: str) -> dict:
    """
    Consulta boletos em aberto para um usuário.
    """
    boletos = base_boletos.get(user_id)

    if not boletos:
        return {
            "status": "sem_boletos",
            "message": "Nenhum boleto em aberto encontrado para este usuário"
        }

    return {
        "status": "sucesso",
        "data": boletos
    }

@Tool
def consultar_boletos_em_aberto(id: str) -> str:
    """
    Consulta boletos em aberto para um usuário com base no ID fornecido.

    Args:
        id (str): ID do usuário.

    Returns:
        str: Lista de boletos em aberto em formato JSON ou "sem_boletos".
    """
    resultado = consultar_boletos_em_aberto_service(id)
    return json.dumps(resultado, ensure_ascii=False)
    
    
def enviar_boletos_em_aberto_por_email(
    id_cliente: str,
    boletos_ids: list
) -> dict:
    """
    Envia boletos selecionados por email com anexo.

    Args:
        id_cliente (str): ID do cliente.
        boletos_ids (list): Lista de IDs dos boletos selecionados.
    """

    # 1️⃣ Valida cliente
    cliente = next(
        (c for c in base_clientes.values() if c.get("id") == id_cliente),
        None
    )

    if not cliente:
        return {
            "status": "erro",
            "message": "Cliente não encontrado"
        }

    # 2️⃣ Busca boletos do cliente
    boletos_cliente = base_boletos.get(id_cliente, [])
    boletos_encontrados = [
        b for b in boletos_cliente if b.get("id_boleto") in boletos_ids
    ]

    if not boletos_encontrados:
        return {
            "status": "erro",
            "message": "Nenhum boleto encontrado para os IDs informados"
        }

    # 3️⃣ Configurações de email (use variáveis de ambiente)
    remetente = os.getenv("EMAIL_REMETENTE", "rsmoraesconsultoria@gmail.com")
    senha = os.getenv("EMAIL_SENHA", "zaft oghc mwlg seih")
    destinatario = cliente.get("email")

    if not destinatario:
        return {
            "status": "erro",
            "message": "Cliente não possui email cadastrado"
        }

    # 4️⃣ Monta email
    msg = MIMEMultipart("alternative")
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = "Boletos solicitados - Ouribank"

    blocos_boletos = ""
    for b in boletos_encontrados:
        blocos_boletos += f"""
        <div style="margin-bottom: 15px; padding: 12px;
             border: 1px solid #e5e5e5; border-radius: 6px; background: #fafafa;">
            <strong>{b.get('nome_boleto')}</strong><br>
            Vencimento: {b.get('data_vencimento')}<br>
            Valor: {b.get('valor_fatura')}
        </div>
        """

    corpo_email_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Olá <strong>{cliente.get('nome')}</strong>,</p>

        <p>Conforme solicitado, seguem abaixo os boletos enviados:</p>

        <hr style="border-top: 1px solid #ddd; margin: 20px 0;">

        {blocos_boletos}

        <hr style="border-top: 1px solid #ddd; margin: 20px 0;">

        <p>Atenciosamente,<br>
        <strong>Assistente Virtual Ouribank</strong></p>

        <img src="https://abracam.com/wp-content/uploads/2023/10/ourinvest-09-1-1024x569.png"
             alt="Ouribank" width="150" style="margin-top: 20px;">
    </body>
    </html>
    """

    msg.attach(MIMEText(corpo_email_html, "html"))

    # 5️⃣ Anexo (opcional)
    try:
        nome_arquivo = "boleto.pdf"
        with open(nome_arquivo, "rb") as anexo:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(anexo.read())
            encoders.encode_base64(parte)
            parte.add_header(
                "Content-Disposition",
                f"attachment; filename={nome_arquivo}"
            )
            msg.attach(parte)
    except FileNotFoundError:
        pass  # segue sem anexo

    # 6️⃣ Envia email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, destinatario, msg.as_string())
    except Exception as e:
        return {
            "status": "erro",
            "message": f"Erro ao enviar email: {str(e)}"
        }

    # 7️⃣ Sucesso
    return {
        "status": "sucesso",
        "message": f"Boletos enviados com sucesso para {destinatario}",
        "boletos_enviados": [b.get("id_boleto") for b in boletos_encontrados]
    }
    
@Tool
def enviar_boletos_em_aberto_por_email_tool(id_cliente: str, boletos_ids: list) -> str:
    """
    Envia boletos selecionados por email com anexo.

    Args:
        id_cliente (str): ID do cliente.
        boletos_ids (list): Lista de IDs dos boletos selecionados (ex: ["B1", "B2"]).
    """
    resultado = enviar_boletos_em_aberto_por_email(
        id_cliente,
        boletos_ids
    )

    return json.dumps(resultado, ensure_ascii=False)


def bloquear_e_solicitar_cartao_simulado(cpf: str, motivo: str = None) -> dict:
    """
    Simula o bloqueio do cartão e a abertura da solicitação de um novo cartão.

    Args:
      cpf (str): CPF apenas números.
      motivo (str): motivo opcional (ex: perdido, roubado, danificado).

    Retorna:
      dict: {
        "status": "ok" | "erro" | "confirmacao_necessaria",
        "acao": "bloqueado_e_solicitado" | "bloqueado" | "solicitado",
        "mensagem": str,
        "ticket_id": str (quando aplicável),
        "simulado": True
      }
    """
    # Validações básicas
    if not cpf.isdigit() or len(cpf) not in (11,):
        return {"status": "erro", "mensagem": "CPF inválido. Informe apenas números (11 dígitos)."}

    # Regras de confirmação (simulação): exigimos confirmação textual antes de prosseguir
    # Aqui assumimos que a confirmação já foi recebida pelo agente — se for necessária:
    # return {"status":"confirmacao_necessaria", "mensagem":"Confirma bloquear o cartão e solicitar novo? Responda 'CONFIRMAR' para prosseguir."}

    # Simular criação de ticket / registro
    
    ticket = f"SIM-{uuid.uuid4().hex[:8]}"

    # Simular pequena latência/processamento
    # (no código real não usar sleep em servidores assíncronos; aqui é apenas simulação)
    # time.sleep(0.2)

    return {
        "status": "ok",
        "acao": "bloqueado_e_solicitado",
        "mensagem": f"Cartão com últimos 4 dígitos XXX bloqueado com sucesso. Solicitação de novo cartão aberta (ticket {ticket}).",
        "ticket_id": ticket,
        "simulado": True
    }

@Tool
def consultar_protocolos_em_aberto(usuario_id: int) -> str:
    """
    Consulta todos os protocolos abertos de um usuário na base de dados.

    Args:
        usuario_id (int): ID do usuário para buscar os protocolos.
        
    Returns:
        str: Lista de protocolos em formato JSON ou "usuário não encontrado".
    """
    # Verifica se o usuário possui protocolos
    protocolos = chamados_db.get(usuario_id)

    if protocolos:
        return json.dumps(protocolos, ensure_ascii=False)
    else:
        return "usuário não encontrado"
    
def gerar_protocolo_aleatorio() -> str:
    """Gera um protocolo aleatório no formato PROTO-XXXXXX"""
    return f"PROTO-{random.randint(100000, 999999)}"



async def enviar_protocolo_por_email(cpf: str, protocolo: dict) -> str:
    """
    Envia e-mail de confirmação de criação de protocolo de segunda via de cartão.

    Args:
        id_cliente (str): ID do cliente.
        protocolo (dict): Dados do protocolo a ser enviado.
    """
    print(f"Enviando protocolo por email: {protocolo}")
    # Verifica cliente
    cliente = base_clientes.get(cpf)
    if not cliente:
        return "Cliente não encontrado."
   
    # ---- ENVIO DE EMAIL VIA GMAIL ----
    remetente = "rsmoraesconsultoria@gmail.com"
    senha = "zaft oghc mwlg seih"
    destinatario = cliente["email"]

    msg = MIMEMultipart("alternative")
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = "Solicitação de 2ª via de cartão - Ouribank"

    # Monta o HTML do protocolo formatado
    bloco_protocolo = f"""
        <div style="margin-bottom: 15px; padding: 12px; border: 1px solid #e5e5e5; border-radius: 6px; background: #fafafa;">
            <strong>Protocolo: {protocolo['protocolo']}</strong><br>
            <span>Tipo: {protocolo['tipo']}</span><br>
            <span>Data da solicitação: {protocolo['data_criacao']}</span><br>
            <span>Previsão de conclusão: {protocolo['previsao_conclusao']}</span><br>
            <span>Descrição: {protocolo['descricao']}</span>
        </div>
        """

    # Corpo do e-mail formatado em HTML
    corpo_email_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Olá <strong>{cliente['nome']}</strong>,</p>

        <p>
        Conforme solicitado, segue o protocolo de sua solicitação de 2ª via do cartão:
        </p>

        <hr style="border: 0; border-top: 1px solid #ddd; margin: 20px 0;">

        {bloco_protocolo}

        <hr style="border: 0; border-top: 1px solid #ddd; margin: 20px 0;">

        <p>Atenciosamente,<br>
        <strong>Assistente Virtual Ouribank</strong></p>

        <img src="https://abracam.com/wp-content/uploads/2023/10/ourinvest-09-1-1024x569.png" alt="Ouribank" width="150" style="margin-top: 20px;">
    </body>
    </html>
    """

    msg.attach(MIMEText(corpo_email_html, "html"))


    # Envia via Gmail
    with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
        servidor.starttls()
        servidor.login(remetente, senha)
        servidor.sendmail(remetente, destinatario, msg.as_string())

    return f"Boletos enviados com sucesso para o email {cliente['email']}."

@Tool
async def criar_protocolo(usuario_id: int, cpf: str, descricao: str) -> str:
    """
    Cria um novo protocolo de 2ª via de cartão para o usuário e adiciona à base de dados.

    Se já existir algum protocolo aberto para o usuário, retorna uma mensagem informando que não é possível criar outro.

    Args:
        usuario_id (int): ID do usuário que está solicitando.
        cpf (str): CPF do cliente a ser consultado.
        descricao (str): Motivo da solicitação do novo protocolo.

    Returns:
        str: Dados do protocolo criado em formato JSON.
    """

    protocolos = chamados_db.get(usuario_id, [])
    if protocolos:
        return (
            "Não é possível criar outro protocolo, pois ainda existe outro protocolo aberto.\n"
            f"Protocolos atuais: {json.dumps(protocolos, ensure_ascii=False)}"
        )

    # Datas
    hoje = datetime.today()
    data_criacao = hoje.strftime("%Y-%m-%d")
    previsao_conclusao = (hoje + timedelta(days=10)).strftime("%Y-%m-%d")

    # Gera protocolo aleatório
    protocolo_id = gerar_protocolo_aleatorio()

    # Cria novo protocolo
    novo_protocolo = {
        "protocolo": protocolo_id,
        "tipo": "2ª_via_cartao",
        "data_criacao": data_criacao,
        "previsao_conclusao": previsao_conclusao,
        "solicitação_dentro_do_prazo": True,
        "descricao": descricao
    }

    # Adiciona à base
    if usuario_id in chamados_db:
        chamados_db[usuario_id].append(novo_protocolo)
        
    else:
        chamados_db[usuario_id] = [novo_protocolo]
    #Envia email com o protocolo
    print(f"Enviando email para {usuario_id} com protocolo {novo_protocolo}")
    await enviar_protocolo_por_email(str(cpf), novo_protocolo)
    
    return json.dumps(novo_protocolo, ensure_ascii=False)

async def criar_protocolo_2_via_cartao(usuario_id: int, cpf: str, descricao: str) -> str:
    """
    Cria um novo protocolo de 2ª via de cartão para o usuário e adiciona à base de dados.

    Se já existir algum protocolo aberto para o usuário, retorna uma mensagem informando que não é possível criar outro.

    Args:
        usuario_id (int): ID do usuário que está solicitando.
        cpf (str): CPF do cliente a ser consultado.
        descricao (str): Motivo da solicitação do novo protocolo.

    Returns:
        str: Dados do protocolo criado em formato JSON.
    """

    protocolos = chamados_db.get(usuario_id, [])
    if protocolos:
        return (
            "Não é possível criar outro protocolo, pois ainda existe outro protocolo aberto.\n"
            f"Protocolos atuais: {json.dumps(protocolos, ensure_ascii=False)}"
        )

    # Datas
    hoje = datetime.today()
    data_criacao = hoje.strftime("%Y-%m-%d")
    previsao_conclusao = (hoje + timedelta(days=10)).strftime("%Y-%m-%d")

    # Gera protocolo aleatório
    protocolo_id = gerar_protocolo_aleatorio()

    # Cria novo protocolo
    novo_protocolo = {
        "protocolo": protocolo_id,
        "tipo": "2ª_via_cartao",
        "data_criacao": data_criacao,
        "previsao_conclusao": previsao_conclusao,
        "solicitação_dentro_do_prazo": True,
        "descricao": descricao
    }

    # Adiciona à base
    if usuario_id in chamados_db:
        chamados_db[usuario_id].append(novo_protocolo)
        
    else:
        chamados_db[usuario_id] = [novo_protocolo]
    #Envia email com o protocolo
    print(f"Enviando email para {usuario_id} com protocolo {novo_protocolo}")
    await enviar_protocolo_por_email(str(cpf), novo_protocolo)
    
    return json.dumps(novo_protocolo, ensure_ascii=False)



