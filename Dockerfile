# atelie-api - FastAPI. Estagio "dev" tem ruff/pytest e hot reload;
# estagio "runtime" e a imagem enxuta de execucao.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 1000 atelie

COPY requirements.txt requirements-dev.txt ./


FROM base AS dev

RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .
RUN chown -R atelie:atelie /app

USER atelie
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM base AS runtime

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R atelie:atelie /app

USER atelie
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
