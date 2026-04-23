"""Asyncio TCP listener with a hard connection cap and graceful shutdown.

The cap is enforced with a plain counter on the State class. Asyncio is
single-threaded cooperative, so no lock is required. The 201st concurrent
connection gets ?BUSY and an immediate close -- never queued -- so callers
see rejection rather than a hang.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import signal

from . import protocol


_log = logging.getLogger("voyager.server")


class State:
    active: int = 0


_active_tasks: set[asyncio.Task] = set()
_active_writers: set[asyncio.StreamWriter] = set()
_conn_ids = itertools.count(1)


def _truncate_peer(peer) -> str:
    if not peer:
        return "?"
    host = peer[0]
    if ":" in host:
        return "[redacted-v6]"
    parts = host.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + ".x"
    return host


async def _handle_factory(max_conn: int, idle_timeout: float, max_line: int):
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        conn_id = next(_conn_ids)
        peer = _truncate_peer(writer.get_extra_info("peername"))

        if State.active >= max_conn:
            _log.info("conn_id=%s peer=%s REJECT cap=%d", conn_id, peer, max_conn)
            try:
                writer.write(f"{protocol.ERR_BUSY}\r\n".encode("ascii"))
                await writer.drain()
            except Exception:
                pass
            _close_quietly(writer)
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return

        State.active += 1
        _log.info("conn_id=%s peer=%s OPEN active=%d", conn_id, peer, State.active)
        task = asyncio.current_task()
        if task is not None:
            _active_tasks.add(task)
        _active_writers.add(writer)

        try:
            await protocol.session(reader, writer, conn_id, idle_timeout, max_line)
        except (ConnectionError, BrokenPipeError, OSError) as exc:
            _log.info("conn_id=%s peer=%s disconnect: %s", conn_id, peer, exc)
        except Exception:
            _log.exception("conn_id=%s unhandled error", conn_id)
        finally:
            State.active -= 1
            if task is not None:
                _active_tasks.discard(task)
            _active_writers.discard(writer)
            _log.info("conn_id=%s CLOSE active=%d", conn_id, State.active)
            _close_quietly(writer)
            try:
                await writer.wait_closed()
            except Exception:
                pass

    return handle


def _close_quietly(writer: asyncio.StreamWriter) -> None:
    try:
        writer.close()
    except Exception:
        pass


async def _broadcast_shutdown() -> None:
    for writer in list(_active_writers):
        try:
            writer.write(f"{protocol.ERR_SHUTDOWN}\r\n".encode("ascii"))
        except Exception:
            pass
    for writer in list(_active_writers):
        _close_quietly(writer)


async def run(
    host: str,
    port: int,
    max_conn: int,
    idle_timeout: float,
    max_line: int,
) -> None:
    loop = asyncio.get_running_loop()
    shutdown = asyncio.Event()

    def _signal_shutdown():
        _log.info("shutdown signal received")
        shutdown.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _signal_shutdown)
        except NotImplementedError:
            pass

    handle = await _handle_factory(max_conn, idle_timeout, max_line)
    server = await asyncio.start_server(
        handle, host, port, limit=max_line + 2
    )

    bind_addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    _log.info(
        "listening on %s (max_conn=%d idle_timeout=%.0fs max_line=%d)",
        bind_addrs, max_conn, idle_timeout, max_line,
    )

    async with server:
        await shutdown.wait()
        _log.info("draining %d active connection(s)", State.active)
        server.close()
        await server.wait_closed()
        # Nudge active sessions to end: send ?SHUTDOWN, close their writers.
        # Each session's next readuntil() unblocks with IncompleteReadError
        # and its handler returns via the finally clause.
        await _broadcast_shutdown()
        if _active_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*_active_tasks, return_exceptions=True),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                _log.warning("drain timeout; %d task(s) still active", len(_active_tasks))
    _log.info("shutdown complete")
