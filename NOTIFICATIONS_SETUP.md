# Sistema de Notificações de Empréstimos

Sistema completo de notificações para empréstimos com suporte a **Email** e **Webhook**, executado automaticamente via scheduler.

## 📋 Features

✅ **Notificações automáticas** de vencimento próximo e atraso  
✅ **Email moderno** com design responsivo  
✅ **Webhook** para integrações externas  
✅ **Sem duplicação** de notificações  
✅ **Histórico completo** de envios  
✅ **Retry automático** em falhas  
✅ **Configurável via ENV**  
✅ **Logs estruturados** com Structlog  
✅ **Testes completos**  
✅ **Production-ready**

---

## 🏗️ Arquitetura

### Estrutura de Arquivos

```
modules/notifications/
├── __init__.py                  # Exports públicos
├── models.py                    # Modelo ORM (LoanNotification)
├── schemas.py                   # Schemas Pydantic
├── repository.py                # Acesso a dados
├── service.py                   # Lógica principal
├── email.py                     # Serviço de email
├── webhook.py                   # Serviço de webhook
└── templates/
    ├── due_soon.html           # Email de vencimento próximo
    └── overdue.html            # Email de empréstimo vencido

core/
└── scheduler.py                 # Job scheduler (APScheduler)
```

### Fluxo de Dados

```
Scheduler (a cada X minutos)
    ↓
scheduler.py (_run_notification_job)
    ↓
NotificationService.process_loan_notifications()
    ↓
Para cada empréstimo ativo:
    ├─ Calcular dias até vencimento
    ├─ Verificar se já foi notificado
    ├─ Enviar email (EmailNotificationService)
    ├─ Enviar webhook (WebhookNotificationService)
    └─ Registrar na DB (LoanNotification)
```

---

## 🔧 Configuração

### 1. Variáveis de Ambiente

Adicione ao arquivo `.env`:

```bash
# Ativação do sistema
NOTIFICATION_ENABLED=true
NOTIFICATION_SCHEDULER_ENABLED=true

# Frequência do scheduler (em minutos)
NOTIFICATION_SCHEDULER_INTERVAL_MINUTES=60

# Quando notificar (dias antes do vencimento)
# Padrão: 3 dias, 1 dia, dia do vencimento
NOTIFICATION_DAYS_BEFORE=3,1,0

# Ativar alertas de atraso
NOTIFICATION_ENABLE_OVERDUE_ALERTS=true

# ===== EMAIL =====
# Provedor: mock (desenvolvimento) ou smtp (produção)
EMAIL_PROVIDER=mock
# EMAIL_PROVIDER=smtp

EMAIL_SENDER_NAME=Biblioteca Virtual
EMAIL_SENDER_ADDRESS=noreply@biblioteca-virtual.com

# SMTP (apenas se EMAIL_PROVIDER=smtp)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_USE_TLS=true

# ===== WEBHOOK =====
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://seu-sistema.com/webhooks/loans
WEBHOOK_TIMEOUT=10.0
WEBHOOK_MAX_RETRIES=3
```

### 2. Banco de Dados

Execute a migração:

```bash
# Com Alembic
alembic upgrade head
```

Isso criará a tabela `loan_notifications` para rastreamento.

### 3. Dependências

Certifique-se que o `pyproject.toml` tem:

```toml
apscheduler==3.10.4
jinja2==3.1.2
httpx==0.27.0  # Já incluído
```

Instale:

```bash
pip install -e .
```

---

## 🚀 Uso

### Automático (Recomendado)

O scheduler inicia automaticamente ao iniciar a aplicação:

```bash
uvicorn biblioteca_virtual.main:app --reload
```

Logs:
```
notification_scheduler_initializing interval_minutes=60
notification_scheduler_started
notification_job_started
notification_job_completed
```

### Manual (CLI/Admin)

Para executar notificações manualmente:

```python
import asyncio
from biblioteca_virtual.core.scheduler import run_notifications_manually

asyncio.run(run_notifications_manually())
```

---

## 📧 Templates de Email

### Email de Vencimento Próximo

**Quando:** 3 dias, 1 dia, e no dia do vencimento

**Conteúdo:**
- ⏰ Ícone de alarme
- Nome do usuário
- Nome do livro
- Data de vencimento
- Dias restantes (grande e destacado)
- Aviso de multa
- Botão de ação
- Design fintech moderno

