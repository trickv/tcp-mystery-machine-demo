FROM python:3.11-slim

WORKDIR /app

# Bridge dep only; server is stdlib-only.
RUN pip install --no-cache-dir websockets==16.0

COPY server/ ./server/
COPY bridge/ ./bridge/
COPY web/ ./web/

RUN adduser --disabled-password --gecos "" --uid 10001 vgr
USER vgr

EXPOSE 4242 8080
ENV PYTHONUNBUFFERED=1

# Default CMD runs the TCP server; docker-compose overrides per service.
CMD ["python", "-m", "server"]
