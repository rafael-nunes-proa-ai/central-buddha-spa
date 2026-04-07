import json

# Coordenadas genéricas do centro de SP (Rua Santa Ifigênia)
COORD_GENERICA_LAT = -23.5383214
COORD_GENERICA_LON = -46.6391624

UNIDADES_FILE = 'data/unidades.json'

print(f"\n{'='*80}")
print(f"LIMPANDO COORDENADAS GENÉRICAS")
print(f"{'='*80}\n")

# Carregar unidades
with open(UNIDADES_FILE, 'r', encoding='utf-8') as f:
    unidades = json.load(f)

limpas = 0

for u in unidades:
    lat = u.get('latitude')
    lon = u.get('longitude')
    
    if lat == COORD_GENERICA_LAT and lon == COORD_GENERICA_LON:
        nome = u.get('nomeFantasiaFranqueada', 'N/A')
        uid = u.get('id', 'N/A')
        
        # Remover coordenadas genéricas
        if 'latitude' in u:
            del u['latitude']
        if 'longitude' in u:
            del u['longitude']
        
        limpas += 1
        print(f"{limpas}. Limpando: {nome} (ID: {uid})")

# Salvar arquivo atualizado
with open(UNIDADES_FILE, 'w', encoding='utf-8') as f:
    json.dump(unidades, f, ensure_ascii=False, indent=4)

print(f"\n{'='*80}")
print(f"✅ Total de unidades limpas: {limpas}")
print(f"📄 Arquivo atualizado: {UNIDADES_FILE}")
print(f"{'='*80}\n")
print("Agora você pode rodar o script de geocodificação novamente!")
print("As unidades serão re-geocodificadas com validação de precisão.")
