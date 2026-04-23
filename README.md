# tcp-mystery-machine-demo

A Voyager 1 emulator TCP server for the V9N AI Coding Bootcamp Claude Skills
demo. The server speaks a deliberately undocumented line-based protocol on
port 4242. No `HELP`, no menu, no navigation hints — every wrong guess
returns `?CMD` or `?SYNTAX`. A paired Claude Code Skill ships the protocol
manual and walks students through exploring the probe.

## Quickstart (local)

```sh
python3 -m server          # listens on 0.0.0.0:4242
echo 'STATUS' | nc -q 1 localhost 4242
```

## Docker

```sh
docker-compose up -d --build      # or: docker compose up -d --build
echo 'STATUS' | nc -q 1 localhost 4242
docker-compose down
```

## Deploy to VPS

See [DEPLOY.md](./DEPLOY.md).

## The Claude Code Skill

1. Ask your Claude Code agent:

   > Install this Skill into the project directory: https://github.com/trickv/tcp-mystery-machine-demo/tree/master/skills/voyager-probe

   Claude will fetch the skill files and drop them in your project's
   `.claude/skills/voyager-probe/`. **Accept the permission prompts** as
   they appear (writing files, reading the repo tree).

2. Check that it loaded:

   ```
   /skills
   ```

   You should see `voyager-probe` in the list. If not, run:

   ```
   /reload-plugins
   ```

3. Use it. Prompt Claude with anything like:

   > connect to the V9N Voyager 1 Emulator

   > what is the voyager telemetry saying

   > give me a tour of the voyager probe

The skill lives in [`skills/voyager-probe/`](./skills/voyager-probe/). Its
command reference is [`reference/commands.md`](./skills/voyager-probe/reference/commands.md),
transport options are [`reference/transports.md`](./skills/voyager-probe/reference/transports.md),
and the guided tour is [`reference/tour.md`](./skills/voyager-probe/reference/tour.md).

## Protocol (abridged)

- Plaintext TCP, CRLF-delimited, port 4242.
- Banner on connect: `VGR1 FDS READY`, then prompt `> `.
- Multi-line replies terminated by a line containing only `.` (SMTP-style).
- Error codes: `?CMD`, `?SYNTAX`, `?BUSY`, `?OVF`, `?TIMEOUT`.
- Everything is read-only and computed live from the system clock
  (distance, RTG watts, light time). Modeled values carry `(APPROX)`.

Full grammar in the skill's command reference. Commands are not documented
here on purpose.

## Layout

```
server/          asyncio listener + protocol + telemetry + dispatcher
skills/          Claude Code skill (the protocol manual)
Dockerfile
docker-compose.yml
DEPLOY.md
```
