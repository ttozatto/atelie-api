# atelie-api

API REST do catalogo de fotografias em print e quadro. FastAPI + SQLAlchemy + PostgreSQL.

Repositorio da interface: `atelie-web` (clonado ao lado desta pasta; o `docker-compose.yml` fica lá).

## Status

Etapa 2 concluida: CRUD de fotos com upload, media servida em `/media` e seed de exemplo.

## Rotas

| Metodo | Rota | Observacao |
| --- | --- | --- |
| `GET` | `/api/photos` | filtros `q`, `category`, `is_published`; paginacao `limit`/`offset` |
| `GET` | `/api/photos/{id}` | detalhe da obra |
| `POST` | `/api/photos` | `multipart/form-data`: imagem + metadados — exige `X-Admin-Token` |
| `PUT` | `/api/photos/{id}` | metadados; imagem nova e opcional — exige `X-Admin-Token` |
| `DELETE` | `/api/photos/{id}` | apaga o registro e o arquivo — exige `X-Admin-Token` |
| `GET` | `/health` | checa a conexao com o banco |

Erros saem no formato `{"detail": "..."}`.

### Upload

Aceita `jpg`, `jpeg`, `png` e `webp` ate 10 MB (415 para formato nao suportado, 413
acima do limite). O arquivo vai para o volume montado em `/app/media` e e servido por
`StaticFiles` em `/media`; o campo `image_path` guarda o caminho publico
(ex.: `/media/a1b2c3.jpg`). Nao ha geracao de thumbnail — o redimensionamento fica com
o `next/image` na interface.

O campo `sizes` chega como texto separado por virgula (`A4, A3, 30x40`) e e gravado
como `text[]`.

## Seed

Gera 8 obras de exemplo com imagens criadas na hora pelo Pillow (retangulo colorido com
o titulo escrito), para a demonstracao nao depender de foto real:

```bash
docker compose exec api python -m scripts.seed
```

O script nao faz nada se o catalogo ja tiver obras.

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

Os testes usam um banco proprio (`atelie_test`, criado automaticamente) e um diretorio
de media temporario, entao nao mexem nos dados de desenvolvimento. Nenhum teste acessa
a rede.
