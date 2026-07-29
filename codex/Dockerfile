FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN npm install -g @openai/codex

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

RUN mkdir -p /data/codex/skills /data/codex/plugins

ENV CODEX_A2A_BASE_DIR=/data/codex
ENV A2A_HOST=0.0.0.0

EXPOSE 8200

ENTRYPOINT ["codex-a2a"]
