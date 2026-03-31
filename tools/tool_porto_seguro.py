from pydantic_ai.tools import Tool
import requests
from typing import Optional

# Base simulada de clientes
base_clientes = {
    "35996699885": {
        "id": "1",
        "nome": "Rodrigo Santos Moraes",
        "cpf": "35996699885",
        "celular": "+5511957423808",
        "email": "rodrigo-smoraes@hotmail.com",
        "estado": "AL",
        "cidade": "Maceió",
        "bairro": "",
        "CEP": "57036-860",
        "endereco": "Rua Ernesto Gomes Maranhão 256",
        "plano": "ODONTO BRONZE",
        "termino_carencia": "2025-12-25"
    },
    "98765432100": {
        "id": "2",
        "nome": "Thiago Morando",
        "cpf": "98765432100",
        "celular": "(21) 99876-5432",
        "email": "thiago.soares@portoseguro.com.br",
        "estado": "BA",
        "cidade": "Feira de Santana",
        "bairro": "Centro",
        "CEP": "44001-584",
        "endereco": "Av. Sampaio 444",
        "plano": "ODONTO OURO",
        "termino_carencia": "2025-10-05"
    }
}

@Tool
def consultar_cliente_porto(cpf: str) -> str:
    """
    Consulta informações do cliente na base de dados Porto Seguro.

    Args:
        cpf (str): CPF do cliente a ser consultado.
        
    Returns:
        str: Informações do cliente em formato JSON ou "nao_encontrado".
    """

    # Verifica se o CPF informado está na base
    cliente_info = base_clientes.get(cpf)

    if cliente_info:
        import json
        return json.dumps(cliente_info, ensure_ascii=False)
    else:
        return "usuário nao encontrado"

@Tool
def consultar_clinicas_porto(
    uf: str,
    cidade: str,
    bairro: str,
    especialidade: str,
    plano: str,
    page: int = 1,
    page_size: int = 10
) -> str:
    """
    Consulta clínicas na base Porto Seguro via API FastAPI.

    Args:
        uf (str): Unidade federativa.
        cidade (str): Cidade em maiuscula e sem acentuação.
        bairro (str): Bairro em maiuscula e sem acentuação, caso não informado utilize o bairro de residência do usuário.
        especialidade (str): Especialidade odontológica opção clinica_geral, cirurgia, clareamento_dental ou clareamento_dental_a_laser.
        plano (str): Plano do cliente, pode ser odonto_bronze, odonto_diamante, odonto_prata, odonto_ouro e odonto_pro_doc.
        page (int, optional): Número da página (padrão 1).
        page_size (int, optional): Tamanho da página (padrão 10).

    Returns:
        str: Resultado da consulta em formato JSON ou "nenhuma clínica encontrada".
    """
    url = "https://hlb6mfkf-8000.brs.devtunnels.ms/clinicas"  # Ajuste para a URL correta do seu FastAPI

    params = {
        "uf": uf,
        "cidade": cidade,
        "bairro": bairro,
        "especialidade": especialidade,
        "plano": plano,
        "page": page,
        "page_size": page_size
    }

    # Remove parâmetros None
    params = {k: v for k, v in params.items() if v is not None}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return "nenhuma clínica encontrada"

        import json
        return json.dumps(data, ensure_ascii=False)

    except requests.RequestException as e:
        return f"erro na consulta: {str(e)}"