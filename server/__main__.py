"""Entrypoint: python -m server"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from . import server


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"invalid {name}={raw!r}; expected int", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
    )
    host = os.environ.get("VOYAGER_HOST_BIND", "0.0.0.0")
    port = _env_int("VOYAGER_PORT", 4242)
    max_conn = _env_int("VOYAGER_MAX_CONN", 200)
    idle_timeout = _env_int("VOYAGER_IDLE_TIMEOUT", 120)
    max_line = _env_int("VOYAGER_MAX_LINE", 256)
    try:
        asyncio.run(server.run(host, port, max_conn, float(idle_timeout), max_line))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
