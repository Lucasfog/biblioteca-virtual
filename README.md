# 📚 Biblioteca Virtual API

> **API REST para gerenciamento de biblioteca digital** com FastAPI, SQLAlchemy 2.0, PostgreSQL e Redis.

---

## 📑 Índice

1. [Introdução](#1-introdução)
2. [Instalação e Execução](#2-instalação-e-execução)
3. [Autenticação no Swagger](#3-autenticação-no-swagger)
4. [Listagem de Rotas](#4-listagem-de-rotas)
5. [Payloads Necessários](#5-payloads-necessários)
6. [Exemplos de Uso](#6-exemplos-de-uso)

---

## 1. 🚀 Introdução

A **Biblioteca Virtual API** é um sistema robusto desenvolvido para gerenciar operações de uma biblioteca digital, incluindo o cadastro de usuários, livros, autores e o controle de empréstimos e devoluções.

O projeto foi construído para ser escalável e pronto para produção, utilizando:
* **Autenticação JWT** para proteção de rotas
* **Controle de estoque** de livros com validação transacional
* **Cache via Redis** para otimização de consultas paginadas
* **Cálculo de multas automáticas** para devoluções em atraso

---

## 2. ⚙️ Instalação e Execução

O projeto utiliza a ferramenta moderna `uv` para um gerenciamento ultrarrápido de dependências e ambientes virtuais.

### Pré-requisitos
* Python 3.11+
* PostgreSQL 16+
* Redis 7+
* [uv](https://docs.astral.sh/uv/) instalado

### Passo a Passo

**1. Instalar dependências e criar ambiente virtual**
```bash
uv sync --all-groups
```

**2. Configurar o ambiente**
```bash
cp .env.example .env
# Edite o .env com suas credenciais de banco de dados e Redis
```

**3. Executar as migrações (Banco de Dados)**
```bash
uv run alembic upgrade head
```

**4. Rodar a aplicação (Modo Desenvolvimento)**
```bash
uv run uvicorn biblioteca_virtual.main:app --reload
```
A API estará disponível em `http://localhost:8000` e a documentação interativa em `http://localhost:8000/docs`.

**5. Rodar os testes**
```bash
uv run pytest
```

**6. Buildar o projeto para produção**
```bash
uv build
```

---

## 3. 🔐 Autenticação no Swagger

Para testar as rotas protegidas diretamente pela interface interativa do Swagger, siga os passos abaixo.

### Credenciais de Exemplo
```json
{
  "username": "admin@example.com",
  "password": "123456"
}
```

### Passo a Passo:
1. **Fazer login:** Acesse o Swagger UI em `http://localhost:8000/docs`. Vá até a rota **`POST /api/v1/auth/token`** e clique em *Try it out*.
2. **Copiar token retornado:** Insira as credenciais de exemplo (email como `username` e a `password`). Clique em **Execute** e copie o valor do `access_token` retornado no corpo da resposta.
3. **Clicar em Authorize no Swagger:** No topo da página do Swagger, clique no botão verde **Authorize**.
4. **Inserir Bearer Token:** Insira `Bearer <seu_token_copiado>` no campo de valor e clique no botão **Authorize** da janela modal.
5. **Testar rotas protegidas:** Agora você pode testar qualquer rota! O ícone de cadeado nas rotas protegidas aparecerá fechado indicando que você está autenticado.

---

## 4. 🗺️ Listagem de Rotas

Visão geral dos endpoints disponíveis na API:

| Método | Rota | Descrição | Auth |
| :---: | :--- | :--- | :---: |
| **POST** | `/api/v1/auth/token` | Realiza autenticação e retorna token JWT | Não |
| **POST** | `/api/v1/users` | Cria um novo usuário no sistema | Não |
| **GET** | `/api/v1/users` | Lista os usuários cadastrados | Sim |
| **GET** | `/api/v1/users/{id}` | Retorna os detalhes de um usuário específico | Sim |
| **POST** | `/api/v1/books` | Cadastra um novo livro no acervo | Sim |
| **GET** | `/api/v1/books` | Lista os livros disponíveis | Sim |
| **GET** | `/api/v1/books/{id}/availability`| Verifica a disponibilidade de cópias de um livro | Sim |
| **POST** | `/api/v1/loans` | Realiza o empréstimo de um livro para um usuário | Sim |
| **POST** | `/api/v1/loans/{id}/return` | Registra a devolução de um livro emprestado | Sim |
| **GET** | `/api/v1/loans/active` | Lista todos os empréstimos ativos | Sim |

---

## 5. 📦 Payloads Necessários

Abaixo estão os formatos de envio (body), query params e headers exigidos nas rotas principais da aplicação.

### Autenticação (`POST /api/v1/auth/token`)
* **Headers**: `Content-Type: application/x-www-form-urlencoded`
* **Body (Form Data)**:
  * `username`: Email do usuário
  * `password`: Senha do usuário

### Criar Usuário (`POST /api/v1/users`)
* **Headers**: `Content-Type: application/json`
* **Body (JSON)**:
```json
{
  "email": "usuario@example.com",
  "password": "SenhaSegura123!",
  "full_name": "Nome do Usuário"
}
```

### Cadastrar Livro (`POST /api/v1/books`)
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <token>`
* **Body (JSON)**:
```json
{
  "title": "Clean Architecture",
  "author_name": "Robert C. Martin",
  "isbn": "978-0134494166",
  "total_copies": 10
}
```

### Realizar Empréstimo (`POST /api/v1/loans`)
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <token>`
* **Body (JSON)**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "book_id": "987fcdeb-51a2-43d7-9012-345678901234",
  "due_date": "2024-12-31"
}
```

### Paginação em Rotas GET (`GET /api/v1/books`, `GET /api/v1/users`)
* **Headers**: `Authorization: Bearer <token>`
* **Query Params**:
  * `offset` (int): Posição inicial (ex: `0`)
  * `limit` (int): Quantidade de registros por página (ex: `10`)

---

## 6. 💻 Exemplos de Uso

### Exemplos via Swagger
1. **Autenticação**: Abra a interface do Swagger, expanda a aba `/api/v1/auth/token`, insira `admin@example.com` no campo username, sua respectiva senha e clique em *Execute*.
2. **Listar Livros**: Após autorizar globalmente no Swagger com seu token, expanda `GET /api/v1/books`, preencha os parâmetros `offset=0` e `limit=10` e clique em *Execute*. A resposta listará os livros registrados no banco de dados.
3. **Fazer Empréstimo**: Expanda `POST /api/v1/loans`, insira os UUIDs válidos de um usuário e de um livro diretamente no payload JSON e clique em *Execute*. Você receberá o status `201 Created` confirmando a operação.

### Exemplos via cURL

**Login e obtenção de token**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=123456"
```

**Criar um novo usuário (Rota Pública)**
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "novo@usuario.com", "password": "Password123!", "full_name": "Novo Usuário"}'
```

**Listar livros (Requer Autenticação)**
```bash
curl -X GET "http://localhost:8000/api/v1/books?offset=0&limit=10" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Registrar devolução de um empréstimo**
```bash
curl -X POST http://localhost:8000/api/v1/loans/LOAN_ID_AQUI/return \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```
