from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import Dict, List, Tuple

from .spec import (
    EMPLOYEES,
    GROUP_A,
    GROUP_B,
    LEAVE_EQUIVALENTS,
    OPERATIONAL,
    OPERATIONAL_SHIFT_TARGET,
    PAID_SHIFT_TARGET,
    PREMIUM_HOLIDAYS,
    PUBLIC_HOLIDAYS,
    all_dates,
    holiday_score_for_day,
    pairing_keys,
    shift_weight_for_day,
    ten_week_cycles,
    weekend_definitions,
)


@dataclass
class Violation:
    rule: str
    day: date | None
    employee: str | None
    description: str
    severity: str
    penalty: float
    resolution: str


@dataclass
class ValidationReport:
    hard_passed: bool
    hard_violations: List[Violation]
    soft_violations: List[Violation]
    employee_summary: Dict[str, Dict[str, float]]
    pairing_matrix: Dict[Tuple[str, str], int]
    fairness_index: float
    fairness_rating: str
    rqs: float
    rqs_rating: str
    metrics: Dict[str, float]


def _employee_group(employee: str) -> str:
    return "A" if employee in GROUP_A else "B"


def _rating(score: float, bins: List[Tuple[int, str]]) -> str:
    for threshold, label in bins:
        if score >= threshold:
            return label
    return bins[-1][1]


def _pairs_for_day_shift(day_assignments: Dict[str, str], shift: str) -> Tuple[str, str]:
    a = [e for e in GROUP_A if day_assignments[e] == shift]
    b = [e for e in GROUP_B if day_assignments[e] == shift]
    if len(a) == 1 and len(b) == 1:
        return a[0], b[0]
    return "", ""


