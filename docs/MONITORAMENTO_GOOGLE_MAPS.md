# 📊 Monitoramento Google Maps API

## 🎯 Visão Geral

Este documento explica como monitorar o consumo da Google Maps API tanto localmente quanto no Google Cloud Console.

---

## 🖥️ Monitoramento Local

### Script de Monitoramento

Execute o script para ver estatísticas detalhadas:

```bash
python scripts/monitorar_google_maps.py
```

**Output esperado:**
```
================================================================================
📊 MONITORAMENTO GOOGLE MAPS API
================================================================================

🌍 GEOCODING API
--------------------------------------------------------------------------------
   📅 Último reset: 2026-04-01
   📊 Requisições este mês: 116
   📈 Total histórico: 116
   ✅ Cota gratuita: 9,884 requisições restantes (1.2% usado)
   💰 Custo este mês: $0.00
   💵 Custo total histórico: $0.00

📏 DISTANCE MATRIX API
--------------------------------------------------------------------------------
   📅 Último reset: 2026-04-01
   📊 Requisições este mês: 0
   📈 Total histórico: 0
   💰 Custo este mês: $0.00
   💵 Custo total histórico: $0.00

================================================================================
💰 CUSTO TOTAL ESTE MÊS: $0.00
💵 CUSTO TOTAL HISTÓRICO: $0.00
================================================================================

📈 PROJEÇÃO PARA FIM DO MÊS
--------------------------------------------------------------------------------
   🌍 Geocoding: 267 requisições → $0.00
   📏 Distance Matrix: 0 requisições → $0.00
   💰 Total projetado: $0.00
================================================================================
```

### Arquivo de Contador

Localização: `data/google_maps_counter.json`

```json
{
  "geocoding": {
    "total": 116,
    "mes_atual": 116,
    "ultimo_reset": "2026-04-01"
  },
  "distance_matrix": {
    "total": 0,
    "mes_atual": 0,
    "ultimo_reset": "2026-04-01"
  }
}
```

### Logs em Tempo Real

Ao executar o bot, você verá logs detalhados:

```
➕ Incrementando geocoding: mes_atual=116, total=116
💾 Contador salvo: geocoding=116/116, distance_matrix=0/0
📊 Google Maps geocoding: 116 requisições este mês (total: 116)
```

---

## ☁️ Monitoramento no Google Cloud Console (FONTE DA VERDADE) ⭐

**⚠️ IMPORTANTE:** O contador local pode falhar. **SEMPRE confie no Google Cloud Console** como fonte oficial de dados!

### 1. Acessar o Console

1. Acesse: https://console.cloud.google.com/
2. Selecione seu projeto
3. No menu lateral, vá em **APIs & Services** → **Dashboard**

### 2. Visualizar Métricas

#### Opção 1: Dashboard de APIs
1. Clique em **APIs & Services** → **Dashboard**
2. Você verá um gráfico com todas as APIs ativas
3. Clique em **Maps JavaScript API** ou **Geocoding API**

#### Opção 2: Métricas Detalhadas
1. Vá em **APIs & Services** → **Enabled APIs & services**
2. Clique em **Geocoding API**
3. Clique na aba **Metrics**
4. Você verá:
   - **Traffic**: Requisições por dia/hora
   - **Errors**: Taxa de erro
   - **Latency**: Tempo de resposta

#### Opção 3: Quotas
1. Vá em **APIs & Services** → **Enabled APIs & services**
2. Clique em **Geocoding API**
3. Clique na aba **Quotas**
4. Você verá:
   - **Requests per day**: Limite diário
   - **Requests per minute**: Limite por minuto
   - **Requests per user per minute**: Limite por usuário

### 3. Configurar Alertas de Billing

1. Vá em **Billing** → **Budgets & alerts**
2. Clique em **CREATE BUDGET**
3. Configure:
   - **Name**: "Google Maps API Alert"
   - **Budget amount**: $10 (ou o valor desejado)
   - **Threshold rules**: 50%, 90%, 100%
