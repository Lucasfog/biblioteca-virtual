# Biblioteca Virtual API

> **API REST profissional para gerenciamento de biblioteca digital** com FastAPI, SQLAlchemy 2.0, PostgreSQL e Redis. Arquitetura em camadas (DDD Light + Service Layer) com foco em qualidade de produção.

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)

---

## Índice

1. [Visão Geral](#-visão-geral)
2. [Instalação e Execução](#-instalação-e-execução)
3. [Autenticação no Swagger](#-autenticação-no-swagger)
4. [Rotas Disponíveis](#-rotas-disponíveis)
5. [Payloads e Exemplos](#-payloads-e-exemplos)
6. [Usando cURL](#-usando-curl)
7. [Arquitetura e Decisões Técnicas](#-arquitetura-e-decisões-técnicas)
8. [Estrutura do Projeto](#-estrutura-do-projeto)

---

## Visão Geral

A **Biblioteca Virtual API** é um sistema robusto para gerenciar empréstimos, devoluções e cadastro de livros. 

**Principais funcionalidades:**
- Autenticação via JWT com middleware global
- CRUD de usuários, livros, autores e empréstimos
- Controle de cópias disponíveis e multa por atraso
- Cache Redis para endpoints paginados
- Rate limiting automático
- Logging estruturado em JSON
- Métricas Prometheus prontas para Grafana
- Health check integrado

---

## Instalação e Execução

### Opção 1: Com Docker (Recomendado)

A forma mais rápida de executar a aplicação com todas as dependências:

```bash
# 1. Clonar o repositório
git clone <seu-repositorio>
cd biblioteca-virtual

# 2. Copiar arquivo de configuração (opcional)
cp .env.example .env

# 3. Executar com Docker Compose
docker compose up --build
```

A API estará disponível em **http://localhost:8000**  
Documentação Swagger em **http://localhost:8000/docs**  
Documentação ReDoc em **http://localhost:8000/redoc**

---

### Opção 2: Instalação Local com `uv`

Para desenvolvedores que preferem executar localmente:

#### Pré-requisitos
- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- `uv` instalado ([Documentação](https://docs.astral.sh/uv/))

#### 2.1 Instalar Dependências
```bash
# Instalar uv (se não estiver instalado)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Criar ambiente virtual e instalar dependências
uv sync --all-groups
```

#### 2.2 Configurar Variáveis de Ambiente
```bash
cp .env.example .env
```

Edite `.env` com suas credenciais:
```env
DATABASE_URL=postgresql+asyncpg://postgres:seu_password@localhost:5432/biblioteca
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=info
```

#### 2.3 Executar Migrações do Banco
```bash
uv run alembic upgrade head
```

#### 2.4 Executar a Aplicação
```bash
# Modo desenvolvimento com hot-reload
uv run uvicorn biblioteca_virtual.main:app --reload

# Modo produção
uv run uvicorn biblioteca_virtual.main:app --host 0.0.0.0 --port 8000
```

A aplicação estará em **http://localhost:8000**

---

#### 2.5 Executar Testes
```bash
# Executar todos os testes
uv run pytest

# Com cobertura de código
uv run pytest --cov=src/biblioteca_virtual

# Modo verboso
uv run pytest -v
```

#### 2.6 Popular Banco com Dados Iniciais (Seed)
```bash
uv run python scripts/seed.py
```

Isso criará usuários e livros de exemplo para testes.

---

#### 2.7 Construir para Produção
```bash
# Você pode use uv para preparar o ambiente
uv build

# Ou use pip normalmente com o ambiente virtual do uv
uv pip install -e .
```

---

## Autenticação no Swagger

### Passo a Passo para Autenticar

1. **Abra o Swagger UI**
   - Acesse: http://localhost:8000/docs

2. **Localize a rota `/api/v1/auth/token`**
   - Role até a seção **Auth**
   - Encontre o endpoint **POST /api/v1/auth/token**

3. **Clique em "Try it out"**
   - O formulário abrirá para você inserir credenciais

4. **Insira as Credenciais de Login**
   
   Use as credenciais abaixo (do seed.py):

   ```json
   {
     "username": "admin@example.com",
     "password": "123456"
   }
   ```

5. **Clique em "Execute"**
   - A resposta conterá o `access_token`
   
   Exemplo de resposta:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

6. **Copie o Token**
   - Selecione todo o valor do `access_token` (sem as aspas)

7. **Configure a Autorização Global**
   - Clique no botão verde **"Authorize"** no canto superior direito
   - Cola o token na caixa: `Bearer seu_token_aqui`
   - Clique em **"Authorize"**
   - Clique em **"Close"** para fechar o diálogo

8. **Teste uma Rota Protegida**
   - Clique em **GET /api/v1/users**
   - Clique em **"Try it out"**
   - Clique em **"Execute"**
   - Você verá a lista de usuários autenticado

### Credenciais de Teste

| Email | Senha | Perfil |
|-------|-------|--------|
| `admin@example.com` | `123456` | Admin |
| `user@example.com` | `123456` | Usuário Comum |

---

## Rotas Disponíveis

### Visão Geral das APIs

| Método | Rota | Descrição | Autenticação | Paginado |
|--------|------|-----------|--------------|----------|
| **POST** | `/api/v1/auth/token` | Fazer login e obter token JWT | ❌ | ❌ |
| **POST** | `/api/v1/users` | Criar novo usuário | ❌ | ❌ |
| **GET** | `/api/v1/users` | Listar usuários | - | - |
| **GET** | `/api/v1/users/{user_id}` | Obter detalhes de usuário | - | ❌ |
| **GET** | `/api/v1/users/{user_id}/loans` | Listar empréstimos do usuário | - | - |
| **POST** | `/api/v1/books` | Criar novo livro | - | ❌ |
| **GET** | `/api/v1/books` | Listar livros | - | - |
| **GET** | `/api/v1/books/{book_id}` | Obter detalhes do livro | - | ❌ |
| **GET** | `/api/v1/books/{book_id}/availability` | Verificar disponibilidade | - | ❌ |
| **POST** | `/api/v1/loans` | Realizar empréstimo | - | ❌ |
| **POST** | `/api/v1/loans/{loan_id}/return` | Devolver livro | - | ❌ |
| **GET** | `/api/v1/loans/active` | Listar empréstimos ativos | - | - |
| **GET** | `/api/v1/loans/{loan_id}` | Obter detalhes do empréstimo | - | ❌ |

---

## Payloads e Exemplos

### 1. Autenticação

#### Fazer Login
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=123456
```

**Resposta (200)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 2. Usuários

#### Criar Usuário
```http
POST /api/v1/users
Content-Type: application/json

{
  "email": "joao.silva@example.com",
  "password": "SenhaSegura123!",
  "full_name": "João Silva"
}
```

**Resposta (201)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "joao.silva@example.com",
  "full_name": "João Silva",
  "is_active": true,
  "created_at": "2024-04-29T10:30:00Z"
}
```

#### Listar Usuários
```http
GET /api/v1/users?offset=0&limit=10
Authorization: Bearer {seu_token}
```

**Resposta (200)**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@example.com",
      "full_name": "Admin User",
      "is_active": true,
      "created_at": "2024-04-29T10:00:00Z"
    }
  ],
  "total": 5,
  "offset": 0,
  "limit": 10
}
```

#### Obter Usuário Específico
```http
GET /api/v1/users/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {seu_token}
```

---

### 3. Livros

#### Criar Livro
```http
POST /api/v1/books
Content-Type: application/json
Authorization: Bearer {seu_token}

{
  "title": "Clean Code",
  "author_name": "Robert C. Martin",
  "isbn": "978-0132350884",
  "total_copies": 5
}
```

**Resposta (201)**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "title": "Clean Code",
  "author": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "Robert C. Martin"
  },
  "isbn": "978-0132350884",
  "total_copies": 5,
  "available_copies": 5,
  "created_at": "2024-04-29T10:30:00Z"
}
```

#### Listar Livros
```http
GET /api/v1/books?offset=0&limit=10
Authorization: Bearer {seu_token}
```

#### Verificar Disponibilidade
```http
GET /api/v1/books/660e8400-e29b-41d4-a716-446655440000/availability
Authorization: Bearer {seu_token}
```

**Resposta (200)**
```json
{
  "book_id": "660e8400-e29b-41d4-a716-446655440000",
  "available": true,
  "available_copies": 5,
  "total_copies": 5
}
```

---

### 4. Empréstimos

#### Realizar Empréstimo
```http
POST /api/v1/loans
Content-Type: application/json
Authorization: Bearer {seu_token}

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "book_id": "660e8400-e29b-41d4-a716-446655440000",
  "due_date": "2024-05-29"
}
```

**Resposta (201)**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "book_id": "660e8400-e29b-41d4-a716-446655440000",
  "borrowed_at": "2024-04-29T10:30:00Z",
  "due_date": "2024-05-29",
  "returned_at": null,
  "status": "active",
  "fine_cents": 0
}
```

#### Devolver Livro
```http
POST /api/v1/loans/880e8400-e29b-41d4-a716-446655440000/return
Authorization: Bearer {seu_token}
```

**Resposta (200)**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "book_id": "660e8400-e29b-41d4-a716-446655440000",
  "borrowed_at": "2024-04-29T10:30:00Z",
  "due_date": "2024-05-29",
  "returned_at": "2024-04-30T14:15:00Z",
  "status": "returned",
  "fine_cents": 0
}
```

#### Listar Empréstimos Ativos
```http
GET /api/v1/loans/active?offset=0&limit=10
Authorization: Bearer {seu_token}
```

---

## Usando cURL

Exemplos práticos para consumir a API via linha de comando.

### 1. Fazer Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=123456"
```

**Salvar o token em uma variável:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=123456" | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

### 2. Criar Usuário (sem autenticação)
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novo@example.com",
    "password": "Senha123!",
    "full_name": "Novo Usuário"
  }'
```

---

### 3. Listar Usuários (com autenticação)
```bash
TOKEN="seu_token_aqui"

curl -X GET "http://localhost:8000/api/v1/users?offset=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4. Criar Livro
```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Design Patterns",
    "author_name": "Gang of Four",
    "isbn": "978-0201633610",
    "total_copies": 3
  }'
```

---

### 5. Listar Livros com Paginação
```bash
TOKEN="seu_token_aqui"

curl -X GET "http://localhost:8000/api/v1/books?offset=0&limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

### 6. Verificar Disponibilidade de Livro
```bash
TOKEN="seu_token_aqui"
BOOK_ID="seu_book_id"

curl -X GET "http://localhost:8000/api/v1/books/$BOOK_ID/availability" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 7. Realizar Empréstimo
```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:8000/api/v1/loans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "book_id": "660e8400-e29b-41d4-a716-446655440000",
    "due_date": "2024-05-29"
  }'
```

---

### 8. Devolver Livro
```bash
TOKEN="seu_token_aqui"
LOAN_ID="seu_loan_id"

curl -X POST "http://localhost:8000/api/v1/loans/$LOAN_ID/return" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 9. Listar Empréstimos Ativos
```bash
TOKEN="seu_token_aqui"

curl -X GET "http://localhost:8000/api/v1/loans/active?offset=0&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## Arquitetura e Decisões Técnicas

### Arquitetura em Camadas

A aplicação segue o padrão **DDD Light + Service Layer**:

```
┌─────────────────────────────────────────┐
│ API Layer (FastAPI Router + Schemas)    │ ← Contratos HTTP
├─────────────────────────────────────────┤
│ Service Layer (Regras de Negócio)       │ ← Orquestração
├─────────────────────────────────────────┤
│ Repository Layer (Acesso a Dados)       │ ← Isolamento por Agregado
├─────────────────────────────────────────┤
│ Core/Shared (Config, Cache, Logging)    │ ← Infraestrutura
└─────────────────────────────────────────┘
```

**Benefícios:**
- Fácil de testar (mocks em cada camada)
- Mudanças no BD não afetam a API
- Regras de negócio centralizadas
- Código organizado e manutenível

---

### Modelo de Banco de Dados

| Tabela | Descrição |
|--------|-----------|
| **users** | Dados de usuários e autenticação |
| **authors** | Autores únicos de livros |
| **books** | Catálogo de livros com controle de cópias |
| **loans** | Histórico de empréstimos e devoluções |

**Regras de Integridade:**
- Cópias disponíveis: `0 <= available_copies <= total_copies`
- Índices em: email, isbn, author_id, loan_status para otimização

---

### Escolhas Tecnológicas

| Tecnologia | Motivo |
|-----------|--------|
| **FastAPI** | Performance, docs automáticas, validação built-in |
| **SQLAlchemy 2.0 async** | Não-bloqueante, tipado, moderno |
| **Pydantic v2** | Validação rigorosa, serialização eficiente |
| **Redis** | Cache de leitura, rate limiting distribuído |
| **Python-Jose (JWT)** | Padrão de autenticação stateless |
| **Structlog** | Logging estruturado em JSON |
| **Prometheus** | Métricas prontas para observabilidade |

---

### Rate Limiting e Cache

- **Rate Limit:** 10-60 requisições por minuto (cofigurável por rota)
- **Cache:** Endpoints GET paginados com TTL automático (via Redis)
- **Invalidação:** Automática em CREATE/UPDATE/DELETE

---

### Fluxo Crítico: Empréstimo de Livro

O fluxo de empréstimo envolve a API recebendo a requisição, validando as regras de negócio e disponibilidade de cópias no Service Layer, realizando a persistência no banco de dados através do Repository, invalidando o cache no Redis e retornando a resposta.

---

## Estrutura do Projeto

```
biblioteca-virtual/
├── src/biblioteca_virtual/
│   ├── main.py                          # Configuração FastAPI
│   ├── api/v1/
│   │   ├── router.py                    # Agregador de rotas
│   │   ├── auth.py                      # Endpoints de autenticação
│   │   ├── users.py                     # Endpoints de usuários
│   │   ├── books.py                     # Endpoints de livros
│   │   └── loans.py                     # Endpoints de empréstimos
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── service.py               # Lógica de autenticação
│   │   │   └── schemas.py               # DTOs de auth
│   │   ├── users/
│   │   │   ├── models.py                # Modelos ORM
│   │   │   ├── service.py               # Lógica de usuários
│   │   │   ├── repository.py            # Acesso a dados
│   │   │   └── schemas.py               # DTOs
│   │   ├── books/
│   │   │   └── ...                      # Mesmo padrão
│   │   └── loans/
│   │       └── ...                      # Mesmo padrão
│   ├── core/
│   │   ├── config.py                    # Variáveis de ambiente
│   │   ├── db.py                        # Conexão PostgreSQL
│   │   ├── cache.py                     # Redis
│   │   ├── security.py                  # JWT
│   │   ├── middleware.py                # Auth middleware
│   │   ├── rate_limit.py                # Rate limiting
│   │   ├── logging.py                   # Estruturação de logs
│   │   ├── metrics.py                   # Prometheus
│   │   └── health.py                    # Health check
│   └── shared/
│       ├── pagination.py                # Paginação padrão
│       └── utils.py                     # Utilitários
├── migrations/                          # Alembic (versionamento de DB)
├── tests/                               # Suite de testes
├── scripts/
│   └── seed.py                          # Dados iniciais
├── docker-compose.yml                   # Stack local (PostgreSQL + Redis)
├── Dockerfile
├── pyproject.toml                       # Configuração Python (uv/pip)
└── README.md
```

---

## Testando a Aplicação

### Executar Testes
```bash
# Todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov=src/biblioteca_virtual

# Apenas testes de integração
uv run pytest tests/test_api_integration.py -v

# Apenas testes de unidade
uv run pytest tests/test_unit_services.py -v
```

---

## Monitoramento

### Health Check
```bash
curl http://localhost:8000/health
```

**Resposta**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### Métricas Prometheus
```bash
curl http://localhost:8000/metrics
```

As métricas podem ser scraped por Prometheus e visualizadas em Grafana.

---

## Contribuindo

1. Crie uma branch: `git checkout -b feature/minha-feature`
2. Commit suas mudanças: `git commit -m "Adiciona minha feature"`
3. Push para a branch: `git push origin feature/minha-feature`
4. Abra um Pull Request

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

## Documentação das Decisões Arquiteturais

A aplicação foi desenhada com uma separação clara de responsabilidades:
- **API Layer**: routers FastAPI, schemas Pydantic v2, validações e contratos claros.
- **Service Layer**: regras de negócio, transações e orquestração.
- **Repository Layer**: isolamento do acesso a dados por agregado.
- **Core/Shared**: configuração, observabilidade, segurança, cache, rate limit e utilitários.

Essa separação facilita testes, evolução de regras e troca de infraestrutura sem impacto nas camadas superiores.

### Modelagem de Banco de Dados

- **users**: dados cadastrais, autenticação e status ativo.
- **authors**: autores únicos por nome.
- **books**: livro vinculado a autor, com controle de cópias.
- **loans**: empréstimos com status, vencimento, devolução e multa.

**Regras aplicadas no modelo:**
- Constraints para manter cópias disponíveis >= 0 e <= total.
- Índices para email, isbn, author_id e status de empréstimo para otimização de consultas.

### Escolhas Tecnológicas e Trade-offs

- **FastAPI**: Escolhido pela performance e geração automática de documentação OpenAPI.
- **SQLAlchemy 2.0 async**: Padrão moderno, tipado e performático para operações de I/O no banco.
- **Pydantic v2**: Garante contratos claros e validação rápida.
- **Auth Middleware Global**: Proteção centralizada blindando todas as rotas (exceto públicas como login e signup) sem overhead de requisições repetidas ao BD (O(1)).
- **Redis**: Cache de leitura em endpoints paginados e rate limit com baixo custo.
- **Observabilidade**: Logging estruturado em JSON com `request_id`, métricas Prometheus prontas para Grafana e Health check para validação de DB e Redis.
- **Trade-offs**: Optamos por um modelo simples de disponibilidade (total/available copies) para evitar consultas complexas e custosas de estoque. Rate limit e cache são ativados apenas quando o Redis está configurado/habilitado.

### Fluxo de Requisição e Infraestrutura

#### Diagrama de Infraestrutura e Fluxo
A infraestrutura utiliza FastAPI rodando em um container Docker, conectando-se ao PostgreSQL para banco de dados relacional e Redis para cache e rate limit. As métricas são exportadas para o Prometheus. O fluxo de empréstimo segue o padrão de requisição para o Router, validação e regras de negócio no Service, controle transacional e consultas ao banco pelo Repository e, em caso de sucesso, retorno para o cliente com invalidação do cache pertinente.

---

## Lista de Funcionalidades Implementadas

- **Gestão de Usuários**: Cadastro, autenticação (JWT) e consulta de usuários.
- **Catálogo de Livros**: Cadastro e listagem de livros e autores, com paginação e cache Redis.
- **Gestão de Empréstimos**:
  - Regras rígidas de prazo e limite de empréstimos ativos por usuário.
  - Cálculo automático de multas em caso de atraso na devolução.
  - Controle transacional de estoque (cópias disponíveis).
- **Segurança e Proteção**:
  - Middleware de autenticação global.
  - Rate limiting utilizando Redis.
- **Qualidade de Produção**:
  - Métricas nativas exportadas no formato Prometheus (`/metrics`).
  - Health checks (`/health`) com validação real de DB e Cache.
  - Logs estruturados para facilitar rastreamento (`request_id`).
- **Resumo dos Endpoints Principais**:
  - **Auth**: `POST /api/v1/auth/token`
  - **Users**: `GET /api/v1/users` | `POST /api/v1/users` (Signup) | `GET /api/v1/users/{id}` | `GET /api/v1/users/{id}/loans`
  - **Books**: `GET /api/v1/books` | `POST /api/v1/books` | `GET /api/v1/books/{id}/availability`
  - **Loans**: `POST /api/v1/loans` | `POST /api/v1/loans/{id}/return` | `GET /api/v1/loans/active` | `GET /api/v1/loans/overdue` | `GET /api/v1/loans/user/{id}`
  - *Obs: Todos os endpoints GET que retornam listas utilizam paginação via query params (`?offset=0&limit=50`).*

---

## Exemplos de Uso da API

Abaixo um fluxo rápido demonstrando como interagir com a API utilizando o `cURL`.

### 1. Criar um novo usuário (Signup)

```bash
curl -X POST http://localhost:8000/api/v1/users \
	-H "Content-Type: application/json" \
	-d '{"full_name":"Admin","email":"admin@biblioteca.com","password":"Admin123!"}'
```

### 2. Gerar o token de autenticação (Login)

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
	-H "Content-Type: application/x-www-form-urlencoded" \
	-d "username=admin@biblioteca.com&password=Admin123!"
```
*O retorno será um JSON contendo o `access_token`.*

### 3. Utilizar o token para consultas protegidas (ex: listar livros)

Copie o `<token>` retornado no passo anterior e envie no header `Authorization`:

```bash
curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/books?offset=0&limit=50
```

### 4. Consultar status da aplicação e métricas

```bash
# Health check (Público)
curl http://localhost:8000/health

# Métricas (Público, para o Prometheus)
curl http://localhost:8000/metrics
```

---

## Sistema de Notificações de Empréstimos

Sistema automático de notificações para avisar sobre vencimento e atraso de empréstimos via **Email** e **Webhook**.

### Features

- Notificações automáticas nos dias 3, 1 e 0 antes do vencimento  
- Alertas diários para empréstimos vencidos  
- Emails moderno com design responsivo  
- Webhooks para integrações externas  
- Sem duplicação de notificações  
- Histórico completo de envios  
- Configurável via variáveis de ambiente  

### Configuração Rápida

1. **Copiar arquivo de configuração**:
```bash
cp .env.example.notifications .env
```

2. **Ativar no `.env`**:
```bash
NOTIFICATION_ENABLED=true
NOTIFICATION_SCHEDULER_ENABLED=true
NOTIFICATION_SCHEDULER_INTERVAL_MINUTES=60
EMAIL_PROVIDER=mock  # mock para dev, smtp para produção
```

3. **Executar migração**:
```bash
alembic upgrade head
```

4. **Reiniciar a aplicação**:
```bash
uvicorn biblioteca_virtual.main:app --reload
```

### Documentação Completa

Para configuração detalhada, provedor de email SMTP, webhook e troubleshooting, veja [NOTIFICATIONS_SETUP.md](./NOTIFICATIONS_SETUP.md).

### Uso Manual

```bash
# Processar todas as notificações agora
python scripts/notifications_admin.py process

# Enviar notificação para empréstimo específico
python scripts/notifications_admin.py send-manual <loan_id>

# Listar notificações pendentes
python scripts/notifications_admin.py list
```

### Exemplos

**Email de Vencimento Próximo**
```
Assunto: ⏰ Seu empréstimo vence em 3 dia(s)

Olá João Silva,

Gostaríamos de lembrá-lo que seu empréstimo está próximo do vencimento.
Por favor, devolva o livro no prazo para evitar multa.

📚 Livro: Clean Code
📅 Vencimento: 10/05/2026
⏳ Dias até vencimento: 3
```

**Email de Atraso**
```
Assunto: 🚨 Empréstimo vencido há 5 dia(s)

Olá João Silva,

Infelizmente, seu empréstimo passou do prazo de devolução.
Isto está gerando multa por atraso. Por favor, devolva o livro o quanto antes.
```

**Webhook Payload**
```json
{
  "event": "loan_due_soon",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "loan_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "book_title": "Clean Code",
  "due_date": "2026-05-10T14:30:00",
  "days_left": 3,
  "is_overdue": false,
  "timestamp": "2026-05-07T10:15:00"
}
```

---
