"""Command dispatcher and response templates.

Responses are lists of uppercase lines. Multi-line responses are terminated by
protocol.EOR (a single "." on its own line) at the transport layer, not here.
Single-line responses (including error codes) are returned as a one-element
list and rendered without a terminator.

Dispatch is case-insensitive; tokens are upcased before routing. Unknown
top-level commands return ?CMD; known commands with bad subcommands or args
return ?SYNTAX.
"""

from __future__ import annotations

from . import telemetry


QUIT = object()

ERR_SYNTAX = "?SYNTAX"
ERR_CMD = "?CMD"


INSTRUMENTS: dict[str, tuple[str, str, str | None, str]] = {
    "MAG":  ("MAGNETOMETER",                "ON",  None,         "B=0.42 NT HELIOSHEATH"),
    "PWS":  ("PLASMA WAVE SUBSYSTEM",       "ON",  None,         "F=2.4 KHZ AMP=3.1E-7 V/M"),
    "CRS":  ("COSMIC RAY SUBSYSTEM",        "OFF", "2025-02-25", "REASON=POWER"),
    "LECP": ("LOW-ENERGY CHARGED PARTICLE", "OFF", "2026-04-17", "REASON=POWER"),
    "UVS":  ("ULTRAVIOLET SPECTROMETER",    "OFF", "2016-04-19", "REASON=POWER"),
    "PLS":  ("PLASMA SCIENCE",              "OFF", "2007-02-01", "REASON=FAILURE"),
    "IRIS": ("INFRARED INTERFEROMETER",     "OFF", "1998-01-01", "REASON=POWER"),
    "PPS":  ("PHOTOPOLARIMETER",            "OFF", "1991-01-01", "REASON=FAILURE"),
    "PRA":  ("PLANETARY RADIO ASTRONOMY",   "OFF", "2008-02-21", "REASON=POWER"),
}


LOG_EVENTS: list[tuple[str, str]] = [
    ("1977-09-05", "LAUNCH CAPE CANAVERAL LC-41 TITAN IIIE-CENTAUR"),
    ("1979-03-05", "JUPITER CLOSEST APPROACH 349000 KM"),
    ("1980-11-12", "SATURN CLOSEST APPROACH 124000 KM"),
    ("1980-11-12", "TITAN FLYBY -- TRAJECTORY BENT NORTH OUT OF ECLIPTIC"),
    ("1990-02-14", "PALE BLUE DOT IMAGE -- CAMERA POWERED OFF AFTER"),
    ("1998-01-01", "IRIS POWERED OFF -- RTG MARGIN"),
    ("2004-12-16", "TERMINATION SHOCK CROSSED -- HELIOSHEATH ENTRY"),
    ("2012-08-25", "HELIOPAUSE CROSSED -- INTERSTELLAR SPACE"),
    ("2013-09-12", "NASA ANNOUNCES INTERSTELLAR CROSSING"),
    ("2017-11-28", "TRAJECTORY CORRECTION -- BACKUP TCM THRUSTERS REACTIVATED"),
    ("2022-05-18", "AACS TELEMETRY ANOMALY -- ATTITUDE DATA GARBLED"),
    ("2023-11-14", "FDS MEMORY FAULT -- TELEMETRY UNREADABLE"),
    ("2024-04-18", "FDS CODE RELOCATED -- ENGINEERING DATA RESTORED"),
    ("2024-06-13", "FDS FULL SCIENCE DATA RESTORED"),
    ("2025-02-25", "CRS POWERED OFF -- RTG MARGIN"),
    ("2026-04-17", "LECP POWERED OFF -- RTG MARGIN"),
]


def dispatch(tokens: list[str]):
    if not tokens:
        return []
    head, *rest = tokens
    handler = _TOP_LEVEL.get(head)
    if handler is None:
        return [ERR_CMD]
    return handler(rest)


def _cmd_status(args: list[str]):
    if args:
        return [ERR_SYNTAX]
    now = telemetry.now_utc()
    elapsed = telemetry.format_elapsed(telemetry.mission_elapsed(now))
    au = telemetry.distance_au(now)
    km = telemetry.distance_km(now)
    owlt = telemetry.format_hms(telemetry.one_way_light_time(now))
    rtg = telemetry.rtg_watts(now)
    active = sum(1 for v in INSTRUMENTS.values() if v[1] == "ON")
    total = len(INSTRUMENTS)
    station, dss = telemetry.current_dsn_station(now)
    return [
        "VGR1 STATUS",
        f"MET      {elapsed}",
        f"DIST     {au:.2f} AU   {km:.3E} KM   ~{owlt} OWLT",
        f"RTG      {rtg:.1f} W (APPROX)",
        f"INST     {active}/{total} ACTIVE",
        f"DSN      {station} {dss}",
        f"UPTIME   {elapsed}",
    ]


def _cmd_rtg(args: list[str]):
    if not args:
        return [ERR_SYNTAX]
    sub = args[0]
    if sub == "PWR" and len(args) == 1:
        now = telemetry.now_utc()
        return [
            "RTG PWR",
            f"OUTPUT   {telemetry.rtg_watts(now):.1f} W (APPROX)",
            f"DECAY    {telemetry.RTG_DECAY_W_PER_YEAR} W/YR LINEAR MODEL",
            "SRC      GPHS-RTG X3 PU-238",
            "NOTE     APPROXIMATE; NOT LIVE JPL TELEMETRY",
        ]
    return [ERR_SYNTAX]