4. Adicione e-mail para notificações

### 4. Visualizar Custos

1. Vá em **Billing** → **Reports**
2. Filtre por:
   - **Service**: Maps Platform
   - **SKU**: Geocoding API, Distance Matrix API
3. Você verá:
   - Custo diário
   - Custo acumulado no mês
   - Projeção de custo

### 5. Exportar Dados

Para análise detalhada:

1. Vá em **Billing** → **Billing export**
2. Configure exportação para:
   - **BigQuery**: Para análise SQL
   - **Cloud Storage**: Para arquivos CSV

---

## � Consulta Programática (API)

### Opção 1: Cloud Monitoring API (Métricas)

**Vantagens:**
- ✅ Dados em tempo real
- ✅ Histórico completo
- ✅ Gratuito
- ✅ Fonte oficial do Google

**Setup:**

1. **Instale o cliente:**
   ```bash
   pip install google-cloud-monitoring
   ```

2. **Configure credenciais:**
   - Vá em: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Crie uma Service Account
   - Baixe o JSON de credenciais
   - Adicione ao `.env`:
     ```
     GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
     GOOGLE_CLOUD_PROJECT_ID=seu-projeto-id
     ```

3. **Habilite a API:**
   - https://console.cloud.google.com/apis/library/monitoring.googleapis.com

4. **Execute o script:**
   ```bash
   python scripts/consultar_google_cloud_metrics.py
   ```

**Output esperado:**
```
================================================================================
📊 MÉTRICAS REAIS DO GOOGLE CLOUD - GEOCODING API
================================================================================

📅 Período: 2026-03-14 até 2026-04-13

📊 Requisições por dia:
--------------------------------------------------------------------------------
   2026-04-13: 116 requisições
   2026-04-12: 0 requisições
   2026-04-11: 0 requisições
   ...

================================================================================
📈 TOTAL: 116 requisições nos últimos 30 dias
================================================================================
```

### Opção 2: BigQuery Export (RECOMENDADO para Billing)

**Vantagens:**
- ✅ Dados de faturamento precisos
- ✅ Consultas SQL poderosas
- ✅ Histórico ilimitado
- ✅ Exportação automática

**Setup:**

1. **Configure exportação:**
   - Vá em: https://console.cloud.google.com/billing/export
   - Clique em **BigQuery export**
   - Selecione um dataset ou crie um novo
   - Ative a exportação

2. **Consulte com SQL:**
   ```sql
   SELECT
     DATE(usage_start_time) as data,
     service.description as servico,
     sku.description as sku,
     SUM(usage.amount) as quantidade,
     SUM(cost) as custo_usd
   FROM `seu-projeto.billing_dataset.gcp_billing_export_v1_XXXXX`
   WHERE service.description = 'Maps'
     AND sku.description LIKE '%Geocoding%'
     AND DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
   GROUP BY data, servico, sku
   ORDER BY data DESC
   ```

3. **Resultado:**
   ```
   data       | servico | sku                    | quantidade | custo_usd
   -----------|---------|------------------------|------------|----------
   2026-04-13 | Maps    | Geocoding API Requests | 116        | 0.00
   2026-04-12 | Maps    | Geocoding API Requests | 0          | 0.00
   ```

### Opção 3: Cloud Billing API

Para consultar custos programaticamente:

```bash
pip install google-cloud-billing
```

**Documentação:**
- https://cloud.google.com/billing/docs/reference/rest

---

## 🎯 Recomendação Final

**Para monitoramento de produção:**

1. **Diário:** Google Cloud Console (visual, rápido)
2. **Semanal:** BigQuery Export (análise detalhada)
3. **Alertas:** Cloud Monitoring Alerts (automático)
4. **Backup:** Contador local (estimativa apenas)

**Ordem de confiabilidade:**
1. 🥇 Google Cloud Console / BigQuery
2. 🥈 Cloud Monitoring API
3. 🥉 Contador local (pode falhar)

---

## �📋 Pricing Atual (2025)

### Geocoding API

