"""
Tools para o Bot Central - Geolocalização e Informações de Unidades
"""

import os
import requests
import json
import time
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
            unidades = json.load(f)
            return unidades, "https://buddhaspa.com.br/unidades"
    except Exception as e:
        print(f"❌ Erro ao carregar unidades: {e}")
        return [], "https://buddhaspa.com.br/unidades"


def _geocode_por_cep_sync(cep: str) -> tuple:
    """Geocodifica CEP para sincronização com API (usado apenas para novas unidades)"""
    try:
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        if len(cep_limpo) != 8:
            return None, None
        
        # ViaCEP
        response = requests.get(f'https://viacep.com.br/ws/{cep_limpo}/json/', timeout=5)
        if response.status_code != 200 or response.json().get('erro'):
            return None, None
        
        data = response.json()
        logradouro = data.get('logradouro', '')
        bairro = data.get('bairro', '')
        cidade = data.get('localidade', '')
        uf = data.get('uf', '')
        
        if logradouro:
            endereco = f"{logradouro}, {bairro}, {cidade} - {uf}, Brasil"
        else:
            endereco = f"{cidade} - {uf}, Brasil"
        
        # Nominatim
        time.sleep(1)
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': endereco, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'BuddhaSpaBot/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                return float(results[0]['lat']), float(results[0]['lon'])
        
        return None, None
    except:
        return None, None


