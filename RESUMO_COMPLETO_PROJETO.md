# 📋 Resumo Completo - Bot Central Buddha Spa

> **Documento de Referência para Novos Chats**  
> Última atualização: 27/04/2026

---

## 🎯 Visão Geral do Projeto

**Bot Central** é um agente de IA independente desenvolvido para a **Buddha Spa**, especializado em:
- ✅ Fornecer **informações de contato** das unidades
- ✅ Encontrar a **unidade mais próxima** usando CEP ou bairro
- ✅ Direcionar clientes para **reagendamento** e **cancelamento**
- ❌ **NÃO faz agendamentos diretos** (direciona para as unidades)

---

## 🏗️ Arquitetura do Sistema

### Stack Tecnológica
```
Backend: FastAPI (Python)
IA: AWS Bedrock (Claude Sonnet 4.5)
Framework IA: Pydantic AI
Banco de Dados: PostgreSQL
Geocodificação: Google Maps API
Deploy: Docker + Docker Compose
```

### Estrutura de Diretórios
```
agente_central/
├── app.py                          # Servidor FastAPI principal
├── agents/
│   ├── agent_central.py            # Definição do agente de IA
│   └── deps.py                     # Dependências/contexto do agente
├── tools/
│   └── tool_central.py             # Ferramentas do agente (35KB)
├── services/
│   ├── google_maps_service.py      # Integração Google Maps
│   └── users.py                    # Serviços de usuário
├── store/
│   ├── database.py                 # Operações PostgreSQL
│   └── context.py                  # Gerenciamento de contexto
├── data/
│   ├── unidades.json               # Base de unidades (153KB)
│   └── google_maps_counter.json    # Contador de requisições API
├── security/
│   └── auth.py                     # Autenticação API Key
├── utils.py                        # Funções utilitárias
└── docs/                           # Documentação de monitoramento
```

---

## 🔑 Componentes Principais

### 1. **app.py** - Servidor FastAPI

**Porta:** 8001 (configurável via `PORT` env)

**Endpoints:**
- `GET /` - Health check
- `POST /chat-central` - Endpoint principal do bot

**Características:**
- ✅ Proteção contra processamento duplicado (locks)
- ✅ Sessões isoladas com prefixo `central_`
- ✅ Detecção de palavras de encerramento (`sair`, `encerrar`)
- ✅ Flag `finalizar_sessao` para React Flow
- ✅ Recarregamento de contexto do banco após tools
- ✅ Middleware CORS habilitado

**Fluxo de Requisição:**
```
1. Recebe mensagem do usuário
2. Verifica API Key (security/auth.py)
3. Cria/recupera sessão com prefixo "central_"
4. Carrega histórico de mensagens
5. Executa central_agent
6. Salva novas mensagens
7. Recarrega contexto do banco (tools podem ter atualizado)
8. Retorna resposta + flag finalizar_sessao (se aplicável)
```

---

### 2. **agent_central.py** - Agente de IA

**Modelo:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (AWS Bedrock)

**System Prompt:** ~450 linhas com instruções detalhadas

**Principais Fluxos:**

#### A) **Fluxo de Agendamento**
```
1. Usuário menciona "agendar"
2. Tool: incrementar_tentativas_agendamento()
3. Solicita CEP ou bairro
4. Processa localização
5. Mostra unidade(s) mais próxima(s)
6. Se tentativas >= 2: Mostra contato e encerra
```

#### B) **Fluxo de Reagendamento**
```
1. Usuário menciona "reagendar"
2. Pergunta: "Quer informações ou realizar reagendamento?"
3. Se REALIZAR:
   - Pergunta nome da unidade
   - Tool: buscar_unidade_por_nome()
   - Mostra contato da unidade
4. Pergunta: "Posso ajudar em algo mais?"
```

#### C) **Fluxo de Cancelamento**
```
1. Usuário menciona "cancelar"
2. Tool: marcar_contexto_cancelamento()
3. Pergunta: "Quer informações ou realizar cancelamento?"
4. Se REALIZAR:
   - Pergunta nome da unidade
   - Tool: buscar_unidade_por_nome()
   - Mostra contato da unidade
5. Pergunta: "Posso ajudar em algo mais?"
```

#### D) **Processamento CEP/Bairro**
```
CEP:
1. Tool: buscar_endereco_por_cep(cep)
2. Retorna: "VALIDO|cidade|estado|bairro"
3. Tool: encontrar_unidades_no_raio()
4. Retorna: "UNICA|dados" ou "MULTIPLAS|lista"

BAIRRO:
1. Tool: buscar_bairros_por_nome(nome_bairro)
2. Retorna: "UNICO|cidade|estado" ou "MULTIPLOS|lista"
3. Tool: encontrar_unidade_mais_proxima()
```

