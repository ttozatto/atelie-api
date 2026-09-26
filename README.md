# atelie-api

API REST do **Ateliê**, catálogo online de fotografias em print e quadro. Guarda as obras
e os clientes interessados, recebe o upload das imagens e consulta o ViaCEP para
preencher endereços.

FastAPI, SQLAlchemy 2 e PostgreSQL 16, com as imagens num armazenamento de objetos
compatível com a API do Amazon S3. Tudo rodando em Docker.

Repositório da interface: `atelie-web` — onde fica o `docker-compose.yml` que sobe o
sistema inteiro, o diagrama da arquitetura e a documentação do ViaCEP.

## Pré-requisitos

Docker e Docker Compose v2. Nada de Python no host: todo comando roda em contêiner.

## Instalação e execução

Este repositório **não sobe sozinho**. O `docker-compose.yml` com banco, API e interface
fica no repositório `atelie-web`, e os dois precisam estar clonados **lado a lado**:

```
./atelie-web/     # contém o docker-compose.yml
./atelie-api/     # este repositório
```

O serviço `api` do compose constrói a imagem com `build.context: ../atelie-api`, por isso
a pasta vizinha precisa existir com esse nome.

```bash
# na mesma pasta, clone os dois repositórios
git clone <url-do-repositorio>/atelie-web.git
git clone <url-do-repositorio>/atelie-api.git
cd atelie-web
cp .env.example .env
docker compose up --build
```

| Endereço | O que é |
| --- | --- |
| http://localhost:8000/docs | Swagger, com todas as rotas documentadas |
| http://localhost:8000/health | Health check da API e do banco |
| http://localhost:8000/media/… | Imagens enviadas |

As tabelas são criadas no startup com `Base.metadata.create_all()` (MVP sem migrações).

### Dados de exemplo

O seed popula o catálogo com **20 obras** (18 publicadas e 2 em rascunho, nas quatro
categorias) e **5 clientes** com endereços reais, conferidos no ViaCEP:

```bash
docker compose exec api python -m scripts.seed
```

