import json

# Coordenadas genéricas do centro de SP (Rua Santa Ifigênia)
COORD_GENERICA_LAT = -23.5383214
COORD_GENERICA_LON = -46.6391624

with open('data/unidades.json', 'r', encoding='utf-8') as f:
    unidades = json.load(f)

print(f"\n{'='*80}")
print(f"UNIDADES COM COORDENADAS GENÉRICAS (Centro de SP)")
print(f"Lat: {COORD_GENERICA_LAT} | Lon: {COORD_GENERICA_LON}")
print(f"{'='*80}\n")

genericas = []

for u in unidades:
    lat = u.get('latitude')
    lon = u.get('longitude')
    
    if lat == COORD_GENERICA_LAT and lon == COORD_GENERICA_LON:
        genericas.append(u)
        nome = u.get('nomeFantasiaFranqueada', 'N/A')
        uid = u.get('id', 'N/A')
        endereco = u.get('enderecoFranqueada', 'N/A')
        numero = u.get('numeroFranqueada', '')
        bairro = u.get('bairroFranqueada', '')
        cidade = u.get('cidadeFranqueada', '')
        
        print(f"{len(genericas)}. {nome} (ID: {uid})")
        print(f"   Endereço: {endereco}, {numero} - {bairro}")
        print(f"   Cidade: {cidade}")
        print()

print(f"{'='*80}")
print(f"Total de unidades com coordenadas genéricas: {len(genericas)}")
print(f"{'='*80}\n")

# Salvar lista de IDs para limpeza
ids_genericas = [u['id'] for u in genericas]
print(f"IDs afetados: {ids_genericas}")
