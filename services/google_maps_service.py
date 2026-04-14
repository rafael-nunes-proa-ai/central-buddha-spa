"""
Serviço de Geocodificação usando Google Maps API
Substitui LocationIQ com monitoramento de requisições
"""

import googlemaps
import os
import json
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
import threading

load_dotenv()

# Cliente Google Maps
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Arquivo para contador de requisições
COUNTER_FILE = Path(__file__).parent.parent / "data" / "google_maps_counter.json"

# Limites de alerta
# MODELO 2025: Google oferece 10.000 requisições GRÁTIS/mês para Geocoding API
# Após 10.000: $5 por 1.000 requisições (10k-100k), depois $4/1k (100k-500k)
LIMITE_ALERTA_GEOCODING = 5000  # Alerta quando atingir 50% da cota gratuita (10.000)
LIMITE_ALERTA_DISTANCE = 5000   # Alerta quando atingir 5.000 requisições

# Lock para evitar race condition
_counter_lock = threading.Lock()


def _carregar_contador():
    """Carrega contador de requisições do arquivo"""
    if not COUNTER_FILE.exists():
        return {
            "geocoding": {"total": 0, "mes_atual": 0, "ultimo_reset": str(date.today().replace(day=1))},
            "distance_matrix": {"total": 0, "mes_atual": 0, "ultimo_reset": str(date.today().replace(day=1))}
        }
    
    try:
        with open(COUNTER_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "geocoding": {"total": 0, "mes_atual": 0, "ultimo_reset": str(date.today().replace(day=1))},
            "distance_matrix": {"total": 0, "mes_atual": 0, "ultimo_reset": str(date.today().replace(day=1))}
        }


def _salvar_contador(contador):
    """Salva contador de requisições no arquivo"""
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COUNTER_FILE, 'w') as f:
        json.dump(contador, f, indent=2)
    print(f"💾 Contador salvo: geocoding={contador['geocoding']['mes_atual']}/{contador['geocoding']['total']}, distance_matrix={contador['distance_matrix']['mes_atual']}/{contador['distance_matrix']['total']}")


def _incrementar_contador(tipo: str):
    """
    Incrementa contador e verifica limites
    
    Args:
        tipo: 'geocoding' ou 'distance_matrix'
    """
    with _counter_lock:
        contador = _carregar_contador()
        
        # Reset mensal
        hoje = date.today()
        primeiro_dia_mes = str(hoje.replace(day=1))
        
        if contador[tipo]["ultimo_reset"] != primeiro_dia_mes:
            print(f"🔄 Reset mensal do contador {tipo}")
            contador[tipo]["mes_atual"] = 0
            contador[tipo]["ultimo_reset"] = primeiro_dia_mes
        
        # Incrementa
        contador[tipo]["total"] += 1
        contador[tipo]["mes_atual"] += 1
        
        print(f"➕ Incrementando {tipo}: mes_atual={contador[tipo]['mes_atual']}, total={contador[tipo]['total']}")
        
        # Salva
        _salvar_contador(contador)
        
        # Retorna valor atualizado para logging
        mes_atual = contador[tipo]["mes_atual"]
        total = contador[tipo]["total"]
        
        # Verifica limites (dentro do lock)
        if tipo == "geocoding" and mes_atual == LIMITE_ALERTA_GEOCODING:
            print("=" * 80)
            print("🚨 ALERTA: VOCÊ ATINGIU 50% DA COTA GRATUITA!")
            print(f"📊 Requisições este mês: {mes_atual}")
            print(f"⚠️  Cota gratuita: 10.000/mês (Geocoding API - Essentials)")
            print(f"💰 Após 10.000: $5 por 1.000 requisições (até 100k)")
            print(f"💰 Após 100.000: $4 por 1.000 requisições (até 500k)")
            print("=" * 80)
        
        if tipo == "geocoding" and mes_atual == 10000:
            print("=" * 80)
            print("⚠️️️ ⚠️️️ ATENÇÃO: COTA GRATUITA EXCEDIDA! ⚠️️️ ⚠️️️")
            print(f"📊 Requisições este mês: {mes_atual}")
            print(f"🚫 Você ultrapassou as 10.000 requisições gratuitas!")
            print(f"💰 Agora você está sendo cobrado: $5 por 1.000 requisições")
            print("=" * 80)
        
        if tipo == "distance_matrix" and mes_atual == LIMITE_ALERTA_DISTANCE:
            print("=" * 80)
            print("🚨 ALERTA: ALTO USO DE DISTANCE MATRIX API!")
            print(f"📊 Requisições este mês: {mes_atual}")
            print(f"⚠️  Distance Matrix é PAGO desde a primeira requisição")
            print(f"💰 Custo: $5 por 1.000 requisições (até 100k)")
            print(f"💰 Após 100.000: $4 por 1.000 requisições (até 500k)")
            print("=" * 80)
        
        # Log normal
        print(f"📊 Google Maps {tipo}: {mes_atual} requisições este mês (total: {total})")
        
        return mes_atual, total


