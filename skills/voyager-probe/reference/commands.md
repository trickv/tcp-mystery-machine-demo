# Command reference

All commands are uppercase whitespace-separated tokens. Arguments are
case-insensitive (server upcases). Unknown top-level commands return `?CMD`;
bad arguments return `?SYNTAX`. Multi-line replies end with a line containing
only `.`.

## Grammar

| Command | Args | Reply | Notes |
|---|---|---|---|
| `STATUS` | — | multi-line | mission overview |
| `RTG PWR` | — | multi-line | radioisotope power detail |
| `INST LIST` | — | multi-line | all instruments + state |
| `INST <NAME>` | `MAG` / `PWS` / `CRS` / `LECP` / `UVS` / `PLS` / `IRIS` / `PPS` / `PRA` | multi-line | per-instrument |
| `FDS MEM` | — | multi-line | Flight Data Subsystem memory map |
| `FDS STATUS` | — | multi-line | FDS state |
| `CCS MEM` | — | multi-line | Computer Command Subsystem |
| `CCS STATUS` | — | multi-line | CCS state |
| `AACS MEM` | — | multi-line | Attitude + Articulation Control |
| `AACS STATUS` | — | multi-line | AACS state |
| `AACS ATT` | — | multi-line | current attitude reference |
| `DSN LINK` | — | multi-line | DSN station + bitrates + light time |
| `LOG` | — | multi-line | last 10 events |
| `LOG <N>` | positive int | multi-line | last N events (clamped to catalog size) |
| `QUIT` / `BYE` / `LOGOUT` | — | `73 DE VGR1` | closes connection |

## Example transcripts

### STATUS

```
VGR1 STATUS
MET      48Y 08M 01D
DIST     170.22 AU   2.546E+10 KM   ~23:35:39 OWLT
RTG      248.7 W (APPROX)
INST     2/9 ACTIVE
DSN      CANBERRA DSS-43
UPTIME   48Y 08M 01D
.
```

- `MET` — mission elapsed time since 1977-09-05 launch.
- `DIST` — distance from Earth, AU + km + one-way light time.
- `RTG` — radioisotope thermoelectric generator output (APPROX).
- `INST` — count of powered instruments / total.
- `DSN` — notional tracking complex (rotates Canberra / Madrid / Goldstone by UTC hour).

### INST LIST

```
INST LIST
MAG   ON
PWS   ON
CRS   OFF 2025-02-25
LECP  OFF 2026-04-17
UVS   OFF 2016-04-19
PLS   OFF 2007-02-01
IRIS  OFF 1998-01-01
PPS   OFF 1991-01-01
PRA   OFF 2008-02-21
.
```

### INST MAG (on)

```
INST MAG
NAME     MAGNETOMETER
STATE    ON
READING  B=0.42 NT HELIOSHEATH
NOTE     APPROX
.
```

### INST CRS (off)

```
INST CRS
NAME     COSMIC RAY SUBSYSTEM
STATE    OFF
SINCE    2025-02-25
REASON=POWER
.
```

### FDS MEM (the 2024 recovery story)

```
FDS MEM
TOTAL    69632 W (16-BIT)
MAP      0000-3FFF  PRIMARY ROM
         4000-7FFF  PRIMARY RAM
         8000-BFFF  BACKUP RAM (REROUTED 2024-04-18)
         C000-FFFF  SCIENCE BUFFER
RELOC    3% OF CODE RELOCATED FROM FAILED CHIP 2024-04 TO 2024-06
NOTE     APPROX MAP; NARRATIVE ACCURATE
.
```

### DSN LINK

```
DSN LINK
STATION  CANBERRA DSS-43 70M
DOWN     160 BPS
UP       16 BPS
OWLT     23:35:39
RTLT     47:11:18
NOTE     OWLT/RTLT COMPUTED FROM DISTANCE MODEL (APPROX)
.
```

### LOG 5

```
LOG
2026-04-17  LECP POWERED OFF -- RTG MARGIN
2025-02-25  CRS POWERED OFF -- RTG MARGIN
2024-06-13  FDS FULL SCIENCE DATA RESTORED
2024-04-18  FDS CODE RELOCATED -- ENGINEERING DATA RESTORED
2023-11-14  FDS MEMORY FAULT -- TELEMETRY UNREADABLE
.
```

## Errors

| Code | Meaning |
|---|---|
| `?CMD` | unknown top-level command |
| `?SYNTAX` | known command, bad args |
| `?BUSY` | server at 200-connection cap; closed |
| `?OVF` | input line > 256 bytes; closed |
| `?TIMEOUT` | 120s idle; closed |

Every modeled field (distance, RTG watts, OWLT/RTLT, readings) carries
`(APPROX)` or `~`. Nothing in this server is live JPL telemetry.
