"""
Script para geocodificar todas as unidades do JSON
Adiciona latitude e longitude diretamente no unidades.json
SEM CACHE - Consulta sempre as APIs
"""

import json
import requests
import time
import re
import os
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv não instalado. Execute: pip install python-dotenv")
    print("   Ou configure LOCATIONIQ_API_KEY diretamente no script.\n")

UNIDADES_FILE = 'data/unidades.json'

# LocationIQ API Key (melhor cobertura no Brasil que Nominatim)
# Obtenha gratuitamente em: https://locationiq.com/
# 5.000 requisições/dia grátis
LOCATIONIQ_API_KEY = os.getenv('LOCATIONIQ_API_KEY', '')

def geocode_locationiq(query: str, api_key: str, require_precise: bool = True, debug: bool = True) -> tuple:
    """Geocodifica usando LocationIQ (melhor cobertura no Brasil)
    
    Args:
        query: Endereço para geocodificar
        api_key: API Key do LocationIQ
        require_precise: Se True, rejeita resultados genéricos de cidade/estado
        debug: Se True, mostra detalhes da resposta da API
    
    Returns:
        (lat, lon) se encontrado com precisão adequada, senão (None, None)
    """
    if not api_key:
        if debug:
            print(f"    ⚠️ LocationIQ API Key não configurada")
        return None, None
    
    try:
        time.sleep(1)  # Rate limit
        
        url = "https://us1.locationiq.com/v1/search"
        params = {
            'key': api_key,
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        if debug:
            print(f"    🔍 Query LocationIQ: {query}")
        
        response = requests.get(url, params=params, timeout=10)
        
        if debug:
            print(f"    📡 Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            
            if debug:
                print(f"    📊 Resultados encontrados: {len(results)}")
            
            if results and len(results) > 0:
                result = results[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                if debug:
                    result_type = result.get('type', 'N/A')
                    result_class = result.get('class', 'N/A')
                    display_name = result.get('display_name', 'N/A')
                    print(f"    📍 Tipo: {result_type} | Classe: {result_class}")
                    print(f"    📌 Local: {display_name}")
                    print(f"    🌐 Coordenadas: {lat}, {lon}")
                
                # Validar precisão do resultado
                if require_precise:
                    result_type = result.get('type', '')
                    result_class = result.get('class', '')
                    
                    invalid_types = ['city', 'state', 'country', 'administrative']
                    
                    if result_type in invalid_types or result_class == 'boundary':
                        print(f"    ❌ REJEITADO: Resultado muito genérico ({result_type}/{result_class})")
                        return None, None
                    
                    address = result.get('address', {})
                    has_street = 'road' in address or 'street' in address
                    
                    if not has_street and result_type not in ['building', 'house', 'amenity']:
                        print(f"    ❌ REJEITADO: Sem detalhes de rua no resultado")
                        return None, None
                
                return lat, lon
            else:
                if debug:
                    print(f"    ❌ Nenhum resultado encontrado")
        else:
            if debug:
                print(f"    ❌ Erro HTTP: {response.status_code}")
                if response.status_code == 401:
                    print(f"    ⚠️ API Key inválida ou expirada")
                elif response.status_code == 429:
                    print(f"    ⚠️ Limite de requisições excedido")
        
        return None, None
        
    except Exception as e:
        print(f"    ⚠️ Erro LocationIQ: {e}")
        return None, None

def geocode_nominatim(query: str, require_precise: bool = True, debug: bool = True) -> tuple:
    """Geocodifica usando Nominatim (OpenStreetMap) com validação de precisão
    
    Args:
        query: Endereço para geocodificar
        require_precise: Se True, rejeita resultados genéricos de cidade/estado
        debug: Se True, mostra detalhes da resposta da API
    
    Returns:
        (lat, lon) se encontrado com precisão adequada, senão (None, None)
    """
    try:
        time.sleep(1)  # Rate limit: 1 req/segundo
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': query, 'format': 'json', 'limit': 1, 'addressdetails': 1}
        headers = {'User-Agent': 'BuddhaSpaBot/1.0'}
        
        if debug:
            print(f"    🔍 Query: {query}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if debug:
            print(f"    📡 Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            
            if debug:
                print(f"    📊 Resultados encontrados: {len(results)}")
            
            if results and len(results) > 0:
                result = results[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                if debug:
                    result_type = result.get('type', 'N/A')
                    result_class = result.get('class', 'N/A')
                    display_name = result.get('display_name', 'N/A')
                    print(f"    📍 Tipo: {result_type} | Classe: {result_class}")
                    print(f"    📌 Local: {display_name}")
                    print(f"    🌐 Coordenadas: {lat}, {lon}")
                
                # Validar precisão do resultado
                if require_precise:
                    result_type = result.get('type', '')
                    result_class = result.get('class', '')
                    
                    # Rejeitar se for apenas cidade, estado ou país
                    # Aceitar apenas: house, building, road, amenity, etc.
                    invalid_types = ['city', 'state', 'country', 'administrative']
                    
                    if result_type in invalid_types or result_class == 'boundary':
                        print(f"    ❌ REJEITADO: Resultado muito genérico ({result_type}/{result_class})")
                        return None, None
                    
                    # Verificar se tem detalhes de endereço (rua, número, etc.)
                    address = result.get('address', {})
                    has_street = 'road' in address or 'street' in address
                    
                    if not has_street and result_type not in ['building', 'house', 'amenity']:
                        print(f"    ❌ REJEITADO: Sem detalhes de rua no resultado")
                        return None, None
                
                return lat, lon
            else:
                if debug:
                    print(f"    ❌ Nenhum resultado encontrado")
        else:
            if debug:
                print(f"    ❌ Erro HTTP: {response.status_code}")
        
        return None, None
        
    except Exception as e:
        print(f"    ⚠️ Erro Nominatim: {e}")
        return None, None

def formatar_endereco_limpo(endereco: str, numero: str, bairro: str, cidade: str, uf: str, cep: str) -> str:
    """Formata endereço no padrão limpo: Rua X, 123 - Bairro - Cidade - UF - CEP"""
    partes = []
    
    # Endereço + número
    if endereco:
        if numero:
            partes.append(f"{endereco}, {numero}")
        else:
            partes.append(endereco)
    
    # Bairro
    if bairro:
        partes.append(bairro)
    
    # Cidade
    if cidade:
        partes.append(cidade)
    
    # UF
    if uf:
        partes.append(uf)
    
    # CEP
    if cep:
        partes.append(cep)
    
    return " - ".join(partes)

def geocode_com_fallback(unidade: dict) -> tuple:
    """
    Geocodifica com fallback robusto:
    1. Tenta por endereço completo formatado (padrão limpo)
    2. Tenta por CEP via ViaCEP + Nominatim
    3. Tenta por endereço sem número
    """
    nome = unidade.get('nomeFantasiaFranqueada', 'N/A')
    cep = unidade.get('cepFranqueada', '')
    endereco = unidade.get('enderecoFranqueada', '')
    numero = unidade.get('numeroFranqueada', '')
    bairro = unidade.get('bairroFranqueada', '')
    cidade = unidade.get('cidadeFranqueada', '')
    uf = unidade.get('ufFranqueada', '')
    
    # TENTATIVA 1: LocationIQ com endereço completo formatado
    if endereco and cidade and uf and LOCATIONIQ_API_KEY:
        try:
            print(f"    → TENTATIVA 1: LocationIQ - Endereço formatado")
            query = formatar_endereco_limpo(endereco, numero, bairro, cidade, uf, cep)
            print(f"    📝 Formato: {query}")
            
            lat, lon = geocode_locationiq(query, LOCATIONIQ_API_KEY, require_precise=True, debug=True)
            if lat and lon:
                print(f"    ✅ SUCESSO por LocationIQ")
                return lat, lon
        except Exception as e:
            print(f"    ⚠️ Erro LocationIQ: {e}")
    
    # TENTATIVA 1B: Nominatim (fallback se LocationIQ falhar)
    if endereco and cidade and uf:
        try:
            print(f"    → TENTATIVA 1B: Nominatim - Endereço formatado")
            query = formatar_endereco_limpo(endereco, numero, bairro, cidade, uf, cep)
            
            lat, lon = geocode_nominatim(query, require_precise=True, debug=False)
            if lat and lon:
                print(f"    ✅ SUCESSO por Nominatim")
                return lat, lon
        except Exception as e:
            print(f"    ⚠️ Erro Nominatim: {e}")
    
    # TENTATIVA 2: CEP via ViaCEP
    if cep:
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        if len(cep_limpo) == 8:
            try:
                print(f"    → TENTATIVA 2: CEP via ViaCEP")
                response = requests.get(f'https://viacep.com.br/ws/{cep_limpo}/json/', timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('erro'):
                        logradouro = data.get('logradouro', '')
                        bairro_cep = data.get('bairro', '')
                        cidade_cep = data.get('localidade', '')
                        uf_cep = data.get('uf', '')
                        
                        if logradouro:
                            query = f"{logradouro} - {bairro_cep} - {cidade_cep} - {uf_cep} - {cep}"
                            print(f"    📝 Formato: {query}")
                            lat, lon = geocode_nominatim(query, require_precise=True, debug=True)
                            if lat and lon:
                                print(f"    ✅ SUCESSO por CEP")
                                return lat, lon
            except Exception as e:
                print(f"    ⚠️ Erro ViaCEP: {e}")
    
    # TENTATIVA 3: Endereço sem número (às vezes ajuda)
    if endereco and cidade and uf:
        try:
            print(f"    → TENTATIVA 3: Endereço sem número")
            query = formatar_endereco_limpo(endereco, '', bairro, cidade, uf, '')
            print(f"    📝 Formato: {query}")
            
            lat, lon = geocode_nominatim(query, require_precise=True, debug=True)
            if lat and lon:
                print(f"    ✅ SUCESSO por endereço sem número")
                return lat, lon
        except Exception as e:
            print(f"    ⚠️ Erro endereço sem número: {e}")
    
    # TENTATIVA 3: Apenas cidade/estado
    if cidade and uf:
        try:
            print(f"    → Tentando por cidade/estado (GENÉRICO - não recomendado)")
            query = f"{cidade} - {uf}, Brasil"
            # Cidade/estado sempre retorna genérico, então pulamos
            print(f"    ⊘ Pulando tentativa genérica por cidade")
            return None, None
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
        
        # Pula se já tiver latitude e longitude
        if unidade.get('latitude') and unidade.get('longitude'):
            print(f"  ✓ Já geocodificada")
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
