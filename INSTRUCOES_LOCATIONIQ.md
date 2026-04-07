# 🗺️ Configuração LocationIQ para Geocodificação

## Por que LocationIQ?

O **Nominatim** (OpenStreetMap) tem cobertura limitada no Brasil - muitos endereços não estão mapeados.

O **LocationIQ** usa dados do OSM + dados próprios, com **melhor cobertura para endereços brasileiros**.

---

## 📋 Passo a Passo

### 1. Criar Conta Gratuita

1. Acesse: https://locationiq.com/
2. Clique em **"Sign Up"** (canto superior direito)
3. Preencha:
   - Email
   - Senha
   - Nome
4. Confirme o email

### 2. Obter API Key

1. Faça login em: https://my.locationiq.com/
2. No dashboard, você verá sua **Access Token**
3. Copie a API Key (formato: `pk.xxxxxxxxxxxxxxxxxxxxx`)

### 3. Configurar no Projeto

**Opção A: Variável de Ambiente (Recomendado)**

1. Crie arquivo `.env` na raiz do projeto:
   ```bash
   LOCATIONIQ_API_KEY=pk.sua_api_key_aqui
   ```

2. Instale python-dotenv (se ainda não tiver):
   ```bash
   pip install python-dotenv
   ```

3. Adicione no início do `geocode_unidades.py`:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

**Opção B: Editar Diretamente no Script**

Abra `geocode_unidades.py` e substitua:
```python
LOCATIONIQ_API_KEY = os.getenv('LOCATIONIQ_API_KEY', '')
```

Por:
```python
LOCATIONIQ_API_KEY = 'pk.sua_api_key_aqui'
```

### 4. Executar Geocodificação

```bash
python geocode_unidades.py
```

---

## 📊 Limites do Plano Gratuito

- ✅ **5.000 requisições/dia**
- ✅ **Sem cartão de crédito**
- ✅ **Sem expiração**

Para as 10 unidades que faltam, você usará apenas **~30 requisições** (3 tentativas por unidade).

---

## 🔍 Como Funciona

O script agora tenta **3 métodos** em ordem:

1. **LocationIQ** - Endereço completo formatado
2. **Nominatim** - Fallback se LocationIQ falhar
3. **ViaCEP + LocationIQ** - Busca por CEP

Se LocationIQ não estiver configurado, usa apenas Nominatim (como antes).

---

## ⚠️ Troubleshooting

### Erro: "API Key inválida"
- Verifique se copiou a key completa (começa com `pk.`)
- Confirme que a conta está ativa

### Erro: "Limite excedido"
- Você atingiu 5.000 requisições hoje
- Aguarde até amanhã ou crie outra conta

### Ainda não encontra endereços
- LocationIQ também depende do OSM
- Para endereços muito específicos, considere Google Geocoding API
- Ou geocodifique manualmente via Google Maps

---

## 🎯 Próximos Passos

Após configurar a API Key:

1. Execute: `python geocode_unidades.py`
2. O script tentará geocodificar as 10 unidades que falharam
3. Verifique o resultado no terminal (logging detalhado)
4. Confira `data/unidades.json` atualizado

---

## 📞 Suporte

- Documentação: https://locationiq.com/docs
- Dashboard: https://my.locationiq.com/
- Suporte: support@locationiq.com
