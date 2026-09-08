from datetime import date

from noc_roster.spec import (
    END_DATE,
    OPERATIONAL_SHIFT_TARGET,
    PUBLIC_HOLIDAYS,
    START_DATE,
    all_dates,
    end_date_for_start,
    weekend_definitions,
)


def test_roster_date_range_is_365_days() -> None:
    dates = all_dates()
    assert dates[0] == START_DATE
    assert dates[-1] == END_DATE
    assert len(dates) == 365


def test_custom_start_date_covers_full_calendar_year() -> None:
    start_date = date(2027, 8, 1)
    dates = all_dates(start_date)
    assert dates[-1] == end_date_for_start(start_date) == date(2028, 7, 31)
    assert len(dates) == 366


def test_public_holiday_count() -> None:
    assert len(PUBLIC_HOLIDAYS) == 53
    assert date(2026, 8, 9) not in PUBLIC_HOLIDAYS
    assert date(2026, 8, 10) in PUBLIC_HOLIDAYS
    assert date(2026, 12, 25) in PUBLIC_HOLIDAYS
    assert date(2027, 1, 1) in PUBLIC_HOLIDAYS
    assert date(2030, 6, 16) not in PUBLIC_HOLIDAYS
    assert date(2030, 6, 17) in PUBLIC_HOLIDAYS
    assert date(2030, 12, 26) in PUBLIC_HOLIDAYS


def test_operational_target_math() -> None:
    total_operational_assignments = 365 * 6
    assert total_operational_assignments == 2190
    assert total_operational_assignments // 10 == OPERATIONAL_SHIFT_TARGET


def test_weekend_owner_rotation_has_full_weekends() -> None:
    weekends = weekend_definitions(all_dates())
    assert len(weekends) >= 52
    assert weekends[0].owner == "S1"
    assert weekends[1].owner == "S2"
