from datetime import date

from noc_roster.spec import (
    END_DATE,
    EMPLOYEES,
    MAX_ACTUAL_FULL_WEEKEND_OFF_RANGE,
    OPERATIONAL_SHIFT_TARGET,
    PUBLIC_HOLIDAYS,
    START_DATE,
    all_dates,
    weekend_definitions,
)
from noc_roster.validator import validate_roster


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


def test_actual_full_weekends_off_must_be_within_two() -> None:
    dates = all_dates()
    weekends = weekend_definitions(dates)
    assignments = {(day, employee): "M" for day in dates for employee in EMPLOYEES}

    for weekend in weekends[:5]:
        for employee in EMPLOYEES:
            assignments[(dates[weekend.saturday_idx], employee)] = "OFF"
            assignments[(dates[weekend.sunday_idx], employee)] = "OFF"
    for weekend in weekends[5:7]:
        for employee in [EMPLOYEES[0]]:
            assignments[(dates[weekend.saturday_idx], employee)] = "OFF"
            assignments[(dates[weekend.sunday_idx], employee)] = "OFF"

    boundary_report = validate_roster(assignments)

    assert MAX_ACTUAL_FULL_WEEKEND_OFF_RANGE == 2
    assert boundary_report.employee_summary["S1"]["Actual Full Weekends Off"] == 7
    assert boundary_report.employee_summary["S10"]["Actual Full Weekends Off"] == 5
    assert not any(v.rule == "Actual Full Weekend Off Balance" for v in boundary_report.hard_violations)

    for weekend in weekends[7:10]:
        assignments[(dates[weekend.saturday_idx], EMPLOYEES[0])] = "OFF"
        assignments[(dates[weekend.sunday_idx], EMPLOYEES[0])] = "OFF"

    report = validate_roster(assignments)

    assert report.employee_summary["S1"]["Actual Full Weekends Off"] == 10
    assert report.employee_summary["S10"]["Actual Full Weekends Off"] == 5
    assert any(v.rule == "Actual Full Weekend Off Balance" for v in report.hard_violations)
