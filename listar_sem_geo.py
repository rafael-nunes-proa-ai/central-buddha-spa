import json

with open('data/unidades.json', 'r', encoding='utf-8') as f:
    unidades = json.load(f)

sem_geo = [u for u in unidades if not u.get('latitude') or not u.get('longitude')]

print(f"\n{'='*80}")
print(f"UNIDADES SEM GEOCODIFICAÇÃO ({len(sem_geo)} unidades)")
print(f"{'='*80}\n")

for i, u in enumerate(sem_geo, 1):
    nome = u.get('nomeFantasiaFranqueada', 'N/A')
    uid = u.get('id', 'N/A')
    cep = u.get('cepFranqueada', 'vazio')
    cidade = u.get('cidadeFranqueada', 'null')
    uf = u.get('ufFranqueada', '')
    
    print(f"{i}. {nome}")
    print(f"   ID: {uid} | CEP: {cep} | Cidade: {cidade} | UF: {uf}")
    print()

print(f"{'='*80}")
print(f"Total sem geocodificação: {len(sem_geo)}")
print(f"Total com geocodificação: {len(unidades) - len(sem_geo)}")
print(f"{'='*80}")
