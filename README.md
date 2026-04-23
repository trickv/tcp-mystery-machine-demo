# v9n-voyager1-lab

A pretend Voyager 1 spacecraft computer, running on the internet at
**`voyager1.v9n.us:4242`**. It speaks a deliberately undocumented
line-based protocol over raw TCP. There's no `HELP`, no menu, no
banner longer than four words. Every wrong guess you type returns
`?CMD` or `?SYNTAX`. That is by design.

This is a **learning tool** for the V9N AI Coding Bootcamp, built
around the Claude Code Skills concept. It is not a simulator, not
a reconstruction of JPL's actual flight software, and not connected
to anything real. Think of it as what you might imagine Voyager 1's
computer does from the outside — plausible, evocative, and entirely
fictional in its details. Any number you see that looks like
telemetry is labeled `(APPROX)` for a reason.

## Try it in your browser

Open **<https://voyager1.v9n.us/>** for a terminal emulator. No install,
no netcat, no firewall arguments. Just type and see what the probe says
back. Start with `STATUS`.

## Try it from the command line

Open a socket and type commands at the `> ` prompt:

```sh
telnet voyager1.v9n.us 4242
# or
nc voyager1.v9n.us 4242
```

Type `STATUS` then Enter. Try other things. Type `QUIT` when you're
done (or Ctrl-] then `quit` to force-close telnet).

Stuck on Windows or missing a tool? See
<https://voyager1.v9n.us/connect.html> for per-OS instructions
(or the skill's imperative version at
[`skills/voyager-probe/reference/transports.md`](./skills/voyager-probe/reference/transports.md)
if you want to see how the skill itself connects — no magic).

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

   ```
   Install this Skill into the project directory: https://github.com/trickv/v9n-voyager1-lab/tree/master/skills/voyager-probe
   ```

   Accept the permission prompts.

2. Check that it loaded:

   ```
   /skills
   ```

   If `voyager-probe` doesn't show up, run `/reload-plugins`.

3. Use it. Try any of these in Claude Code:

   ```
   connect to the V9N Voyager 1 Emulator
   ```

   ```
   what is the voyager telemetry saying
   ```

   ```
   give me a tour of the voyager probe
   ```

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
