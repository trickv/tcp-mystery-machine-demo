# Deployment runbook

Target: Ubuntu 22.04+ VPS with a public IP. Port 4242/tcp open. Docker +
compose plugin installed.

## Prereqs

```sh
sudo apt update
sudo apt install -y docker.io docker-compose-plugin netcat-openbsd ufw
sudo usermod -aG docker "$USER"   # log out / back in after this
```

## First-time setup

```sh
sudo ufw allow 4242/tcp
sudo ufw reload
git clone git@github.com:trickv/tcp-mystery-machine-demo.git
cd tcp-mystery-machine-demo
docker compose up -d --build
```

## Verify from the VPS

```sh
echo 'STATUS' | nc -q 1 localhost 4242
docker compose logs -f --tail=50
```

Expected: banner + STATUS block terminated by `.`, container logs show
`listening on ('0.0.0.0', 4242)` and a connect/close pair for the smoke.

## Verify from the outside

```sh
echo 'STATUS' | nc -q 1 <vps-host> 4242
```

If you get connection refused: check `sudo ufw status`, check
`ss -ltnp | grep 4242` on the VPS, check the container is running
(`docker compose ps`).

## Update

```sh
git pull
docker compose up -d --build
```

## Stop

```sh
docker compose down
```

## Logs

Already rotated by compose (json-file, 10 MB × 3). To inspect:

```sh
docker compose logs --tail=200
docker compose logs -f
```

## Troubleshooting

- **Port already in use** (`bind: address already in use`): find and kill
  whatever's holding 4242.
  ```sh
  sudo ss -ltnp | grep 4242
  ```
- **UFW blocking**: `sudo ufw status` should show `4242/tcp ALLOW`.
- **Container restart loop**: `docker compose logs` for the stack trace.
  Most likely a Python import error from a hand-edit.
- **Too many reconnects from one student**: the 200-connection cap plus
  120s idle timeout prevents abuse. `?BUSY` is the expected response at
  cap — students see it, they retry.

## Configuration knobs (via compose env)

| Env var | Default | Effect |
|---|---|---|
| `VOYAGER_PORT` | `4242` | Listen port inside the container (also update `ports:` mapping if changed) |
| `VOYAGER_MAX_CONN` | `200` | Hard concurrent-connection cap |
| `VOYAGER_IDLE_TIMEOUT` | `120` | Seconds of silence before `?TIMEOUT` + close |
| `VOYAGER_MAX_LINE` | `256` | Max bytes per input line before `?OVF` + close |
