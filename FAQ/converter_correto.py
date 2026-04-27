import json
import re

# Ler o arquivo original
with open('faq_backup.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Definir as categorias manualmente (ordem de aparição no arquivo)
CATEGORIES = [
    "Políticas de trocas, devoluções e reembolsos",
    "Corporativo",
    "Cupons de desconto e promoções",
    "Valores e Formas de pagamento",
    "Serviços",
    "Produtos",
    "Vouchers",
    "Unidades, Agendamento e Horários",
    "Pacotes",
    "O Buddha Spa"
]

# Estrutura do JSON
faq_data = {
    "version": "1.0",
    "last_updated": "2026-04-22",
    "categories": []
}

# Encontrar índices das categorias
category_indices = {}
for i, line in enumerate(lines):
    line_stripped = line.strip()
    for cat_name in CATEGORIES:
        if line_stripped == cat_name:
            category_indices[cat_name] = i
            break

# Processar cada categoria
for cat_idx, cat_name in enumerate(CATEGORIES):
    if cat_name not in category_indices:
        print(f"⚠️  Categoria não encontrada: {cat_name}")
        continue
    
    # Determinar range de linhas da categoria
    start_idx = category_indices[cat_name]
    if cat_idx + 1 < len(CATEGORIES):
        next_cat = CATEGORIES[cat_idx + 1]
        end_idx = category_indices.get(next_cat, len(lines))
    else:
        end_idx = len(lines)
    
    # Criar categoria
    category_id = re.sub(r'[^a-z0-9]+', '_', cat_name.lower()).strip('_')
    category = {
        "id": category_id,
        "name": cat_name,
        "keywords": [],
        "faqs": []
    }
    
    # Processar linhas da categoria
    current_q_num = None
    current_question = None
    current_answer = []
    
    for i in range(start_idx, end_idx):
        line = lines[i].rstrip()
        
        # Detectar pergunta: linha que começa com número E termina com ?
        match = re.match(r'^(\d+(?:\.\d+)?)\.\s+(.+\?)$', line)
        if match:
            # Salvar pergunta anterior
            if current_question:
                answer = '\n'.join(current_answer).strip()
                if answer:
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', answer)
                    links = re.findall(r'https?://[^\s]+', answer)
                    
                    faq_item = {
                        "id": f"{category_id}_{current_q_num.replace('.', '_')}",
                        "question": current_question,
                        "answer": answer,
                        "keywords": [],
                        "contacts": {}
                    }
                    
                    if emails:
                        faq_item["contacts"]["email"] = emails[0]
                    if links:
                        faq_item["contacts"]["links"] = links
                    
                    category["faqs"].append(faq_item)
            
            # Nova pergunta
            current_q_num = match.group(1)
            current_question = match.group(2).strip()
            current_answer = []
        elif current_question and line.strip():
            # Acumular resposta (ignorar linhas vazias)
            current_answer.append(line)
    
    # Salvar última pergunta da categoria
    if current_question and current_answer:
        answer = '\n'.join(current_answer).strip()
        if answer:
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', answer)
            links = re.findall(r'https?://[^\s]+', answer)
            
            faq_item = {
                "id": f"{category_id}_{current_q_num.replace('.', '_')}",
                "question": current_question,
                "answer": answer,
                "keywords": [],
                "contacts": {}
            }
            
            if emails:
                faq_item["contacts"]["email"] = emails[0]
            if links:
                faq_item["contacts"]["links"] = links
            
            category["faqs"].append(faq_item)
    
    if category["faqs"]:
        faq_data["categories"].append(category)
        print(f"✅ {cat_name}: {len(category['faqs'])} perguntas")
    else:
        print(f"⚠️  {cat_name}: 0 perguntas")

# Salvar JSON
with open('faq.json', 'w', encoding='utf-8') as f:
    json.dump(faq_data, f, ensure_ascii=False, indent=2)

print(f"\n📊 Total de categorias: {len(faq_data['categories'])}")
total_faqs = sum(len(cat['faqs']) for cat in faq_data['categories'])
print(f"📝 Total de perguntas: {total_faqs}")
