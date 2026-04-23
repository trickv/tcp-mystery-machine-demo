# V9N Voyager 1 Emulator

There is a Voyager 1 spacecraft emulator running at **`voyager1.v9n.us:4242`**.
It speaks a deliberately undocumented line-based protocol over raw TCP.
There's no `HELP`, no menu, no banner longer than four words.

Every wrong guess you type returns `?CMD` or `?SYNTAX`. That is by design.

## Try it yourself

If you have `nc` (netcat) handy:

```sh
echo 'STATUS' | nc -q 1 voyager1.v9n.us 4242
```

BSD nc (macOS) doesn't have `-q`; use `-w 2` instead. Classic `telnet`
works for interactive poking too, though Ctrl-] and CRLF will both bite
you eventually.

You'll get a brief status block. To find out what else to type — the
whole point is that you can't. The server won't tell you.

## The cheat sheet

The full command grammar is documented in
[`skills/voyager-probe/reference/commands.md`](./skills/voyager-probe/reference/commands.md).
Keep it open in one window, a terminal open in another, and you can
explore the probe by hand: status, instruments, memory maps, DSN link,
mission log.

Also useful:
- [`skills/voyager-probe/reference/transports.md`](./skills/voyager-probe/reference/transports.md)
  — how to talk to the server from macOS, Linux, Windows PowerShell,
  Python, and Node.
- [`skills/voyager-probe/reference/tour.md`](./skills/voyager-probe/reference/tour.md)
  — a suggested exploration order if you don't know where to start.

## Or: install the Claude Code Skill and let it do the work

Flipping between a reference doc and a terminal gets old quickly.
Instead, you can install a Claude Code Skill that knows the protocol
and drives it for you.

1. Ask your Claude Code agent:

   > Install this Skill into the project directory: https://github.com/trickv/tcp-mystery-machine-demo/tree/master/skills/voyager-probe

   Accept the permission prompts.

2. Check that it loaded:

   ```
   /skills
   ```

   If `voyager-probe` doesn't show up, run `/reload-plugins`.

3. Use it:

   > connect to the V9N Voyager 1 Emulator

   > what is the voyager telemetry saying

   > give me a tour of the voyager probe

The skill always echoes the exact shell command it used — so you
still learn the protocol while it drives.

## What's actually emulated

- Real Voyager 1 vocabulary: `FDS`, `CCS`, `AACS`, `DSN`, `RTG`, `INST`, `LOG`.
- Live-computed telemetry: distance, RTG power, one-way light time,
  current DSN tracking station all tick with the wall clock.
- The 2024 FDS memory-chip recovery story is baked into `FDS MEM` /
  `FDS STATUS` and the mission log.
- All modeled values carry `(APPROX)` or `~` — nothing here is live
  JPL downlink.

It's read-only. You can't break it. Nine instruments, ~16 mission
events, two dozen commands. Have fun.