def _cmd_inst(args: list[str]):
    if not args:
        return [ERR_SYNTAX]
    head = args[0]
    if head == "LIST" and len(args) == 1:
        lines = ["INST LIST"]
        for name, (_full, state, since, _extra) in INSTRUMENTS.items():
            if state == "ON":
                lines.append(f"{name:<5} ON")
            else:
                lines.append(f"{name:<5} OFF {since}")
        return lines
    if head in INSTRUMENTS and len(args) == 1:
        full, state, since, extra = INSTRUMENTS[head]
        if state == "ON":
            return [
                f"INST {head}",
                f"NAME     {full}",
                f"STATE    ON",
                f"READING  {extra}",
                "NOTE     APPROX",
            ]
        return [
            f"INST {head}",
            f"NAME     {full}",
            f"STATE    OFF",
            f"SINCE    {since}",
            f"{extra}",
        ]
    return [ERR_SYNTAX]


def _cmd_fds(args: list[str]):
    if not args:
        return [ERR_SYNTAX]
    sub = args[0]
    if sub == "MEM" and len(args) == 1:
        return [
            "FDS MEM",
            "TOTAL    69632 W (16-BIT)",
            "MAP      0000-3FFF  PRIMARY ROM",
            "         4000-7FFF  PRIMARY RAM",
            "         8000-BFFF  BACKUP RAM (REROUTED 2024-04-18)",
            "         C000-FFFF  SCIENCE BUFFER",
            "RELOC    3% OF CODE RELOCATED FROM FAILED CHIP 2024-04 TO 2024-06",
            "NOTE     APPROX MAP; NARRATIVE ACCURATE",
        ]
    if sub == "STATUS" and len(args) == 1:
        return [
            "FDS STATUS",
            "STATE    NOMINAL (POST-RECOVERY)",
            "REDUN    2 UNITS 16-BIT CMOS",
            "LAST ERR 2023-11-14 MEMORY CHIP FAULT",
            "RECOVER  2024-06-13 FULL SCIENCE DATA",
            "NOTE     APPROX",
        ]
    return [ERR_SYNTAX]


def _cmd_ccs(args: list[str]):
    if not args:
        return [ERR_SYNTAX]
    sub = args[0]
    if sub == "MEM" and len(args) == 1:
        return [
            "CCS MEM",
            "TOTAL    4096 W (18-BIT) PLATED-WIRE NON-VOLATILE",
            "UNITS    2 REDUNDANT",
            "ROLE     COMMAND DISPATCH + MEMORY MANAGEMENT",
            "NOTE     APPROX",
        ]
    if sub == "STATUS" and len(args) == 1:
        return [
            "CCS STATUS",
            "STATE    NOMINAL",
            "ACTIVE   UNIT A",
            "STANDBY  UNIT B",
            "NOTE     APPROX",
        ]
    return [ERR_SYNTAX]


def _cmd_aacs(args: list[str]):
    if not args:
        return [ERR_SYNTAX]
    sub = args[0]
    if sub == "MEM" and len(args) == 1:
        return [
            "AACS MEM",
            "TOTAL    4096 W (18-BIT) PLATED-WIRE NON-VOLATILE",
            "UNITS    2 REDUNDANT",
            "ROLE     ATTITUDE + ARTICULATION CONTROL",
            "NOTE     APPROX",
        ]
    if sub == "STATUS" and len(args) == 1:
        return [
            "AACS STATUS",
            "STATE    NOMINAL",
            "THRUST   BACKUP TCM (SINCE 2017-11-28)",
            "LAST ERR 2022-05-18 GARBLED ATTITUDE DATA",
            "NOTE     APPROX",
        ]
    if sub == "ATT" and len(args) == 1:
        return [
            "AACS ATT",
            "MODE     CELESTIAL REFERENCE",
            "STAR     ALPHA CENTAURI",
            "ROLL     0.02 DEG/S",
            "NOTE     APPROX",
        ]
    return [ERR_SYNTAX]


def _cmd_dsn(args: list[str]):
    if not args:
        return [ERR_SYNTAX]
    sub = args[0]
    if sub == "LINK" and len(args) == 1:
        now = telemetry.now_utc()
        station, dss = telemetry.current_dsn_station(now)
        owlt = telemetry.format_hms(telemetry.one_way_light_time(now))
        rtlt = telemetry.format_hms(telemetry.round_trip_light_time(now))
        return [
            "DSN LINK",
            f"STATION  {station} {dss} 70M",
            "DOWN     160 BPS",
            "UP       16 BPS",
            f"OWLT     {owlt}",
            f"RTLT     {rtlt}",
            "NOTE     OWLT/RTLT COMPUTED FROM DISTANCE MODEL (APPROX)",
        ]
    return [ERR_SYNTAX]


def _cmd_log(args: list[str]):
    n = 10
    if len(args) == 1:
        try:
            n = int(args[0])
        except ValueError:
            return [ERR_SYNTAX]
        if n < 1:
            return [ERR_SYNTAX]
    elif len(args) > 1:
        return [ERR_SYNTAX]
    n = min(n, len(LOG_EVENTS))
    tail = LOG_EVENTS[-n:]
    lines = ["LOG"]
    for date, text in reversed(tail):
        lines.append(f"{date}  {text}")
    return lines


def _cmd_quit(args: list[str]):
    if args:
        return [ERR_SYNTAX]
    return QUIT


_TOP_LEVEL = {
    "STATUS": _cmd_status,
    "RTG": _cmd_rtg,
    "INST": _cmd_inst,
    "FDS": _cmd_fds,
    "CCS": _cmd_ccs,
    "AACS": _cmd_aacs,
    "DSN": _cmd_dsn,
    "LOG": _cmd_log,
    "QUIT": _cmd_quit,
    "BYE": _cmd_quit,
    "LOGOUT": _cmd_quit,
}
