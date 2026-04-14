"""
Script para remover latitude e longitude de todas as unidades
"""

import json
from pathlib import Path

def remover_coordenadas():
    """Remove campos latitude e longitude do unidades.json"""
    
    unidades_file = Path(__file__).parent.parent / "data" / "unidades.json"
    
    print("=" * 80)
    print("🗑️  REMOVENDO COORDENADAS")
    print("=" * 80)
    
    # Carrega unidades
    print(f"\n📂 Carregando: {unidades_file}")
    with open(unidades_file, 'r', encoding='utf-8') as f:
        unidades = json.load(f)
    
    print(f"✅ Total de unidades: {len(unidades)}")
    
    # Remove coordenadas
    removidas = 0
    for unidade in unidades:
        tinha_coords = False
        
        if 'latitude' in unidade:
            del unidade['latitude']
            tinha_coords = True
        
        if 'longitude' in unidade:
            del unidade['longitude']
            tinha_coords = True
        
        if tinha_coords:
            removidas += 1
    
    # Salva
    with open(unidades_file, 'w', encoding='utf-8') as f:
        json.dump(unidades, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ Coordenadas removidas de {removidas} unidades")
    print(f"💾 Arquivo atualizado: {unidades_file}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        remover_coordenadas()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