**Tools Disponíveis:**
- `buscar_endereco_por_cep` - Geocodifica CEP
- `encontrar_unidade_mais_proxima` - Busca unidade mais próxima
- `encontrar_unidades_no_raio` - Busca múltiplas unidades no raio
- `buscar_bairros_por_nome` - Busca bairros por nome
- `listar_todas_unidades` - Lista todas as unidades
- `incrementar_tentativas_agendamento` - Previne loop infinito
- `buscar_unidade_por_nome` - Busca unidade por nome/cidade/bairro
- `obter_info_unidade` - Obtém informações de unidade específica
- `encerrar_atendimento` - Encerra sessão
- `marcar_contexto_cancelamento` - Marca contexto de cancelamento
- `registrar_step` - Tracking de navegação
- `registrar_assunto` - Tracking de assuntos

---

### 3. **deps.py** - Contexto do Agente

```python
@dataclass
class MyDeps:
    session_id: str
    
    # GEOLOCALIZAÇÃO
    cep_informado: Optional[str] = None
    bairro_informado: Optional[str] = None
    cidade_informada: Optional[str] = None
    estado_informado: Optional[str] = None
    latitude_usuario: Optional[float] = None
    longitude_usuario: Optional[float] = None
    unidade_encontrada: Optional[dict] = None
    unidades_multiplas: Optional[list] = None
    
    # CONTROLE
    tentativas_agendamento: int = 0
    
    # REAGENDAMENTO
    quer_reagendar: Optional[bool] = None
    quer_info_reagendamento: Optional[bool] = None
    precisa_contato_unidade: Optional[bool] = None
    nome_unidade_reagendamento: Optional[str] = None
    
    # CANCELAMENTO
    contexto_cancelamento: Optional[bool] = None
    
    # TRACKING
    steps: Optional[list[str]] = None
    assuntos: Optional[list[str]] = None
    
    # FINALIZAÇÃO
    finalizar_sessao: Optional[bool] = None
```

---

### 4. **database.py** - Persistência PostgreSQL

**Tabelas:**
- `sessions` - Sessões de conversa
- `messages` - Histórico de mensagens

**Funções Principais:**
```python
ensure_session(session_id)           # Cria sessão se não existe
get_session(session_id)              # Recupera sessão
add_messages(session_id, msgs)       # Salva mensagens
get_messages(session_id)             # Carrega histórico
update_context(session_id, data)     # Atualiza contexto
delete_session(session_id)           # Deleta sessão
cleanup_sessions(ttl_days=7)         # Limpeza automática
```

**Otimizações:**
- ✅ Remove campo `instructions` antes de salvar (gerado dinamicamente)
- ✅ Filtra mensagens inválidas/vazias
- ✅ Validação com `ModelMessagesTypeAdapter`
- ✅ Cleanup automático de sessões antigas (7 dias)

---

### 5. **google_maps_service.py** - Geocodificação

**APIs Utilizadas:**
- **Geocoding API** - Converte CEP em coordenadas
- **Distance Matrix API** - Calcula distância real de trajeto

**Monitoramento de Custos:**
```python
LIMITE_ALERTA_GEOCODING = 5000  # 50% da cota gratuita
LIMITE_ALERTA_DISTANCE = 5000   # Alerta de alto uso

# Geocoding API - Gratuito até 10.000/mês
# Após 10.000: $5 por 1.000 requisições (10k-100k)
# Após 100.000: $4 por 1.000 requisições (100k-500k)

# Distance Matrix API - PAGO desde a primeira requisição
# $5 por 1.000 requisições (até 100k)
```

**Contador de Requisições:**
- Arquivo: `data/google_maps_counter.json`
- Reset mensal automático
- Logs detalhados de uso
- Thread-safe (lock)

**Sistema de Alertas por E-mail (NOVO):**
- ✅ **AWS SES** para envio de e-mails
- ✅ Alerta automático em **5.000 requisições** (50% da cota)
- ✅ Alerta crítico em **10.000 requisições** (100% da cota)
- ✅ E-mails HTML formatados com estatísticas
- ✅ Múltiplos destinatários configuráveis
- 📧 Arquivo: `services/email_service.py`
- 📄 Documentação: `docs/CONFIGURAR_ALERTAS_EMAIL.md`

**Funções:**
```python
geocode_cep(cep)                     # CEP → coordenadas + endereço
calcular_distancia_real(...)         # Distância real de trajeto
obter_estatisticas()                 # Estatísticas de uso
```

---

### 6. **tool_central.py** - Ferramentas do Agente

**Arquivo:** 35.688 bytes (código extenso)

**Principais Tools:**

#### `buscar_endereco_por_cep(cep)`
- Valida formato do CEP
- Chama Google Maps Geocoding API
- Armazena coordenadas no contexto
- Retorna: `"VALIDO|cidade|estado|bairro"` ou `"INVALIDO|erro"`

