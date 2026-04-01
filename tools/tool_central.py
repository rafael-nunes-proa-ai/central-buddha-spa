"""
Tools para o Bot Central - Geolocalização e Informações de Unidades
"""

import os
import requests
import json
from pydantic_ai import RunContext
from pydantic_ai.tools import Tool
from agents.deps import MyDeps
from store.database import update_context, get_session
from geopy.distance import geodesic
from utils import registrar_step, registrar_assunto
import re


# Carrega dados das unidades
def _carregar_unidades():
    """Carrega dados das unidades do arquivo JSON"""
    try:
        with open('data/unidades.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['unidades'], data['link_todas_unidades']
    except Exception as e:
        print(f"❌ Erro ao carregar unidades: {e}")
        return [], "https://buddhaspa.com.br/unidades"


@Tool
async def buscar_endereco_por_cep(
    ctx: RunContext[MyDeps],
    cep: str
) -> str:
    """
    Valida CEP e retorna endereço completo usando ViaCEP.
    
    Args:
        cep: CEP informado pelo usuário (com ou sem hífen)
    
    Returns:
        str: "VALIDO|cidade|estado|bairro" ou "INVALIDO|mensagem_erro"
    """
    conversation_id = ctx.deps.session_id
    
    # Limpa CEP (remove hífen e espaços)
    cep_limpo = re.sub(r'[^0-9]', '', cep)
    
    print("=" * 80)
    print("🔍 TOOL: buscar_endereco_por_cep")
    print(f"CEP informado: {cep}")
    print(f"CEP limpo: {cep_limpo}")
    print("=" * 80)
    
    # Valida formato
    if len(cep_limpo) != 8:
        print("❌ CEP inválido: formato incorreto")
        return "INVALIDO|CEP deve ter 8 dígitos"
    
    # Consulta ViaCEP
    try:
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # Verifica se CEP existe
        if data.get('erro'):
            print("❌ CEP não encontrado")
            return "INVALIDO|CEP não encontrado"
        
        cidade = data.get('localidade', '')
        estado = data.get('uf', '')
        bairro = data.get('bairro', '')
        
        # Armazena no contexto
        update_context(conversation_id, {
            'cep_informado': cep_limpo,
            'cidade_informada': cidade,
            'estado_informado': estado,
            'bairro_informado': bairro
        })
        
        print(f"✅ CEP válido:")
        print(f"   Cidade: {cidade}")
        print(f"   Estado: {estado}")
        print(f"   Bairro: {bairro}")
        print("=" * 80)
        
        return f"VALIDO|{cidade}|{estado}|{bairro}"
    
    except Exception as e:
        print(f"❌ Erro ao consultar ViaCEP: {e}")
        print("=" * 80)
        return "INVALIDO|Erro ao consultar CEP"


@Tool
async def buscar_coordenadas_por_endereco(
    ctx: RunContext[MyDeps]
) -> str:
    """
    Busca coordenadas (lat/lon) usando Nominatim (OpenStreetMap).
    Usa cidade, estado e bairro do contexto.
    
    Returns:
        str: "ENCONTRADO|latitude|longitude" ou "NAO_ENCONTRADO"
    """
    conversation_id = ctx.deps.session_id
    
    # Busca dados do contexto
    session = get_session(conversation_id)
    context = session[2] if session else {}
    
    if isinstance(context, str):
        try:
            context = json.loads(context) if context else {}
        except:
            context = {}
    
    cidade = context.get('cidade_informada', '')
    estado = context.get('estado_informado', '')
    bairro = context.get('bairro_informado', '')
    
    print("=" * 80)
    print("🌍 TOOL: buscar_coordenadas_por_endereco")
    print(f"Cidade: {cidade}")
    print(f"Estado: {estado}")
    print(f"Bairro: {bairro}")
    print("=" * 80)
    
    if not cidade or not estado:
        print("❌ Dados insuficientes")
        return "NAO_ENCONTRADO"
    
    # Monta query para Nominatim
    if bairro:
        query = f"{bairro}, {cidade}, {estado}, Brasil"
    else:
        query = f"{cidade}, {estado}, Brasil"
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'BuddhaSpaBot/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            print("❌ Coordenadas não encontradas")
            return "NAO_ENCONTRADO"
        
        latitude = float(data[0]['lat'])
        longitude = float(data[0]['lon'])
        
        # Armazena no contexto
        update_context(conversation_id, {
            'latitude_usuario': latitude,
            'longitude_usuario': longitude
        })
        
        print(f"✅ Coordenadas encontradas:")
        print(f"   Latitude: {latitude}")
        print(f"   Longitude: {longitude}")
        print("=" * 80)
        
        return f"ENCONTRADO|{latitude}|{longitude}"
    
    except Exception as e:
        print(f"❌ Erro ao buscar coordenadas: {e}")
        print("=" * 80)
        return "NAO_ENCONTRADO"


@Tool
async def encontrar_unidade_mais_proxima(
    ctx: RunContext[MyDeps]
) -> str:
    """
    Encontra a unidade mais próxima usando cálculo geodésico.
    Usa latitude e longitude do contexto.
    
    Returns:
        str: Informações formatadas da unidade mais próxima ou mensagem de erro
    """
    conversation_id = ctx.deps.session_id
    
    # Busca dados do contexto
    session = get_session(conversation_id)
    context = session[2] if session else {}
    
    if isinstance(context, str):
        try:
            context = json.loads(context) if context else {}
        except:
            context = {}
    
    lat_usuario = context.get('latitude_usuario')
    lon_usuario = context.get('longitude_usuario')
    
    print("=" * 80)
    print("📍 TOOL: encontrar_unidade_mais_proxima")
    print(f"Lat usuário: {lat_usuario}")
    print(f"Lon usuário: {lon_usuario}")
    print("=" * 80)
    
    if not lat_usuario or not lon_usuario:
        print("❌ Coordenadas do usuário não disponíveis")
        return "❌ Não foi possível determinar sua localização."
    
    # Carrega unidades
    unidades, link_todas = _carregar_unidades()
    
    if not unidades:
        print("❌ Nenhuma unidade cadastrada")
        return f"❌ Erro ao carregar unidades. Veja todas em: {link_todas}"
    
    # Calcula distância para cada unidade
    usuario_coords = (lat_usuario, lon_usuario)
    unidades_com_distancia = []
    
    for unidade in unidades:
        unidade_coords = (unidade['latitude'], unidade['longitude'])
        distancia_km = geodesic(usuario_coords, unidade_coords).kilometers
        
        unidades_com_distancia.append({
            **unidade,
            'distancia_km': distancia_km
        })
    
    # Ordena por distância
    unidades_com_distancia.sort(key=lambda x: x['distancia_km'])
    
    # Pega a mais próxima
    unidade_proxima = unidades_com_distancia[0]
    
    # Armazena no contexto
    update_context(conversation_id, {
        'unidade_encontrada': unidade_proxima
    })
    
    # Formata resposta
    distancia_formatada = f"{unidade_proxima['distancia_km']:.1f} km"
    
    mensagem = f"""✅ Encontrei a unidade mais próxima de você! 😊

📍 **{unidade_proxima['nome']}**
📏 Distância: {distancia_formatada}
🏠 Endereço: {unidade_proxima['endereco_completo']}
📞 Telefone: {unidade_proxima['telefone']}
📱 WhatsApp: {unidade_proxima['whatsapp']}
📧 E-mail: {unidade_proxima['email']}
🕒 Horário: {unidade_proxima['horario_funcionamento']}
🗺️ Ver no mapa: {unidade_proxima['link_maps']}

Deseja consultar outra unidade?"""
    
    print(f"✅ Unidade encontrada: {unidade_proxima['nome']}")
    print(f"   Distância: {distancia_formatada}")
    print("=" * 80)
    
    return mensagem


@Tool
async def encontrar_unidades_no_raio(
    ctx: RunContext[MyDeps]
) -> str:
    """
    Encontra unidades num raio de 5km da unidade mais próxima.
    Retorna até 5 unidades mais próximas para o usuário escolher.
    Usa latitude e longitude do contexto.
    
    Returns:
        str: "UNICA|dados" ou "MULTIPLAS|lista_nomes" ou "NAO_ENCONTRADO"
    """
    conversation_id = ctx.deps.session_id
    
    # Busca dados do contexto
    session = get_session(conversation_id)
    context = session[2] if session else {}
    
    if isinstance(context, str):
        try:
            context = json.loads(context) if context else {}
        except:
            context = {}
    
    lat_usuario = context.get('latitude_usuario')
    lon_usuario = context.get('longitude_usuario')
    
    print("=" * 80)
    print("📍 TOOL: encontrar_unidades_no_raio")
    print(f"Lat usuário: {lat_usuario}")
    print(f"Lon usuário: {lon_usuario}")
    print("=" * 80)
    
    if not lat_usuario or not lon_usuario:
        print("❌ Coordenadas do usuário não disponíveis")
        return "NAO_ENCONTRADO"
    
    # Carrega unidades
    unidades, link_todas = _carregar_unidades()
    
    if not unidades:
        print("❌ Nenhuma unidade cadastrada")
        return "NAO_ENCONTRADO"
    
    # Calcula distância para cada unidade
    usuario_coords = (lat_usuario, lon_usuario)
    unidades_com_distancia = []
    
    for unidade in unidades:
        unidade_coords = (unidade['latitude'], unidade['longitude'])
        distancia_km = geodesic(usuario_coords, unidade_coords).kilometers
        
        unidades_com_distancia.append({
            **unidade,
            'distancia_km': distancia_km
        })
    
    # Ordena por distância
    unidades_com_distancia.sort(key=lambda x: x['distancia_km'])
    
    # Pega a mais próxima
    unidade_proxima = unidades_com_distancia[0]
    
    # Busca outras unidades num raio de 5km da mais próxima
    raio_km = 5.0
    unidades_no_raio = []
    
    for unidade in unidades_com_distancia:
        if unidade['nome'] != unidade_proxima['nome']:  # Exclui a própria unidade
            unidade_coords = (unidade['latitude'], unidade['longitude'])
            proxima_coords = (unidade_proxima['latitude'], unidade_proxima['longitude'])
            distancia_da_proxima = geodesic(proxima_coords, unidade_coords).kilometers
            
            if distancia_da_proxima <= raio_km:
                unidades_no_raio.append(unidade)
    
    # Se não encontrou outras unidades no raio, retorna apenas a mais próxima
    if not unidades_no_raio:
        print(f"✅ Apenas uma unidade encontrada: {unidade_proxima['nome']}")
        print("=" * 80)
        
        # Armazena no contexto
        update_context(conversation_id, {
            'unidade_encontrada': unidade_proxima,
            'unidades_multiplas': None
        })
        
        dados = f"{unidade_proxima['nome']}|{unidade_proxima['endereco_completo']}|{unidade_proxima['telefone']}|{unidade_proxima['whatsapp']}|{unidade_proxima['email']}|{unidade_proxima['horario_funcionamento']}|{unidade_proxima['link_maps']}"
        return f"UNICA|{dados}"
    
    # Se encontrou outras unidades no raio, retorna lista (máximo 5)
    todas_unidades = [unidade_proxima] + unidades_no_raio[:4]  # Máximo 5 unidades
    
    print(f"✅ Múltiplas unidades encontradas: {len(todas_unidades)}")
    for u in todas_unidades:
        print(f"   - {u['nome']}")
    print("=" * 80)
    
    # Armazena no contexto
    update_context(conversation_id, {
        'unidade_encontrada': unidade_proxima,
        'unidades_multiplas': todas_unidades
    })
    
    # Retorna lista de nomes
    lista_nomes = [u['nome'] for u in todas_unidades]
    return f"MULTIPLAS|{'|'.join(lista_nomes)}"


@Tool
async def buscar_bairros_por_nome(
    ctx: RunContext[MyDeps],
    nome_bairro: str
) -> str:
    """
    Busca bairros pelo nome usando Nominatim.
    Pode retornar múltiplos resultados se houver bairros com mesmo nome.
    
    Args:
        nome_bairro: Nome do bairro informado pelo usuário
    
    Returns:
        str: "UNICO|cidade|estado" ou "MULTIPLOS|lista" ou "NAO_ENCONTRADO"
    """
    conversation_id = ctx.deps.session_id
    
    print("=" * 80)
    print("🔍 TOOL: buscar_bairros_por_nome")
    print(f"Bairro: {nome_bairro}")
    print("=" * 80)
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{nome_bairro}, Brasil",
            'format': 'json',
            'limit': 10,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'BuddhaSpaBot/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            print("❌ Bairro não encontrado")
            return "NAO_ENCONTRADO"
        
        # Filtra apenas resultados do Brasil
        resultados_brasil = []
        for item in data:
            address = item.get('address', {})
            if address.get('country') == 'Brasil' or address.get('country_code') == 'br':
                cidade = address.get('city') or address.get('town') or address.get('municipality', '')
                estado = address.get('state', '')
                
                if cidade and estado:
                    resultados_brasil.append({
                        'bairro': nome_bairro,
                        'cidade': cidade,
                        'estado': estado,
                        'latitude': float(item['lat']),
                        'longitude': float(item['lon'])
                    })
        
        if not resultados_brasil:
            print("❌ Nenhum resultado no Brasil")
            return "NAO_ENCONTRADO"
        
        # Remove duplicatas (mesma cidade/estado)
        resultados_unicos = []
        vistos = set()
        for r in resultados_brasil:
            chave = f"{r['cidade']}|{r['estado']}"
            if chave not in vistos:
                vistos.add(chave)
                resultados_unicos.append(r)
        
        if len(resultados_unicos) == 1:
            # Apenas um bairro encontrado
            resultado = resultados_unicos[0]
            
            # Armazena no contexto
            update_context(conversation_id, {
                'bairro_informado': resultado['bairro'],
                'cidade_informada': resultado['cidade'],
                'estado_informado': resultado['estado'],
                'latitude_usuario': resultado['latitude'],
                'longitude_usuario': resultado['longitude']
            })
            
            print(f"✅ Bairro único encontrado:")
            print(f"   {resultado['bairro']} - {resultado['cidade']}/{resultado['estado']}")
            print("=" * 80)
            
            return f"UNICO|{resultado['cidade']}|{resultado['estado']}"
        
        else:
            # Múltiplos bairros encontrados
            lista_bairros = []
            for i, r in enumerate(resultados_unicos[:5], 1):  # Limita a 5
                lista_bairros.append(f"{i}. {r['bairro']} - {r['cidade']}/{r['estado']}")
            
            lista_formatada = "\n".join(lista_bairros)
            
            print(f"⚠️ Múltiplos bairros encontrados: {len(resultados_unicos)}")
            print("=" * 80)
            
            return f"MULTIPLOS|{lista_formatada}"
    
    except Exception as e:
        print(f"❌ Erro ao buscar bairro: {e}")
        print("=" * 80)
        return "NAO_ENCONTRADO"


@Tool
async def listar_todas_unidades(
    ctx: RunContext[MyDeps]
) -> str:
    """
    Lista todas as unidades disponíveis.
    
    Returns:
        str: Lista formatada de todas as unidades
    """
    print("=" * 80)
    print("📋 TOOL: listar_todas_unidades")
    print("=" * 80)
    
    unidades, link_todas = _carregar_unidades()
    
    if not unidades:
        return f"❌ Erro ao carregar unidades. Veja todas em: {link_todas}"
    
    mensagem = "📍 **Todas as unidades Buddha Spa:**\n\n"
    
    for unidade in unidades:
        mensagem += f"**{unidade['nome']}**\n"
        mensagem += f"📍 {unidade['endereco_completo']}\n"
        mensagem += f"📞 {unidade['telefone']}\n"
        mensagem += f"📱 {unidade['whatsapp']}\n"
        mensagem += f"🗺️ {unidade['link_maps']}\n\n"
    
    mensagem += f"\n🔗 Ver todas no site: {link_todas}"
    
    print(f"✅ Listadas {len(unidades)} unidades")
    print("=" * 80)
    
    return mensagem


@Tool
async def incrementar_tentativas_agendamento(ctx: RunContext[MyDeps]) -> str:
    """
    Incrementa contador de tentativas de agendamento.
    Use esta tool SEMPRE que o usuário mencionar agendamento, compra, atendimento direto.
    Usado para evitar loop infinito quando usuário insiste em agendar.
    
    Returns:
        Confirmação do incremento
    """
    ctx.deps.tentativas_agendamento += 1
    
    print("=" * 80)
    print(f"⚠️ TENTATIVA DE AGENDAMENTO INCREMENTADA: {ctx.deps.tentativas_agendamento}")
    print("=" * 80)
    
    return "ok"


@Tool
async def marcar_contexto_cancelamento(ctx: RunContext[MyDeps]) -> str:
    """
    Marca o contexto como cancelamento para que outras tools possam detectar.
    Use esta tool SEMPRE no início do fluxo de cancelamento.
    Apenas marca o contexto internamente, não registra assunto.
    
    Returns:
        Confirmação do registro
    """
    # Marca contexto de cancelamento internamente
    ctx.deps.contexto_cancelamento = True
    
    print("=" * 80)
    print("🟠 CONTEXTO MARCADO: Cancelamento (interno)")
    print("=" * 80)
    
    return "ok"


@Tool
async def buscar_unidade_por_nome(
    ctx: RunContext[MyDeps],
    nome_unidade: str
) -> str:
    """
    Busca unidade/franqueada na API Belle Software pelo nome ou bairro.
    Usado no fluxo de reagendamento e cancelamento para encontrar o contato da unidade.
    
    Args:
        nome_unidade: Nome da unidade, bairro ou cidade informado pelo usuário
    
    Returns:
        str: "ENCONTRADA|dados" ou "MULTIPLAS|lista" ou "NAO_ENCONTRADA"
    """
    conversation_id = ctx.deps.session_id
    
    print("=" * 80)
    print("🔍 TOOL: buscar_unidade_por_nome")
    print(f"Nome/Bairro informado: {nome_unidade}")
    print(f"� Contexto cancelamento: {ctx.deps.contexto_cancelamento}")
    print("=" * 80)
    
    # Busca na API Belle
    try:
        token = os.getenv("PRD_LABELLE_TOKEN")
        if not token:
            return "ERRO|Token da API Belle não configurado"
        
        url = "https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/franqueadas"
        headers = {"Authorization": token}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erro na API Belle: {response.status_code}")
            return f"ERRO|Erro ao buscar unidades (código {response.status_code})"
        
        franqueadas = response.json()
        
        # Normaliza o termo de busca
        termo_busca = nome_unidade.lower().strip()
        
        # Filtra unidades que contenham o termo em qualquer campo relevante
        unidades_encontradas = []
        for unidade in franqueadas:
            nome_fantasia_franqueadora = (unidade.get('nomeFantasiaFranqueadora') or '').lower()
            razao_social_franqueadora = (unidade.get('razaoSocialFranqueadora') or '').lower()
            nome_fantasia_franqueada = (unidade.get('nomeFantasiaFranqueada') or '').lower()
            razao_social_franqueada = (unidade.get('razaoSocialFranqueada') or '').lower()
            bairro = (unidade.get('bairroFranqueada') or '').lower()
            cidade = (unidade.get('cidadeFranqueada') or '').lower()
            
            if (termo_busca in nome_fantasia_franqueadora or 
                termo_busca in razao_social_franqueadora or
                termo_busca in nome_fantasia_franqueada or
                termo_busca in razao_social_franqueada or
                termo_busca in bairro or 
                termo_busca in cidade):
                unidades_encontradas.append(unidade)
        
        if len(unidades_encontradas) == 0:
            print("❌ Nenhuma unidade encontrada")
            return "NAO_ENCONTRADA"
        
        elif len(unidades_encontradas) == 1:
            unidade = unidades_encontradas[0]
            
            # Armazena no contexto
            ctx.deps.nome_unidade_reagendamento = unidade.get('nomeFantasiaFranqueadora')
            update_context(conversation_id, {
                'nome_unidade_reagendamento': ctx.deps.nome_unidade_reagendamento
            })
            
            # Formata dados da unidade
            nome = unidade.get('nomeFantasiaFranqueadora', 'N/A')
            endereco = f"{unidade.get('enderecoFranqueada', '')}, {unidade.get('numeroFranqueada', '')}"
            bairro = unidade.get('bairroFranqueada', '')
            cidade = unidade.get('cidadeFranqueada', '')
            uf = unidade.get('ufFranqueada', '')
            cep = unidade.get('cepFranqueada', '')
            telefone = unidade.get('telefoneFranqueada', 'Não informado')
            celular = unidade.get('celularFranqueada', 'Não informado')
            email = unidade.get('emailFranqueada', 'Não informado')
            
            dados = f"{nome}|{endereco}|{bairro}|{cidade}|{uf}|{cep}|{telefone}|{celular}|{email}"
            
            print(f"✅ Unidade encontrada: {nome}")
            print("=" * 80)
            
            return f"ENCONTRADA|{dados}"
        
        else:
            # Múltiplas unidades encontradas
            lista_unidades = []
            for idx, unidade in enumerate(unidades_encontradas[:10], start=1):  # Limita a 10 resultados
                nome = unidade.get('nomeFantasiaFranqueadora', 'N/A')
                cidade = unidade.get('cidadeFranqueada', 'N/A')
                bairro = unidade.get('bairroFranqueada', 'N/A')
                lista_unidades.append(f"{idx}. {nome} - {bairro}, {cidade}")
            
            lista_str = "\n".join(lista_unidades)
            
            print(f"⚠️ Múltiplas unidades encontradas: {len(unidades_encontradas)}")
            print("=" * 80)
            
            return f"MULTIPLAS|{lista_str}"
    
    except requests.exceptions.Timeout:
        print("❌ Timeout na API Belle")
        return "ERRO|Timeout ao buscar unidades"
    except Exception as e:
        print(f"❌ Erro ao buscar unidade: {str(e)}")
        return f"ERRO|{str(e)}"


@Tool
async def encerrar_atendimento(ctx: RunContext[MyDeps]) -> str:
    """
    Encerra o atendimento e deleta a sessão de conversa.
    Deve ser chamada quando o usuário não quer mais ajuda ou solicita encerramento.
    
    Returns:
        str: Mensagem de despedida
    """
    from store.database import delete_session
    
    conversation_id = ctx.deps.session_id
    
    print("=" * 80)
    print("🔴 ENCERRANDO ATENDIMENTO")
    print(f"Session ID: {conversation_id}")
    print("=" * 80)
    
    try:
        delete_session(conversation_id)
        print(f"✅ Sessão {conversation_id} deletada com sucesso")
        print("=" * 80)
        return "Obrigado por entrar em contato com a Buddha Spa! 😊\n\nVolte sempre que precisar! 🙏"
    except Exception as e:
        print(f"❌ Erro ao deletar sessão: {e}")
        print("=" * 80)
        return "Obrigado por entrar em contato com a Buddha Spa! 😊\n\nVolte sempre que precisar! 🙏"
