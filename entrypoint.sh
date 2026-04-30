#!/bin/sh
set -e

echo "Aguardando PostgreSQL estar pronto..."
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" > /dev/null 2>&1; do
  echo "PostgreSQL ainda não está pronto, aguardando..."
  sleep 1
done

echo "PostgreSQL pronto!"

echo "Executando migrações..."
uv run alembic upgrade head

if [ "${ENV:-dev}" != "prod" ]; then
  echo "Populando dados de teste..."
  uv run python scripts/seed.py
fi

echo "Iniciando aplicação..."
exec uv run uvicorn biblioteca_virtual.main:app --host 0.0.0.0 --port 8000