#### `encontrar_unidades_no_raio(raio_km=50)`
- Busca unidades em `data/unidades.json`
- Calcula distância euclidiana
- Ordena por proximidade
- Retorna: `"UNICA|dados"` ou `"MULTIPLAS|lista_nomes"`

#### `encontrar_unidade_mais_proxima()`
- Similar ao anterior, mas retorna apenas a mais próxima
- Usado após seleção de bairro

#### `buscar_bairros_por_nome(nome_bairro)`
- Busca em `data/unidades.json`
- Retorna: `"UNICO|cidade|estado"` ou `"MULTIPLOS|lista"`

#### `buscar_unidade_por_nome(nome_unidade)`
- Busca fuzzy por nome/cidade/bairro
- Suporta seleção numérica (1, 2, 3...)
- Retorna: `"ENCONTRADA|dados"`, `"MULTIPLAS|lista"` ou `"NAO_ENCONTRADA"`

#### `obter_info_unidade(input_usuario)`
- Usado quando há múltiplas unidades
- Aceita número ou nome
- Retorna: `"ENCONTRADA|dados"` ou `"NAO_ENCONTRADA"`

#### `encerrar_atendimento(motivo="usuario_nao_precisa")`
- Deleta sessão do banco
- Retorna mensagem de despedida
- **CRÍTICO:** Sempre chamar quando usuário diz "não" a "Posso ajudar em algo mais?"

---

## 📊 Dados e Configuração

### **data/unidades.json**
```json
{
  "unidades": [
    {
      "nome": "Buddha Spa - Moema",
      "endereco": "Rua Exemplo, 123",
      "bairro": "Moema",
      "cidade": "São Paulo",
      "uf": "SP",
      "cep": "04567-890",
      "telefone": "(11) 1234-5678",
      "celular": "(11) 91234-5678",
      "email": "moema@buddhaspa.com.br",
      "horario": "Seg-Sex: 9h-20h, Sáb: 9h-18h",
      "latitude": -23.5505,
      "longitude": -46.6333,
      "link_maps": "https://maps.google.com/..."
    }
  ]
}
```

**Total:** 153KB (múltiplas unidades)

### **Variáveis de Ambiente (.env)**
```bash
# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buddha_central
DB_USER=postgres
DB_PASSWORD=senha

# APIs
GOOGLE_MAPS_API_KEY=AIza...
API_KEY=chave_secreta_api

# AWS Bedrock
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# AWS SES - Alertas por E-mail
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY=AKIARPR3UDY7H33SUTUK
AWS_SES_SECRET_KEY=BAsfcjvKqcVxKzxLyld0ImOPoa8se8C2u4Uc9DHOCT2l
EMAIL_FROM=naoresponda@proatecnologia.com.br
ALERT_EMAIL_1=responsavel1@exemplo.com.br
ALERT_EMAIL_2=responsavel2@exemplo.com.br

# Servidor
PORT=8001
```

---

## 🔐 Segurança

### **security/auth.py**
```python
async def verificar_api_key(api_key: str = Header(...)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="API Key inválida")
    return api_key
```

**Uso:**
```python
@app.post("/chat-central")
async def post_chat_central(req: ChatRequest, api_key: str = Depends(verificar_api_key)):
    ...
```

---

## 🚀 Deploy e Execução

### **Docker Compose**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
    env_file:
      - .env
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: buddha_central
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: senha
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### **Comandos**
```bash
# Desenvolvimento
python app.py

# Docker
docker-compose up -d

# Logs
docker-compose logs -f app

# Rebuild
docker-compose up -d --build
```

---

## 📈 Monitoramento

### **Google Maps API**
- Contador em `data/google_maps_counter.json`
- Alertas automáticos em 50% da cota
- Reset mensal automático
- Documentação: `docs/MONITORAMENTO_GOOGLE_MAPS.md`

### **Logs do Sistema**
```
🏢 BOT CENTRAL - NOVA MENSAGEM
Session ID: central_abc123
Mensagem: quero agendar

🔍 Google Geocoding: Buscando CEP 01234-567
✅ CEP encontrado: São Paulo/SP - Bairro: Centro
📍 Coordenadas: -23.5505, -46.6333
📊 Google Maps geocoding: 1234 requisições este mês (total: 5678)

📍 STEP REGISTRADO: Solicitação de CEP ou bairro
🗺️ Histórico: Solicitação de CEP ou bairro

✅ BOT CENTRAL - RESPOSTA:
Encontrei a unidade mais próxima de você. 😊
...
```

---

## 🎨 Regras de Negócio

### **Terminologia Obrigatória**
- ✅ Sempre usar "**terapia**" (não "massagem")
- ❌ Nunca corrigir o cliente se ele usar "massagem"
- ✅ Aceitar naturalmente, mas responder com "terapia"

