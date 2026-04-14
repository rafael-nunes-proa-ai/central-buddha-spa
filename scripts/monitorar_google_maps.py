"""
Script para monitorar consumo da Google Maps API
Mostra estatísticas detalhadas e custos estimados
"""

import json
from pathlib import Path
from datetime import date

COUNTER_FILE = Path(__file__).parent.parent / "data" / "google_maps_counter.json"

# Pricing Google Maps API 2025
GEOCODING_FREE = 10000  # Primeiras 10k gratuitas
GEOCODING_PRICE_10K_100K = 5.00  # $5 por 1.000 (10k-100k)
GEOCODING_PRICE_100K_500K = 4.00  # $4 por 1.000 (100k-500k)

DISTANCE_PRICE = 5.00  # $5 por 1.000 desde a primeira

def calcular_custo_geocoding(requisicoes: int) -> float:
    """Calcula custo de geocoding baseado no volume"""
    if requisicoes <= GEOCODING_FREE:
        return 0.0
    
    custo = 0.0
    requisicoes_pagas = requisicoes - GEOCODING_FREE
    
    # Faixa 10k-100k: $5/1k
    if requisicoes_pagas <= 90000:
        custo = (requisicoes_pagas / 1000) * GEOCODING_PRICE_10K_100K
    else:
        # Primeiros 90k a $5/1k
        custo = 90 * GEOCODING_PRICE_10K_100K
        # Resto a $4/1k
        requisicoes_pagas -= 90000
        custo += (requisicoes_pagas / 1000) * GEOCODING_PRICE_100K_500K
    
    return custo

def calcular_custo_distance(requisicoes: int) -> float:
    """Calcula custo de distance matrix (pago desde a primeira)"""
    if requisicoes <= 100000:
        return (requisicoes / 1000) * DISTANCE_PRICE
    else:
        # Primeiros 100k a $5/1k
        custo = 100 * DISTANCE_PRICE
        # Resto a $4/1k
        requisicoes_pagas = requisicoes - 100000
        custo += (requisicoes_pagas / 1000) * 4.00
        return custo

def main():
    if not COUNTER_FILE.exists():
        print("❌ Arquivo de contador não encontrado!")
        print(f"   Esperado em: {COUNTER_FILE}")
        return
    
    with open(COUNTER_FILE, 'r') as f:
        contador = json.load(f)
    
    geo = contador.get('geocoding', {})
    dist = contador.get('distance_matrix', {})
    
    print("=" * 80)
    print("📊 MONITORAMENTO GOOGLE MAPS API")
    print("=" * 80)
    print()
    
    # Geocoding
    print("🌍 GEOCODING API")
    print("-" * 80)
    print(f"   📅 Último reset: {geo.get('ultimo_reset', 'N/A')}")
    print(f"   📊 Requisições este mês: {geo.get('mes_atual', 0):,}")
    print(f"   📈 Total histórico: {geo.get('total', 0):,}")
    
    geo_mes = geo.get('mes_atual', 0)
    if geo_mes <= GEOCODING_FREE:
        restante = GEOCODING_FREE - geo_mes
        percentual = (geo_mes / GEOCODING_FREE) * 100
        print(f"   ✅ Cota gratuita: {restante:,} requisições restantes ({percentual:.1f}% usado)")
        print(f"   💰 Custo este mês: $0.00")
    else:
        excedente = geo_mes - GEOCODING_FREE
        custo = calcular_custo_geocoding(geo_mes)
        print(f"   ⚠️  Cota gratuita EXCEDIDA em {excedente:,} requisições")
        print(f"   💰 Custo este mês: ${custo:.2f}")
    
    custo_total_geo = calcular_custo_geocoding(geo.get('total', 0))
    print(f"   💵 Custo total histórico: ${custo_total_geo:.2f}")
    print()
    
    # Distance Matrix
    print("📏 DISTANCE MATRIX API")
    print("-" * 80)
    print(f"   📅 Último reset: {dist.get('ultimo_reset', 'N/A')}")
    print(f"   📊 Requisições este mês: {dist.get('mes_atual', 0):,}")
    print(f"   📈 Total histórico: {dist.get('total', 0):,}")
    
    dist_mes = dist.get('mes_atual', 0)
    custo_dist_mes = calcular_custo_distance(dist_mes)
    print(f"   💰 Custo este mês: ${custo_dist_mes:.2f}")
    
    custo_total_dist = calcular_custo_distance(dist.get('total', 0))
    print(f"   💵 Custo total histórico: ${custo_total_dist:.2f}")
    print()
    
    # Total
    print("=" * 80)
    custo_mes_total = calcular_custo_geocoding(geo_mes) + custo_dist_mes
    custo_historico_total = custo_total_geo + custo_total_dist
    print(f"💰 CUSTO TOTAL ESTE MÊS: ${custo_mes_total:.2f}")
    print(f"💵 CUSTO TOTAL HISTÓRICO: ${custo_historico_total:.2f}")
    print("=" * 80)
    print()
    
    # Projeção mensal
    hoje = date.today()
    dia_atual = hoje.day
    dias_no_mes = 30  # Aproximação
    
    if dia_atual > 0:
        taxa_diaria_geo = geo_mes / dia_atual
        taxa_diaria_dist = dist_mes / dia_atual
        
        projecao_geo = int(taxa_diaria_geo * dias_no_mes)
        projecao_dist = int(taxa_diaria_dist * dias_no_mes)
        
        custo_projetado_geo = calcular_custo_geocoding(projecao_geo)
        custo_projetado_dist = calcular_custo_distance(projecao_dist)
        custo_projetado_total = custo_projetado_geo + custo_projetado_dist
        
        print("📈 PROJEÇÃO PARA FIM DO MÊS")
        print("-" * 80)
        print(f"   🌍 Geocoding: {projecao_geo:,} requisições → ${custo_projetado_geo:.2f}")
        print(f"   📏 Distance Matrix: {projecao_dist:,} requisições → ${custo_projetado_dist:.2f}")
        print(f"   💰 Total projetado: ${custo_projetado_total:.2f}")
        print("=" * 80)

if __name__ == "__main__":
    main()
