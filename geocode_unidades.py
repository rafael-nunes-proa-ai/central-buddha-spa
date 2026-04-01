"""
Script para geocodificar todas as unidades do JSON
Adiciona latitude e longitude diretamente no unidades.json
SEM CACHE - Consulta sempre as APIs
"""

import json
import requests
import time
import re

UNIDADES_FILE = 'data/unidades.json'

def geocode_nominatim(query: str) -> tuple:
    """Geocodifica usando Nominatim (OpenStreetMap)"""
    try:
        time.sleep(1)  # Rate limit: 1 req/segundo
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': query, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'BuddhaSpaBot/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                return lat, lon
        
        return None, None
        
    except Exception as e:
        print(f"    ⚠️ Erro Nominatim: {e}")
        return None, None

def geocode_com_fallback(unidade: dict) -> tuple:
    """
    Geocodifica com fallback robusto:
    1. Tenta por CEP via ViaCEP + Nominatim
    2. Tenta por endereço completo
    3. Tenta por cidade/estado
    """
    nome = unidade.get('nomeFantasiaFranqueada', 'N/A')
    cep = unidade.get('cepFranqueada', '')
    endereco = unidade.get('enderecoFranqueada', '')
    numero = unidade.get('numeroFranqueada', '')
    bairro = unidade.get('bairroFranqueada', '')
    cidade = unidade.get('cidadeFranqueada', '')
    uf = unidade.get('ufFranqueada', '')
    
    # TENTATIVA 1: CEP via ViaCEP
    if cep:
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        if len(cep_limpo) == 8:
            try:
                print(f"    → Tentando por CEP: {cep_limpo}")
                response = requests.get(f'https://viacep.com.br/ws/{cep_limpo}/json/', timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('erro'):
                        logradouro = data.get('logradouro', '')
                        bairro_cep = data.get('bairro', '')
                        cidade_cep = data.get('localidade', '')
                        uf_cep = data.get('uf', '')
                        
                        if logradouro:
                            query = f"{logradouro}, {bairro_cep}, {cidade_cep} - {uf_cep}, Brasil"
                        else:
                            query = f"{cidade_cep} - {uf_cep}, Brasil"
                        
                        lat, lon = geocode_nominatim(query)
                        if lat and lon:
                            print(f"    ✓ Sucesso por CEP")
                            return lat, lon
            except Exception as e:
                print(f"    ⚠️ Erro ViaCEP: {e}")
    
    # TENTATIVA 2: Endereço completo
    if endereco and cidade and uf:
        try:
            print(f"    → Tentando por endereço completo")
            query_parts = [endereco]
            if numero:
                query_parts.append(numero)
            if bairro:
                query_parts.append(bairro)
            query_parts.append(cidade)
            query_parts.append(uf)
            query_parts.append("Brasil")
            
            query = ", ".join(query_parts)
            lat, lon = geocode_nominatim(query)
            if lat and lon:
                print(f"    ✓ Sucesso por endereço completo")
                return lat, lon
        except Exception as e:
            print(f"    ⚠️ Erro endereço completo: {e}")
    
    # TENTATIVA 3: Apenas cidade/estado
    if cidade and uf:
        try:
            print(f"    → Tentando por cidade/estado")
            query = f"{cidade} - {uf}, Brasil"
            lat, lon = geocode_nominatim(query)
            if lat and lon:
                print(f"    ✓ Sucesso por cidade/estado")
                return lat, lon
        except Exception as e:
            print(f"    ⚠️ Erro cidade/estado: {e}")
    
    print(f"    ✗ FALHOU em todas as tentativas")
    return None, None

def main():
    """Geocodifica todas as unidades e salva no JSON"""
    print("=" * 80)
    print("🌍 GEOCODIFICANDO UNIDADES - SEM CACHE")
    print("=" * 80)
    
    # Carrega unidades
    try:
        with open(UNIDADES_FILE, 'r', encoding='utf-8') as f:
            unidades = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar {UNIDADES_FILE}: {e}")
        return
    
    print(f"\n� Total de unidades: {len(unidades)}\n")
    
    geocoded = 0
    skipped = 0
    failed = 0
    
    for i, unidade in enumerate(unidades, 1):
        nome = unidade.get('nomeFantasiaFranqueada', 'N/A')
        
        print(f"\n[{i}/{len(unidades)}] {nome}")
        
        # Pula se não tiver endereço mínimo
        if not unidade.get('cidadeFranqueada') or not unidade.get('ufFranqueada'):
            print(f"  ⊘ Sem cidade/estado")
            skipped += 1
            continue
        
        # Pula se encerrada
        data_encerramento = unidade.get('dataEncerramento', '')
        if data_encerramento and data_encerramento not in ['', '00/00/0000']:
            print(f"  ⊘ Encerrada em {data_encerramento}")
            skipped += 1
            continue
        
        # Geocodifica com fallback
        lat, lon = geocode_com_fallback(unidade)
        
        if lat and lon:
            unidade['latitude'] = lat
            unidade['longitude'] = lon
            geocoded += 1
        else:
            failed += 1
        
        # Salva a cada 10 unidades para não perder progresso
        if i % 10 == 0:
            try:
                with open(UNIDADES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(unidades, f, ensure_ascii=False, indent=4)
                print(f"\n  💾 Progresso salvo ({i}/{len(unidades)})")
            except Exception as e:
                print(f"\n  ⚠️ Erro ao salvar progresso: {e}")
    
    # Salva JSON final
    try:
        with open(UNIDADES_FILE, 'w', encoding='utf-8') as f:
            json.dump(unidades, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"\n❌ Erro ao salvar arquivo final: {e}")
        return
    
    print("\n" + "=" * 80)
    print("✅ GEOCODIFICAÇÃO CONCLUÍDA")
    print("=" * 80)
    print(f"✓ Geocodificadas: {geocoded}")
    print(f"⊘ Puladas: {skipped}")
    print(f"✗ Falhas: {failed}")
    print(f"📄 Arquivo atualizado: {UNIDADES_FILE}")
    print("=" * 80)

if __name__ == '__main__':
    main()
