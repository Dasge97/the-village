# La aldea: compila la web y la sirve junto con el mundo (python -m jevmura.servidor).

FROM node:24-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY web/ ./
RUN npm run build

FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Europe/Madrid
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY jevmura/ jevmura/
COPY --from=web /web/dist web/dist

RUN useradd --create-home --uid 1000 aldea && mkdir -p /app/datos && chown aldea /app/datos
USER aldea
ENV JEVMURA_DB=/app/datos/mundo.db
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/salud', timeout=4)"
CMD ["python", "-m", "jevmura.servidor", "--puerto", "8000"]