def geocode_cep(cep: str):
    """
    Converte CEP em coordenadas usando Google Maps Geocoding API
    
    Args:
        cep: CEP brasileiro (com ou sem formatação)
    
    Returns:
        dict: {
            'lat': float,
            'lng': float,
            'bairro': str,
            'cidade': str,
            'estado': str,
            'endereco_completo': str
        } ou None se não encontrado
    """
    try:
        # Incrementa contador
        _incrementar_contador("geocoding")
        
        # Remove formatação do CEP
        cep_limpo = cep.replace('-', '').replace('.', '').replace(' ', '').strip()
        
        print(f"🔍 Google Geocoding: Buscando CEP {cep_limpo}")
        
        # Busca no Google Maps
        result = gmaps.geocode(f'{cep_limpo}, Brasil')
        
        if not result:
            print(f"❌ CEP {cep_limpo} não encontrado")
            return None
        
        location = result[0]['geometry']['location']
        address_components = result[0]['address_components']
        
        # Extrai componentes do endereço
        bairro = next((c['long_name'] for c in address_components 
                      if 'sublocality' in c['types'] or 'sublocality_level_1' in c['types']), '')
        
        cidade = next((c['long_name'] for c in address_components 
                      if 'administrative_area_level_2' in c['types']), '')
        
        estado = next((c['short_name'] for c in address_components 
                      if 'administrative_area_level_1' in c['types']), '')
        
        resultado = {
            'lat': location['lat'],
            'lng': location['lng'],
            'bairro': bairro,
            'cidade': cidade,
            'estado': estado,
            'endereco_completo': result[0]['formatted_address']
        }
        
        print(f"✅ CEP encontrado: {cidade}/{estado} - Bairro: {bairro}")
        print(f"📍 Coordenadas: {resultado['lat']}, {resultado['lng']}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro ao geocodificar CEP {cep}: {e}")
        return None


def calcular_distancia_real(origem_lat, origem_lng, destino_lat, destino_lng):
    """
    Calcula distância real de trajeto usando Google Distance Matrix API
    
    Args:
        origem_lat: Latitude de origem
        origem_lng: Longitude de origem
        destino_lat: Latitude de destino
        destino_lng: Longitude de destino
    
    Returns:
        dict: {
            'distancia_metros': int,
            'distancia_texto': str,  # "5.2 km"
            'duracao_segundos': int,
            'duracao_texto': str     # "15 mins"
        } ou None se erro
    """
    try:
        # Incrementa contador
        _incrementar_contador("distance_matrix")
        
        print(f"🚗 Google Distance Matrix: Calculando distância real")
        
        result = gmaps.distance_matrix(
            origins=[(origem_lat, origem_lng)],
            destinations=[(destino_lat, destino_lng)],
            mode='driving',
            language='pt-BR'
        )
        
        if result['rows'][0]['elements'][0]['status'] == 'OK':
            element = result['rows'][0]['elements'][0]
            
            resultado = {
                'distancia_metros': element['distance']['value'],
                'distancia_texto': element['distance']['text'],
                'duracao_segundos': element['duration']['value'],
                'duracao_texto': element['duration']['text']
            }
            
            print(f"✅ Distância: {resultado['distancia_texto']} - Tempo: {resultado['duracao_texto']}")
            
            return resultado
        else:
            print(f"❌ Não foi possível calcular distância")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao calcular distância: {e}")
        return None


def obter_estatisticas():
    """
    Retorna estatísticas de uso da API
    
    Returns:
        dict: Contador completo com estatísticas
    """
    return _carregar_contador()
