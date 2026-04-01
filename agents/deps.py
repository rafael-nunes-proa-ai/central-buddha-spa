from dataclasses import dataclass
from typing import Optional

@dataclass
class MyDeps:
    """
    Dependências do Bot Central - Apenas campos necessários para geolocalização e contato
    """
    session_id: str
    
    # BOT CENTRAL - GEOLOCALIZAÇÃO
    cep_informado: Optional[str] = None
    bairro_informado: Optional[str] = None
    cidade_informada: Optional[str] = None
    estado_informado: Optional[str] = None
    latitude_usuario: Optional[float] = None
    longitude_usuario: Optional[float] = None
    unidade_encontrada: Optional[dict] = None
    unidades_multiplas: Optional[list] = None  # Lista de unidades quando encontra múltiplas no raio
    
    # BOT CENTRAL - CONTROLE DE TENTATIVAS
    tentativas_agendamento: int = 0  # Contador para evitar loop quando usuário insiste em agendar
    
    # BOT CENTRAL - REAGENDAMENTO
    quer_reagendar: Optional[bool] = None  # Se usuário quer reagendar
    quer_info_reagendamento: Optional[bool] = None  # Se quer apenas informações sobre reagendamento
    precisa_contato_unidade: Optional[bool] = None  # Se precisa do contato da unidade
    nome_unidade_reagendamento: Optional[str] = None  # Nome da unidade informada pelo usuário
    
    # BOT CENTRAL - CANCELAMENTO
    contexto_cancelamento: Optional[bool] = None  # Marcador interno para contexto de cancelamento
    
    # TRACKING DE NAVEGAÇÃO
    steps: Optional[list[str]] = None  # Histórico de steps percorridos pelo usuário
    assuntos: Optional[list[str]] = None  # Histórico de assuntos/temas da conversa (ex: contato unidade)