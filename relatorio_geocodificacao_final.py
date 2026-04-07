import json

with open('data/unidades.json', 'r', encoding='utf-8') as f:
    unidades = json.load(f)

print(f"\n{'='*80}")
print(f"📊 RELATÓRIO FINAL DE GEOCODIFICAÇÃO")
print(f"{'='*80}\n")

# Separar unidades
com_geo = []
sem_geo = []

for u in unidades:
    if u.get('latitude') and u.get('longitude'):
        com_geo.append(u)
    else:
        sem_geo.append(u)

# Estatísticas gerais
total = len(unidades)
total_com = len(com_geo)
total_sem = len(sem_geo)
percentual = (total_com / total * 100) if total > 0 else 0

print(f"📈 ESTATÍSTICAS GERAIS:")
print(f"   Total de unidades: {total}")
print(f"   ✅ Com geocodificação: {total_com} ({percentual:.1f}%)")
print(f"   ❌ Sem geocodificação: {total_sem} ({100-percentual:.1f}%)")
print()

# Unidades SEM geocodificação
if sem_geo:
    print(f"{'='*80}")
    print(f"❌ UNIDADES SEM GEOCODIFICAÇÃO ({len(sem_geo)} unidades)")
    print(f"{'='*80}\n")
    
    for i, u in enumerate(sem_geo, 1):
        nome = u.get('nomeFantasiaFranqueada', 'N/A')
        uid = u.get('id', 'N/A')
        cep = u.get('cepFranqueada', 'vazio')
        endereco = u.get('enderecoFranqueada', 'vazio')
        cidade = u.get('cidadeFranqueada', 'null')
        
        print(f"{i}. {nome} (ID: {uid})")
        print(f"   CEP: {cep} | Cidade: {cidade}")
        print(f"   Endereço: {endereco}")
        print()

# Resumo das últimas geocodificações (LocationIQ)
print(f"{'='*80}")
print(f"🗺️ ÚLTIMAS GEOCODIFICAÇÕES (LocationIQ)")
print(f"{'='*80}\n")

# Pegar as últimas 10 unidades com geocodificação
ultimas_geo = [u for u in com_geo if u.get('latitude') and u.get('longitude')][-10:]

for i, u in enumerate(ultimas_geo, 1):
    nome = u.get('nomeFantasiaFranqueada', 'N/A')
    lat = u.get('latitude')
    lon = u.get('longitude')
    endereco = u.get('enderecoFranqueada', 'N/A')
    
    print(f"{i}. {nome}")
    print(f"   📍 {lat}, {lon}")
    print(f"   📌 {endereco}")
    print()

print(f"{'='*80}")
print(f"✅ GEOCODIFICAÇÃO FINALIZADA COM SUCESSO!")
print(f"{'='*80}\n")
