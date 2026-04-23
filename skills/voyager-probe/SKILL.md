---
name: voyager-probe
description: Connect to and query the Voyager 1 TCP emulator (aka TCP Mystery Machine) at VOYAGER_HOST:4242. Use when the user asks to connect to the voyager probe, talk to the voyager server, query the tcp mystery machine, check voyager telemetry, or anything about VGR1 / FDS / DSN / RTG over raw TCP.
allowed-tools:
  - Bash
  - Read
---

# Voyager Probe (TCP Mystery Machine)

A raw TCP, plaintext, line-oriented server emulating the Voyager 1 spacecraft
computer. There is no `HELP`, no `?`, no menu. This skill is the protocol
manual. Use it whenever the user wants to talk to VGR1 / the voyager probe /
the tcp mystery machine.

## Server coordinates

- Host: `$VOYAGER_HOST` (fallback `voyager.example.com`).
- Port: `4242`.
- Protocol: plaintext TCP, CRLF line endings.
- Connect-time banner: `VGR1 FDS READY`, followed by prompt `> `.

## Response framing (how to parse)

- **Single-line reply**: one line, CRLF, then the prompt `> `. Includes all
  error codes.
- **Multi-line reply**: lines CRLF, terminated by a line containing just `.`
  (single dot) CRLF. SMTP-style terminator.
- **Error codes**:
  - `?CMD` — unknown top-level command.
  - `?SYNTAX` — known command, bad arguments.
  - `?BUSY` — server at connection cap; connection closed.
  - `?OVF` — input line too long; connection closed.
  - `?TIMEOUT` — idle disconnect.

All server output is uppercase. Commands are upcased before parsing.

## Transport selection

Always use **one-shot** queries (send command → read until `.` or quiet →
close). Never hold a socket open waiting for multiple commands unless running
a guided tour batch.

Priority order for sending a command:

1. `nc` — detect flavor first (see `reference/transports.md`).
2. `ncat` (nmap).
3. `python3 -c` one-liner.
4. `node -e` one-liner.

Concrete invocations live in `reference/transports.md`. Read that file when
picking the transport or if the first choice fails.

## Educational contract (hard rule)

Every reply to the student must include the exact shell command used, so
they can reproduce it themselves. Format:

```
I ran:
    echo 'STATUS' | nc -q 1 "$VOYAGER_HOST" 4242

Response:
    VGR1 FDS READY
    > VGR1 STATUS
    MET      48Y 08M 01D
    ...
    .
```

Don't paraphrase the raw response on the first pass — show it verbatim, then
explain. Students should see the protocol warts and all.

## Commands

See `reference/commands.md` for the full grammar. Don't invent commands; if
uncertain, look it up. Quick list:

- `STATUS` — overview (MET, distance, RTG, instrument count, DSN station).
- `RTG PWR` — detailed RTG output.
- `INST LIST` — all 9 instruments and state.
- `INST <NAME>` — detail for MAG / PWS / CRS / LECP / UVS / PLS / IRIS / PPS / PRA.
- `FDS MEM` / `FDS STATUS` — Flight Data Subsystem (16-bit CMOS, 2024 recovery).
- `CCS MEM` / `CCS STATUS` — Computer Command Subsystem (18-bit plated wire).
- `AACS MEM` / `AACS STATUS` / `AACS ATT` — Attitude control.
- `DSN LINK` — current Deep Space Network link stats.
- `LOG [n]` — last `n` mission events (default 10).
- `QUIT` / `BYE` / `LOGOUT` — close.

## Guided tour

When the student asks "what should I look at?" or "show me around", follow
`reference/tour.md`. One step at a time — do not dump every command at once.
The student should spend minutes, not seconds, poking at this. Wait for
engagement between steps.

## Anti-patterns

- Do **not** send `HELP`, `?`, `MENU`, `COMMANDS`. They return `?CMD` — the
  server deliberately refuses to document itself.
- Do **not** open interactive `telnet` or hold sockets open across turns.
- Do **not** hallucinate command names. If unsure, consult
  `reference/commands.md`.
- Do **not** assume numeric values are real JPL telemetry. Fields marked
  `(APPROX)` or `~` are modeled from simple decay curves, not downlink.
