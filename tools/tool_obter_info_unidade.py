"""
Tool para obter informações detalhadas de uma unidade específica
"""

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool
from agents.deps import MyDeps
from store.database import get_session
import json


@Tool
async def obter_info_unidade(
    ctx: RunContext[MyDeps],
    nome_unidade: str
) -> str:
    """
    Obtém informações detalhadas de uma unidade específica do contexto.
    Usa a lista de unidades_multiplas armazenada no contexto.
    
    Args:
        nome_unidade: Nome da unidade escolhida pelo usuário
    
    Returns:
        str: "ENCONTRADA|dados" ou "NAO_ENCONTRADA"
    """
    conversation_id = ctx.deps.session_id
    
    # Busca unidades_multiplas do deps (já carregado do banco)
    unidades_multiplas = ctx.deps.unidades_multiplas
    
    print("=" * 80)
    print("🔍 TOOL: obter_info_unidade")
    print(f"Unidade solicitada: {nome_unidade}")
    print(f"Unidades disponíveis: {len(unidades_multiplas) if unidades_multiplas else 0}")
    print("=" * 80)
    
    if not unidades_multiplas:
        print("❌ Nenhuma unidade múltipla no contexto")
        return "NAO_ENCONTRADA"
    
    # Verifica se é um número (seleção por índice)
    unidade_encontrada = None
    
    try:
        # Tenta converter para número (1, 2, 3, etc.)
        indice = int(nome_unidade) - 1  # Converte para índice 0-based
        if 0 <= indice < len(unidades_multiplas):
            unidade_encontrada = unidades_multiplas[indice]
            print(f"✅ Unidade selecionada por índice {indice + 1}")
    except ValueError:
        # Não é um número, busca por nome
        nome_lower = nome_unidade.lower()
        for unidade in unidades_multiplas:
            if nome_lower in unidade['nome'].lower():
                unidade_encontrada = unidade
                print(f"✅ Unidade selecionada por nome: {nome_unidade}")
                break
    
    if not unidade_encontrada:
        print(f"❌ Unidade '{nome_unidade}' não encontrada na lista")
        return "NAO_ENCONTRADA"
    
    print(f"✅ Unidade encontrada: {unidade_encontrada['nome']}")
    print("=" * 80)
    
    # Retorna dados formatados
    dados = f"{unidade_encontrada['nome']}|{unidade_encontrada['endereco_completo']}|{unidade_encontrada['telefone']}|{unidade_encontrada['whatsapp']}|{unidade_encontrada['email']}|{unidade_encontrada['horario_funcionamento']}|{unidade_encontrada['link_maps']}"
    return f"ENCONTRADA|{dados}"
