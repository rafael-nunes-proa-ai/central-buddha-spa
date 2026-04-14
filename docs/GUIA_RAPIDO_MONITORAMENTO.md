# 🚀 Guia Rápido: Como Ver Requisições Reais

## ⚡ Método Mais Rápido (2 minutos)

### 1. Acesse o Google Cloud Console

🔗 **https://console.cloud.google.com/apis/dashboard**

### 2. Clique em "Geocoding API"

Você verá um card com:
- Nome: **Geocoding API**
- Status: Enabled
- Gráfico de uso

### 3. Clique na aba "Metrics"

Você verá:
```
📊 Traffic (Requisições)
   Hoje: 116 requests
   Ontem: 0 requests
   Esta semana: 116 requests
   Este mês: 116 requests
```

**PRONTO! Esses são os dados REAIS e OFICIAIS.** ✅

---

## 💰 Ver Custos (3 minutos)

### 1. Acesse Billing Reports

🔗 **https://console.cloud.google.com/billing/reports**

### 2. Configure filtros

- **Service**: Maps Platform
- **SKU**: Geocoding API
- **Period**: This month

### 3. Veja o resultado

```
Geocoding API Requests
116 requests × $0.00 = $0.00
(Dentro da cota gratuita)
```

---

## 📱 Configurar Alertas (5 minutos)

### 1. Crie um Budget

🔗 **https://console.cloud.google.com/billing/budgets**

### 2. Configure

- **Name**: Google Maps Alert
- **Budget amount**: $10/mês
- **Threshold**: 50%, 90%, 100%
- **Email**: seu-email@exemplo.com

### 3. Salve

Você receberá e-mail quando:
- ✉️ Atingir $5 (50%)
- ✉️ Atingir $9 (90%)
- ✉️ Atingir $10 (100%)

---

## 🔍 Comparação: Local vs Cloud

| Aspecto | Contador Local | Google Cloud Console |
|---------|----------------|---------------------|
| **Confiabilidade** | 🟡 Pode falhar | 🟢 100% confiável |
| **Tempo real** | 🟢 Sim | 🟢 Sim |
| **Histórico** | 🟡 Desde instalação | 🟢 Ilimitado |
| **Custos** | ❌ Não mostra | 🟢 Mostra exato |
| **Acesso** | 🟡 Precisa SSH | 🟢 Qualquer lugar |
| **Alertas** | 🟡 Apenas logs | 🟢 E-mail automático |

**Recomendação:** Use o Google Cloud Console como fonte da verdade! 🎯

---

## 📊 Exemplo Real

### Cenário: Você quer saber quantas requisições fez hoje

#### ❌ Forma ERRADA:
```bash
# Olhar o contador local
cat data/google_maps_counter.json
# Resultado: 116 (pode estar desatualizado!)
```

#### ✅ Forma CORRETA:
1. Abra: https://console.cloud.google.com/apis/dashboard
2. Clique em "Geocoding API"
3. Veja o gráfico de hoje
4. **Resultado oficial: 116 requisições** ✅

---

## 🎯 Checklist de Monitoramento

### Diário
- [ ] Abrir Google Cloud Console
- [ ] Verificar gráfico de requisições
- [ ] Conferir se está dentro da cota

### Semanal
- [ ] Verificar Billing Reports
- [ ] Conferir custos acumulados
- [ ] Ajustar alertas se necessário

### Mensal
- [ ] Revisar uso total do mês
- [ ] Planejar próximo mês
- [ ] Otimizar se necessário

---

## 🆘 FAQ

### P: O contador local mostra 100, mas o Google mostra 116. Qual está certo?

**R:** O Google está certo! O contador local pode ter perdido 16 requisições por:
- Restart do Docker
- Race condition
- Erro de escrita no arquivo

**Solução:** Sempre confie no Google Cloud Console.

---

### P: Como sei se estou sendo cobrado?

**R:** Vá em Billing Reports. Se aparecer custo > $0.00, você está sendo cobrado.

**Exemplo:**
```
✅ 5.000 requests × $0.00 = $0.00 (Grátis)
⚠️ 15.000 requests × $0.025 = $25.00 (Cobrando)
```

---

### P: Posso confiar 100% no Google Cloud Console?

**R:** SIM! É a fonte oficial. O Google usa esses dados para te cobrar, então é 100% preciso.

---

### P: E se eu quiser exportar os dados?

**R:** Configure BigQuery Export:
1. https://console.cloud.google.com/billing/export
2. Ative BigQuery export
3. Consulte com SQL quando quiser

---

## 🔗 Links Úteis

- **Dashboard**: https://console.cloud.google.com/apis/dashboard
- **Metrics**: https://console.cloud.google.com/apis/api/geocoding-backend.googleapis.com/metrics
- **Billing**: https://console.cloud.google.com/billing/reports
- **Budgets**: https://console.cloud.google.com/billing/budgets
- **Documentação**: https://cloud.google.com/monitoring/docs

---

**Última atualização:** Abril 2026
