"""Line-oriented protocol: banner, prompt, framing, error codes, session loop."""

from __future__ import annotations

import asyncio
import logging

from . import commands


BANNER = "VGR1 FDS READY"
PROMPT = b"> "
EOR = "."

ERR_BUSY = "?BUSY"
ERR_OVF = "?OVF"
ERR_TIMEOUT = "?TIMEOUT"

_log = logging.getLogger("voyager.protocol")


class LineOverflow(Exception):
    pass


class IdleTimeout(Exception):
    pass


class ConnectionClosed(Exception):
    pass


async def write_line(writer: asyncio.StreamWriter, line: str) -> None:
    writer.write(line.encode("ascii", errors="replace") + b"\r\n")
    await writer.drain()


async def write_block(writer: asyncio.StreamWriter, lines: list[str]) -> None:
    for line in lines:
        writer.write(line.encode("ascii", errors="replace") + b"\r\n")
    writer.write(EOR.encode("ascii") + b"\r\n")
    await writer.drain()


async def _write_prompt(writer: asyncio.StreamWriter) -> None:
    writer.write(PROMPT)
    await writer.drain()


async def read_line(
    reader: asyncio.StreamReader,
    max_line: int,
    idle_timeout: float,
) -> str:
    try:
        raw = await asyncio.wait_for(reader.readuntil(b"\n"), timeout=idle_timeout)
    except asyncio.TimeoutError:
        raise IdleTimeout()
    except asyncio.IncompleteReadError:
        raise ConnectionClosed()
    except (asyncio.LimitOverrunError, ValueError):
        raise LineOverflow()
    if len(raw) > max_line:
        raise LineOverflow()
    stripped = raw.rstrip(b"\r\n")
    return stripped.decode("ascii", errors="replace")


async def session(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    conn_id: int,
    idle_timeout: float,
    max_line: int,
) -> None:
    await write_line(writer, BANNER)
    await _write_prompt(writer)
    while True:
        try:
            line = await read_line(reader, max_line, idle_timeout)
        except IdleTimeout:
            await _safe_write_line(writer, ERR_TIMEOUT)
            return
        except LineOverflow:
            await _safe_write_line(writer, ERR_OVF)
            return
        except ConnectionClosed:
            return

        tokens = line.upper().split()
        result = commands.dispatch(tokens)

        if result is commands.QUIT:
            await write_line(writer, "73 DE VGR1")
            return

        if not result:
            await _write_prompt(writer)
            continue

        if len(result) == 1:
            await write_line(writer, result[0])
        else:
            await write_block(writer, result)

        await _write_prompt(writer)


async def _safe_write_line(writer: asyncio.StreamWriter, line: str) -> None:
    try:
        await write_line(writer, line)
    except Exception:
        pass
