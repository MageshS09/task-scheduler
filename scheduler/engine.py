"""Four-stage scheduling pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .dependency_graph import topological_sort
from .dp_allocator import knapsack_allocate
from .greedy_scheduler import greedy_schedule
from .models import Task, validate_unique_ids
from .priority_queue import TaskPriorityQueue


@dataclass
class EngineResult:
    """Everything produced by :func:`run_engine`, stage by stage."""

    topological_order: list[str] = field(default_factory=list)
    priority_order: list[str] = field(default_factory=list)
    greedy_schedule: list[Task | None] = field(default_factory=list)
    greedy_selected: list[Task] = field(default_factory=list)
    final_selected: list[Task] = field(default_factory=list)
    total_profit: float = 0.0


def run_engine(tasks: Sequence[Task], resource_budget: int) -> EngineResult:
    """Validate dependencies, then pick tasks by deadline and resource budget.

    1. Topological sort (fails fast on unknown or circular dependencies).
    2. Priority queue ordering by (deadline, -profit).
    3. Greedy job sequencing under deadlines.
    4. 0/1 knapsack over the greedy selection under ``resource_budget``.

    Each selection stage optimizes its own constraint; a selected task's prerequisites
    are *not* guaranteed to be selected (see the README's known limitation).

    Raises:
        ValueError: Duplicate ids or an invalid budget.
        UnknownDependencyError, CircularDependencyError: Invalid dependency graph.
    """
    validate_unique_ids(tasks)
    ordered = topological_sort(tasks)
    priority = TaskPriorityQueue(ordered).drain()
    schedule, greedy_selected = greedy_schedule(tasks)
    final_selected, total_profit = knapsack_allocate(greedy_selected, resource_budget)
    return EngineResult(
        topological_order=[task.id for task in ordered],
        priority_order=[task.id for task in priority],
        greedy_schedule=schedule,
        greedy_selected=greedy_selected,
        final_selected=final_selected,
        total_profit=total_profit,
    )
