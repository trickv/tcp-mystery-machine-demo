# Guided tour

When the student asks for a tour / overview / "what should I look at?",
walk them through these six steps **one at a time**. After each step, pause
and wait for engagement — a question, a request to dig deeper, or a prompt
to continue. The goal is a minutes-long exploration, not a data dump.

Every step: show the exact shell invocation, show the raw server output
verbatim, then explain one or two interesting things. Invite follow-ups
rather than marching through.

## Before step 1: pick `$NC`

The examples below use `"$NC"` as a placeholder for the user's netcat
invocation. Before the first step, detect the flavor and set it:

```sh
if nc -h 2>&1 | grep -q -- '-q'; then
  NC="nc -q 1"          # OpenBSD nc (most Linux)
else
  NC="nc -w 2"          # BSD nc (macOS)
fi
```

If `nc` is missing entirely, fall back to the Python one-liner from
`reference/transports.md`. Do not use `telnet`.

## Step 1 — `STATUS`

```sh
echo 'STATUS' | $NC "$VOYAGER_HOST" 4242
```

The overview. Point out:
- `MET` — Mission Elapsed Time. This ticks every query.
- `DIST` — Voyager 1 is now >170 AU from Earth; light takes ~23.5 hours one-way.
- `RTG` — power has dropped below 250W. The probe is dying slowly.
- `INST 2/9` — only MAG and PWS are still powered.
- `UPTIME` — time since the FDS reboot in 2024. Note how it differs from MET.

Ask: "Want to see which instruments are still on, or dig into the power situation first?"

## Step 2 — `DSN LINK`

```sh
echo 'DSN LINK' | $NC "$VOYAGER_HOST" 4242
```

The communications link. Point out:
- 160 bits per second down, 16 bps up. Modems in 1977 were faster than this.
- OWLT / RTLT — round-trip is ~47 hours. Sending a command and getting a reply takes two days.
- DSN station rotates by Earth rotation (Canberra / Madrid / Goldstone).

Ask: "Notice the bitrate? Want to see what that bitrate is carrying?"

## Step 3 — `INST LIST`

```sh
echo 'INST LIST' | $NC "$VOYAGER_HOST" 4242
```

Which instruments are alive. Point out:
- Only MAG and PWS remain.
- Shutdown dates read like a graveyard — IRIS 1998, PPS 1991, PLS 2007, UVS 2016, LECP 2026-04.
- Each shutdown buys a few more watts of RTG margin for the survivors.

Ask: "Want to see what MAG is actually reading right now?"

## Step 4 — `INST MAG`

```sh
echo 'INST MAG' | $NC "$VOYAGER_HOST" 4242
```

A live instrument readout. Point out:
- `B=0.42 NT` — magnetic field strength in the heliosheath. For reference, Earth's surface field is ~50,000 nT. Voyager is in an extraordinarily quiet magnetic environment.
- `NOTE APPROX` — this isn't real telemetry, it's a plausible model.

Ask: "Want to see the probe's brain? It's 70KB of memory total."

## Step 5 — `FDS MEM`

```sh
echo 'FDS MEM' | $NC "$VOYAGER_HOST" 4242
```

The Flight Data Subsystem. Point out:
- 69,632 words of 16-bit CMOS RAM. That's ~140KB. Your phone has ~100 million times this.
- The `REROUTED 2024-04-18` line: a memory chip failed in Nov 2023. Engineers spent five months finding 3% of the code a new home in the remaining working memory. At 15 billion miles.
- Try `CCS MEM` and `AACS MEM` too — those use older 18-bit plated-wire memory (literally wires physically woven through magnetic cores).

Ask: "Want to see the mission history?"

## Step 6 — `LOG 20`

```sh
echo 'LOG 20' | $NC "$VOYAGER_HOST" 4242
```

The timeline. Point out:
- 1977 launch. 1979 Jupiter. 1980 Saturn + Titan — the Titan flyby bent the trajectory north out of the ecliptic, putting Voyager on its interstellar path.
- 1990 "Pale Blue Dot" — cameras powered off afterward.
- 2012 heliopause crossing. Voyager 1 became the first human-made object in interstellar space.
- 2024 FDS recovery — the team's greatest achievement: debugging 46-year-old hardware at 46-hour round-trip latency.

End the tour: "That's the tour. `LOG 50` for more detail, or poke at any command you want. Syntax is just uppercase tokens — the server will return `?CMD` or `?SYNTAX` if you miss, and close with `?OVF` if you type a line longer than 256 bytes."

## Tour pacing rules

- One step per turn. Never batch.
- Always include the exact shell command so the student can re-run it, with `$NC` expanded to the concrete flag set (e.g. `nc -q 1` or `nc -w 2`).
- Always include the raw output verbatim before explaining.
- End each step with a question that invites direction, not a summary.
- If the student wanders off-tour, follow their lead. The tour is a default, not a script.
