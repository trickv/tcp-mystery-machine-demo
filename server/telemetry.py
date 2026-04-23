"""Live-computed Voyager 1 telemetry.

All values are computed from the system clock plus hard-coded anchor constants.
No network, no filesystem, no subprocess. If datetime.now() works, this works.

Constants are approximations. Distance grows linearly at ~3.6 AU/year (actual
heliocentric velocity of Voyager 1). RTG output decays roughly linearly at
~4.8 W/year over short timescales (true decay is exponential per Pu-238
half-life plus load-dependent thermocouple degradation, but linear is fine for
a demo that ticks over minutes or hours).

Anchors are pinned to 2026-04-01 so the numbers match public status pages
around that time. Over a bootcamp-length session the values drift visibly but
remain plausible.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


LAUNCH_EPOCH = datetime(1977, 9, 5, 12, 56, 0, tzinfo=timezone.utc)

DISTANCE_ANCHOR_DATE = datetime(2026, 4, 1, tzinfo=timezone.utc)
DISTANCE_ANCHOR_AU = 170.0
DISTANCE_RATE_AU_PER_YEAR = 3.6

RTG_ANCHOR_DATE = datetime(2026, 4, 1, tzinfo=timezone.utc)
RTG_ANCHOR_WATTS = 249.0
RTG_DECAY_W_PER_YEAR = 4.8

LIGHT_SECONDS_PER_AU = 499.0
AU_KM = 149_597_870.7

_SECONDS_PER_YEAR = 365.25 * 86400.0


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def mission_elapsed(now: datetime) -> timedelta:
    return now - LAUNCH_EPOCH


def distance_au(now: datetime) -> float:
    years = (now - DISTANCE_ANCHOR_DATE).total_seconds() / _SECONDS_PER_YEAR
    return DISTANCE_ANCHOR_AU + DISTANCE_RATE_AU_PER_YEAR * years


def distance_km(now: datetime) -> float:
    return distance_au(now) * AU_KM


def rtg_watts(now: datetime) -> float:
    years = (now - RTG_ANCHOR_DATE).total_seconds() / _SECONDS_PER_YEAR
    return RTG_ANCHOR_WATTS - RTG_DECAY_W_PER_YEAR * years


def one_way_light_time(now: datetime) -> timedelta:
    seconds = distance_au(now) * LIGHT_SECONDS_PER_AU
    return timedelta(seconds=seconds)


def round_trip_light_time(now: datetime) -> timedelta:
    return 2 * one_way_light_time(now)


def format_hms(td: timedelta) -> str:
    total = int(td.total_seconds())
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_elapsed(td: timedelta) -> str:
    # Approximate Y/M/D breakdown. Months are 30-day, years are 365-day —
    # imprecise but readable; exact calendar math isn't needed for a teleprinter
    # readout.
    total_days = int(td.total_seconds() // 86400)
    years, rem = divmod(total_days, 365)
    months, days = divmod(rem, 30)
    return f"{years:02d}Y {months:02d}M {days:02d}D"


def current_dsn_station(now: datetime) -> tuple[str, str]:
    # Rotate by UTC hour across the three DSN complexes. Canberra is the real
    # primary for Voyager 1 (southern declination), but rotating reads better
    # for a demo.
    hour = now.hour
    if hour < 8:
        return ("CANBERRA", "DSS-43")
    if hour < 16:
        return ("MADRID", "DSS-63")
    return ("GOLDSTONE", "DSS-14")