| Volume | Preço |
|--------|-------|
| 0 - 10.000/mês | **GRÁTIS** |
| 10.001 - 100.000/mês | $5 por 1.000 |
| 100.001 - 500.000/mês | $4 por 1.000 |
| 500.001+/mês | Contato com vendas |

### Distance Matrix API

| Volume | Preço |
|--------|-------|
| 0 - 100.000/mês | $5 por 1.000 |
| 100.001 - 500.000/mês | $4 por 1.000 |
| 500.001+/mês | Contato com vendas |

**⚠️ IMPORTANTE:** Distance Matrix é **PAGO DESDE A PRIMEIRA REQUISIÇÃO**!

---

## 🔔 Alertas Configurados

### Alertas Locais (no código)

1. **50% da cota gratuita** (5.000 requisições):
   ```
   🚨 ALERTA: VOCÊ ATINGIU 50% DA COTA GRATUITA!
   ```

2. **Cota gratuita excedida** (10.000 requisições):
   ```
   ⚠️️️ ATENÇÃO: COTA GRATUITA EXCEDIDA!
   💰 Agora você está sendo cobrado: $5 por 1.000 requisições
   ```

3. **Alto uso de Distance Matrix** (5.000 requisições):
   ```
   🚨 ALERTA: ALTO USO DE DISTANCE MATRIX API!
   ```

### Alertas no Google Cloud

Configure em **Billing** → **Budgets & alerts**

---

## 📊 Exemplo de Consumo Real

### Cenário: 100 usuários/dia consultando CEP

**Cálculo:**
- 100 usuários × 30 dias = 3.000 requisições/mês
- Sincronização de unidades: ~150 requisições/mês (se houver mudanças)
- **Total: ~3.150 requisições/mês**

**Custo:**
- Dentro da cota gratuita (10.000/mês)
- **Custo: $0.00**

### Cenário: 500 usuários/dia consultando CEP

**Cálculo:**
- 500 usuários × 30 dias = 15.000 requisições/mês
- Sincronização: ~150 requisições/mês
- **Total: ~15.150 requisições/mês**

**Custo:**
- Gratuitas: 10.000
- Pagas: 5.150 × ($5/1.000) = $25.75
- **Custo: $25.75/mês**

---

## 🛡️ Proteções Implementadas

1. **Lock de sincronização**: Evita race conditions
2. **Contador persistente**: Salvo em `data/google_maps_counter.json`
3. **Reset mensal automático**: Zera contador no dia 1 de cada mês
4. **Logs detalhados**: Todas as requisições são logadas
5. **Alertas em tempo real**: Avisos quando atingir limites

---

## 🔍 Troubleshooting

### Contador não está atualizando

1. Verifique permissões do arquivo:
   ```bash
   ls -la data/google_maps_counter.json
   ```

2. Verifique logs do Docker:
   ```bash
   docker compose logs bot_central | grep "Contador salvo"
   ```

3. Execute o script de monitoramento:
   ```bash
   python scripts/monitorar_google_maps.py
   ```

### Divergência entre contador local e Google Cloud

- O contador local pode estar desatualizado se o Docker foi reiniciado
- Sempre confie nos dados do Google Cloud Console como fonte da verdade
- Use o contador local apenas para estimativas

### Como resetar o contador

**⚠️ CUIDADO:** Isso não afeta o billing real do Google!

```bash
# Backup
cp data/google_maps_counter.json data/google_maps_counter.backup.json

# Reset
echo '{
  "geocoding": {"total": 0, "mes_atual": 0, "ultimo_reset": "2026-04-01"},
  "distance_matrix": {"total": 0, "mes_atual": 0, "ultimo_reset": "2026-04-01"}
}' > data/google_maps_counter.json
```

---

## 📞 Suporte

- **Documentação oficial**: https://developers.google.com/maps/documentation
- **Pricing**: https://mapsplatform.google.com/pricing/
- **Console**: https://console.cloud.google.com/
- **Suporte Google**: https://cloud.google.com/support

---

**Última atualização:** Abril 2026
