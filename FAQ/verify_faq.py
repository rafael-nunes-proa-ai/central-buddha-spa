import json

with open('faq.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total de categorias: {len(data['categories'])}\n")
for i, cat in enumerate(data['categories'], 1):
    print(f"\n{i}. {cat['name']} ({len(cat['faqs'])} perguntas)")
    for j, faq in enumerate(cat['faqs'], 1):
        print(f"   {j}. {faq['question'][:80]}")
