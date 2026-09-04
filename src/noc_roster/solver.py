from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import ceil
import threading
import time
import sys
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

from .spec import (
    ASSIGNMENTS,
    EMPLOYEES,
    GROUP_A,
    GROUP_B,
    OPERATIONAL,
    OPERATIONAL_SHIFT_TARGET,
    PREMIUM_HOLIDAYS,
    PUBLIC_HOLIDAYS,
    all_dates,
    holiday_score_for_day,
    pairing_keys,
    shift_weight_for_day,
    ten_week_cycles,
    weekend_definitions,
)
from .validator import validate_roster


@dataclass
class SolverSettings:
    time_limit_seconds: int = 120
    random_seed: int = 42
    num_search_workers: int = 8
    progress_logging: bool = False
    progress_interval_seconds: int = 10
    cp_sat_search_logs: bool = False
    stop_on_first_feasible: bool = False


@dataclass
class SolveResult:
    solved: bool
    status: str
    assignments: Dict[Tuple[date, str], str]
    objective_value: int
    best_objective_bound: float
    objective_terms: Dict[str, int]
    solve_seconds: float
    iterations: int
    branches: int
    early_stop_requested: bool


class _ProgressSolutionLogger(cp_model.CpSolverSolutionCallback):
    def __init__(
        self,
        interval_seconds: int,
        dates: List[date],
        x: Dict[Tuple[str, int, str], cp_model.IntVar],
        stop_on_first_feasible: bool,
    ) -> None:
        super().__init__()
        self._interval_seconds = max(1, interval_seconds)
        self._dates = dates
        self._x = x
        self._stop_on_first_feasible = stop_on_first_feasible
        self._state_lock = threading.Lock()
        self._last_log_time = -1.0
        self._solution_count = 0
        self.last_objective = None
        self.last_best_bound = None
        self.last_conflicts = 0
        self.last_branches = 0
        self.last_wall_time = 0.0
        self.last_fairness_index = None
        self.last_fairness_rating = None
        self.last_rqs = None
        self.last_rqs_rating = None
        self.last_hard_passed = None
        self.last_hard_violations = None

    def _capture_quality_snapshot(self) -> None:
        assignments: Dict[Tuple[date, str], str] = {}
        for d_idx, day in enumerate(self._dates):
            for e in EMPLOYEES:
                for s in ASSIGNMENTS:
                    if self.Value(self._x[(e, d_idx, s)]) == 1:
                        assignments[(day, e)] = s
                        break

        report = validate_roster(assignments)
        self.last_fairness_index = report.fairness_index
        self.last_fairness_rating = report.fairness_rating
        self.last_rqs = report.rqs
        self.last_rqs_rating = report.rqs_rating
        self.last_hard_passed = report.hard_passed
        self.last_hard_violations = len(report.hard_violations)

    def OnSolutionCallback(self) -> None:
        with self._state_lock:
            self._solution_count += 1
            now = self.WallTime()
            self.last_wall_time = now
            self.last_objective = self.ObjectiveValue()
            self.last_best_bound = self.BestObjectiveBound()
            self.last_conflicts = self.NumConflicts()
            self.last_branches = self.NumBranches()
            self._capture_quality_snapshot()

            if self._solution_count == 1 or now - self._last_log_time >= self._interval_seconds:
                self._last_log_time = now
                print(
                    (
                        f"[progress] t={now:.1f}s "
                        f"solution_found=yes "
                        f"solution={self._solution_count} "
                        f"objective={self.ObjectiveValue():.0f} "
                        f"best_bound={self.BestObjectiveBound():.0f} "
                        f"FI={self.last_fairness_index:.2f} ({self.last_fairness_rating}) "
                        f"RQS={self.last_rqs:.2f} ({self.last_rqs_rating}) "
                        f"hard_passed={self.last_hard_passed} "
                        f"hard_violations={self.last_hard_violations} "
                        f"conflicts={self.NumConflicts()} "
                        f"branches={self.NumBranches()}"
                    ),
                    flush=True,
                )

            if self._stop_on_first_feasible and self._solution_count >= 1:
                print("[control] stop_on_first_feasible active, stopping after first feasible solution.", flush=True)
                self.StopSearch()

    @property
    def solution_count(self) -> int:
        return self._solution_count

    def snapshot(self) -> Dict[str, object]:
        with self._state_lock:
            return {
                "solution_count": self._solution_count,
                "last_objective": self.last_objective,
                "last_best_bound": self.last_best_bound,
                "last_conflicts": self.last_conflicts,
                "last_branches": self.last_branches,
                "last_fairness_index": self.last_fairness_index,
                "last_fairness_rating": self.last_fairness_rating,
                "last_rqs": self.last_rqs,
                "last_rqs_rating": self.last_rqs_rating,
                "last_hard_passed": self.last_hard_passed,
                "last_hard_violations": self.last_hard_violations,
            }


