"""Task model and input validation."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@dataclass
class Task:
    """A unit of work with a deadline, a profit, a resource cost and prerequisites.

    Every task takes exactly one time slot. ``deadline`` is the last slot (1-based)
    in which it may run.

    Raises:
        ValueError: If any field has an invalid type or value.
    """

    id: str
    name: str
    deadline: int
    profit: float
    resource_cost: int
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Task id must be a non-empty string")
        if not isinstance(self.name, str):
            raise ValueError(f"Task {self.id!r}: name must be a string")
        if not _is_int(self.deadline):
            raise ValueError(f"Task {self.id!r}: deadline must be an integer")
        if self.deadline <= 0:
            raise ValueError(f"Task {self.id!r}: deadline must be positive, got {self.deadline}")
        if not _is_number(self.profit) or not math.isfinite(self.profit):
            raise ValueError(f"Task {self.id!r}: profit must be a finite number")
        if self.profit < 0:
            raise ValueError(f"Task {self.id!r}: profit must not be negative, got {self.profit}")
        if not _is_int(self.resource_cost):
            raise ValueError(f"Task {self.id!r}: resource_cost must be an integer")
        if self.resource_cost < 0:
            raise ValueError(f"Task {self.id!r}: resource_cost must not be negative, got {self.resource_cost}")
        if not isinstance(self.dependencies, list) or not all(isinstance(d, str) for d in self.dependencies):
            raise ValueError(f"Task {self.id!r}: dependencies must be a list of task ids")


def validate_unique_ids(tasks: Iterable[Task]) -> None:
    """Raise ``ValueError`` naming every task id that appears more than once."""
    seen: set = set()
    duplicates: list = []
    for task in tasks:
        if task.id in seen and task.id not in duplicates:
            duplicates.append(task.id)
        seen.add(task.id)
    if duplicates:
        raise ValueError(f"Duplicate task ids: {', '.join(duplicates)}")
