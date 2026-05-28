FROM python:3.11-slim

# Install supercronic for cron-in-Docker (signals-safe, no root daemon needed)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
    && curl -fsSL "$SUPERCRONIC_URL" -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic \
    && apt-get remove -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the summariser once (useful for one-shot / dev invocations).
# Override CMD in docker-compose to use supercronic for scheduled runs.
CMD ["python", "-m", "api.main"]
