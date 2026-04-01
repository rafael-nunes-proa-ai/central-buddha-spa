"""
Script para pré-geocodificar todas as unidades do JSON
Executa uma vez para popular lat/lon no arquivo unidades.json
"""

import json
import requests
import time
import re
import os

CACHE_FILE = 'data/geocode_cache.json'
UNIDADES_FILE = 'data/unidades.json'

def load_cache():
    """Carrega cache de coordenadas"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_cache(cache):
    """Salva cache de coordenadas"""
    try:
        os.makedirs('data', exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar cache: {e}")

def geocode_por_cep(cep: str, cache: dict) -> tuple:
    """Geocodifica CEP usando cache + ViaCEP + Nominatim"""
    try:
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        if len(cep_limpo) != 8:
            return None, None
        
        # Verifica cache
        if cep_limpo in cache:
            cached = cache[cep_limpo]
            if cached.get('lat') and cached.get('lon'):
                print(f"  ✓ Cache: {cep_limpo}")
                return cached['lat'], cached['lon']
        
        # ViaCEP
        response = requests.get(f'https://viacep.com.br/ws/{cep_limpo}/json/', timeout=5)
        if response.status_code != 200 or response.json().get('erro'):
            print(f"  ✗ ViaCEP: {cep_limpo}")
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
        time.sleep(1)  # Rate limit
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': endereco, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'BuddhaSpaBot/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                
                # Salva no cache
                cache[cep_limpo] = {'lat': lat, 'lon': lon}
                save_cache(cache)
                
                print(f"  ✓ Geocoded: {cep_limpo} -> {cidade}/{uf}")
                return lat, lon
        
        print(f"  ✗ Nominatim: {cep_limpo}")
        return None, None
        
    except Exception as e:
        print(f"  ✗ Erro: {cep} - {e}")
        return None, None

def main():
    """Geocodifica todas as unidades e salva no JSON"""
    print("=" * 80)
    print("🌍 GEOCODIFICANDO UNIDADES")
    print("=" * 80)
    
    # Carrega unidades
    with open(UNIDADES_FILE, 'r', encoding='utf-8') as f:
        unidades = json.load(f)
    
    print(f"\n📋 Total de unidades: {len(unidades)}")
    
    # Carrega cache
    cache = load_cache()
    print(f"💾 Cache: {len(cache)} CEPs já geocodificados\n")
    
    geocoded = 0
    skipped = 0
    failed = 0
    
    for i, unidade in enumerate(unidades, 1):
        nome = unidade.get('nomeFantasiaFranqueada', 'N/A')
        cep = unidade.get('cepFranqueada', '')
        
        print(f"\n[{i}/{len(unidades)}] {nome}")
        
        # Pula se não tiver CEP ou endereço
        if not cep or not unidade.get('enderecoFranqueada'):
            print(f"  ⊘ Sem CEP/endereço")
            skipped += 1
            continue
        
        # Pula se encerrada
        data_encerramento = unidade.get('dataEncerramento', '00/00/0000')
        if data_encerramento and data_encerramento != '00/00/0000':
            print(f"  ⊘ Encerrada")
            skipped += 1
            continue
        
        # Geocodifica
        lat, lon = geocode_por_cep(cep, cache)
        
        if lat and lon:
            unidade['latitude'] = lat
            unidade['longitude'] = lon
            unidade['link_maps'] = f"https://maps.google.com/?q={lat},{lon}"
            geocoded += 1
        else:
            failed += 1
    
    # Salva JSON atualizado
    with open(UNIDADES_FILE, 'w', encoding='utf-8') as f:
        json.dump(unidades, f, ensure_ascii=False, indent=4)
    
    print("\n" + "=" * 80)
    print("✅ GEOCODIFICAÇÃO CONCLUÍDA")
    print("=" * 80)
    print(f"✓ Geocodificadas: {geocoded}")
    print(f"⊘ Puladas: {skipped}")
    print(f"✗ Falhas: {failed}")
    print(f"💾 Cache salvo: {len(cache)} CEPs")
    print(f"📄 Arquivo atualizado: {UNIDADES_FILE}")
    print("=" * 80)

if __name__ == '__main__':
    main()
