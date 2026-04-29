# 📚 DOCUMENTAÇÃO COMPLETA - BOT CENTRAL BUDDHA SPA

> **Projeto:** Agente Central de Atendimento  
> **Última Atualização:** 28 de Abril de 2026  
> **Versão:** 2.0 (com Sistema de Dúvidas Gerais)  
> **Autor:** Rafael Nunes

---

## 📑 ÍNDICE

1. [Visão Geral](#-visão-geral)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Componentes Principais](#-componentes-principais)
4. [Agentes de IA](#-agentes-de-ia)
5. [Fluxos de Atendimento](#-fluxos-de-atendimento)
6. [Sistema de Dúvidas Gerais](#-sistema-de-dúvidas-gerais)
7. [Tools (Ferramentas)](#-tools-ferramentas)
8. [Banco de Dados](#-banco-de-dados)
9. [APIs Externas](#-apis-externas)
10. [Deploy e Configuração](#-deploy-e-configuração)
11. [Monitoramento](#-monitoramento)
12. [Troubleshooting](#-troubleshooting)

---

## 🎯 VISÃO GERAL

O **Bot Central** é um agente de IA independente desenvolvido para a Buddha Spa, especializado em:

✅ **Fornecer informações de contato** das unidades  
✅ **Encontrar a unidade mais próxima** usando CEP ou bairro  
✅ **Responder dúvidas gerais** sobre políticas, procedimentos e serviços (FAQ)  
✅ **Direcionar clientes** para reagendamento e cancelamento  
❌ **NÃO faz agendamentos diretos** (direciona para as unidades)

### Principais Características

- **Dois agentes especializados**: Central Agent (geolocalização) + Dúvidas Agent (FAQ)
- **Transições automáticas** entre agentes conforme contexto
- **Geocodificação inteligente** com Google Maps API
- **Sistema anti-loop** para tentativas repetidas de agendamento
- **Persistência de contexto** em PostgreSQL
- **Monitoramento de custos** da API do Google Maps

---

## 🏗️ ARQUITETURA DO SISTEMA

### Stack Tecnológica

```
Backend:          FastAPI (Python 3.10)
IA:               AWS Bedrock (Claude Sonnet 4.5)
Framework IA:     Pydantic AI
Banco de Dados:   PostgreSQL 15
Geocodificação:   Google Maps API (Geocoding + Distance Matrix)
Deploy:           Docker + Docker Compose
Porta:            8001 (configurável via PORT env)
```

### Estrutura de Diretórios

```
agente_central/
├── app.py                          # Servidor FastAPI principal (309 linhas)
├── agents/
│   ├── agent_central.py            # Central Agent + Dúvidas Agent (641 linhas)
│   └── deps.py                     # Contexto/dependências (42 linhas)
├── tools/
│   └── tool_central.py             # Ferramentas do agente (46KB, 1240 linhas)
├── services/
│   ├── google_maps_service.py      # Integração Google Maps (249 linhas)
│   └── users.py                    # Serviços de usuário
├── store/
│   ├── database.py                 # Operações PostgreSQL (213 linhas)
│   └── context.py                  # Gerenciamento de contexto
├── security/
│   └── auth.py                     # Autenticação API Key
├── data/
│   ├── unidades.json               # Base de unidades (153KB)
│   └── google_maps_counter.json    # Contador de requisições API
├── FAQ/
│   ├── faq.json                    # Base de conhecimento (59KB, 765 linhas)
│   ├── converter_correto.py        # Conversor de FAQ
│   └── verify_faq.py               # Validador de FAQ
├── docs/
│   ├── MONITORAMENTO_GOOGLE_MAPS.md
│   ├── CONFIGURAR_ALERTAS_GOOGLE_CLOUD.md
│   └── GUIA_RAPIDO_MONITORAMENTO.md
├── scripts/
│   ├── geocodificar_unidades.py    # Geocodificação em massa
│   ├── monitorar_google_maps.py    # Monitoramento de uso
│   └── consultar_google_cloud_metrics.py
├── db/
│   └── init.sql                    # Schema do banco
├── utils.py                        # Funções utilitárias (294 linhas)
├── docker-compose.yml              # Orquestração de containers
├── Dockerfile                      # Build da aplicação
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de variáveis de ambiente
├── RESUMO_COMPLETO_PROJETO.md      # Resumo do projeto (562 linhas)
└── IMPLEMENTACAO_DUVIDAS_GERAIS.md # Doc de implementação FAQ (404 linhas)
```

---

## 🔑 COMPONENTES PRINCIPAIS

### 1. app.py - Servidor FastAPI

**Porta:** 8001 (configurável via `PORT` env)

#### Endpoints

- `GET /` - Health check
- `POST /chat-central` - Endpoint principal do bot (requer API Key)

#### Características

- ✅ **Proteção contra processamento duplicado** (locks por session_id)
- ✅ **Sessões isoladas** com prefixo `central_`
- ✅ **Detecção de encerramento** via palavras-chave (`sair`, `encerrar`)
- ✅ **Flag `finalizar_sessao`** para integração com React Flow
- ✅ **Recarregamento de contexto** do banco após execução de tools
- ✅ **Middleware CORS** habilitado
- ✅ **Roteamento entre agentes** (central_agent ↔ duvidas_agent)
- ✅ **Transição silenciosa** (emoji 🔄 para reprocessamento automático)
- ✅ **Formatação WhatsApp** (remove `**texto**` e `---`)

#### Fluxo de Requisição

```
1. Recebe mensagem do usuário via POST /chat-central
2. Verifica API Key (security/auth.py)
3. Aplica lock para evitar processamento duplicado
4. Cria/recupera sessão com prefixo "central_"
5. Carrega histórico de mensagens do PostgreSQL
6. Carrega contexto da sessão
7. Determina qual agente usar (central_agent ou duvidas_agent)
8. Executa agente selecionado
9. Detecta transições silenciosas (🔄) e reprocessa se necessário
10. Verifica se sessão foi deletada (encerramento via tool)
11. Salva novas mensagens no banco
12. Recarrega contexto do banco (tools podem ter atualizado)
13. Mescla contexto (deps + banco)
14. Formata resposta para WhatsApp
15. Retorna resposta + flag finalizar_sessao (se aplicável)
16. Remove lock
```

#### Proteção contra Loop Infinito

```python
# Lock para evitar processamento duplicado
processing_locks = {}

if session_id in processing_locks:
    raise HTTPException(status_code=429, detail="Mensagem já está sendo processada")

processing_locks[session_id] = True
```

---

### 2. deps.py - Contexto do Agente

Define a estrutura de dados compartilhada entre agentes e tools:

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
    
    # DÚVIDAS GERAIS
    opcoes_faq: Optional[list] = None
    agente_atual: Optional[str] = None
```

---

## 🤖 AGENTES DE IA

### Central Agent

**Modelo:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (AWS Bedrock)  
**System Prompt:** ~450 linhas  
**Temperature:** Padrão (não configurado)  
**Retries:** 2

#### Responsabilidades

1. **Geolocalização** - Encontrar unidades próximas via CEP/bairro
2. **Informações de contato** - Fornecer dados das unidades
3. **Reagendamento** - Direcionar para unidade específica
4. **Cancelamento** - Direcionar para unidade específica
5. **Transições** - Encaminhar para duvidas_agent quando necessário

#### Tools Disponíveis

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
- `ir_para_duvidas_gerais` - Transição para duvidas_agent
- `registrar_step` - Tracking de navegação
- `registrar_assunto` - Tracking de assuntos

#### Regras Importantes

1. **Terminologia obrigatória:** Sempre usar "terapia" (não "massagem")
2. **Nunca corrigir o cliente:** Aceitar "massagem" mas responder com "terapia"
3. **Encerramento obrigatório:** Sempre chamar `encerrar_atendimento` quando usuário responder "não" a "Posso ajudar em algo mais?"
4. **Prevenção de loop:** Se `tentativas_agendamento >= 2`, mostrar contato e encerrar
5. **Transição silenciosa:** Responder apenas "🔄" ao usar `ir_para_duvidas_gerais` com pergunta direta

---

### Dúvidas Agent

**Modelo:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (AWS Bedrock)  
**System Prompt:** ~160 linhas  
**Temperature:** 0.1 (baixa para respostas precisas)  
**Max Tokens:** 1000  
**Retries:** 2

#### Responsabilidades

1. **Responder dúvidas** usando exclusivamente o FAQ estruturado
2. **Identificar transições** para agendamento/cancelamento/reagendamento
3. **Evitar alucinações** - NUNCA inventar informações

#### Tools Disponíveis

- `buscar_resposta_faq` - Busca resposta no FAQ
- `mostrar_resposta_faq_escolhida` - Mostra resposta da opção escolhida
- `ir_para_agendamento_de_duvidas` - Transição para central_agent (agendamento)
- `ir_para_cancelamento_de_duvidas` - Transição para central_agent (cancelamento)
- `ir_para_reagendamento_de_duvidas` - Transição para central_agent (reagendamento)
- `encerrar_atendimento` - Encerra sessão

#### Regras Anti-Alucinação

1. **Fonte única:** APENAS `buscar_resposta_faq` como fonte de informação
2. **Obrigatoriedade:** SEMPRE chamar a tool antes de responder
3. **Independência:** Cada pergunta é tratada como NOVA e INDEPENDENTE
4. **Sem complemento:** NUNCA adicionar informações além do que a tool retornou
5. **Sem invenção:** Se a tool não encontrar, admitir que não sabe
6. **Formatação restrita:** 
   - ✅ Usar `*texto*` (1 asterisco)
   - ❌ PROIBIDO `**texto**` (2 asteriscos)
   - ❌ PROIBIDO `---` (separadores)

---

## 🔄 FLUXOS DE ATENDIMENTO

### 1. Fluxo de Agendamento

```
USUÁRIO: "Quero agendar uma terapia"
   ↓
CENTRAL_AGENT: incrementar_tentativas_agendamento()
   ↓
CENTRAL_AGENT: "Me informe seu CEP ou bairro para encontrar a unidade mais próxima 📍"
   ↓
USUÁRIO: "01310-100"
   ↓
CENTRAL_AGENT: buscar_endereco_por_cep("01310-100")
   ↓
TOOL: "VALIDO|São Paulo|SP|Bela Vista"
   ↓
CENTRAL_AGENT: encontrar_unidades_no_raio()
   ↓
TOOL: "UNICA|Buddha Spa - Av. Paulista|..."
   ↓
CENTRAL_AGENT: Mostra dados da unidade
   ↓
CENTRAL_AGENT: "Deseja consultar outra unidade?"
   ↓
USUÁRIO: "Não"
   ↓
CENTRAL_AGENT: "Posso ajudar em algo mais?"
   ↓
USUÁRIO: "Não, obrigado"
   ↓
CENTRAL_AGENT: encerrar_atendimento("usuario_nao_precisa")
   ↓
RESPOSTA: {response: "...", finalizar_sessao: true}
```

### 2. Fluxo de Reagendamento (Informações)

```
USUÁRIO: "Quero reagendar"
   ↓
CENTRAL_AGENT: "Você deseja receber informações sobre como reagendar ou quer realizar um reagendamento?"
   ↓
USUÁRIO: "Quero informações"
   ↓
CENTRAL_AGENT: ir_para_duvidas_gerais()
   ↓
CENTRAL_AGENT: Atualiza contexto → agente_atual = "duvidas_agent"
   ↓
CENTRAL_AGENT: Responde "🔄" (transição silenciosa)
   ↓
APP.PY: Detecta transição silenciosa
   ↓
APP.PY: Reprocessa mensagem com duvidas_agent
   ↓
DUVIDAS_AGENT: buscar_resposta_faq("reagendamento")
   ↓
DUVIDAS_AGENT: Retorna resposta do FAQ
   ↓
DUVIDAS_AGENT: "Posso ajudar com mais alguma coisa? 😊"
```

### 3. Fluxo de Dúvidas Gerais

```
USUÁRIO: "Qual o prazo para devolução?"
   ↓
DUVIDAS_AGENT: buscar_resposta_faq("Qual o prazo para devolução?")
   ↓
TOOL: Busca no FAQ com similaridade de texto
   ↓
TOOL: "RESPOSTA_ENCONTRADA|O prazo é de 7 dias corridos..."
   ↓
DUVIDAS_AGENT: Mostra resposta
   ↓
DUVIDAS_AGENT: "Consegui esclarecer sua dúvida? Posso te ajudar com mais alguma coisa? 😊"
   ↓
USUÁRIO: "Quero agendar"
   ↓
DUVIDAS_AGENT: ir_para_agendamento_de_duvidas()
   ↓
DUVIDAS_AGENT: Atualiza contexto → agente_atual = "central_agent", intencao = "agendamento"
   ↓
PRÓXIMA MENSAGEM: Roteada para CENTRAL_AGENT
   ↓
CENTRAL_AGENT: Inicia fluxo de agendamento
```

### 4. Fluxo de Múltiplas Opções FAQ

```
USUÁRIO: "Como funciona a troca?"
   ↓
DUVIDAS_AGENT: buscar_resposta_faq("Como funciona a troca?")
   ↓
TOOL: Encontra 3 opções similares
   ↓
TOOL: "MULTIPLAS_OPCOES|1. Troca de produtos|2. Troca de vouchers|3. Troca de serviços"
   ↓
DUVIDAS_AGENT: "🔍 Encontrei algumas opções relacionadas à sua pergunta:
   
   1. Troca de produtos físicos
   2. Troca ou devolução de vouchers
   3. Troca de serviços agendados
   
   Qual delas responde melhor sua dúvida? Digite o número. 😊"
   ↓
USUÁRIO: "2"
   ↓
DUVIDAS_AGENT: mostrar_resposta_faq_escolhida(2)
   ↓
TOOL: Retorna resposta completa da opção 2
   ↓
DUVIDAS_AGENT: Mostra resposta com contatos
```

---

## 🛠️ TOOLS (FERRAMENTAS)

### Geolocalização

#### `buscar_endereco_por_cep(cep: str)`

Geocodifica CEP usando Google Maps Geocoding API.

**Entrada:** CEP (com ou sem formatação)  
**Saída:** `"VALIDO|cidade|estado|bairro"` ou `"INVALIDO|erro"`  
**Efeitos colaterais:** Atualiza `latitude_usuario`, `longitude_usuario`, `cidade_informada`, `estado_informado`, `bairro_informado` no contexto

**Exemplo:**
```python
# Input: "01310-100"
# Output: "VALIDO|São Paulo|SP|Bela Vista"
# Contexto atualizado:
#   latitude_usuario: -23.5505
#   longitude_usuario: -46.6333
#   cidade_informada: "São Paulo"
#   estado_informado: "SP"
#   bairro_informado: "Bela Vista"
```

#### `encontrar_unidades_no_raio(raio_km: int = 50)`

Busca unidades em um raio a partir das coordenadas do usuário.

**Entrada:** Raio em km (padrão: 50)  
**Saída:** 
- `"UNICA|nome|endereco|telefone|whatsapp|email|horario|link_maps"`
- `"MULTIPLAS|nome1|nome2|nome3..."`
- `"NAO_ENCONTRADO"`

**Efeitos colaterais:** Atualiza `unidade_encontrada` ou `unidades_multiplas` no contexto

#### `encontrar_unidade_mais_proxima()`

Busca a unidade mais próxima (usado após seleção de bairro).

**Saída:** `"ENCONTRADA|nome|endereco|telefone|whatsapp|email|horario|link_maps"`

#### `buscar_bairros_por_nome(nome_bairro: str)`

Busca bairros por nome no arquivo de unidades.

**Saída:**
- `"UNICO|cidade|estado"`
- `"MULTIPLOS|1. Bairro - Cidade, Estado|2. ..."`
- `"NAO_ENCONTRADO"`

#### `buscar_unidade_por_nome(nome_unidade: str)`

Busca fuzzy por nome/cidade/bairro. Suporta seleção numérica.

**Saída:**
- `"ENCONTRADA|nome|endereco|bairro|cidade|uf|cep|telefone|celular|email"`
- `"MULTIPLAS|1. Nome - Bairro, Cidade|2. ..."`
- `"NAO_ENCONTRADA"`

#### `obter_info_unidade(input_usuario: str)`

Usado quando há múltiplas unidades. Aceita número ou nome.

**Saída:**
- `"ENCONTRADA|nome|endereco|telefone|whatsapp|email|horario|link_maps"`
- `"NAO_ENCONTRADA"`

#### `listar_todas_unidades()`

Lista todas as unidades disponíveis.

**Saída:** Link para página de unidades

---

### FAQ (Dúvidas Gerais)

#### `buscar_resposta_faq(pergunta_usuario: str)`

Busca resposta no FAQ usando similaridade de texto.

**Algoritmo:**
1. Normaliza texto (remove acentos, lowercase)
2. Calcula similaridade com SequenceMatcher (70%) + palavras comuns (30%)
3. Score mínimo: 0.3
4. Retorna resposta única ou múltiplas opções

**Saída:**
- `"RESPOSTA_ENCONTRADA|[resposta completa]"`
- `"MULTIPLAS_OPCOES|[lista numerada]"`
- `"NAO_ENCONTRADO|Não encontrei uma resposta..."`

**Efeitos colaterais:** Se múltiplas opções, atualiza `opcoes_faq` no contexto

#### `mostrar_resposta_faq_escolhida(numero_opcao: int)`

Mostra resposta da opção escolhida pelo usuário.

**Entrada:** Número da opção (1, 2, 3...)  
**Saída:** `"RESPOSTA|[resposta completa]"`  
**Efeitos colaterais:** Limpa `opcoes_faq` do contexto

---

### Transições

#### `ir_para_duvidas_gerais()`

Marca transição de central_agent para duvidas_agent.

**Efeitos colaterais:** 
- `agente_atual = "duvidas_agent"`
- `intencao = "duvidas_gerais"`

#### `ir_para_agendamento_de_duvidas()`

Marca transição de duvidas_agent para central_agent (agendamento).

**Efeitos colaterais:**
- `agente_atual = "central_agent"`
- `intencao = "agendamento"`

#### `ir_para_cancelamento_de_duvidas()`

Marca transição de duvidas_agent para central_agent (cancelamento).

**Efeitos colaterais:**
- `agente_atual = "central_agent"`
- `intencao = "cancelamento"`

#### `ir_para_reagendamento_de_duvidas()`

Marca transição de duvidas_agent para central_agent (reagendamento).

**Efeitos colaterais:**
- `agente_atual = "central_agent"`
- `intencao = "reagendamento"`

---

### Controle

#### `incrementar_tentativas_agendamento()`

Incrementa contador para evitar loop infinito.

**Efeitos colaterais:** `tentativas_agendamento += 1`

#### `marcar_contexto_cancelamento()`

Marca contexto de cancelamento.

**Efeitos colaterais:** `contexto_cancelamento = True`

#### `encerrar_atendimento(motivo: str = "usuario_nao_precisa")`

Deleta sessão do banco e retorna mensagem de despedida.

**Entrada:** Motivo do encerramento  
**Saída:** Mensagem de despedida  
**Efeitos colaterais:** Deleta sessão e mensagens do PostgreSQL

---

### Tracking

#### `registrar_step(step: str)`

Registra step de navegação no histórico.

**Entrada:** Nome do step (ex: "Solicitação de CEP ou bairro")  
**Efeitos colaterais:** Adiciona step ao array `steps`

#### `registrar_assunto(assunto: str)`

Registra assunto/tema da conversa.

**Entrada:** Assunto (ex: "contato unidade")  
**Efeitos colaterais:** Adiciona assunto ao array `assuntos`

---

## 💾 BANCO DE DADOS

### PostgreSQL 15

**Host:** `postgres_central` (Docker) ou `localhost` (local)  
**Porta:** 5432 (interna) / 5434 (externa)  
**Database:** `bot_central`  
**User:** `postgres`  
**Password:** Configurável via `.env`

### Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    current_agent TEXT,
    context JSONB,
    last_updated TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    message JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Funções Principais

#### `ensure_session(session_id: str)`

Cria sessão se não existe.

```python
# Insere com current_agent = "central_agent" e context = {}
INSERT INTO sessions (session_id, current_agent, context, last_updated)
VALUES (%s, %s, %s::jsonb, NOW())
ON CONFLICT (session_id) DO NOTHING
```

#### `get_session(session_id: str)`

Recupera sessão.

**Retorno:** `(session_id, current_agent, context, last_updated)` ou `None`

#### `add_messages(session_id: str, new_msgs: list)`

Salva mensagens no banco.

**Otimizações:**
- Remove campo `instructions` antes de salvar (gerado dinamicamente)
- Filtra mensagens inválidas/vazias
- Validação com `ModelMessagesTypeAdapter`

#### `get_messages(session_id: str)`

Carrega histórico de mensagens.

**Retorno:** Lista de `ModelMessage` (pydantic_ai)

**Otimizações:**
- Filtra mensagens sem `parts` ou com `parts` vazio
- Tenta validar e remove mensagens inválidas se necessário

#### `update_context(session_id: str, data: dict)`

Atualiza contexto da sessão (merge com contexto existente).

```python
UPDATE sessions
SET context = COALESCE(context, '{}'::jsonb) || %s::jsonb,
    last_updated = NOW()
WHERE session_id = %s
```

#### `delete_session(session_id: str)`

Deleta sessão e mensagens.

```python
DELETE FROM messages WHERE session_id=%s
DELETE FROM sessions WHERE session_id=%s
```

#### `cleanup_sessions(ttl_days: int = 7)`

Remove sessões antigas (executado em background).

**Critério:** `last_updated < NOW() - ttl_days`

---

## 🌐 APIS EXTERNAS

### Google Maps API

**Chave:** `GOOGLE_MAPS_API_KEY` (env)  
**Região:** Global  
**Monitoramento:** `data/google_maps_counter.json`

#### Geocoding API

**Uso:** Converte CEP em coordenadas + endereço completo

**Cota Gratuita:** 10.000 requisições/mês  
**Custo após cota:**
- 10k-100k: $5 por 1.000 requisições
- 100k-500k: $4 por 1.000 requisições

**Alertas:**
- 50% da cota (5.000 req): ⚠️ Alerta
- 100% da cota (10.000 req): 🚨 Cota excedida

#### Distance Matrix API

**Uso:** Calcula distância real de trajeto (opcional, não usado atualmente)

**Custo:** PAGO desde a 1ª requisição
- Até 100k: $5 por 1.000 requisições
- 100k-500k: $4 por 1.000 requisições

**Alerta:** 5.000 requisições

#### Monitoramento

```python
# Contador automático com reset mensal
{
  "geocoding": {
    "total": 1234,
    "mes_atual": 567,
    "ultimo_reset": "2026-04-01"
  },
  "distance_matrix": {
    "total": 0,
    "mes_atual": 0,
    "ultimo_reset": "2026-04-01"
  }
}
```

**Logs:**
```
📊 Google Maps geocoding: 567 requisições este mês (total: 1234)
🚨 ALERTA: VOCÊ ATINGIU 50% DA COTA GRATUITA!
```

---

### AWS Bedrock

**Modelo:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0`  
**Região:** `us-east-1` (configurável)  
**Credenciais:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

**Configuração:**
```python
from pydantic_ai.models.bedrock import BedrockConverseModel

model = BedrockConverseModel('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
```

---

### API de Franqueadas (Opcional)

**URL:** `https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/franqueadas`  
**Token:** `PRD_LABELLE_TOKEN` (env)  
**Uso:** Sincronização automática de unidades (se configurado)

**Comportamento:**
- Se token não configurado: Usa `data/unidades.json` local
- Se API falhar: Fallback para dados locais
- Sincronização: Compara apenas campos de endereço (ignora lat/lng)

---

## 🚀 DEPLOY E CONFIGURAÇÃO

### Variáveis de Ambiente (.env)

```bash
# AWS CREDENTIALS (para AWS Bedrock - Claude)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=sua_access_key_aqui
AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui

# Google Maps API Key
GOOGLE_MAPS_API_KEY=sua_chave_google_maps_aqui

# BANCO DE DADOS POSTGRESQL
DB_HOST=postgres_central  # Para Docker
DB_PORT=5432
DB_NAME=bot_central
DB_USER=postgres
DB_PASSWORD=postgres

# API
PORT=8001
API_KEY=seu_api_key_secreto_aqui

# AMBIENTE
ENV=dev

# OPCIONAL: API de Franqueadas
PRD_LABELLE_TOKEN=seu_token_aqui
```

### Docker Compose

```bash
# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f app_central

# Rebuild
docker-compose up -d --build

# Parar serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

### Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env com suas credenciais

# Executar
python app.py

# Ou com uvicorn
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### Estrutura Docker

**Serviços:**
- `app_central` - Aplicação FastAPI (porta 8001)
- `postgres_central` - PostgreSQL 15 (porta 5434)

**Volumes:**
- `postgres_central_data` - Persistência do banco

**Network:**
- `central_network` - Rede bridge interna

---

## 📊 MONITORAMENTO

### Google Maps API

**Arquivo:** `data/google_maps_counter.json`

**Comandos:**
```bash
# Monitorar uso
python scripts/monitorar_google_maps.py

# Consultar métricas no Google Cloud
python scripts/consultar_google_cloud_metrics.py
```

**Documentação:**
- `docs/MONITORAMENTO_GOOGLE_MAPS.md` - Guia completo
- `docs/CONFIGURAR_ALERTAS_GOOGLE_CLOUD.md` - Configuração de alertas
- `docs/GUIA_RAPIDO_MONITORAMENTO.md` - Guia rápido

### Logs do Sistema

```
================================================================================
🏢 BOT CENTRAL - NOVA MENSAGEM
Session ID: central_abc123
Mensagem: quero agendar
================================================================================
🤖 Current Agent: central_agent
📊 Histórico: 0 mensagens
🔍 Google Geocoding: Buscando CEP 01234-567
✅ CEP encontrado: São Paulo/SP - Bairro: Centro
📍 Coordenadas: -23.5505, -46.6333
📊 Google Maps geocoding: 567 requisições este mês (total: 1234)
📍 STEP REGISTRADO: Solicitação de CEP ou bairro
🗺️ Histórico: Solicitação de CEP ou bairro
================================================================================
✅ BOT CENTRAL - RESPOSTA:
Encontrei a unidade mais próxima de você. 😊
...
================================================================================
```

### Tracking de Navegação

**Steps registrados:**
- "Solicitação de CEP ou bairro"
- "Não encontrou unidade CEP"
- "Encontrou unidade bairro"
- "Reagendamento"
- "Cancelamento"
- "Coletar unidade"

**Assuntos registrados:**
- "Encontrou unidade"
- "Encontrou mais de uma unidade CEP"
- "Informações da unidade CEP"
- "Consultar outras unidades CEP"
- "contato unidade"

---

## 🔧 TROUBLESHOOTING

### Problemas Comuns

#### 1. Sessão não encerra

**Sintomas:** Usuário diz "não" mas conversa continua

**Diagnóstico:**
- ✅ Verificar se `encerrar_atendimento()` foi chamada
- ✅ Verificar logs: `🔴 FINALIZAR_SESSAO`
- ✅ Verificar flag `finalizar_sessao: true` na resposta

**Solução:**
- Revisar system prompt do agente
- Verificar palavras de encerramento no código
- Testar com diferentes variações de "não"

#### 2. Contexto não persiste

**Sintomas:** Agente "esquece" informações entre mensagens

**Diagnóstico:**
- ✅ Verificar `update_context()` nas tools
- ✅ Verificar recarregamento do contexto em `app.py` (linha 236)
- ✅ Verificar merge de contexto (linhas 252-272)

**Solução:**
- Adicionar logs em `update_context()`
- Verificar se tool está salvando no banco
- Verificar se app.py está recarregando após agent.run()

#### 3. Google Maps quota excedida

**Sintomas:** Erro ao geocodificar CEP

**Diagnóstico:**
- ✅ Verificar `data/google_maps_counter.json`
- ✅ Verificar logs de alerta
- ✅ Consultar Google Cloud Console

**Solução:**
- Otimizar buscas (cache, raio menor)
- Aumentar cota (pago)
- Usar API alternativa (LocationIQ, OpenCage)

#### 4. Mensagens duplicadas

**Sintomas:** Mesma mensagem processada múltiplas vezes

**Diagnóstico:**
- ✅ Verificar lock em `app.py` (linha 88-92)
- ✅ Verificar `processing_locks` dictionary
- ✅ Verificar logs: `⚠️ BLOQUEADO`

**Solução:**
- Verificar se lock está sendo removido no `finally`
- Aumentar timeout do cliente
- Verificar se React Flow está reenviando

#### 5. Agente não usa tool correta

**Sintomas:** Agente inventa resposta ao invés de chamar tool

**Diagnóstico:**
- ✅ Verificar system prompt (instruções claras?)
- ✅ Verificar temperature (muito alta?)
- ✅ Verificar logs de execução de tools

**Solução:**
- Tornar instruções mais imperativas
- Reduzir temperature (0.0 - 0.3)
- Adicionar exemplos no system prompt

#### 6. Transição entre agentes não funciona

**Sintomas:** Agente não muda de central para dúvidas ou vice-versa

**Diagnóstico:**
- ✅ Verificar `agente_atual` no contexto
- ✅ Verificar logs: `🤖 Current Agent`
- ✅ Verificar se tool de transição foi chamada
- ✅ Verificar detecção de transição silenciosa (🔄)

**Solução:**
- Verificar `update_context()` nas tools de transição
- Verificar lógica de roteamento em `app.py` (linhas 146-149)
- Verificar detecção de emoji 🔄 (linhas 182-209)

#### 7. FAQ não encontra resposta

**Sintomas:** Dúvidas agent diz "não encontrei" para perguntas que existem no FAQ

**Diagnóstico:**
- ✅ Verificar `FAQ/faq.json` (pergunta existe?)
- ✅ Verificar keywords da pergunta
- ✅ Verificar score de similaridade (mínimo: 0.3)
- ✅ Verificar normalização de texto

**Solução:**
- Adicionar keywords relevantes no FAQ
- Ajustar score mínimo (linha da tool)
- Melhorar algoritmo de similaridade
- Adicionar sinônimos no FAQ

#### 8. Formatação incorreta no WhatsApp

**Sintomas:** `**texto**` ou `---` aparecem no WhatsApp

**Diagnóstico:**
- ✅ Verificar função `format_whatsapp()` em `app.py`
- ✅ Verificar system prompt do duvidas_agent (regras de formatação)

**Solução:**
- Aplicar `format_whatsapp()` na resposta final
- Reforçar regras no system prompt
- Testar com diferentes formatações

---

## 📚 DOCUMENTAÇÃO ADICIONAL

### Arquivos de Referência

- `RESUMO_COMPLETO_PROJETO.md` - Resumo executivo (562 linhas)
- `IMPLEMENTACAO_DUVIDAS_GERAIS.md` - Implementação do FAQ (404 linhas)
- `docs/MONITORAMENTO_GOOGLE_MAPS.md` - Monitoramento da API
- `docs/CONFIGURAR_ALERTAS_GOOGLE_CLOUD.md` - Configuração de alertas
- `docs/GUIA_RAPIDO_MONITORAMENTO.md` - Guia rápido

### Scripts Auxiliares

- `geocode_unidades.py` - Geocodifica unidades em massa
- `identificar_coordenadas_genericas.py` - Identifica coordenadas genéricas
- `limpar_coordenadas_genericas.py` - Limpa coordenadas genéricas
- `listar_sem_geo.py` - Lista unidades sem geocodificação
- `relatorio_geocodificacao_final.py` - Relatório de geocodificação
- `monitorar_google_maps.py` - Monitoramento de uso da API
- `consultar_google_cloud_metrics.py` - Consulta métricas no Google Cloud

---

## 🎯 PRÓXIMAS MELHORIAS

### Sistema de Dúvidas Gerais

- [ ] Cache de respostas frequentes
- [ ] Analytics de perguntas mais comuns
- [ ] Feedback do usuário sobre qualidade da resposta
- [ ] Sugestões de perguntas relacionadas
- [ ] Integração com base de conhecimento externa

### Geolocalização

- [ ] Cache de geocodificação de CEPs
- [ ] Suporte a localização via GPS (latitude/longitude)
- [ ] Cálculo de distância real (Distance Matrix API)
- [ ] Ordenação por distância real ao invés de euclidiana

### Monitoramento

- [ ] Dashboard de métricas em tempo real
- [ ] Alertas via email/SMS quando quota atingir limite
- [ ] Relatórios automáticos mensais
- [ ] Tracking de conversões (agendamentos realizados)

### Performance

- [ ] Cache de sessões em Redis
- [ ] Compressão de mensagens antigas
- [ ] Otimização de queries do PostgreSQL
- [ ] Load balancing com múltiplos workers

---

## 📞 CONTATOS E SUPORTE

**Projeto:** Bot Central - Buddha Spa  
**Tecnologia:** FastAPI + Pydantic AI + AWS Bedrock  
**Banco de Dados:** PostgreSQL  
**Deploy:** Docker + Docker Compose  
**Autor:** Rafael Nunes  
**Data:** Abril de 2026

---

## 🔑 PALAVRAS-CHAVE

`bot central`, `buddha spa`, `agente ia`, `pydantic ai`, `aws bedrock`, `claude sonnet`, `fastapi`, `postgresql`, `google maps api`, `geocodificação`, `geolocalização`, `chatbot`, `assistente virtual`, `reagendamento`, `cancelamento`, `unidades spa`, `contato unidades`, `faq`, `dúvidas gerais`, `sistema de perguntas`, `multi-agente`

---

**Fim da Documentação Completa** ✅
