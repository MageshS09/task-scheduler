"""0/1 knapsack allocation under a shared resource budget."""

from __future__ import annotations

from collections.abc import Sequence

from .models import Task


def knapsack_allocate(tasks: Sequence[Task], budget: int) -> tuple[list[Task], float]:
    """Choose the subset of ``tasks`` with maximum total profit whose total
    ``resource_cost`` does not exceed ``budget``.

    Returns ``(selected, total_profit)`` with ``selected`` in input order. If nothing
    fits, returns ``([], 0.0)``; that is a valid allocation, not an error.

    Raises:
        ValueError: If ``budget`` is not a non-negative integer.

    The budget is capped at the total cost of all tasks (a larger budget cannot
    change the answer), which bounds the table size. Time O(n * B), space O(n * B)
    with B = min(budget, total cost).
    """
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise ValueError("resource budget must be an integer")
    if budget < 0:
        raise ValueError(f"resource budget must not be negative, got {budget}")
    if not tasks:
        return [], 0.0

    capacity = min(budget, sum(task.resource_cost for task in tasks))
    best = [0.0] * (capacity + 1)  # best[b] = max profit using budget <= b over tasks seen so far
    took = [bytearray(capacity + 1) for _ in tasks]  # took[i][b]: task i improved best[b]

    for i, task in enumerate(tasks):
        cost, profit = task.resource_cost, task.profit
        for b in range(capacity, cost - 1, -1):
            candidate = best[b - cost] + profit
            if candidate > best[b]:
                best[b] = candidate
                took[i][b] = 1

    selected: list[Task] = []
    b = capacity
    for i in range(len(tasks) - 1, -1, -1):
        if took[i][b]:
            selected.append(tasks[i])
            b -= tasks[i].resource_cost
    selected.reverse()
    return selected, float(sum(task.profit for task in selected))
