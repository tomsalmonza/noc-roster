from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple

START_DATE = date(2026, 8, 1)
END_DATE = date(2027, 7, 31)

EMPLOYEES = [f"S{i}" for i in range(1, 11)]
GROUP_A = [f"S{i}" for i in range(1, 6)]
GROUP_B = [f"S{i}" for i in range(6, 11)]

ASSIGNMENTS = ["M", "A", "N", "SB", "OFF"]
OPERATIONAL = ["M", "A", "N"]
WORKED = ["M", "A", "N"]

WEEKEND_OWNER_ROTATION = [f"S{i}" for i in range(1, 11)]

PUBLIC_HOLIDAYS: Dict[date, str] = {
    date(2026, 8, 10): "National Women's Day (Observed)",
    date(2026, 9, 24): "Heritage Day",
    date(2026, 12, 16): "Day of Reconciliation",
    date(2026, 12, 25): "Christmas Day",
    date(2026, 12, 26): "Day of Goodwill",
    date(2027, 1, 1): "New Year's Day",
    date(2027, 3, 22): "Human Rights Day (Observed)",
    date(2027, 3, 26): "Good Friday",
    date(2027, 3, 29): "Family Day",
    date(2027, 4, 27): "Freedom Day",
    date(2027, 5, 1): "Workers' Day",
    date(2027, 6, 16): "Youth Day",
}

PREMIUM_HOLIDAYS = {
    date(2026, 12, 25),
    date(2026, 12, 26),
    date(2027, 1, 1),
}

HOLIDAY_SCORES = {
    "standard": 10,
    "goodwill": 15,
    "christmas": 20,
    "newyear": 20,
}

STANDARD_SHIFT_WEIGHTS = {
    "M": 10,
    "A": 10,
    "N": 12,
    "SB": 0,
    "OFF": 0,
}

PUBLIC_HOLIDAY_SHIFT_WEIGHTS = {
    "M": 13,
    "A": 13,
    "N": 15,
}

CHRISTMAS_SHIFT_WEIGHTS = {
    "M": 18,
    "A": 18,
    "N": 20,
}

NEWYEAR_SHIFT_WEIGHTS = {
    "M": 18,
    "A": 18,
    "N": 20,
}

PAID_SHIFT_TARGET = 260
LEAVE_EQUIVALENTS = 41
OPERATIONAL_SHIFT_TARGET = 219

# Temporary December Shift removal
TEMPORARY_SHIFT_REMOVAL_START = date(2026, 12, 20)
TEMPORARY_SHIFT_REMOVAL_END = date(2027, 1, 4)


@dataclass(frozen=True)
class WeekendDefinition:
    weekend_number: int
    saturday_idx: int
    sunday_idx: int
    owner: str


def all_dates() -> List[date]:
    out: List[date] = []
    current = START_DATE
    while current <= END_DATE:
        out.append(current)
        current += timedelta(days=1)
    return out


# Temporary December Shift removal
def is_temporary_shift_removal_day(day: date) -> bool:
    return TEMPORARY_SHIFT_REMOVAL_START <= day <= TEMPORARY_SHIFT_REMOVAL_END


def date_index_map(dates: List[date]) -> Dict[date, int]:
    return {d: idx for idx, d in enumerate(dates)}


def holiday_score_for_day(day: date) -> int:
    if day == date(2026, 12, 25):
        return HOLIDAY_SCORES["christmas"]
    if day == date(2026, 12, 26):
        return HOLIDAY_SCORES["goodwill"]
    if day == date(2027, 1, 1):
        return HOLIDAY_SCORES["newyear"]
    if day in PUBLIC_HOLIDAYS:
        return HOLIDAY_SCORES["standard"]
    return 0


def shift_weight_for_day(day: date, shift: str) -> int:
    if shift not in OPERATIONAL:
        return 0
    if day == date(2026, 12, 25):
        return CHRISTMAS_SHIFT_WEIGHTS[shift]
    if day == date(2027, 1, 1):
        return NEWYEAR_SHIFT_WEIGHTS[shift]
    if day in PUBLIC_HOLIDAYS:
        return PUBLIC_HOLIDAY_SHIFT_WEIGHTS[shift]
    return STANDARD_SHIFT_WEIGHTS[shift]


def weekend_definitions(dates: List[date]) -> List[WeekendDefinition]:
    weekends: List[WeekendDefinition] = []
    sat_idx = None
    for idx, d in enumerate(dates):
        if d.weekday() == 5:
            sat_idx = idx
            sun_idx = idx + 1
            if sun_idx < len(dates) and dates[sun_idx].weekday() == 6:
                weekend_no = len(weekends) + 1
                owner = WEEKEND_OWNER_ROTATION[(weekend_no - 1) % len(WEEKEND_OWNER_ROTATION)]
                weekends.append(
                    WeekendDefinition(
                        weekend_number=weekend_no,
                        saturday_idx=sat_idx,
                        sunday_idx=sun_idx,
                        owner=owner,
                    )
                )
    return weekends


def ten_week_cycles(weekends: List[WeekendDefinition]) -> List[List[WeekendDefinition]]:
    cycles: List[List[WeekendDefinition]] = []
    for i in range(0, len(weekends), 10):
        cycles.append(weekends[i : i + 10])
    return cycles


def holiday_name(day: date) -> str:
    return PUBLIC_HOLIDAYS.get(day, "")


def day_name(day: date) -> str:
    return day.strftime("%A")


def quarter_for_date(day: date) -> str:
    if day.month in (8, 9, 10):
        return "Q1"
    if day.month in (11, 12, 1):
        return "Q2"
    if day.month in (2, 3, 4):
        return "Q3"
    return "Q4"


def pairing_keys() -> List[Tuple[str, str]]:
    return [(a, b) for a in GROUP_A for b in GROUP_B]
