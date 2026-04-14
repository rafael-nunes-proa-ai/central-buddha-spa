"""
Script para geocodificar todas as unidades usando Google Maps API
Remove latitude/longitude existentes e busca coordenadas corretas via Google
"""

import json
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para importar o serviço
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.google_maps_service import geocode_cep
import time

def geocodificar_unidades():
    """
    Lê unidades.json, remove lat/lng, geocodifica via Google Maps e salva
    """
    
    # Caminhos dos arquivos
    unidades_file = Path(__file__).parent.parent / "data" / "unidades.json"
    output_file = Path(__file__).parent.parent / "data" / "unidades_geocodificadas.json"
    
    print("=" * 80)
    print("🗺️  GEOCODIFICAÇÃO DE UNIDADES - GOOGLE MAPS API")
    print("=" * 80)
    
    # Carrega unidades
    print(f"\n📂 Carregando: {unidades_file}")
    with open(unidades_file, 'r', encoding='utf-8') as f:
        unidades = json.load(f)
    
    print(f"✅ Total de unidades: {len(unidades)}")
    
    # Estatísticas
    total = len(unidades)
    sucesso = 0
    falhas = 0
    sem_cep = 0
    
    # Processa cada unidade
    for i, unidade in enumerate(unidades, 1):
        nome = unidade.get('nomeFantasiaFranqueada', 'Sem nome')
        cep = unidade.get('cepFranqueada', '')
        
        print(f"\n[{i}/{total}] {nome}")
        print(f"CEP: {cep}")
        
        # Remove latitude e longitude existentes
        if 'latitude' in unidade:
            del unidade['latitude']
        if 'longitude' in unidade:
            del unidade['longitude']
        
        # Valida CEP
        if not cep or cep.strip() == '':
            print("⚠️  CEP não informado - pulando")
            sem_cep += 1
            continue
        
        # Geocodifica via Google Maps
        try:
            resultado = geocode_cep(cep)
            
            if resultado:
                # Adiciona coordenadas
                unidade['latitude'] = resultado['lat']
                unidade['longitude'] = resultado['lng']
                
                print(f"✅ Geocodificado: {resultado['lat']}, {resultado['lng']}")
                print(f"   {resultado['endereco_completo']}")
                sucesso += 1
            else:
                print("❌ Não foi possível geocodificar")
                falhas += 1
            
            # Aguarda 0.5s entre requisições (evitar rate limit)
            if i < total:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            falhas += 1
    
    # Salva resultado
    print("\n" + "=" * 80)
    print("💾 SALVANDO RESULTADO")
    print("=" * 80)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unidades, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ Arquivo salvo: {output_file}")
    
    # Estatísticas finais
    print("\n" + "=" * 80)
    print("📊 ESTATÍSTICAS FINAIS")
    print("=" * 80)
    print(f"Total de unidades: {total}")
    print(f"✅ Geocodificadas com sucesso: {sucesso}")
    print(f"❌ Falhas: {falhas}")
    print(f"⚠️  Sem CEP: {sem_cep}")
    print(f"📊 Taxa de sucesso: {(sucesso/total*100):.1f}%")
    
    # Pergunta se quer substituir o arquivo original
    print("\n" + "=" * 80)
    print("⚠️  ATENÇÃO")
    print("=" * 80)
    print(f"Arquivo gerado: {output_file.name}")
    print(f"Backup original: unidades_backup.json")
    print("\nPara substituir o arquivo original, execute:")
    print(f"  Copy-Item '{output_file}' -Destination '{unidades_file}' -Force")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        geocodificar_unidades()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
