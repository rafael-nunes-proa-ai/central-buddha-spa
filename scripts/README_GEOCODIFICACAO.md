# 🗺️ Geocodificação de Unidades - Google Maps API

## 📋 O QUE FAZ

Este script geocodifica todas as unidades do `unidades.json` usando a **Google Maps Geocoding API**, substituindo as coordenadas antigas (que vieram de API pública com erros) por coordenadas precisas do Google.

---

## ✅ BACKUP JÁ CRIADO

```
✅ data/unidades_backup.json (backup do arquivo original)
```

---

## 🚀 COMO USAR

### **Opção 1: Processo Completo (Recomendado)**

Execute o script que faz tudo automaticamente:

```powershell
python scripts/geocodificar_unidades.py
```

**O que ele faz:**
1. ✅ Carrega `unidades.json`
2. ✅ Remove `latitude` e `longitude` de cada unidade
3. ✅ Geocodifica via Google Maps usando o CEP
4. ✅ Adiciona novas coordenadas corretas
5. ✅ Salva em `unidades_geocodificadas.json`
6. ✅ Mostra estatísticas completas

**Depois, se estiver tudo OK:**

```powershell
# Substitui o arquivo original
Copy-Item "data\unidades_geocodificadas.json" -Destination "data\unidades.json" -Force
```

---

### **Opção 2: Processo em Etapas**

#### **Etapa 1: Remover coordenadas antigas**

```powershell
python scripts/remover_coordenadas.py
```

#### **Etapa 2: Geocodificar**

```powershell
python scripts/geocodificar_unidades.py
```

---

## 📊 EXEMPLO DE SAÍDA

```
================================================================================
🗺️  GEOCODIFICAÇÃO DE UNIDADES - GOOGLE MAPS API
================================================================================

📂 Carregando: c:\...\data\unidades.json
✅ Total de unidades: 150

[1/150] Buddha Spa Teresina
CEP: 64049-518
📊 Google Maps geocoding: 1 requisições este mês (total: 1)
🔍 Google Geocoding: Buscando CEP 64049518
✅ CEP encontrado: Teresina/PI - Bairro: Fátima
📍 Coordenadas: -5.0902277, -42.8129529
✅ Geocodificado: -5.0902277, -42.8129529
   Rua Aviador Irapuan Rocha, Fátima, Teresina - PI, Brasil

[2/150] Buddha Spa Espinheiro
CEP: 52020-010
...

================================================================================
📊 ESTATÍSTICAS FINAIS
================================================================================
Total de unidades: 150
✅ Geocodificadas com sucesso: 148
❌ Falhas: 0
⚠️  Sem CEP: 2
📊 Taxa de sucesso: 98.7%

================================================================================
⚠️  ATENÇÃO
================================================================================
Arquivo gerado: unidades_geocodificadas.json
Backup original: unidades_backup.json

Para substituir o arquivo original, execute:
  Copy-Item 'data\unidades_geocodificadas.json' -Destination 'data\unidades.json' -Force

================================================================================
```

---

## ⚠️ IMPORTANTE

### **Requisições da API:**
- O script faz **1 requisição por unidade**
- Com ~150 unidades = **150 requisições**
- Cota gratuita: **10.000/mês** ✅
- Tempo estimado: **~2 minutos** (0.5s entre requisições)

### **Segurança:**
- ✅ Backup automático criado
- ✅ Gera arquivo separado primeiro (`unidades_geocodificadas.json`)
- ✅ Você decide quando substituir o original

---

## 🔄 REVERTER MUDANÇAS

Se algo der errado:

```powershell
# Restaura o backup
Copy-Item "data\unidades_backup.json" -Destination "data\unidades.json" -Force
```

---

## 📝 ARQUIVOS CRIADOS

```
agente_central/
├── data/
│   ├── unidades.json                    # Original
│   ├── unidades_backup.json             # ✅ Backup
│   └── unidades_geocodificadas.json     # ✅ Novo (com coordenadas Google)
└── scripts/
    ├── geocodificar_unidades.py         # ✅ Script principal
    ├── remover_coordenadas.py           # ✅ Script auxiliar
    └── README_GEOCODIFICACAO.md         # ✅ Este arquivo
```

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Execute: `python scripts/geocodificar_unidades.py`
2. ✅ Verifique o arquivo gerado: `data/unidades_geocodificadas.json`
3. ✅ Se estiver OK, substitua o original
4. ✅ Teste o bot com as novas coordenadas

---

**Pronto para executar! 🚀**
