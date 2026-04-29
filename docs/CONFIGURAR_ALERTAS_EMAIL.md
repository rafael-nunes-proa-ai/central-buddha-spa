# 📧 Sistema de Alertas por E-mail - Google Maps API

## 📋 Visão Geral

Sistema automático de alertas por e-mail que notifica os responsáveis quando:
- ✅ **50% da cota gratuita** é atingida (5.000 requisições)
- 🚨 **100% da cota gratuita** é excedida (10.000 requisições)

---

## 🔧 Configuração

### 1. **Variáveis de Ambiente**

Adicione as seguintes variáveis no arquivo `.env`:

```bash
# ============================================================================
# AWS SES - Sistema de Alertas por E-mail
# ============================================================================
# Credenciais AWS SES para envio de alertas de monitoramento
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY=AKIARPR3UDY7H33SUTUK
AWS_SES_SECRET_KEY=BAsfcjvKqcVxKzxLyld0ImOPoa8se8C2u4Uc9DHOCT2l

# E-mail remetente (deve estar verificado no AWS SES)
EMAIL_FROM=naoresponda@proatecnologia.com.br

# E-mails dos responsáveis que receberão os alertas
ALERT_EMAIL_1=email.responsavel1@exemplo.com.br
ALERT_EMAIL_2=email.responsavel2@exemplo.com.br
```

### 2. **Instalar Dependência**

O sistema usa **boto3** (AWS SDK para Python):

```bash
pip install boto3
```

Ou adicione ao `requirements.txt`:
```
boto3>=1.28.0
```

### 3. **Verificar E-mail no AWS SES**

⚠️ **IMPORTANTE:** O e-mail remetente (`EMAIL_FROM`) deve estar **verificado** no AWS SES.

**Passos:**
1. Acesse: https://console.aws.amazon.com/ses/
2. Vá em **Verified identities**
3. Clique em **Create identity**
4. Escolha **Email address**
5. Digite: `naoresponda@proatecnologia.com.br`
6. Clique em **Create identity**
7. Verifique o e-mail recebido e clique no link de confirmação

---

## 🧪 Testar o Sistema

### **Opção 1: Script de Teste Interativo**

```bash
python testar_alertas_email.py
```

Menu:
```
1. Enviar e-mail de teste simples
2. Enviar alerta de 50% da cota (5.000 requisições)
3. Enviar alerta de 100% da cota (10.000 requisições)
0. Sair
```

### **Opção 2: Teste Direto via Python**

```python
from services.email_service import testar_envio_email

testar_envio_email()
```

---

## 📊 Como Funciona

### **Fluxo de Monitoramento:**

```
1. Usuário informa CEP
   ↓
2. google_maps_service.py chama Google Maps API
   ↓
3. Contador é incrementado (_incrementar_contador)
   ↓
4. Verifica se atingiu limites (5.000 ou 10.000)
   ↓
5. Se sim: Envia alerta por e-mail
   ↓
6. E-mail é enviado via AWS SES
```

### **Alertas Configurados:**

#### **Alerta 1: 50% da Cota (5.000 requisições)**
- **Assunto:** 🚨 ALERTA: Google Maps API - 50% da Cota Gratuita Atingida
- **Tipo:** Aviso (laranja)
- **Ação:** Monitorar uso

#### **Alerta 2: 100% da Cota (10.000 requisições)**
- **Assunto:** 🚨🚨 URGENTE: Google Maps API - Cota Gratuita EXCEDIDA!
- **Tipo:** Crítico (vermelho)
- **Ação:** Ação imediata necessária

---

## 📧 Exemplo de E-mail

### **Alerta de 50%:**

```
🚨 ALERTA AUTOMÁTICO
Buddha Spa - Bot Central

🚨 50% da Cota Gratuita Atingida!

📊 ESTATÍSTICAS DE USO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requisições este mês: 5,000
Total histórico: 5,000
Cota gratuita mensal: 10.000 requisições
Percentual usado: 50.0%
Data/Hora: 29/04/2026 12:00:00

💰 INFORMAÇÕES DE CUSTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cota gratuita: 10.000 requisições/mês
Após 10.000: $5 por 1.000 requisições (até 100k)
Após 100.000: $4 por 1.000 requisições (até 500k)

✅ AÇÕES RECOMENDADAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Revisar uso no dashboard do Google Cloud
- Verificar logs do bot para identificar picos de uso
- Considerar otimizações se necessário (cache, redução de chamadas)
- Monitorar próximos dias para evitar exceder a cota

Dashboard: https://console.cloud.google.com/apis/dashboard
```