### **Encerramento Obrigatório**
Quando usuário responder **NÃO** a "Posso ajudar em algo mais?":
- ✅ **SEMPRE** chamar `encerrar_atendimento()`
- ❌ **NUNCA** apenas agradecer sem encerrar

**Palavras de encerramento:**
- "não", "não preciso", "obrigado", "tudo certo", "está bem", "só isso", "valeu"

### **Prevenção de Loop Infinito**
- Contador: `tentativas_agendamento`
- Se `>= 2`: Mostra contato da unidade e encerra gentilmente
- Tool: `incrementar_tentativas_agendamento()`

---

## 🔄 Fluxo Completo de Exemplo

```
USUÁRIO: Oi
BOT: Olá! Sou o assistente virtual da central de atendimento Buddha SPA.
     Como posso ajudar? 😊

USUÁRIO: Quero agendar uma massagem
BOT: [incrementar_tentativas_agendamento]
     Esse tipo de atendimento é feito diretamente com as unidades. 😊
     Me informe seu CEP, bairro ou envie sua localização para que eu 
     te direcione à unidade mais próxima. 📍

USUÁRIO: 01310-100
BOT: [buscar_endereco_por_cep("01310-100")]
     [encontrar_unidades_no_raio()]
     Encontrei a unidade mais próxima de você. 😊
     
     📍 Buddha Spa - Av. Paulista
     🏠 Endereço: Av. Paulista, 1000 - Bela Vista, São Paulo - SP
     🕒 Horário: Seg-Sex: 9h-20h, Sáb: 9h-18h
     📞 Telefone: (11) 1234-5678
     📱 WhatsApp: (11) 91234-5678
     📧 E-mail: paulista@buddhaspa.com.br
     🗺️ Ver no mapa: [link]
     
     Deseja consultar outra unidade?

USUÁRIO: Não
BOT: Posso ajudar em algo mais?

USUÁRIO: Não, obrigado
BOT: [encerrar_atendimento("usuario_nao_precisa")]
     Obrigado por entrar em contato com a Buddha Spa! 😊
     Volte sempre que precisar! 🙏
     
     [finalizar_sessao: true]
```

---

## 🐛 Debugging e Troubleshooting

### **Problemas Comuns**

#### 1. **Sessão não encerra**
- ✅ Verificar se `encerrar_atendimento()` foi chamada
- ✅ Verificar logs: `🔴 FINALIZAR_SESSAO`
- ✅ Verificar flag `finalizar_sessao: true` na resposta

#### 2. **Contexto não persiste**
- ✅ Verificar `update_context()` nas tools
- ✅ Verificar recarregamento do contexto em `app.py` (linha 177)
- ✅ Verificar merge de contexto (linhas 193-211)

#### 3. **Google Maps quota excedida**
- ✅ Verificar `data/google_maps_counter.json`
- ✅ Verificar logs de alerta
- ✅ Considerar otimizar buscas (cache, raio menor)

#### 4. **Mensagens duplicadas**
- ✅ Verificar lock em `app.py` (linha 72-76)
- ✅ Verificar `processing_locks` dictionary

---

## 📚 Documentação Adicional

### **Arquivos de Documentação**
- `docs/MONITORAMENTO_GOOGLE_MAPS.md` - Guia de monitoramento da API
- `docs/CONFIGURAR_ALERTAS_GOOGLE_CLOUD.md` - Configuração de alertas
- `docs/GUIA_RAPIDO_MONITORAMENTO.md` - Guia rápido
- `docs/CONFIGURAR_ALERTAS_EMAIL.md` - **Sistema de alertas por e-mail (NOVO)**

### **Scripts Auxiliares**
- `geocode_unidades.py` - Geocodifica unidades em massa
- `identificar_coordenadas_genericas.py` - Identifica coordenadas genéricas
- `limpar_coordenadas_genericas.py` - Limpa coordenadas genéricas
- `listar_sem_geo.py` - Lista unidades sem geocodificação
- `relatorio_geocodificacao_final.py` - Relatório de geocodificação

-
## 📞 Contatos e Suporte

**Projeto:** Bot Central - Buddha Spa  
**Tecnologia:** FastAPI + Pydantic AI + AWS Bedrock  
**Banco de Dados:** PostgreSQL  
**Deploy:** Docker + Docker Compose  

---

## 🔑 Palavras-Chave para Busca

`bot central`, `buddha spa`, `agente ia`, `pydantic ai`, `aws bedrock`, `claude sonnet`, `fastapi`, `postgresql`, `google maps api`, `geocodificação`, `geolocalização`, `chatbot`, `assistente virtual`, `reagendamento`, `cancelamento`, `unidades spa`, `contato unidades`

---

**Fim do Resumo Completo** ✅