def validate_roster(assignments: Dict[Tuple[date, str], str]) -> ValidationReport:
    dates = all_dates()
    by_day: Dict[date, Dict[str, str]] = {d: {} for d in dates}
    for (d, e), s in assignments.items():
        by_day[d][e] = s

    hard_violations: List[Violation] = []
    soft_violations: List[Violation] = []

    employee_summary: Dict[str, Dict[str, float]] = {
        e: {
            "Morning Shifts": 0,
            "Afternoon Shifts": 0,
            "Night Shifts": 0,
            "Operational Shifts": 0,
            "Standby Assignments": 0,
            "Off Assignments": 0,
            "Paid Shift Target": PAID_SHIFT_TARGET,
            "Leave Equivalents": LEAVE_EQUIVALENTS,
            "Weekend Operational Shifts": 0,
            "Designated Full Weekends Off": 0,
            "Actual Full Weekends Off": 0,
            "Public Holidays Worked": 0,
            "Premium Holidays Worked": 0,
            "Holiday Worked Score": 0,
            "Shift Weight Score": 0,
            "Pairing Diversity Score": 0,
            "RQS Penalty Total": 0,
        }
        for e in EMPLOYEES
    }

    pairing_matrix = {k: 0 for k in pairing_keys()}

    # Hard: every employee exactly one assignment each day.
    for d in dates:
        assigned_employees = by_day[d].keys()
        if set(assigned_employees) != set(EMPLOYEES):
            hard_violations.append(
                Violation(
                    rule="Daily Assignment",
                    day=d,
                    employee=None,
                    description="Not all employees have assignments.",
                    severity="Hard",
                    penalty=0,
                    resolution="Regenerate roster with complete daily coverage.",
                )
            )

        for e in EMPLOYEES:
            s = by_day[d].get(e)
            if s is None:
                continue
            if s == "M":
                employee_summary[e]["Morning Shifts"] += 1
                employee_summary[e]["Operational Shifts"] += 1
            elif s == "A":
                employee_summary[e]["Afternoon Shifts"] += 1
                employee_summary[e]["Operational Shifts"] += 1
            elif s == "N":
                employee_summary[e]["Night Shifts"] += 1
                employee_summary[e]["Operational Shifts"] += 1
            elif s == "SB":
                employee_summary[e]["Standby Assignments"] += 1
            elif s == "OFF":
                employee_summary[e]["Off Assignments"] += 1

            if d.weekday() in (5, 6) and s in OPERATIONAL:
                employee_summary[e]["Weekend Operational Shifts"] += 1

            if d in PUBLIC_HOLIDAYS and s in OPERATIONAL:
                employee_summary[e]["Public Holidays Worked"] += 1
                employee_summary[e]["Holiday Worked Score"] += holiday_score_for_day(d) / 10.0
            if d in PREMIUM_HOLIDAYS and s in OPERATIONAL:
                employee_summary[e]["Premium Holidays Worked"] += 1

            employee_summary[e]["Shift Weight Score"] += shift_weight_for_day(d, s) / 10.0

    # Consecutive-night additional weighting.
    for e in EMPLOYEES:
        for i, d in enumerate(dates):
            if i == 0:
                continue
            if by_day[d][e] == "N" and by_day[dates[i - 1]][e] == "N":
                employee_summary[e]["Shift Weight Score"] += 0.1
            if i >= 2 and by_day[d][e] == "N" and by_day[dates[i - 1]][e] == "N" and by_day[dates[i - 2]][e] == "N":
                employee_summary[e]["Shift Weight Score"] += 0.1

    # Hard: daily staffing and group split.
    for d in dates:
        counts = defaultdict(int)
        for e in EMPLOYEES:
            counts[by_day[d][e]] += 1

        expected = {"M": 2, "A": 2, "N": 2, "SB": 2, "OFF": 2}
        for s, v in expected.items():
            if counts[s] != v:
                hard_violations.append(
                    Violation(
                        rule="Daily Staffing",
                        day=d,
                        employee=None,
                        description=f"Shift {s} has {counts[s]} instead of {v}.",
                        severity="Hard",
                        penalty=0,
                        resolution="Rebalance daily staffing counts.",
                    )
                )

        for s in OPERATIONAL:
            ga = sum(1 for e in GROUP_A if by_day[d][e] == s)
            gb = sum(1 for e in GROUP_B if by_day[d][e] == s)
            if ga != 1 or gb != 1:
                hard_violations.append(
                    Violation(
                        rule="Group Pairing",
                        day=d,
                        employee=None,
                        description=f"Shift {s} does not have 1x Group A and 1x Group B.",
                        severity="Hard",
                        penalty=0,
                        resolution="Enforce cross-group operational pairing.",
                    )
                )

        ga_sb = sum(1 for e in GROUP_A if by_day[d][e] == "SB")
        gb_sb = sum(1 for e in GROUP_B if by_day[d][e] == "SB")
        if ga_sb != 1 or gb_sb != 1:
            hard_violations.append(
                Violation(
                    rule="Standby Group Split",
                    day=d,
                    employee=None,
                    description="Standby does not include one employee from each group.",
                    severity="Hard",
                    penalty=0,
                    resolution="Re-enforce standby group balance.",
                )
            )

    # Hard: max 3 consecutive nights and no N->M.
    for e in EMPLOYEES:
        night_run = 0
        for i, d in enumerate(dates):
            s = by_day[d][e]
            if s == "N":
                night_run += 1
            else:
                night_run = 0
            if night_run > 3:
                hard_violations.append(
                    Violation(
                        rule="Maximum Consecutive Nights",
                        day=d,
                        employee=e,
                        description="Employee exceeds 3 consecutive night shifts.",
                        severity="Hard",
                        penalty=0,
                        resolution="Break night sequence with OFF or SB.",
                    )
                )

            if i < len(dates) - 1 and s == "N" and by_day[dates[i + 1]][e] == "M":
                hard_violations.append(
                    Violation(
                        rule="Night to Morning",
                        day=dates[i + 1],
                        employee=e,
                        description="Night followed by Morning is prohibited.",
                        severity="Hard",
                        penalty=0,
                        resolution="Change next-day assignment away from Morning.",
                    )
                )

    # Hard: exactly 219 operational shifts per employee.
    for e in EMPLOYEES:
        if employee_summary[e]["Operational Shifts"] != OPERATIONAL_SHIFT_TARGET:
            hard_violations.append(
                Violation(
                    rule="Operational Shift Count",
                    day=None,
                    employee=e,
                    description=(
                        f"Employee has {employee_summary[e]['Operational Shifts']} operational shifts, "
                        f"expected {OPERATIONAL_SHIFT_TARGET}."
                    ),
                    severity="Hard",
                    penalty=0,
                    resolution="Rebalance annual operational assignment totals.",
                )
            )

    # Weekend ownership hard checks.
    weekends = weekend_definitions(dates)
    designated_counts = defaultdict(int)
    for wk in weekends:
        owner = wk.owner
        designated_counts[owner] += 1
        if by_day[dates[wk.saturday_idx]][owner] != "OFF" or by_day[dates[wk.sunday_idx]][owner] != "OFF":
            hard_violations.append(
                Violation(
                    rule="Weekend Ownership",
                    day=dates[wk.saturday_idx],
                    employee=owner,
                    description="Designated weekend owner does not have SAT+SUN OFF.",
                    severity="Hard",
                    penalty=0,
                    resolution="Enforce full weekend off for designated owner.",
                )
            )
        employee_summary[owner]["Designated Full Weekends Off"] += 1

    for cycle in ten_week_cycles(weekends):
        per_emp = defaultdict(int)
        for wk in cycle:
            per_emp[wk.owner] += 1
        for e, c in per_emp.items():
            if c > 1:
                hard_violations.append(
                    Violation(
                        rule="Ten-Week Weekend Rule",
                        day=dates[cycle[0].saturday_idx],
                        employee=e,
                        description="Employee designated as weekend owner more than once in ten-week cycle.",
                        severity="Hard",
                        penalty=0,
                        resolution="Fix weekend owner rotation assignment.",
                    )
                )

    # Actual full weekends off.
    for wk in weekends:
        sat = dates[wk.saturday_idx]
        sun = dates[wk.sunday_idx]
        for e in EMPLOYEES:
            if by_day[sat][e] == "OFF" and by_day[sun][e] == "OFF":
                employee_summary[e]["Actual Full Weekends Off"] += 1

    # Pairing matrix and diversity score.
    for d in dates:
        for s in OPERATIONAL:
            pair = _pairs_for_day_shift(by_day[d], s)
            if pair in pairing_matrix:
                pairing_matrix[pair] += 1

    pair_values = list(pairing_matrix.values())
    pair_avg = mean(pair_values)
    for e in EMPLOYEES:
        related_pairs = [pairing_matrix[(a, b)] for (a, b) in pairing_matrix if a == e or b == e]
        employee_summary[e]["Pairing Diversity Score"] = mean(related_pairs)

    # Soft scoring and penalties.
    rqs = 100.0

    for e in EMPLOYEES:
        for i in range(len(dates) - 1):
            d1 = dates[i]
            d2 = dates[i + 1]
            if by_day[d1][e] == "SB" and by_day[d2][e] == "M":
                rqs -= 2
                employee_summary[e]["RQS Penalty Total"] += 2
                soft_violations.append(
                    Violation(
                        rule="Standby to Morning",
                        day=d2,
                        employee=e,
                        description="Standby followed by Morning.",
                        severity="Soft",
                        penalty=2,
                        resolution="Prefer SB/OFF or Afternoon after standby.",
                    )
                )

            if i >= 1 and by_day[dates[i - 1]][e] == "N" and by_day[d1][e] == "N" and by_day[d2][e] == "A":
                rqs -= 1
                employee_summary[e]["RQS Penalty Total"] += 1
                soft_violations.append(
                    Violation(
                        rule="Night Block to Afternoon",
                        day=d2,
                        employee=e,
                        description="Night block followed by Afternoon.",
                        severity="Soft",
                        penalty=1,
                        resolution="Prefer SB or OFF after night block.",
                    )
                )

        for i in range(1, len(dates) - 1):
            prev = dates[i - 1]
            cur = dates[i]
            nxt = dates[i + 1]
            prev_work = by_day[prev][e] in OPERATIONAL
            cur_off = by_day[cur][e] == "OFF"
            next_work = by_day[nxt][e] in OPERATIONAL
            night_block_exempt = i >= 2 and by_day[dates[i - 2]][e] == "N" and by_day[prev][e] == "N"
            if prev_work and cur_off and next_work and not night_block_exempt:
                rqs -= 1
                employee_summary[e]["RQS Penalty Total"] += 1
                soft_violations.append(
                    Violation(
                        rule="Isolated Off Day",
                        day=cur,
                        employee=e,
                        description="Work -> OFF -> Work isolated off pattern.",
                        severity="Soft",
                        penalty=1,
                        resolution="Prefer OFF OFF or OFF around standby.",
                    )
                )

        # Consecutive worked day penalties.
        worked_run = 0
        for d in dates:
            if by_day[d][e] in OPERATIONAL:
                worked_run += 1
            else:
                if worked_run == 7:
                    rqs -= 2
                    employee_summary[e]["RQS Penalty Total"] += 2
                elif worked_run == 8:
                    rqs -= 4
                    employee_summary[e]["RQS Penalty Total"] += 4
                elif worked_run > 8:
                    rqs -= 10
                    employee_summary[e]["RQS Penalty Total"] += 10
                worked_run = 0

    # Friday night before designated weekend off.
    for wk in weekends:
        owner = wk.owner
        fri_idx = wk.saturday_idx - 1
        if fri_idx >= 0:
            fri = dates[fri_idx]
            if by_day[fri][owner] == "N":
                rqs -= 1
                employee_summary[owner]["RQS Penalty Total"] += 1
                soft_violations.append(
                    Violation(
                        rule="Friday Night Before Designated Weekend Off",
                        day=fri,
                        employee=owner,
                        description="Friday Night precedes designated full weekend off.",
                        severity="Soft",
                        penalty=1,
                        resolution="Prefer non-night assignment on Friday.",
                    )
                )

    # Distribution penalties.
    avg_weekend = mean(employee_summary[e]["Weekend Operational Shifts"] for e in EMPLOYEES)
    avg_standby = mean(employee_summary[e]["Standby Assignments"] for e in EMPLOYEES)
    avg_night = mean(employee_summary[e]["Night Shifts"] for e in EMPLOYEES)
    avg_holiday_score = mean(employee_summary[e]["Holiday Worked Score"] for e in EMPLOYEES)
    avg_weight = mean(employee_summary[e]["Shift Weight Score"] for e in EMPLOYEES)
    avg_premium = mean(employee_summary[e]["Premium Holidays Worked"] for e in EMPLOYEES)

    for e in EMPLOYEES:
        weekend_excess = max(0.0, employee_summary[e]["Weekend Operational Shifts"] - (avg_weekend + 1))
        if weekend_excess > 0:
            rqs -= weekend_excess
            employee_summary[e]["RQS Penalty Total"] += weekend_excess

        standby_excess = max(0.0, employee_summary[e]["Standby Assignments"] - (avg_standby * 1.10))
        if standby_excess > 0:
            rqs -= standby_excess
            employee_summary[e]["RQS Penalty Total"] += standby_excess

        night_excess = max(0.0, employee_summary[e]["Night Shifts"] - (avg_night * 1.05))
        if night_excess > 0:
            rqs -= night_excess
            employee_summary[e]["RQS Penalty Total"] += night_excess

        holiday_score_excess = max(0.0, employee_summary[e]["Holiday Worked Score"] - avg_holiday_score)
        if holiday_score_excess > 0:
            rqs -= holiday_score_excess
            employee_summary[e]["RQS Penalty Total"] += holiday_score_excess

        premium_excess = max(0.0, employee_summary[e]["Premium Holidays Worked"] - avg_premium)
        if premium_excess > 0:
            penalty = 2 * premium_excess
            rqs -= penalty
            employee_summary[e]["RQS Penalty Total"] += penalty

        if avg_weight > 0:
            percent_above = ((employee_summary[e]["Shift Weight Score"] - avg_weight) / avg_weight) * 100
            if percent_above > 2:
                penalty = max(0.0, int((percent_above - 2) / 2))
                rqs -= penalty
                employee_summary[e]["RQS Penalty Total"] += penalty

    expected_pair = mean(pair_values)
    for (a, b), c in pairing_matrix.items():
        excess = max(0.0, c - expected_pair)
        if excess > 0:
            penalty = 0.5 * excess
            rqs -= penalty
            employee_summary[a]["RQS Penalty Total"] += penalty / 2
            employee_summary[b]["RQS Penalty Total"] += penalty / 2

    rqs = max(0.0, round(rqs, 2))

    # Fairness index (variance-based normalized score over required components).
    def variance(vals: List[float]) -> float:
        m = mean(vals)
        return mean((v - m) ** 2 for v in vals)

    fairness_components = {
        "Operational": variance([employee_summary[e]["Operational Shifts"] for e in EMPLOYEES]),
        "Morning": variance([employee_summary[e]["Morning Shifts"] for e in EMPLOYEES]),
        "Afternoon": variance([employee_summary[e]["Afternoon Shifts"] for e in EMPLOYEES]),
        "Night": variance([employee_summary[e]["Night Shifts"] for e in EMPLOYEES]),
        "Weekend": variance([employee_summary[e]["Weekend Operational Shifts"] for e in EMPLOYEES]),
        "Standby": variance([employee_summary[e]["Standby Assignments"] for e in EMPLOYEES]),
        "Off": variance([employee_summary[e]["Off Assignments"] for e in EMPLOYEES]),
        "Holiday Score": variance([employee_summary[e]["Holiday Worked Score"] for e in EMPLOYEES]),
        "Premium": variance([employee_summary[e]["Premium Holidays Worked"] for e in EMPLOYEES]),
        "Shift Weight": variance([employee_summary[e]["Shift Weight Score"] for e in EMPLOYEES]),
        "Pairing": variance(pair_values),
        "Weekend Ownership": variance([employee_summary[e]["Designated Full Weekends Off"] for e in EMPLOYEES]),
    }

    # Convert component variances to penalties with bounded influence.
    fi_penalty = 0.0
    for _, v in fairness_components.items():
        fi_penalty += min(8.0, v)

    fairness_index = max(0.0, round(100.0 - fi_penalty, 2))

    fairness_rating = _rating(
        fairness_index,
        [(95, "Excellent"), (90, "Very Good"), (80, "Good"), (70, "Acceptable"), (0, "Review Required")],
    )
    rqs_rating = _rating(
        rqs,
        [(95, "Excellent"), (90, "Very Good"), (80, "Good"), (70, "Acceptable"), (60, "Poor"), (0, "Rebuild Recommended")],
    )

    metrics = {
        "Operational Shift Variance": fairness_components["Operational"],
        "Morning Shift Variance": fairness_components["Morning"],
        "Afternoon Shift Variance": fairness_components["Afternoon"],
        "Night Shift Variance": fairness_components["Night"],
        "Weekend Shift Variance": fairness_components["Weekend"],
        "Standby Variance": fairness_components["Standby"],
        "Holiday Worked Score Variance": fairness_components["Holiday Score"],
        "Shift Weight Score Variance": fairness_components["Shift Weight"],
        "Pairing Diversity Variance": fairness_components["Pairing"],
    }

    return ValidationReport(
        hard_passed=len(hard_violations) == 0,
        hard_violations=hard_violations,
        soft_violations=soft_violations,
        employee_summary=employee_summary,
        pairing_matrix=pairing_matrix,
        fairness_index=fairness_index,
        fairness_rating=fairness_rating,
        rqs=rqs,
        rqs_rating=rqs_rating,
        metrics=metrics,
    )