def _and2(model: cp_model.CpModel, a: cp_model.IntVar, b: cp_model.IntVar, name: str) -> cp_model.IntVar:
    z = model.NewBoolVar(name)
    model.Add(z <= a)
    model.Add(z <= b)
    model.Add(z >= a + b - 1)
    return z


def _and3(
    model: cp_model.CpModel,
    a: cp_model.IntVar,
    b: cp_model.IntVar,
    c: cp_model.IntVar,
    name: str,
) -> cp_model.IntVar:
    z = model.NewBoolVar(name)
    model.Add(z <= a)
    model.Add(z <= b)
    model.Add(z <= c)
    model.Add(z >= a + b + c - 2)
    return z


def _all_true(model: cp_model.CpModel, vars_: List[cp_model.IntVar], name: str) -> cp_model.IntVar:
    z = model.NewBoolVar(name)
    for v in vars_:
        model.Add(z <= v)
    model.Add(z >= sum(vars_) - (len(vars_) - 1))
    return z


def solve_roster(settings: SolverSettings | None = None) -> SolveResult:
    settings = settings or SolverSettings()

    def log(msg: str) -> None:
        if settings.progress_logging:
            print(msg, flush=True)

    log("[build] Initializing model...")
    dates = all_dates()
    num_days = len(dates)
    model = cp_model.CpModel()

    shift_idx = {s: i for i, s in enumerate(ASSIGNMENTS)}

    x: Dict[Tuple[str, int, str], cp_model.IntVar] = {}
    log("[build] Creating decision variables...")
    for e in EMPLOYEES:
        for d in range(num_days):
            for s in ASSIGNMENTS:
                x[(e, d, s)] = model.NewBoolVar(f"x_{e}_{d}_{s}")

    log("[build] Applying hard constraints...")
    for e in EMPLOYEES:
        for d in range(num_days):
            model.Add(sum(x[(e, d, s)] for s in ASSIGNMENTS) == 1)

    for d in range(num_days):
        model.Add(sum(x[(e, d, "M")] for e in EMPLOYEES) == 2)
        model.Add(sum(x[(e, d, "A")] for e in EMPLOYEES) == 2)
        model.Add(sum(x[(e, d, "N")] for e in EMPLOYEES) == 2)
        model.Add(sum(x[(e, d, "SB")] for e in EMPLOYEES) == 2)
        model.Add(sum(x[(e, d, "OFF")] for e in EMPLOYEES) == 2)

        for s in OPERATIONAL:
            model.Add(sum(x[(e, d, s)] for e in GROUP_A) == 1)
            model.Add(sum(x[(e, d, s)] for e in GROUP_B) == 1)

        model.Add(sum(x[(e, d, "SB")] for e in GROUP_A) == 1)
        model.Add(sum(x[(e, d, "SB")] for e in GROUP_B) == 1)

    for e in EMPLOYEES:
        for d in range(num_days - 3):
            model.Add(sum(x[(e, d + k, "N")] for k in range(4)) <= 3)

    for e in EMPLOYEES:
        for d in range(num_days - 1):
            model.Add(x[(e, d, "N")] + x[(e, d + 1, "M")] <= 1)

    for e in EMPLOYEES:
        model.Add(sum(x[(e, d, s)] for d in range(num_days) for s in OPERATIONAL) == OPERATIONAL_SHIFT_TARGET)

    weekends = weekend_definitions(dates)
    for wk in weekends:
        model.Add(x[(wk.owner, wk.saturday_idx, "OFF")] == 1)
        model.Add(x[(wk.owner, wk.sunday_idx, "OFF")] == 1)

    # Ten-week designated weekend ownership cap is guaranteed by fixed rotation.
    for cycle in ten_week_cycles(weekends):
        for e in EMPLOYEES:
            if sum(1 for w in cycle if w.owner == e) > 1:
                raise ValueError("Weekend owner rotation violates ten-week rule.")

    penalty_terms: List[Tuple[str, cp_model.LinearExpr, int]] = []

    log("[build] Applying soft constraints and objectives...")
    # Priority 2: fatigue management soft constraints.
    standby_to_morning_count = []
    night_block_to_afternoon_count = []
    isolated_off_count = []
    over6_work_penalty = []

    for e in EMPLOYEES:
        for d in range(num_days - 1):
            sb_m = _and2(model, x[(e, d, "SB")], x[(e, d + 1, "M")], f"sbm_{e}_{d}")
            standby_to_morning_count.append(sb_m)

        for d in range(1, num_days - 1):
            nb_af = _and3(model, x[(e, d - 1, "N")], x[(e, d, "N")], x[(e, d + 1, "A")], f"nbaf_{e}_{d}")
            night_block_to_afternoon_count.append(nb_af)

        for d in range(1, num_days - 1):
            worked_prev = model.NewBoolVar(f"worked_prev_{e}_{d}")
            model.Add(worked_prev == sum(x[(e, d - 1, s)] for s in OPERATIONAL))

            worked_next = model.NewBoolVar(f"worked_next_{e}_{d}")
            model.Add(worked_next == sum(x[(e, d + 1, s)] for s in OPERATIONAL))

            base_iso = _and3(model, worked_prev, x[(e, d, "OFF")], worked_next, f"base_iso_{e}_{d}")

            if d >= 2:
                night_block_before = _and2(model, x[(e, d - 2, "N")], x[(e, d - 1, "N")], f"nbefore_{e}_{d}")
                true_iso = model.NewBoolVar(f"true_iso_{e}_{d}")
                model.Add(true_iso <= base_iso)
                model.Add(true_iso <= 1 - night_block_before)
                model.Add(true_iso >= base_iso - night_block_before)
                isolated_off_count.append(true_iso)
            else:
                isolated_off_count.append(base_iso)

        worked = [model.NewBoolVar(f"worked_{e}_{d}") for d in range(num_days)]
        for d in range(num_days):
            model.Add(worked[d] == sum(x[(e, d, s)] for s in OPERATIONAL))

        for start in range(num_days - 6):
            w7 = _all_true(model, worked[start : start + 7], f"w7_{e}_{start}")
            over6_work_penalty.append((w7, 2))
        for start in range(num_days - 7):
            w8 = _all_true(model, worked[start : start + 8], f"w8_{e}_{start}")
            over6_work_penalty.append((w8, 2))
        for start in range(num_days - 8):
            w9 = _all_true(model, worked[start : start + 9], f"w9_{e}_{start}")
            over6_work_penalty.append((w9, 6))

    penalty_terms.append(("fatigue_standby_to_morning", sum(standby_to_morning_count), 200000))
    penalty_terms.append(("fatigue_night_block_to_afternoon", sum(night_block_to_afternoon_count), 100000))
    penalty_terms.append(("fatigue_isolated_off", sum(isolated_off_count), 100000))
    penalty_terms.append(("fatigue_long_work_blocks", sum(v * w for v, w in over6_work_penalty), 120000))

    # Friday night before designated weekend off.
    fri_night_weekend_owner = []
    for wk in weekends:
        fri = wk.saturday_idx - 1
        if fri >= 0:
            fri_night_weekend_owner.append(x[(wk.owner, fri, "N")])
    penalty_terms.append(("weekend_owner_friday_night", sum(fri_night_weekend_owner), 80000))

    # Priority 4: holiday fairness.
    holiday_indices = [idx for idx, d in enumerate(dates) if d in PUBLIC_HOLIDAYS]
    holiday_score_vars: Dict[str, cp_model.IntVar] = {}
    holiday_score_total = 0
    for d in holiday_indices:
        holiday_score_total += holiday_score_for_day(dates[d]) * 6

    for e in EMPLOYEES:
        score = model.NewIntVar(0, 10000, f"holiday_score_{e}")
        model.Add(
            score
            == sum(
                holiday_score_for_day(dates[d]) * x[(e, d, s)]
                for d in holiday_indices
                for s in OPERATIONAL
            )
        )
        holiday_score_vars[e] = score

    holiday_dev_terms = []
    for e in EMPLOYEES:
        dev = model.NewIntVar(0, 20000, f"holiday_dev_{e}")
        model.Add(dev >= holiday_score_vars[e] * 10 - holiday_score_total)
        model.Add(dev >= holiday_score_total - holiday_score_vars[e] * 10)
        holiday_dev_terms.append(dev)
    penalty_terms.append(("holiday_score_variance", sum(holiday_dev_terms), 4000))

    premium_indices = [idx for idx, d in enumerate(dates) if d in PREMIUM_HOLIDAYS]
    premium_counts: Dict[str, cp_model.IntVar] = {}
    for e in EMPLOYEES:
        c = model.NewIntVar(0, 20, f"premium_count_{e}")
        model.Add(c == sum(x[(e, d, s)] for d in premium_indices for s in OPERATIONAL))
        premium_counts[e] = c

    premium_total = len(premium_indices) * 6
    premium_dev_terms = []
    premium_excess_terms = []
    for e in EMPLOYEES:
        dev = model.NewIntVar(0, 200, f"premium_dev_{e}")
        model.Add(dev >= premium_counts[e] * 10 - premium_total)
        model.Add(dev >= premium_total - premium_counts[e] * 10)
        premium_dev_terms.append(dev)

        excess = model.NewIntVar(0, 20, f"premium_excess_{e}")
        model.Add(excess >= premium_counts[e] - 2)
        model.Add(excess >= 0)
        premium_excess_terms.append(excess)
    penalty_terms.append(("premium_holiday_variance", sum(premium_dev_terms), 3000))
    penalty_terms.append(("premium_holiday_above_two", sum(premium_excess_terms), 6000))

    # Premium holiday preference pairings.
    idx_christmas = dates.index(date(2026, 12, 25))
    idx_goodwill = dates.index(date(2026, 12, 26))
    idx_newyear = dates.index(date(2027, 1, 1))

    premium_overlap_penalties = []
    for e in EMPLOYEES:
        christmas_any = model.NewBoolVar(f"xmas_any_{e}")
        model.Add(christmas_any == sum(x[(e, idx_christmas, s)] for s in OPERATIONAL))

        goodwill_any = model.NewBoolVar(f"goodwill_any_{e}")
        model.Add(goodwill_any == sum(x[(e, idx_goodwill, s)] for s in OPERATIONAL))

        newyear_any = model.NewBoolVar(f"newyear_any_{e}")
        model.Add(newyear_any == sum(x[(e, idx_newyear, s)] for s in OPERATIONAL))

        xmas_newyear = _and2(model, christmas_any, newyear_any, f"xmas_newyear_{e}")
        xmas_goodwill = _and2(model, christmas_any, goodwill_any, f"xmas_goodwill_{e}")
        xmas_night_newyear_night = _and2(
            model,
            x[(e, idx_christmas, "N")],
            x[(e, idx_newyear, "N")],
            f"xmasnight_newyearnight_{e}",
        )
        premium_overlap_penalties.extend([xmas_newyear, xmas_goodwill, xmas_night_newyear_night])

    penalty_terms.append(("premium_overlap_preferences", sum(premium_overlap_penalties), 2500))

    # Priority 5: weekend fairness.
    weekend_day_indices = [i for i, d in enumerate(dates) if d.weekday() in (5, 6)]
    weekend_total_ops = len(weekend_day_indices) * 6
    weekend_counts: Dict[str, cp_model.IntVar] = {}
    weekend_dev_terms = []
    weekend_excess_terms = []
    actual_full_weekend_counts: Dict[str, cp_model.IntVar] = {}
    actual_full_weekend_dev_terms = []
    actual_full_weekend_total = 0
    for e in EMPLOYEES:
        c = model.NewIntVar(0, 366, f"weekend_ops_{e}")
        model.Add(c == sum(x[(e, d, s)] for d in weekend_day_indices for s in OPERATIONAL))
        weekend_counts[e] = c

        dev = model.NewIntVar(0, 4000, f"weekend_dev_{e}")
        model.Add(dev >= c * 10 - weekend_total_ops)
        model.Add(dev >= weekend_total_ops - c * 10)
        weekend_dev_terms.append(dev)

        excess = model.NewIntVar(0, 366, f"weekend_excess_{e}")
        model.Add(excess >= c * 10 - (weekend_total_ops + 10))
        model.Add(excess >= 0)
        weekend_excess_terms.append(excess)

        full_weekend_count = model.NewIntVar(0, len(weekends), f"actual_full_weekends_{e}")
        full_weekend_vars = []
        for wk in weekends:
            full_weekend = _and2(
                model,
                x[(e, wk.saturday_idx, "OFF")],
                x[(e, wk.sunday_idx, "OFF")],
                f"actual_full_weekend_{e}_{wk.weekend_number}",
            )
            full_weekend_vars.append(full_weekend)
        model.Add(full_weekend_count == sum(full_weekend_vars))
        actual_full_weekend_counts[e] = full_weekend_count
        actual_full_weekend_total += full_weekend_count

    for e in EMPLOYEES:
        dev = model.NewIntVar(0, len(weekends) * 10, f"actual_full_weekend_dev_{e}")
        model.Add(dev >= actual_full_weekend_counts[e] * 10 - actual_full_weekend_total)
        model.Add(dev >= actual_full_weekend_total - actual_full_weekend_counts[e] * 10)
        actual_full_weekend_dev_terms.append(dev)

    penalty_terms.append(("weekend_variance", sum(weekend_dev_terms), 3000))
    penalty_terms.append(("weekend_above_avg_plus_one", sum(weekend_excess_terms), 600))
    penalty_terms.append(("actual_full_weekend_variance", sum(actual_full_weekend_dev_terms), 3000))
    penalty_terms.append(("actual_full_weekend_total", -actual_full_weekend_total, 100))

    # Priority 6: shift-type fairness (preferred 71-75 each).
    shift_balance_terms = []
    for e in EMPLOYEES:
        for s in ("M", "A", "N"):
            c = model.NewIntVar(0, num_days, f"count_{s}_{e}")
            model.Add(c == sum(x[(e, d, s)] for d in range(num_days)))

            below = model.NewIntVar(0, 100, f"below_{s}_{e}")
            above = model.NewIntVar(0, 100, f"above_{s}_{e}")
            model.Add(below >= 71 - c)
            model.Add(below >= 0)
            model.Add(above >= c - 75)
            model.Add(above >= 0)
            shift_balance_terms.append(below)
            shift_balance_terms.append(above)

    penalty_terms.append(("shift_type_range_71_75", sum(shift_balance_terms), 3000))

    # Priority 7: shift weight fairness.
    shift_weight_vars: Dict[str, cp_model.IntVar] = {}
    shift_weight_total = 0
    for d in range(num_days):
        for s in OPERATIONAL:
            shift_weight_total += shift_weight_for_day(dates[d], s) * 2

    for e in EMPLOYEES:
        # Base shift weights.
        base_weight = sum(
            shift_weight_for_day(dates[d], s) * x[(e, d, s)] for d in range(num_days) for s in OPERATIONAL
        )

        # Consecutive-night additional fatigue weighting.
        extra_terms = []
        for d in range(1, num_days):
            sec = _and2(model, x[(e, d - 1, "N")], x[(e, d, "N")], f"night_second_{e}_{d}")
            extra_terms.append(sec)
        for d in range(2, num_days):
            third = _and3(
                model,
                x[(e, d - 2, "N")],
                x[(e, d - 1, "N")],
                x[(e, d, "N")],
                f"night_third_{e}_{d}",
            )
            extra_terms.append(third)

        score = model.NewIntVar(0, 50000, f"shift_weight_{e}")
        model.Add(score == base_weight + sum(extra_terms))
        shift_weight_vars[e] = score

    shift_weight_dev_terms = []
    shift_weight_excess_terms = []
    for e in EMPLOYEES:
        dev = model.NewIntVar(0, 100000, f"shift_weight_dev_{e}")
        model.Add(dev >= shift_weight_vars[e] * 10 - shift_weight_total)
        model.Add(dev >= shift_weight_total - shift_weight_vars[e] * 10)
        shift_weight_dev_terms.append(dev)

        # RQS rule: -1 per additional 2% above team average.
        excess2 = model.NewIntVar(0, 2000, f"shift_weight_2pct_excess_{e}")
        model.Add(excess2 >= shift_weight_vars[e] * 1000 - shift_weight_total * 102)
        model.Add(excess2 >= 0)
        shift_weight_excess_terms.append(excess2)

    penalty_terms.append(("shift_weight_variance", sum(shift_weight_dev_terms), 2200))
    penalty_terms.append(("shift_weight_above_2pct", sum(shift_weight_excess_terms), 60))

    # Standby and off balance.
    standby_dev_terms = []
    off_dev_terms = []
    standby_excess_terms = []
    night_excess_terms = []
    for e in EMPLOYEES:
        standby_count = model.NewIntVar(0, num_days, f"standby_count_{e}")
        off_count = model.NewIntVar(0, num_days, f"off_count_{e}")
        night_count = model.NewIntVar(0, num_days, f"night_count_{e}")
        model.Add(standby_count == sum(x[(e, d, "SB")] for d in range(num_days)))
        model.Add(off_count == sum(x[(e, d, "OFF")] for d in range(num_days)))
        model.Add(night_count == sum(x[(e, d, "N")] for d in range(num_days)))

        avg_sb = (2 * num_days) // 10
        avg_off = (2 * num_days) // 10

        sb_dev = model.NewIntVar(0, 1000, f"sb_dev_{e}")
        off_dev = model.NewIntVar(0, 1000, f"off_dev_{e}")
        model.Add(sb_dev >= standby_count - avg_sb)
        model.Add(sb_dev >= avg_sb - standby_count)
        model.Add(off_dev >= off_count - avg_off)
        model.Add(off_dev >= avg_off - off_count)
        standby_dev_terms.append(sb_dev)
        off_dev_terms.append(off_dev)

        sb_excess = model.NewIntVar(0, 1000, f"sb_excess_{e}")
        model.Add(sb_excess >= standby_count - int(avg_sb * 1.1))
        model.Add(sb_excess >= 0)
        standby_excess_terms.append(sb_excess)

        night_excess = model.NewIntVar(0, 1000, f"night_excess_{e}")
        model.Add(night_excess >= night_count - int(73 * 1.05))
        model.Add(night_excess >= 0)
        night_excess_terms.append(night_excess)

    penalty_terms.append(("standby_balance", sum(standby_dev_terms), 1000))
    penalty_terms.append(("off_balance", sum(off_dev_terms), 1000))
    penalty_terms.append(("standby_above_110pct", sum(standby_excess_terms), 200))
    penalty_terms.append(("night_above_105pct", sum(night_excess_terms), 200))

    # Priority 9: pairing diversity.
    pair_vars = {}
    pair_counts = {}
    for a, b in pairing_keys():
        day_shift_pairs = []
        for d in range(num_days):
            for s in OPERATIONAL:
                pv = _and2(model, x[(a, d, s)], x[(b, d, s)], f"pair_{a}_{b}_{d}_{s}")
                pair_vars[(a, b, d, s)] = pv
                day_shift_pairs.append(pv)
        c = model.NewIntVar(0, num_days * 3, f"pair_count_{a}_{b}")
        model.Add(c == sum(day_shift_pairs))
        pair_counts[(a, b)] = c

    total_pairings = num_days * 3
    avg_pair_scaled = int((total_pairings * 10) / len(pairing_keys()))

    pair_dev_terms = []
    pair_repetition_terms = []
    for a, b in pairing_keys():
        c = pair_counts[(a, b)]
        dev = model.NewIntVar(0, 10000, f"pair_dev_{a}_{b}")
        model.Add(dev >= c * 10 - avg_pair_scaled)
        model.Add(dev >= avg_pair_scaled - c * 10)
        pair_dev_terms.append(dev)

        excess = model.NewIntVar(0, 1000, f"pair_excess_{a}_{b}")
        model.Add(excess >= c - ceil(total_pairings / len(pairing_keys())))
        model.Add(excess >= 0)
        pair_repetition_terms.append(excess)

    penalty_terms.append(("pairing_diversity_variance", sum(pair_dev_terms), 800))
    penalty_terms.append(("pairing_repeat_penalty", sum(pair_repetition_terms), 500))

    objective = []
    for _, expr, weight in penalty_terms:
        objective.append(expr * weight)
    model.Minimize(sum(objective))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = settings.time_limit_seconds
    solver.parameters.random_seed = settings.random_seed
    solver.parameters.num_search_workers = settings.num_search_workers
    solver.parameters.log_search_progress = settings.cp_sat_search_logs

    if settings.cp_sat_search_logs:
        solver.log_callback = lambda msg: print(msg, end="", flush=True)

    callback = (
        _ProgressSolutionLogger(
            settings.progress_interval_seconds,
            dates,
            x,
            settings.stop_on_first_feasible,
        )
        if settings.progress_logging
        else None
    )
    heartbeat_stop = threading.Event()
    user_stop_requested = threading.Event()

    def heartbeat() -> None:
        started = time.monotonic()
        interval = max(1, settings.progress_interval_seconds)
        while not heartbeat_stop.wait(interval):
            elapsed = time.monotonic() - started
            if callback is None:
                print(f"[progress] t={elapsed:.1f}s solution_found=no searching...", flush=True)
                continue
            snap = callback.snapshot()
            if snap["solution_count"] == 0:
                print(
                    f"[progress] t={elapsed:.1f}s solution_found=no searching... no feasible solution yet",
                    flush=True,
                )
            else:
                obj = snap["last_objective"] if snap["last_objective"] is not None else float("nan")
                bound = snap["last_best_bound"] if snap["last_best_bound"] is not None else float("nan")
                fi = snap["last_fairness_index"] if snap["last_fairness_index"] is not None else float("nan")
                fi_rating = snap["last_fairness_rating"] if snap["last_fairness_rating"] is not None else "n/a"
                rqs = snap["last_rqs"] if snap["last_rqs"] is not None else float("nan")
                rqs_rating = snap["last_rqs_rating"] if snap["last_rqs_rating"] is not None else "n/a"
                print(
                    (
                        f"[progress] t={elapsed:.1f}s "
                        f"solution_found=yes "
                        f"solutions={snap['solution_count']} "
                        f"last_objective={obj:.0f} "
                        f"last_best_bound={bound:.0f} "
                        f"FI={fi:.2f} ({fi_rating}) "
                        f"RQS={rqs:.2f} ({rqs_rating}) "
                        f"hard_passed={snap['last_hard_passed']} "
                        f"hard_violations={snap['last_hard_violations']} "
                        f"last_conflicts={snap['last_conflicts']} "
                        f"last_branches={snap['last_branches']}"
                    ),
                    flush=True,
                )

    def keyboard_exit_listener() -> None:
        while not heartbeat_stop.is_set():
            try:
                line = sys.stdin.readline()
            except Exception:
                return
            if not line:
                return
            if line.strip().lower() in {"q", "quit", "exit", "x"}:
                print("[control] Early-stop requested by user keypress.", flush=True)
                user_stop_requested.set()
                try:
                    solver.StopSearch()
                except Exception:
                    pass
                return

    heartbeat_thread = None
    keyboard_thread = None
    if settings.progress_logging:
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        keyboard_thread = threading.Thread(target=keyboard_exit_listener, daemon=True)
        keyboard_thread.start()

    log("[solve] Starting CP-SAT solve...")
    if settings.progress_logging:
        log(
            (
                f"[solve] Settings: time_limit={settings.time_limit_seconds}s "
                f"workers={settings.num_search_workers} seed={settings.random_seed} "
                f"interval={settings.progress_interval_seconds}s "
                f"cp_sat_logs={settings.cp_sat_search_logs} "
                f"stop_on_first_feasible={settings.stop_on_first_feasible}"
            )
        )
        log("[control] Press q then Enter to stop early.")

    if settings.stop_on_first_feasible:
        solver.parameters.stop_after_first_solution = True

    try:
        if callback:
            if hasattr(solver, "SolveWithSolutionCallback"):
                status_code = solver.SolveWithSolutionCallback(model, callback)
            else:
                # Older/newer OR-Tools builds may expose callback solve as Solve(model, callback).
                status_code = solver.Solve(model, callback)
        else:
            status_code = solver.Solve(model)
    finally:
        heartbeat_stop.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=1.0)
        if keyboard_thread is not None:
            keyboard_thread.join(timeout=0.1)
    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    status = status_map.get(status_code, "UNKNOWN")

    assignments: Dict[Tuple[date, str], str] = {}
    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for d, day in enumerate(dates):
            for e in EMPLOYEES:
                for s in ASSIGNMENTS:
                    if solver.Value(x[(e, d, s)]) == 1:
                        assignments[(day, e)] = s
                        break

    term_values: Dict[str, int] = {}
    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for name, expr, _ in penalty_terms:
            term_values[name] = int(solver.Value(expr))

    if settings.progress_logging:
        print(
            (
                f"[solve] Finished status={status} wall_time={solver.WallTime():.2f}s "
                f"objective={solver.ObjectiveValue() if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 'n/a'} "
                f"best_bound={solver.BestObjectiveBound()} conflicts={solver.NumConflicts()} "
                f"branches={solver.NumBranches()} "
                f"early_stop_requested={user_stop_requested.is_set()}"
            ),
            flush=True,
        )

    return SolveResult(
        solved=status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE),
        status=status,
        assignments=assignments,
        objective_value=int(solver.ObjectiveValue()) if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE) else -1,
        best_objective_bound=solver.BestObjectiveBound(),
        objective_terms=term_values,
        solve_seconds=solver.WallTime(),
        iterations=solver.NumConflicts(),
        branches=solver.NumBranches(),
        early_stop_requested=user_stop_requested.is_set(),
    )