---

## 🔍 Verificar Logs

### **Logs de Envio:**

```
📧 ENVIANDO E-MAIL DE ALERTA
De: naoresponda@proatecnologia.com.br
Para: responsavel1@exemplo.com.br, responsavel2@exemplo.com.br
Assunto: 🚨 ALERTA: Google Maps API - 50% da Cota Gratuita Atingida
✅ E-mail enviado com sucesso!
📬 MessageId: 0100018f1234abcd-12345678-1234-1234-1234-123456789abc-000000
```

### **Logs de Erro:**

```
❌ ERRO ao enviar e-mail: MessageRejected: Email address is not verified.
```

**Solução:** Verificar o e-mail remetente no AWS SES (ver seção 3).

---

## 🚨 Troubleshooting

### **Problema 1: E-mail não enviado**

**Erro:**
```
⚠️ AWS SES não configurado. E-mail não enviado.
```

**Solução:**
- Verificar se as variáveis de ambiente estão configuradas no `.env`
- Verificar se o arquivo `.env` está sendo carregado

### **Problema 2: Email address is not verified**

**Erro:**
```
❌ ERRO ao enviar e-mail: MessageRejected: Email address is not verified.
```

**Solução:**
- Verificar o e-mail remetente no AWS SES (console.aws.amazon.com/ses/)
- Confirmar o e-mail de verificação recebido

### **Problema 3: Invalid credentials**

**Erro:**
```
❌ ERRO ao enviar e-mail: InvalidClientTokenId: The security token included in the request is invalid.
```

**Solução:**
- Verificar se `AWS_SES_ACCESS_KEY` e `AWS_SES_SECRET_KEY` estão corretos
- Verificar se as credenciais têm permissão para usar SES

### **Problema 4: Nenhum e-mail configurado**

**Erro:**
```
⚠️ Nenhum e-mail de alerta configurado.
```

**Solução:**
- Adicionar `ALERT_EMAIL_1` e/ou `ALERT_EMAIL_2` no `.env`

---

## 📊 Monitoramento

### **Arquivo de Contador:**

`data/google_maps_counter.json`

```json
{
  "geocoding": {
    "total": 5000,
    "mes_atual": 5000,
    "ultimo_reset": "2026-04-01"
  },
  "distance_matrix": {
    "total": 0,
    "mes_atual": 0,
    "ultimo_reset": "2026-04-01"
  }
}
```

### **Reset Automático:**

- O contador `mes_atual` é resetado automaticamente todo dia 1º do mês
- O contador `total` é mantido historicamente

---

## 🔐 Segurança

### **Boas Práticas:**

1. ✅ **Nunca commitar** credenciais no Git
2. ✅ Usar `.env` para variáveis sensíveis
3. ✅ Adicionar `.env` no `.gitignore`
4. ✅ Usar credenciais IAM com permissões mínimas (apenas SES)
5. ✅ Rotacionar credenciais periodicamente

### **Permissões IAM Necessárias:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📚 Referências

- **AWS SES Documentation:** https://docs.aws.amazon.com/ses/
- **Boto3 SES:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html
- **Google Maps Pricing:** https://developers.google.com/maps/billing-and-pricing/faq

---

## ✅ Checklist de Implementação

- [x] Criar `services/email_service.py`
- [x] Integrar com `google_maps_service.py`
- [x] Adicionar variáveis no `.env.example`
- [x] Criar script de teste `testar_alertas_email.py`
- [x] Documentar configuração
- [ ] Adicionar `boto3` no `requirements.txt`
- [ ] Configurar variáveis no `.env` de produção
- [ ] Verificar e-mail remetente no AWS SES
- [ ] Testar envio de e-mail
- [ ] Validar recebimento pelos responsáveis

---

**Última atualização:** 29/04/2026