def _sincronizar_unidades_com_api():
    """
    Sincroniza unidades.json com a API de franqueadas se houver diferenças.
    Ignora latitude/longitude na comparação.
    Geocodifica novas unidades ou unidades com endereço alterado.
    """
    try:
        print("🔄 Sincronizando com API de franqueadas...")
        
        # Busca token da API
        api_token = os.getenv('PRD_LABELLE_TOKEN', '')
        if not api_token:
            print("⚠️ Token da API não configurado, usando dados locais")
            return False
        
        # Chama API
        headers = {'Authorization': api_token}
        response = requests.get(
            'https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/franqueadas',
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️ Erro na API (status {response.status_code}), usando dados locais")
            return False
        
        franqueadas_api = response.json()
        
        # Carrega dados locais
        try:
            with open('data/unidades.json', 'r', encoding='utf-8') as f:
                unidades_locais = json.load(f)
        except:
            unidades_locais = []
        
        # Cria dicionário de unidades locais por ID para comparação
        locais_por_id = {u.get('id'): u for u in unidades_locais if u.get('id')}
        
        # Compara ignorando latitude/longitude
        def campos_relevantes(unidade):
            """Retorna apenas campos relevantes para comparação (sem lat/lon)"""
            campos = unidade.copy()
            campos.pop('latitude', None)
            campos.pop('longitude', None)
            return campos
        
        precisa_atualizar = False
        unidades_para_geocodificar = []
        
        # Verifica cada unidade da API
        for unidade_api in franqueadas_api:
            unidade_id = unidade_api.get('id')
            
            if unidade_id in locais_por_id:
                # Unidade existe localmente, compara campos relevantes
                local = locais_por_id[unidade_id]
                
                if campos_relevantes(unidade_api) != campos_relevantes(local):
                    # Endereço ou outros dados mudaram
                    print(f"   📝 Unidade alterada: {unidade_api.get('nomeFantasiaFranqueada')}")
                    precisa_atualizar = True
                    unidades_para_geocodificar.append(unidade_api)
                else:
                    # Mantém lat/lon existentes
                    if 'latitude' in local:
                        unidade_api['latitude'] = local['latitude']
                    if 'longitude' in local:
                        unidade_api['longitude'] = local['longitude']
            else:
                # Nova unidade
                print(f"   ➕ Nova unidade: {unidade_api.get('nomeFantasiaFranqueada')}")
                precisa_atualizar = True
                unidades_para_geocodificar.append(unidade_api)
        
        # Verifica se alguma unidade foi removida
        ids_api = {u.get('id') for u in franqueadas_api}
        ids_locais = set(locais_por_id.keys())
        removidas = ids_locais - ids_api
        if removidas:
            print(f"   ➖ Unidades removidas: {len(removidas)}")
            precisa_atualizar = True
        
        if not precisa_atualizar:
            print("✅ unidades.json já está atualizado")
            return False
        
        # Geocodifica unidades novas ou alteradas
        if unidades_para_geocodificar:
            print(f"🌍 Geocodificando {len(unidades_para_geocodificar)} unidades...")
            
            for unidade in unidades_para_geocodificar:
                # Tenta geocodificar por CEP
                cep = unidade.get('cepFranqueada', '')
                if cep:
                    lat, lon = _geocode_por_cep_sync(cep)
                    if lat and lon:
                        unidade['latitude'] = lat
                        unidade['longitude'] = lon
                        print(f"   ✓ {unidade.get('nomeFantasiaFranqueada')}")
                    else:
                        print(f"   ⚠️ Falhou: {unidade.get('nomeFantasiaFranqueada')}")
        
        # Salva nova versão
        print(f"💾 Salvando unidades.json...")
        print(f"   API: {len(franqueadas_api)} unidades")
        print(f"   Local: {len(unidades_locais)} unidades")
        
        with open('data/unidades.json', 'w', encoding='utf-8') as f:
            json.dump(franqueadas_api, f, ensure_ascii=False, indent=4)
        
        print("✅ unidades.json atualizado com sucesso")
        return True
            
    except Exception as e:
        print(f"⚠️ Erro ao sincronizar com API: {e}")
        print("   Continuando com dados locais...")
        return False


@Tool
async def buscar_endereco_por_cep(
    ctx: RunContext[MyDeps],
    cep: str
) -> str:
    """
    Valida CEP e retorna endereço completo usando ViaCEP.
    TAMBÉM sincroniza unidades.json com a API de franqueadas.
    
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
    
    # Sincroniza com API de franqueadas
    _sincronizar_unidades_com_api()
    
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
    
    print(f"✅ {len(unidades)} unidades carregadas")
    
    # Calcula distância para cada unidade
    usuario_coords = (lat_usuario, lon_usuario)
    unidades_com_distancia = []
    
    for unidade in unidades:
        # Pula se não tiver lat/lon pré-calculados
        if not unidade.get('latitude') or not unidade.get('longitude'):
            continue
        
        lat = unidade['latitude']
        lon = unidade['longitude']
        
        unidade_coords = (lat, lon)
        distancia_km = geodesic(usuario_coords, unidade_coords).kilometers
        
        # Monta endereço completo
        endereco_completo = f"{unidade.get('enderecoFranqueada', '')}, {unidade.get('numeroFranqueada', '')}"
        if unidade.get('bairroFranqueada'):
            endereco_completo += f" - {unidade['bairroFranqueada']}"
        if unidade.get('cidadeFranqueada'):
            endereco_completo += f", {unidade['cidadeFranqueada']}"
        if unidade.get('ufFranqueada'):
            endereco_completo += f" - {unidade['ufFranqueada']}"
        if unidade.get('cepFranqueada'):
            endereco_completo += f", CEP: {unidade['cepFranqueada']}"
        
        unidades_com_distancia.append({
            'id': unidade.get('id'),
            'nome': unidade.get('nomeFantasiaFranqueada', 'Buddha Spa'),
            'endereco_completo': endereco_completo,
            'cep': unidade.get('cepFranqueada', ''),
            'telefone': unidade.get('telefoneFranqueada', ''),
            'whatsapp': unidade.get('celularFranqueada', ''),
            'email': unidade.get('emailFranqueada', ''),
            'horario_funcionamento': 'Consulte a unidade',
            'latitude': lat,
            'longitude': lon,
            'link_maps': unidade.get('link_maps', f"https://maps.google.com/?q={lat},{lon}"),
            'distancia_km': distancia_km
        })
    
    if not unidades_com_distancia:
        print("❌ Nenhuma unidade válida encontrada")
        return f"❌ Não encontrei unidades próximas. Veja todas em: {link_todas}"
    
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

📍 *{unidade_proxima['nome']}*
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
    Encontra as 5 unidades mais próximas do usuário.
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
    
    print(f"✅ {len(unidades)} unidades carregadas")
    
    # Calcula distância para cada unidade
    usuario_coords = (lat_usuario, lon_usuario)
    unidades_com_distancia = []
    
    for unidade in unidades:
        # Pula se não tiver lat/lon pré-calculados
        if not unidade.get('latitude') or not unidade.get('longitude'):
            continue
        
        lat = unidade['latitude']
        lon = unidade['longitude']
        
        unidade_coords = (lat, lon)
        distancia_km = geodesic(usuario_coords, unidade_coords).kilometers
        
        # Monta endereço completo
        endereco_completo = f"{unidade.get('enderecoFranqueada', '')}, {unidade.get('numeroFranqueada', '')}"
        if unidade.get('bairroFranqueada'):
            endereco_completo += f" - {unidade['bairroFranqueada']}"
        if unidade.get('cidadeFranqueada'):
            endereco_completo += f", {unidade['cidadeFranqueada']}"
        if unidade.get('ufFranqueada'):
            endereco_completo += f" - {unidade['ufFranqueada']}"
        if unidade.get('cepFranqueada'):
            endereco_completo += f", CEP: {unidade['cepFranqueada']}"
        
        unidades_com_distancia.append({
            'id': unidade.get('id'),
            'nome': unidade.get('nomeFantasiaFranqueada', 'Buddha Spa'),
            'endereco_completo': endereco_completo,
            'cep': unidade.get('cepFranqueada', ''),
            'telefone': unidade.get('telefoneFranqueada', ''),
            'whatsapp': unidade.get('celularFranqueada', ''),
            'email': unidade.get('emailFranqueada', ''),
            'horario_funcionamento': 'Consulte a unidade',
            'latitude': lat,
            'longitude': lon,
            'link_maps': unidade.get('link_maps', f"https://maps.google.com/?q={lat},{lon}"),
            'distancia_km': distancia_km
        })
    
    if not unidades_com_distancia:
        print("❌ Nenhuma unidade válida encontrada")
        return "NAO_ENCONTRADO"
    
    # Ordena por distância (mais próxima primeiro)
    unidades_com_distancia.sort(key=lambda x: x['distancia_km'])
    
    # Pega as 5 mais próximas (ou menos se não houver 5)
    unidades_proximas = unidades_com_distancia[:5]
    
    # Se só encontrou 1 unidade, retorna como única
    if len(unidades_proximas) == 1:
        unidade_unica = unidades_proximas[0]
        print(f"✅ Apenas uma unidade encontrada: {unidade_unica['nome']}")
        print(f"   Distância: {unidade_unica['distancia_km']:.2f} km")
        print("=" * 80)
        
        # Armazena no contexto
        update_context(conversation_id, {
            'unidade_encontrada': unidade_unica,
            'unidades_multiplas': None
        })
        
        dados = f"{unidade_unica['nome']}|{unidade_unica['endereco_completo']}|{unidade_unica['telefone']}|{unidade_unica['whatsapp']}|{unidade_unica['email']}|{unidade_unica['horario_funcionamento']}|{unidade_unica['link_maps']}"
        return f"UNICA|{dados}"
    
    # Se encontrou múltiplas unidades, retorna lista
    print(f"✅ {len(unidades_proximas)} unidades mais próximas encontradas:")
    for i, u in enumerate(unidades_proximas, 1):
        print(f"   {i}. {u['nome']} - {u['distancia_km']:.2f} km")
    print("=" * 80)
    
    # Armazena no contexto
    update_context(conversation_id, {
        'unidade_encontrada': unidades_proximas[0],  # A mais próxima
        'unidades_multiplas': unidades_proximas
    })
    
    # Retorna lista de nomes
    lista_nomes = [u['nome'] for u in unidades_proximas]
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
    
    print(f"✅ {len(unidades)} unidades carregadas")
    
    mensagem = "📍 *Todas as unidades Buddha Spa:*\n\n"
    
    for unidade in unidades:
        # Pula se não tiver lat/lon pré-calculados
        if not unidade.get('latitude') or not unidade.get('longitude'):
            continue
        
        lat = unidade['latitude']
        lon = unidade['longitude']
        
        # Monta endereço completo
        endereco_completo = f"{unidade.get('enderecoFranqueada', '')}, {unidade.get('numeroFranqueada', '')}"
        if unidade.get('bairroFranqueada'):
            endereco_completo += f" - {unidade['bairroFranqueada']}"
        if unidade.get('cidadeFranqueada'):
            endereco_completo += f", {unidade['cidadeFranqueada']}"
        if unidade.get('ufFranqueada'):
            endereco_completo += f" - {unidade['ufFranqueada']}"
        if unidade.get('cepFranqueada'):
            endereco_completo += f", CEP: {unidade['cepFranqueada']}"
        
        mensagem += f"*{unidade.get('nomeFantasiaFranqueada', 'Buddha Spa')}*\n"
        mensagem += f"📍 {endereco_completo}\n"
        mensagem += f"📞 {unidade.get('telefoneFranqueada', 'N/A')}\n"
        mensagem += f"📱 {unidade.get('celularFranqueada', 'N/A')}\n"
        mensagem += f"🗺️ {unidade.get('link_maps', f'https://maps.google.com/?q={lat},{lon}')}\n\n"
    
    mensagem += f"\n🔗 Ver todas no site: {link_todas}"
    
    print(f"✅ Unidades listadas com sucesso")
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