As fotos ficam versionadas em [`scripts/seed_images/`](scripts/seed_images): são imagens
do Unsplash, obtidas via [Lorem Picsum](https://picsum.photos) e usadas sob a
[Unsplash License](https://unsplash.com/license), que dispensa cadastro e permite uso
livre. Os autores estão creditados em
[`scripts/seed_images/CREDITS.md`](scripts/seed_images/CREDITS.md). Como as imagens estão
no repositório, o seed não depende de rede nem de upload manual; se algum arquivo faltar,
o script gera um retângulo colorido com Pillow no lugar.

O script é idempotente: não faz nada se já houver obras (ou clientes) cadastrados.

### Dockerfile

`python:3.12-slim`, usuário não-root (`atelie`) e uvicorn, em dois estágios:

- **`dev`** — usado pelo compose: inclui ruff e pytest e roda `uvicorn --reload`, com o
  código vindo do host por bind mount.
- **`runtime`** — imagem enxuta, só com as dependências de execução.

```bash
docker build --target runtime -t atelie-api .
```

## Variáveis de ambiente

Dentro do compose, os valores vêm do `.env` do repositório `atelie-web`. O
[`.env.example`](.env.example) deste repositório documenta as variáveis que a API lê.
`DATABASE_URL`, `ADMIN_PASSWORD`, `ADMIN_TOKEN`, `S3_ACCESS_KEY` e `S3_SECRET_KEY` não têm
valor padrão no código: sem elas a API não sobe,
em vez de subir com uma credencial conhecida.

| Variável | Descrição | Valor padrão |
| --- | --- | --- |
| `DATABASE_URL` | Conexão SQLAlchemy com o PostgreSQL | **obrigatória** |
| `CORS_ORIGINS` | Origens liberadas no CORS, separadas por vírgula | `http://localhost:3000` |
| `ADMIN_USERNAME` | Usuário aceito na tela de login do painel | `admin` |
| `ADMIN_PASSWORD` | Senha aceita na tela de login do painel | **obrigatória** |
| `ADMIN_TOKEN` | Token comparado ao header `X-Admin-Token` nas rotas de escrita | **obrigatória** |
| `S3_ENDPOINT_URL` | Endereço do armazenamento de objetos | `http://storage:9000` |
| `S3_BUCKET` | Bucket onde as imagens ficam | `atelie-media` |
| `S3_REGION` | Região enviada na assinatura das requisições | `us-east-1` |
| `S3_ACCESS_KEY` | Chave de acesso do armazenamento | **obrigatória** |
| `S3_SECRET_KEY` | Chave secreta do armazenamento | **obrigatória** |
| `VIACEP_BASE_URL` | Base do serviço de CEP | `https://viacep.com.br/ws` |
| `VIACEP_TIMEOUT_SECONDS` | Tempo limite da consulta ao ViaCEP, em segundos | `5` |

## Rotas

Prefixo `/api`. Todos os erros saem no formato `{"detail": "..."}`, documentado no
Swagger como `ErrorResponse`.

| Método | Rota | Observação |
| --- | --- | --- |
| `GET` | `/api/photos` | Filtros `q`, `category`, `is_published`; paginação `limit`/`offset` |
| `GET` | `/api/photos/{id}` | Detalhe da obra; `404` se não existir |
| `POST` | `/api/photos` | `multipart/form-data`: imagem + metadados. Exige `X-Admin-Token` |
| `PUT` | `/api/photos/{id}` | Metadados; imagem nova é opcional. Exige `X-Admin-Token` |
| `DELETE` | `/api/photos/{id}` | Apaga o registro e o arquivo. Exige `X-Admin-Token` |
| `GET` | `/api/customers` | Lista paginada |
| `POST` | `/api/customers` | Cadastro; e-mail duplicado responde `409` |
| `POST` | `/api/auth/login` | Login do painel; credenciais inválidas respondem `401` |
| `GET` | `/api/cep/{cep}` | Proxy tratado do ViaCEP |
| `GET` | `/media/{arquivo}` | Serve os bytes de uma imagem, lidos do armazenamento |
| `GET` | `/health` | Checa a conexão com o banco; `503` se ele não responder |

### Listagens paginadas

`GET /api/photos` e `GET /api/customers` devolvem um envelope com o total, para a
paginação poder ser exibida:

```json
{ "items": [ ... ], "total": 8, "limit": 24, "offset": 0 }
```

### Upload e armazenamento de imagens

Aceita `jpg`, `jpeg`, `png` e `webp` até 10 MB: `415` para formato não suportado e `413`
acima do limite.

As imagens **não** ficam no sistema de arquivos da API nem no banco: vão para um
**armazenamento de objetos com API compatível com o Amazon S3**, acessado com o `boto3`
([`app/services/media.py`](app/services/media.py)). No compose esse serviço é o
[RustFS](https://rustfs.com) (Apache-2.0), um substituto open source do S3 que sobe num
contêiner; trocando as variáveis `S3_*`, o mesmo código fala com o S3 da AWS ou com
qualquer outro serviço compatível.

O objeto recebe um nome aleatório (UUID) e o banco guarda apenas o caminho público em
`image_path` (ex.: `/media/a1b2c3.jpg`). Quem devolve os bytes é a rota
`GET /media/{arquivo}` ([`app/routers/media.py`](app/routers/media.py)), que lê o objeto
e o transmite com `Cache-Control` longo — o navegador nunca fala direto com o
armazenamento, e a interface continua conhecendo só a nossa API. O bucket é criado no
startup, se ainda não existir. Não há geração de thumbnail: o redimensionamento fica com
o `next/image` na interface.

O campo `sizes` chega como texto separado por vírgula (`A4, A3, 30x40`) e é gravado como
`text[]`.

### Proxy do ViaCEP

O ViaCEP é consumido **pela API**, nunca pelo navegador: a interface só conhece
`GET /api/cep/{cep}`. A resposta do serviço externo é convertida para o nosso schema e as
falhas dele viram erros nossos.

| Campo do ViaCEP | Nosso campo |
| --- | --- |
| `logradouro` | `street` |
| `bairro` | `district` |
| `localidade` | `city` |
| `uf` | `state` |

| Situação | Nossa resposta |
| --- | --- |
| CEP encontrado | `200` com `{cep, street, district, city, state}` |
| CEP fora do formato de 8 dígitos | `422`, sem consultar o ViaCEP |
| ViaCEP responde `{"erro": true}` | `404` — "CEP não encontrado" |
| ViaCEP não responde dentro do tempo limite | `504` — "Serviço de CEP não respondeu a tempo" |
| ViaCEP fora do ar ou com resposta inválida | `502` — "Serviço de CEP indisponível" |

Implementação em [`app/services/viacep.py`](app/services/viacep.py). O que é o ViaCEP e
seus termos de uso estão documentados no README do `atelie-web`.

## Login do painel e o ADMIN_TOKEN

> **Isto é um placeholder de MVP acadêmico, não autenticação de verdade.**

São duas peças:

1. **`POST /api/auth/login`** ([`app/routers/auth.py`](app/routers/auth.py)) compara o
   usuário e a senha informados com `ADMIN_USERNAME` e `ADMIN_PASSWORD` (comparação em
   tempo constante, com `secrets.compare_digest`) e, se baterem, devolve o `ADMIN_TOKEN`.
   Credenciais erradas respondem `401`, sem dizer se o errado foi o usuário ou a senha.
2. **A dependency do `X-Admin-Token`** ([`app/security.py`](app/security.py)) protege as
   rotas de escrita de fotos (`POST`, `PUT` e `DELETE /api/photos`): o header precisa ser
   igual a `ADMIN_TOKEN`, ou a resposta é `401`.

As limitações são deliberadas e devem ser ditas em voz alta: existe **um único usuário**,
vindo de variável de ambiente; a senha fica **em texto puro** no ambiente, sem hash; o
token é um **segredo compartilhado fixo**, sem assinatura, sem expiração e sem
possibilidade de revogar. Num sistema real, trocar por usuários persistidos com senha em
hash e sessão ou token assinado com expiração.

## Qualidade

```bash
docker compose exec api ruff check .
docker compose exec api pytest
```

Os testes cobrem o essencial: CRUD de fotos (incluindo token e limites de upload), login
do painel, e-mail duplicado e o proxy de CEP com o ViaCEP mockado (sucesso, CEP
inexistente, timeout e falha). Eles usam um banco próprio (`atelie_test`) e um bucket
próprio (`atelie-media-test`), ambos criados automaticamente, então não mexem nos dados
de desenvolvimento. O banco e o armazenamento são os do compose, na rede interna:
**nenhum teste acessa a internet**.

## Estrutura

```
app/
  main.py         aplicação, CORS, tags do Swagger e criação do bucket
  config.py       variáveis de ambiente (pydantic-settings)
  database.py     engine, sessão e Base do SQLAlchemy
  security.py     placeholder do X-Admin-Token
  models/         tabelas photos e customers
  schemas/        contratos Pydantic de entrada e saída
  routers/        photos, customers, auth, cep, media e health
  services/       media (armazenamento S3) e viacep
scripts/
  seed.py         obras e clientes de exemplo
  seed_images/    fotos de exemplo (Unsplash) + créditos
tests/            pytest
```
