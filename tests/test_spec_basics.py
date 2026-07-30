from datetime import date

from noc_roster.spec import (
    END_DATE,
    OPERATIONAL_SHIFT_TARGET,
    PUBLIC_HOLIDAYS,
    START_DATE,
    all_dates,
    weekend_definitions,
)


def test_roster_date_range_is_365_days() -> None:
    dates = all_dates()
    assert dates[0] == START_DATE
    assert dates[-1] == END_DATE
    assert len(dates) == 365


def test_public_holiday_count() -> None:
    assert len(PUBLIC_HOLIDAYS) == 12
    assert date(2026, 12, 25) in PUBLIC_HOLIDAYS
    assert date(2027, 1, 1) in PUBLIC_HOLIDAYS


def test_operational_target_math() -> None:
    total_operational_assignments = 365 * 6
    assert total_operational_assignments == 2190
    assert total_operational_assignments // 10 == OPERATIONAL_SHIFT_TARGET


def test_weekend_owner_rotation_has_full_weekends() -> None:
    weekends = weekend_definitions(all_dates())
    assert len(weekends) >= 52
    assert weekends[0].owner == "S1"
    assert weekends[1].owner == "S2"
