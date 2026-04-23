"""WebSocket-to-TCP bridge for the V9N Voyager 1 Emulator.

Serves:
  GET /           -> web/index.html
  GET /<file>     -> web/<file>   (static assets; no directory traversal)
  WS  /ws         -> bidirectional relay to the TCP server at
                     (BRIDGE_TCP_HOST, BRIDGE_TCP_PORT)

Bytes received from the browser are written to the TCP socket verbatim;
bytes received from the TCP socket are forwarded to the browser as binary
WebSocket frames. No framing interpretation happens here -- the terminal
in the browser parses the protocol the same way any other client would.

Stdlib only except for `websockets` (single PyPI dep).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import mimetypes
import os
import socket
import sys
from pathlib import Path

from websockets.asyncio.server import serve as ws_serve
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Response


WEB_DIR = Path(__file__).resolve().parent.parent / "web"

_log = logging.getLogger("voyager.bridge")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"invalid {name}={raw!r}; expected int", file=sys.stderr)
        sys.exit(2)


def _not_found() -> Response:
    body = b"not found\n"
    headers = Headers([
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(body))),
    ])
    return Response(404, "Not Found", headers=headers, body=body)


def _serve_static(path: str) -> Response:
    if path in ("", "/"):
        path = "/index.html"
    # Resolve against WEB_DIR and confirm the result stays inside it.
    rel = path.lstrip("/")
    target = (WEB_DIR / rel).resolve()
    try:
        target.relative_to(WEB_DIR)
    except ValueError:
        return _not_found()
    if not target.is_file():
        return _not_found()
    ctype, _ = mimetypes.guess_type(target.name)
    if ctype is None:
        ctype = "application/octet-stream"
    body = target.read_bytes()
    headers = Headers([
        ("Content-Type", ctype),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-cache"),
    ])
    return Response(200, "OK", headers=headers, body=body)


async def _process_request(connection, request):
    """Intercept non-WS requests and serve static files."""
    # Normal WS upgrade requests carry Upgrade: websocket -- let them through.
    if (request.headers.get("Upgrade") or "").lower() == "websocket":
        if request.path == "/ws":
            return None  # proceed with WS handshake
        return _not_found()
    # Everything else is a static GET.
    return _serve_static(request.path)


async def _relay(tcp_ip: str, tcp_port: int, ws) -> None:
    """Connect to the TCP server and pump bytes both directions.

    `tcp_ip` is already a numeric address (pre-resolved at startup), so
    asyncio skips the thread-backed DNS path entirely. This matters on
    low-ulimit hosts where spawning a getaddrinfo thread fails with
    "can't start new thread".
    """
    try:
        reader, writer = await asyncio.open_connection(tcp_ip, tcp_port)
    except OSError as exc:
        try:
            await ws.send(f"?BRIDGE_UPSTREAM_DOWN {exc}\r\n".encode())
        except Exception:
            pass
        await ws.close(code=1011, reason="upstream unreachable")
        return

    peer = ws.remote_address
    _log.info("bridge OPEN ws=%s tcp=%s:%d", peer, tcp_ip, tcp_port)

    async def tcp_to_ws():
        try:
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                await ws.send(chunk)
        except (ConnectionClosed, OSError):
            pass

    async def ws_to_tcp():
        try:
            async for msg in ws:
                if isinstance(msg, str):
                    msg = msg.encode("utf-8", errors="replace")
                writer.write(msg)
                await writer.drain()
        except (ConnectionClosed, OSError):
            pass

    t1 = asyncio.create_task(tcp_to_ws())
    t2 = asyncio.create_task(ws_to_tcp())
    done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in pending:
        try:
            await task
        except Exception:
            pass
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    try:
        await ws.close()
    except Exception:
        pass
    _log.info("bridge CLOSE ws=%s", peer)


async def run(host: str, port: int, tcp_ip: str, tcp_port: int) -> None:
    # Replace the default unbounded ThreadPoolExecutor with a small one so
    # accidental thread-path calls can't blow through the host's nproc limit.
    loop = asyncio.get_running_loop()
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=4))

    async def handler(ws):
        await _relay(tcp_ip, tcp_port, ws)

    async with ws_serve(
        handler,
        host,
        port,
        process_request=_process_request,
        max_size=4096,
    ) as server:
        _log.info(
            "listening on %s:%d (upstream %s:%d, static %s)",
            host, port, tcp_ip, tcp_port, WEB_DIR,
        )
        await server.serve_forever()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
    )
    host = os.environ.get("BRIDGE_HOST_BIND", "0.0.0.0")
    port = _env_int("BRIDGE_PORT", 8428)
    tcp_host = os.environ.get("BRIDGE_TCP_HOST", "127.0.0.1")
    tcp_port = _env_int("BRIDGE_TCP_PORT", 4242)

    # Resolve the upstream synchronously once, up-front. Avoids asyncio's
    # thread-backed getaddrinfo per connection (which is fatal when the
    # host's nproc ulimit is low). If resolution fails, fail loudly at
    # startup rather than on the first student connection.
    try:
        infos = socket.getaddrinfo(tcp_host, tcp_port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        print(f"bridge: cannot resolve BRIDGE_TCP_HOST={tcp_host!r}: {exc}", file=sys.stderr)
        sys.exit(2)
    tcp_ip = infos[0][4][0]
    if tcp_ip != tcp_host:
        print(f"bridge: resolved {tcp_host} -> {tcp_ip}", file=sys.stderr)

    try:
        asyncio.run(run(host, port, tcp_ip, tcp_port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
