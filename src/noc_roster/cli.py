from __future__ import annotations

import argparse
import csv
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Tuple

from .solver import SolverSettings, solve_roster
from .spec import EMPLOYEES, GROUP_A, all_dates
from .validator import validate_roster
from .workbook import write_workbook


def _group_of(employee: str) -> str:
    return "A" if employee in GROUP_A else "B"


def _write_assignment_csv(assignments: Dict[Tuple[datetime.date, str], str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "employee", "group", "assignment"])
        for d in all_dates():
            for e in EMPLOYEES:
                writer.writerow([d.isoformat(), e, _group_of(e), assignments[(d, e)]])


def _read_assignment_csv(path: Path) -> Dict[Tuple[datetime.date, str], str]:
    assignments = {}
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            d = datetime.strptime(row["date"], "%Y-%m-%d").date()
            assignments[(d, row["employee"])] = row["assignment"]
    return assignments


def cmd_generate(args: argparse.Namespace) -> int:
    cpu_count = os.cpu_count() or 1
    auto_workers = max(1, cpu_count - 2)
    workers = args.workers if args.workers is not None else auto_workers

    settings = SolverSettings(
        time_limit_seconds=args.time_limit,
        random_seed=args.random_seed,
        num_search_workers=workers,
        progress_logging=args.progress,
        progress_interval_seconds=args.progress_interval,
        cp_sat_search_logs=args.cp_sat_logs,
        stop_on_first_feasible=args.stop_on_first_feasible,
    )
    result = solve_roster(settings)
    if not result.solved:
        print(f"Solver failed: {result.status}")
        print(f"Solve time (s): {result.solve_seconds:.2f}")
        print(f"Conflicts: {result.iterations}")
        print(f"Branches: {result.branches}")
        print(f"Best objective bound: {result.best_objective_bound}")
        print(f"Early stop requested: {result.early_stop_requested}")
        return 1

    validation = validate_roster(result.assignments)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_workbook(result.assignments, validation, result, str(output_path))

    csv_path = Path(args.csv_output)
    _write_assignment_csv(result.assignments, csv_path)

    print(f"Solver status: {result.status}")
    print(f"Objective value: {result.objective_value}")
    print(f"Best objective bound: {result.best_objective_bound}")
    print(f"Solve time (s): {result.solve_seconds:.2f}")
    print(f"Workers used: {workers}")
    print(f"Conflicts: {result.iterations}")
    print(f"Branches: {result.branches}")
    print(f"Early stop requested: {result.early_stop_requested}")
    print(f"Workbook: {output_path}")
    print(f"Assignments CSV: {csv_path}")
    print(f"Hard constraints passed: {validation.hard_passed}")
    print(f"Hard violations: {len(validation.hard_violations)}")
    print(f"RQS: {validation.rqs} ({validation.rqs_rating})")
    print(f"Fairness Index: {validation.fairness_index} ({validation.fairness_rating})")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1

    assignments = _read_assignment_csv(csv_path)
    validation = validate_roster(assignments)

    print(f"Hard constraints passed: {validation.hard_passed}")
    print(f"Hard violations: {len(validation.hard_violations)}")
    print(f"Soft findings: {len(validation.soft_violations)}")
    print(f"RQS: {validation.rqs} ({validation.rqs_rating})")
    print(f"Fairness Index: {validation.fairness_index} ({validation.fairness_rating})")

    if validation.hard_violations:
        print("First hard violations:")
        for v in validation.hard_violations[:10]:
            day = v.day.isoformat() if v.day else "-"
            emp = v.employee or "-"
            print(f"- [{v.rule}] day={day} employee={emp} desc={v.description}")
    return 0 if validation.hard_passed else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NOC roster generator and validator")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate annual roster and workbook")
    gen.add_argument("--output", default="outputs/NOC_Roster_2026_2027.xlsx", help="Workbook output path")
    gen.add_argument("--csv-output", default="outputs/roster_assignments.csv", help="Assignment CSV output path")
    gen.add_argument("--time-limit", type=int, default=120, help="CP-SAT solve time limit in seconds")
    gen.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of CP-SAT search workers (default: CPU cores minus 2)",
    )
    gen.add_argument("--random-seed", type=int, default=42, help="CP-SAT random seed")
    gen.add_argument("--progress", dest="progress", action="store_true", help="Enable periodic high-level progress logs")
    gen.add_argument("--no-progress", dest="progress", action="store_false", help="Disable periodic high-level progress logs")
    gen.set_defaults(progress=True)
    gen.add_argument(
        "--progress-interval",
        type=int,
        default=10,
        help="Seconds between progress updates when --progress is enabled",
    )
    gen.add_argument("--cp-sat-logs", action="store_true", help="Enable verbose native CP-SAT search logs")
    gen.add_argument(
        "--stop-on-first-feasible",
        action="store_true",
        help="Stop search as soon as the first feasible solution is found",
    )
    gen.set_defaults(func=cmd_generate)

    val = sub.add_parser("validate", help="Validate roster assignment CSV")
    val.add_argument("--csv", required=True, help="Path to assignment CSV")
    val.set_defaults(func=cmd_validate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
