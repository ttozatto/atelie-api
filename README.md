# atelie-api

API REST do catalogo de fotografias em print e quadro. FastAPI + SQLAlchemy + PostgreSQL.

Repositorio da interface: `atelie-web` (clonado ao lado desta pasta; o `docker-compose.yml` fica lá).

## Status

Etapa 1 (infra) concluida: `GET /health` responde e checa a conexao com o banco.

## Como executar

Este repositorio nao roda sozinho: o `docker-compose.yml` que sobe banco, API e
interface fica em `../atelie-web`.

```bash
cd ../atelie-web
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Variaveis de ambiente

| Variavel | Descricao | Exemplo |
| --- | --- | --- |
| `DATABASE_URL` | Conexao SQLAlchemy com o PostgreSQL | `postgresql+psycopg://atelie:atelie@db:5432/atelie` |
| `CORS_ORIGINS` | Origens liberadas no CORS, separadas por virgula | `http://localhost:3000` |
| `ADMIN_TOKEN` | Token comparado ao header `X-Admin-Token` nas rotas de escrita | `troque-este-token` |
| `MEDIA_DIR` | Diretorio das imagens enviadas | `/app/media` |

Copie `.env.example` para `.env` se quiser rodar a API isolada. O `.env` nao e versionado.

## Nota sobre o ADMIN_TOKEN

O painel nao tem autenticacao real. As rotas de escrita de fotos usam uma dependency
do FastAPI que compara o header `X-Admin-Token` com a variavel `ADMIN_TOKEN`.
E um **placeholder de MVP academico**, nao um mecanismo de autenticacao: nao ha
usuarios, sessoes, hash de senha nem expiracao. Nao usar em producao.

## Qualidade

```bash
docker compose exec api ruff check .
docker compose exec api pytest
```
