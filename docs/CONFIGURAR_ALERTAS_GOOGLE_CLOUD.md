# 📧 Como Configurar Alertas de E-mail no Google Cloud

## ✅ RESPOSTA DIRETA

**SIM, é possível configurar alertas de e-mail quando atingir 5.000 requisições!**

Existem **3 métodos oficiais** do Google Cloud:

1. **Budget Alerts** (baseado em custo) - ⚠️ Não funciona para 5.000 requisições
2. **Quota Alerts** (baseado em uso de API) - ✅ **RECOMENDADO**
3. **Cloud Monitoring Alerts** (customizado) - ✅ **MAIS PODEROSO**

---

## 🎯 Método 1: Quota Alerts (MAIS FÁCIL)

**Fonte:** [Google Cloud Quotas Documentation](https://docs.cloud.google.com/docs/quotas/set-up-quota-alerts)

### ⚠️ LIMITAÇÃO IMPORTANTE

Quota Alerts funcionam apenas para **quotas do projeto**, não para **contadores de uso**.

**Problema:** Geocoding API tem cota de **10.000 requisições GRATUITAS/mês**, mas você quer alerta em **5.000**.

**Solução:** Use o Método 2 (Cloud Monitoring) abaixo.

### Como Configurar (se quiser alerta em 100% da quota)

1. Acesse: https://console.cloud.google.com/iam-admin/quotas
2. Filtre por "Geocoding API"
3. Clique em **⋮ More actions** → **Create usage alert**
4. Configure:
   - **Threshold**: 50% (5.000 de 10.000)
   - **Notification channel**: Email
5. Clique em **Create**

---

## 🎯 Método 2: Cloud Monitoring Alerts (RECOMENDADO) ✅

**Fonte:** [Cloud Monitoring API Usage](https://docs.cloud.google.com/apis/docs/monitoring)

Este método permite criar alertas **customizados** baseados em **número exato de requisições**.

### Passo a Passo Completo

#### 1. Acesse Cloud Monitoring

🔗 https://console.cloud.google.com/monitoring/alerting

#### 2. Crie uma Política de Alerta

1. Clique em **+ CREATE POLICY**
2. Clique em **Select a metric**

#### 3. Configure a Métrica

**Filtros:**
- **Resource type**: `Consumed API`
- **Metric**: `serviceruntime.googleapis.com/api/request_count`
- **Service**: `geocoding-backend.googleapis.com`

**MQL Query (Monitoring Query Language):**
```
fetch consumed_api
| metric 'serviceruntime.googleapis.com/api/request_count'
| filter resource.service == 'geocoding-backend.googleapis.com'
| group_by 1d, [value_request_count_sum: sum(value.request_count)]
| every 1d
| condition value_request_count_sum > 5000
```

#### 4. Configure o Threshold

- **Condition type**: Threshold
- **Threshold position**: Above threshold
- **Threshold value**: `5000`
- **For**: `1 minute` (quanto tempo acima do threshold)

#### 5. Configure Notificações

1. Clique em **Notification Channels**
2. Clique em **Manage Notification Channels**
3. Adicione um canal de **Email**:
   - **Display name**: "Alerta Geocoding"
   - **Email address**: seu-email@exemplo.com
4. Salve e selecione o canal criado

#### 6. Nomeie e Salve

- **Alert name**: "Geocoding API - 5.000 requisições"
- **Documentation** (opcional):
  ```
  ⚠️ ALERTA: Geocoding API atingiu 5.000 requisições!
  
  Você está em 50% da cota gratuita (10.000/mês).
  
  Próximos passos:
  - Revisar uso no dashboard
  - Otimizar chamadas se necessário
  - Planejar custos futuros
  ```

#### 7. Clique em **CREATE POLICY**

---

## 📊 Método 3: Budget Alerts (Para Custos)

**Fonte:** [Cloud Billing Budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)

**⚠️ IMPORTANTE:** Budget Alerts são baseados em **CUSTO**, não em número de requisições.

Como 5.000 requisições = **$0.00** (dentro da cota gratuita), **não é possível** criar um Budget Alert para isso.

**Use Budget Alerts para:**
- Alerta quando custo atingir $5
- Alerta quando custo atingir $10
- Alerta quando custo atingir $25

### Como Configurar Budget Alert

1. Acesse: https://console.cloud.google.com/billing/budgets
2. Clique em **CREATE BUDGET**
3. Configure:
   - **Name**: "Google Maps Budget"
   - **Budget type**: Specified amount
   - **Target amount**: $10.00
   - **Threshold rules**:
     - 50% ($5) - Actual spend
     - 90% ($9) - Actual spend
     - 100% ($10) - Actual spend
4. **Email notifications**:
   - ✅ Email alerts to billing admins and users
   - ✅ Link Monitoring email notification channels
5. Clique em **FINISH**

---

## 🔔 Tipos de Notificação Disponíveis

### 1. Email (Padrão)

**Configuração:**
- Automático para Billing Admins
- Customizado via Cloud Monitoring Notification Channels

**Exemplo de e-mail:**
```
Subject: [Google Cloud] Alert: Geocoding API - 5.000 requisições

Your alert policy "Geocoding API - 5.000 requisições" has triggered.

Metric: serviceruntime.googleapis.com/api/request_count
Current value: 5,127 requests
Threshold: 5,000 requests

View in Console: https://console.cloud.google.com/...
```

### 2. SMS

**Configuração:**
1. Vá em: https://console.cloud.google.com/monitoring/alerting/notifications
2. Clique em **ADD NEW**
3. Selecione **SMS**
4. Adicione número de telefone

**Custo:** Grátis até 100 SMS/mês

### 3. Slack

**Configuração:**
1. Crie um Slack Webhook
2. Adicione como Notification Channel
3. Tipo: **Webhook**

### 4. Pub/Sub (Programático)

**Configuração:**
1. Crie um tópico Pub/Sub
2. Configure Cloud Function para processar
3. Envie para Slack, Discord, Telegram, etc.

**Exemplo:**
```python
def process_alert(event, context):
    """Processa alerta e envia para Slack"""
    alert_data = json.loads(base64.b64decode(event['data']))
    
    if alert_data['metric'] == 'api/request_count':
        send_to_slack(f"⚠️ Geocoding: {alert_data['value']} requisições!")
```

---

## 📋 Exemplo Prático: Alerta em 5.000 Requisições

### Configuração Recomendada

**Criar 3 alertas:**

1. **50% da cota (5.000 req)** - Aviso
   - Threshold: 5000
   - Severity: Warning
   - Notification: Email

2. **90% da cota (9.000 req)** - Atenção
   - Threshold: 9000
   - Severity: Error
   - Notification: Email + SMS

3. **100% da cota (10.000 req)** - Crítico
   - Threshold: 10000
   - Severity: Critical
   - Notification: Email + SMS + Slack

### MQL Query Completa

```
fetch consumed_api
| metric 'serviceruntime.googleapis.com/api/request_count'
| filter resource.service == 'geocoding-backend.googleapis.com'
| group_by 1d, [value_request_count_sum: sum(value.request_count)]
| every 1d
| condition val() > 5000
```

---

## ✅ Checklist de Configuração

- [ ] Habilitar Cloud Monitoring API
- [ ] Criar Notification Channel (Email)
- [ ] Criar Alert Policy para 5.000 requisições
- [ ] Criar Alert Policy para 9.000 requisições
- [ ] Criar Alert Policy para 10.000 requisições
- [ ] Criar Budget Alert para $10
- [ ] Testar alertas (forçar threshold)
- [ ] Documentar para equipe

---

## 🧪 Como Testar os Alertas

### Método 1: Forçar Threshold Baixo

Temporariamente, configure threshold para **100 requisições** e faça alguns testes.

### Método 2: Usar Test Notification

1. Vá na Alert Policy
2. Clique em **⋮** → **Test notification**
3. Verifique se recebeu o e-mail

---

## 💡 Dicas Importantes

### 1. Alertas são Informativos, Não Preventivos

**⚠️ IMPORTANTE:** Alertas **NÃO bloqueiam** o uso da API automaticamente!

Eles apenas **notificam** você. Para bloquear, você precisa:
- Configurar quotas no projeto
- Implementar rate limiting no código
- Usar Cloud Functions para desabilitar API

### 2. Delay de Notificação

- **Email**: 1-5 minutos
- **SMS**: 1-3 minutos
- **Pub/Sub**: Quase instantâneo

### 3. Frequência de Alertas

Por padrão, alertas são enviados:
- **Primeira vez**: Imediatamente
- **Repetição**: A cada 24 horas (se condição persistir)

Configure em: **Alert Policy** → **Notification rate limit**

---

## 🔗 Links Oficiais

- **Cloud Monitoring Alerts**: https://console.cloud.google.com/monitoring/alerting
- **Notification Channels**: https://console.cloud.google.com/monitoring/alerting/notifications
- **Budget Alerts**: https://console.cloud.google.com/billing/budgets
- **Quota Alerts**: https://console.cloud.google.com/iam-admin/quotas
- **Documentação**: https://cloud.google.com/monitoring/alerts

---

## 📞 Suporte

- **Documentação oficial**: https://cloud.google.com/monitoring/docs
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/google-cloud-monitoring
- **Suporte Google**: https://cloud.google.com/support

---

**Última atualização:** Abril 2026  
**Fonte:** Documentação oficial do Google Cloud
