from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Tuple

import pandas as pd

from .solver import SolveResult
from .spec import (
    EMPLOYEES,
    GROUP_A,
    GROUP_B,
    LEAVE_EQUIVALENTS,
    OPERATIONAL_SHIFT_TARGET,
    PAID_SHIFT_TARGET,
    PUBLIC_HOLIDAYS,
    all_dates,
    day_name,
    pairing_keys,
    quarter_for_date,
    weekend_definitions,
)
from .validator import ValidationReport, Violation


def _group_of(employee: str) -> str:
    return "A" if employee in GROUP_A else "B"


def _daily_pairs(by_day: Dict[str, str], shift: str) -> str:
    people = [e for e, s in by_day.items() if s == shift]
    return " + ".join(sorted(people))


def _violation_rows(violations: List[Violation], default_severity: str) -> List[Dict[str, object]]:
    rows = []
    for v in violations:
        rows.append(
            {
                "Rule": v.rule,
                "Date": v.day.isoformat() if v.day else "",
                "Employee": v.employee or "",
                "Description": v.description,
                "Severity": v.severity or default_severity,
                "Penalty": v.penalty,
                "Resolution": v.resolution,
            }
        )
    return rows


def write_workbook(
    assignments: Dict[Tuple[date, str], str],
    validation: ValidationReport,
    solve_result: SolveResult,
    output_path: str,
    dates: List[date],
) -> None:
    by_day = {
        d: {e: assignments[(d, e)] for e in EMPLOYEES}
        for d in dates
    }

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # 24.1 Specification Notes
        spec_notes = pd.DataFrame(
            [
                {"Item": "Specification version", "Value": "2.0"},
                {"Item": "Generation date", "Value": datetime.now().isoformat(timespec="seconds")},
                {"Item": "Solver status", "Value": solve_result.status},
                {"Item": "Solve time (seconds)", "Value": round(solve_result.solve_seconds, 2)},
                {"Item": "Objective value", "Value": solve_result.objective_value},
                # Temporary December Shift removal
                {"Item": "Planning assumptions", "Value": "Paid 260, Leave 41, Operational 209-210 during temporary closure"},
                {"Item": "Hard constraint summary", "Value": "Daily assignment/staffing, pairing, nights, N->M, op counts, weekend ownership"},
                {"Item": "Soft constraint summary", "Value": "Fatigue, fairness, holiday, pairing, shift weight, RQS"},
                {"Item": "Optimisation priorities", "Value": "As per hierarchy section 26"},
                {"Item": "Known assumptions", "Value": "Cover process is separate from base roster"},
                {"Item": "Change history", "Value": "Initial generated workbook"},
            ]
        )
        spec_notes.to_excel(writer, index=False, sheet_name="Specification Notes")

        # 24.2 Daily Roster
        daily_rows = []
        for d in dates:
            day_assign = by_day[d]
            daily_rows.append(
                {
                    "Date": d.isoformat(),
                    "Day of Week": day_name(d),
                    "Morning Pair": _daily_pairs(day_assign, "M"),
                    "Afternoon Pair": _daily_pairs(day_assign, "A"),
                    "Night Pair": _daily_pairs(day_assign, "N"),
                    "Standby Employees": _daily_pairs(day_assign, "SB"),
                    "Off Employees": _daily_pairs(day_assign, "OFF"),
                    "Notes": PUBLIC_HOLIDAYS.get(d, ""),
                }
            )
        pd.DataFrame(daily_rows).to_excel(writer, index=False, sheet_name="Daily Roster")

        # 24.3 Employee Summary
        employee_rows = []
        for e in EMPLOYEES:
            s = validation.employee_summary[e]
            employee_rows.append(
                {
                    "Employee": e,
                    "Group": _group_of(e),
                    "Morning Shifts": s["Morning Shifts"],
                    "Afternoon Shifts": s["Afternoon Shifts"],
                    "Night Shifts": s["Night Shifts"],
                    "Operational Shifts": s["Operational Shifts"],
                    "Standby Assignments": s["Standby Assignments"],
                    "Off Assignments": s["Off Assignments"],
                    "Paid Shift Target": PAID_SHIFT_TARGET,
                    "Leave Equivalents": LEAVE_EQUIVALENTS,
                    "Weekend Operational Shifts": s["Weekend Operational Shifts"],
                    "Designated Full Weekends Off": s["Designated Full Weekends Off"],
                    "Actual Full Weekends Off": s["Actual Full Weekends Off"],
                    "Public Holidays Worked": s["Public Holidays Worked"],
                    "Premium Holidays Worked": s["Premium Holidays Worked"],
                    "Holiday Worked Score": s["Holiday Worked Score"],
                    "Shift Weight Score": s["Shift Weight Score"],
                    "Pairing Diversity Score": s["Pairing Diversity Score"],
                    "RQS Penalty Total": s["RQS Penalty Total"],
                }
            )
        pd.DataFrame(employee_rows).to_excel(writer, index=False, sheet_name="Employee Summary")

        # 24.4 Public Holiday Report
        holiday_rows = []
        for d, name in PUBLIC_HOLIDAYS.items():
            if d not in by_day:
                continue
            day_assign = by_day[d]
            holiday_rows.append(
                {
                    "Holiday": name,
                    "Date": d.isoformat(),
                    "Morning Staff": _daily_pairs(day_assign, "M"),
                    "Afternoon Staff": _daily_pairs(day_assign, "A"),
                    "Night Staff": _daily_pairs(day_assign, "N"),
                    "Standby Staff": _daily_pairs(day_assign, "SB"),
                    "Off Staff": _daily_pairs(day_assign, "OFF"),
                }
            )
        holiday_df = pd.DataFrame(holiday_rows)
        holiday_df.to_excel(writer, index=False, sheet_name="Public Holiday Report", startrow=0)

        holiday_score_stats = pd.DataFrame(
            [
                {"Employee": e, "Holiday Worked Score": validation.employee_summary[e]["Holiday Worked Score"], "Premium Holidays": validation.employee_summary[e]["Premium Holidays Worked"]}
                for e in EMPLOYEES
            ]
        )
        holiday_score_stats.to_excel(writer, index=False, sheet_name="Public Holiday Report", startrow=len(holiday_df) + 3)

        # 24.5 Weekend Report
        weekend_rows = []
        for wk in weekend_definitions(dates):
            sat = dates[wk.saturday_idx]
            sun = dates[wk.sunday_idx]
            sat_assign = by_day[sat]
            sun_assign = by_day[sun]
            actual_full = [e for e in EMPLOYEES if sat_assign[e] == "OFF" and sun_assign[e] == "OFF"]
            weekend_rows.append(
                {
                    "Week Number": wk.weekend_number,
                    "Weekend Owner": wk.owner,
                    "Saturday Assignments": "; ".join(f"{e}:{sat_assign[e]}" for e in EMPLOYEES),
                    "Sunday Assignments": "; ".join(f"{e}:{sun_assign[e]}" for e in EMPLOYEES),
                    "Designated Full Weekend Off": wk.owner,
                    "Actual Full Weekends Off": ", ".join(actual_full),
                }
            )
        pd.DataFrame(weekend_rows).to_excel(writer, index=False, sheet_name="Weekend Report")

        # 24.6 Pairing Analysis
        pair_rows = []
        pair_vals = list(validation.pairing_matrix.values())
        pair_avg = sum(pair_vals) / len(pair_vals)
        for a, b in pairing_keys():
            pair_rows.append({"Group A": a, "Group B": b, "Count": validation.pairing_matrix[(a, b)]})
        pair_df = pd.DataFrame(pair_rows)
        pair_df.to_excel(writer, index=False, sheet_name="Pairing Analysis", startrow=0)

        pd.DataFrame(
            [
                {
                    "Average pair count": pair_avg,
                    "Minimum": min(pair_vals),
                    "Maximum": max(pair_vals),
                    "Variance": validation.metrics["Pairing Diversity Variance"],
                }
            ]
        ).to_excel(writer, index=False, sheet_name="Pairing Analysis", startrow=len(pair_df) + 3)

        # 24.7 Fairness Dashboard
        dash_rows = [
            {"Metric": "Fairness Index", "Value": validation.fairness_index},
            {"Metric": "Fairness Rating", "Value": validation.fairness_rating},
            {"Metric": "Roster Quality Score", "Value": validation.rqs},
            {"Metric": "RQS Rating", "Value": validation.rqs_rating},
        ]
        for k, v in validation.metrics.items():
            dash_rows.append({"Metric": k, "Value": v})
        pd.DataFrame(dash_rows).to_excel(writer, index=False, sheet_name="Fairness Dashboard")

        # 24.8 Leave Planner
        leave_rows = []
        for e in EMPLOYEES:
            for q in ["Q1", "Q2", "Q3", "Q4"]:
                leave_rows.append(
                    {
                        "Employee": e,
                        "Quarter": q,
                        "Requested Leave": "",
                        "Approved Leave": "",
                        "Leave Balance": "",
                        "Cover Employee": "",
                        "Cover Status": "",
                    }
                )
        pd.DataFrame(leave_rows).to_excel(writer, index=False, sheet_name="Leave Planner")

        # 24.9 Constraint Violations
        violation_rows = _violation_rows(validation.hard_violations, "Hard") + _violation_rows(validation.soft_violations, "Soft")
        pd.DataFrame(violation_rows).to_excel(writer, index=False, sheet_name="Constraint Violations")

        # 24.10 Optional worksheets
        shift_calendar = []
        for d in dates:
            for e in EMPLOYEES:
                shift_calendar.append(
                    {
                        "Date": d.isoformat(),
                        "Day": day_name(d),
                        "Employee": e,
                        "Assignment": by_day[d][e],
                        "Quarter": quarter_for_date(d),
                    }
                )
        pd.DataFrame(shift_calendar).to_excel(writer, index=False, sheet_name="Shift Calendar")

        pd.DataFrame(columns=["Date", "Absent Employee", "Reason", "Cover Employee", "Priority", "Status"]).to_excel(
            writer, index=False, sheet_name="Cover Log"
        )

        pd.DataFrame(
            [
                # Temporary December Shift removal
                {"Employee": e, "Paid Shift Target": PAID_SHIFT_TARGET, "Leave Equivalents": LEAVE_EQUIVALENTS, "Operational Target": "209-210 (temporary closure)"}
                for e in EMPLOYEES
            ]
        ).to_excel(writer, index=False, sheet_name="Leave Statistics")

        stats_rows = [
            {"Key": "Solve time", "Value": solve_result.solve_seconds},
            {"Key": "Iterations", "Value": solve_result.iterations},
            {"Key": "Objective value", "Value": solve_result.objective_value},
            {"Key": "Hard constraint count", "Value": "See validator hard checks"},
            {"Key": "Soft constraint count", "Value": len(validation.soft_violations)},
        ]
        for k, v in solve_result.objective_terms.items():
            stats_rows.append({"Key": f"Objective term: {k}", "Value": v})
        pd.DataFrame(stats_rows).to_excel(writer, index=False, sheet_name="Solver Statistics")
