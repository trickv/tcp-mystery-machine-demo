# Deployment runbook

Target: the bootcamp VPS is Debian 9 (stretch) with docker 19.03 and
docker-compose 1.8. The compose file uses the v2 schema so compose 1.8
understands it. Port 4242/tcp needs to reach the public internet.

## Prereqs (Debian 9 / stretch)

Assumed already installed: `docker-ce`, `docker-compose` (1.8), `nc`
(`netcat-openbsd`), and a firewall. If any are missing, install with
whatever package manager you use — this runbook doesn't try to
bootstrap them.

## First-time setup

```sh
git clone git@github.com:trickv/tcp-mystery-machine-demo.git
cd tcp-mystery-machine-demo
docker-compose up -d --build
```

Open port 4242 in whatever firewall the host uses (iptables / ufw /
cloud SG). Stretch's `ufw` predates the iptables-nft transition, so if
`ufw` behaves strangely, `iptables -A INPUT -p tcp --dport 4242 -j
ACCEPT` is the direct path.

## Verify from the VPS

```sh
echo 'STATUS' | nc -q 1 localhost 4242
docker-compose logs -f --tail=50
```

Expected: banner + STATUS block terminated by `.`, container logs show
`listening on ('0.0.0.0', 4242)` and a connect/close pair for the smoke.

## Verify from the outside

```sh
echo 'STATUS' | nc -q 1 voyager1.v9n.us 4242
```

If you get connection refused: check the host firewall, check
`ss -ltnp | grep 4242` on the VPS, check the container is running
(`docker-compose ps`).

## Update

```sh
git pull
docker-compose up -d --build
```

## Stop

```sh
docker-compose down
```

## Logs

Already rotated by compose (json-file, 10 MB × 3). To inspect:

```sh
docker-compose logs --tail=200
docker-compose logs -f
```

## Modern-install alternative (not this VPS)

If you're redeploying on a modern host with compose v2 (`docker compose`
as a docker CLI subcommand, space-separated), every `docker-compose` in
this file becomes `docker compose`. Everything else stays the same.

## Troubleshooting

- **Port already in use** (`bind: address already in use`): find and kill
  whatever's holding 4242.
  ```sh
  sudo ss -ltnp | grep 4242
  ```
- **Container restart loop**: `docker-compose logs` for the stack trace.
  Most likely a Python import error from a hand-edit.
- **Compose 1.8 rejects the file**: it predates some v2 keys. If you hit
  an "Unsupported config option" error, pin the failing key in a newer
  compose, or drop the key — most are optional.
- **`restart: unless-stopped` ignored**: older docker-compose versions
  honor `restart: always` more reliably. Swap if needed.
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
