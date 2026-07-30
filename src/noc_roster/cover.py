from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .spec import GROUP_A, GROUP_B


@dataclass
class CoverRequest:
    absent_employee: str
    absent_group: str


@dataclass
class CoverAllocation:
    selected_employee: str | None
    priority_used: int
    reason: str


def allocate_cover(
    request: CoverRequest,
    standby_employees: List[str],
    off_employees: List[str],
) -> CoverAllocation:
    """Apply cover priority from the specification section 16.1."""

    absent_group_set = GROUP_A if request.absent_group == "A" else GROUP_B

    same_group_standby = [e for e in standby_employees if e in absent_group_set and e != request.absent_employee]
    if same_group_standby:
        return CoverAllocation(
            selected_employee=same_group_standby[0],
            priority_used=1,
            reason="Priority 1: standby employee from same group.",
        )

    other_standby = [e for e in standby_employees if e != request.absent_employee]
    if other_standby:
        return CoverAllocation(
            selected_employee=other_standby[0],
            priority_used=2,
            reason="Priority 2: other standby employee.",
        )

    off_pool = [e for e in off_employees if e != request.absent_employee]
    if off_pool:
        return CoverAllocation(
            selected_employee=off_pool[0],
            priority_used=3,
            reason="Priority 3: off employee.",
        )

    return CoverAllocation(
        selected_employee=None,
        priority_used=4,
        reason="Priority 4: manual operational decision required.",
    )


def cover_payload(allocation: CoverAllocation) -> Dict[str, str | int | None]:
    return {
        "selected_employee": allocation.selected_employee,
        "priority_used": allocation.priority_used,
        "reason": allocation.reason,
    }