**Design:**
- Cores: Azul (#667eea) para avisos
- Responsivo
- HTML puro (sem dependências CSS externas)

### Email de Empréstimo Vencido

**Quando:** Diariamente enquanto vencido (1x por dia)

**Conteúdo:**
- 🚨 Ícone de alerta
- Nome do usuário
- Nome do livro
- Data de vencimento (original)
- Dias em atraso
- Informação sobre multa
- Botão de ação urgente

**Design:**
- Cores: Vermelho (#dc2626) para urgência
- Responsivo
- HTML puro

---

## 🔄 Webhook Payload

### Evento: `loan_due_soon`

```json
{
  "event": "loan_due_soon",
  "user_id": "uuid-do-usuario",
  "loan_id": "uuid-do-emprestimo",
  "book_title": "Clean Code",
  "due_date": "2026-05-10T14:30:00",
  "days_left": 3,
  "is_overdue": false,
  "timestamp": "2026-05-07T10:15:00"
}
```

### Evento: `loan_overdue`

```json
{
  "event": "loan_overdue",
  "user_id": "uuid-do-usuario",
  "loan_id": "uuid-do-emprestimo",
  "book_title": "Clean Code",
  "due_date": "2026-05-07T14:30:00",
  "days_left": -3,
  "is_overdue": true,
  "timestamp": "2026-05-10T10:15:00"
}
```

**Seu webhook deve retornar:** `200`, `201` ou `202`

---

## 🛡️ Evitar Duplicação

O sistema evita enviar notificações duplicadas através de:

1. **Para `DUE_SOON`**: Verifica se já existe `SENT` ou `PENDING` deste tipo
2. **Para `OVERDUE`**: Verifica se foi notificado no último dia

Todas as notificações são registradas em `loan_notifications` com:
- `status`: PENDING, SENT ou FAILED
- `sent_at`: timestamp de envio
- `error_message`: detalhes se falhou
- `created_at`: quando foi tentado

---

## 🧪 Testes

### Rodar Todos os Testes

```bash
pytest tests/test_notifications.py -v
```

### Testes Incluídos

✅ Verificação de notificação enviada  
✅ Obtenção de notificações recentes  
✅ Envio de email (vencimento próximo)  
✅ Envio de email (atraso)  
✅ Envio de webhook  
✅ Cálculo de dias restantes  
✅ Prevenção de duplicação  
✅ Registro de notificações  

---

## 📊 Modelos de Dados

### Tabela: `loan_notifications`

```sql
CREATE TABLE loan_notifications (
    id UUID PRIMARY KEY,
    loan_id UUID NOT NULL REFERENCES loans(id),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL,  -- 'due_soon' | 'overdue'
    channel VARCHAR(50) NOT NULL,  -- 'email' | 'webhook'
    status VARCHAR(50) NOT NULL,  -- 'pending' | 'sent' | 'failed'
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX ix_loan_notifications_loan_id (loan_id),
    INDEX ix_loan_notifications_user_id (user_id),
    INDEX ix_loan_notifications_status (status),
    INDEX ix_loan_notifications_created_at (created_at)
);
```

---

## 🔍 Exemplos de Logs

```
logger.info(
    "notification_sent",
    loan_id="123e4567-e89b-12d3-a456-426614174000",
    user_id="123e4567-e89b-12d3-a456-426614174001",
    type="due_soon",
    channel="email"
)

logger.error(
    "notification_failed",
    loan_id="123e4567-e89b-12d3-a456-426614174000",
    error="Connection timeout"
)
```

---

## 🚨 Troubleshooting

### Scheduler não está rodando

```python
# Verifique em main.py se foi adicionado
from biblioteca_virtual.core.scheduler import (
    init_notification_scheduler,
    shutdown_notification_scheduler,
)
```

### Emails não estão sendo enviados

1. Verifique `EMAIL_PROVIDER=mock` (desenvolvimento)
2. Para SMTP, valide credenciais
3. Veja logs: `logger.error(...)`

### Notificações duplicadas

- Verifique DB: `SELECT * FROM loan_notifications WHERE loan_id = '...'`
- Reset: `DELETE FROM loan_notifications WHERE created_at < NOW() - INTERVAL '7 days'`

### Templates não encontrados

```python
# Certifique-se que existe:
src/biblioteca_virtual/modules/notifications/templates/
  ├── due_soon.html
  └── overdue.html
```

---

## 📈 Monitoramento

### Métricas Importantes

```sql
-- Notificações enviadas por dia
SELECT DATE(created_at), COUNT(*) FROM loan_notifications 
WHERE status = 'sent' GROUP BY DATE(created_at);

-- Taxa de falha
SELECT COUNT(*) FILTER (WHERE status = 'failed') * 100.0 / COUNT(*) 
FROM loan_notifications;

-- Empréstimos com notificações pendentes
SELECT COUNT(DISTINCT loan_id) FROM loan_notifications 
WHERE status = 'pending';
```

---

## 🔐 Segurança

- Senhas SMTP não são logadas
- Emails são validados com `email-validator`
- Webhooks só aceitam HTTPS em produção
- Erros não expõem dados sensíveis

---

## 📚 Referências

- **APScheduler**: https://apscheduler.readthedocs.io/
- **Jinja2**: https://jinja.palletsprojects.com/
- **SMTP**: https://docs.python.org/3/library/smtplib.html
- **Structlog**: https://www.structlog.org/

---

## 🎯 Próximas Melhorias

- [ ] SMS notifications
- [ ] Push notifications
- [ ] Notificações por usuário (com preferências)
- [ ] Template builder UI
- [ ] Analytics dashboard
- [ ] A/B testing de templates
- [ ] Multi-idioma

---

## ✅ Checklist de Deploy

- [ ] Migração de BD executada (`alembic upgrade head`)
- [ ] Variáveis de ambiente configuradas
- [ ] `EMAIL_PROVIDER` correto para ambiente
- [ ] SMTP credenciais válidas (se necessário)
- [ ] Webhook URL válida (se necessário)
- [ ] Testes passando (`pytest tests/test_notifications.py`)
- [ ] Logs estruturados ativados
- [ ] APScheduler iniciando sem erros
- [ ] Primeiro email testado manualmente

---

**Desenvolvido por:** Sistema de Notificações Biblioteca Virtual  
**Última atualização:** 29 de abril de 2026
