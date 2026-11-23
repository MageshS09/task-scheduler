"""Job sequencing with deadlines (greedy)."""

from __future__ import annotations

from collections.abc import Sequence

from .models import Task


def greedy_schedule(tasks: Sequence[Task]) -> tuple[list[Task | None], list[Task]]:
    """Pick the profit-maximizing set of unit-time tasks that each meet their own deadline.

    Tasks are considered by descending profit (ties: earlier deadline, then input
    order) and each is placed in the latest free slot at or before its deadline.
    Resource cost and dependencies are deliberately ignored here.

    A schedule can never use more than ``len(tasks)`` slots, so deadlines are
    capped at ``len(tasks)``; this keeps memory proportional to the input even
    for huge deadlines without changing which tasks are selected.

    Returns:
        ``(slots, selected)``: ``slots[i]`` is the task in slot ``i + 1`` (or ``None``),
        with trailing empty slots trimmed; ``selected`` lists the chosen tasks in slot order.

    Time O(n log n + n * d) with d = min(max deadline, n).
    """
    if not tasks:
        return [], []

    horizon = min(max(task.deadline for task in tasks), len(tasks))
    slots: list[Task | None] = [None] * horizon

    ranked = sorted(enumerate(tasks), key=lambda pair: (-pair[1].profit, pair[1].deadline, pair[0]))
    for _, task in ranked:
        for slot in range(min(task.deadline, horizon) - 1, -1, -1):
            if slots[slot] is None:
                slots[slot] = task
                break

    while slots and slots[-1] is None:
        slots.pop()
    selected = [task for task in slots if task is not None]
    return slots, selected
