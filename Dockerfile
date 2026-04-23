FROM python:3.11-slim

WORKDIR /app
COPY server/ ./server/

RUN adduser --disabled-password --gecos "" --uid 10001 vgr
USER vgr

EXPOSE 4242
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "server"]
