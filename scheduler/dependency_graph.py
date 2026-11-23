"""Dependency validation and topological ordering (Kahn's algorithm)."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from .models import Task, validate_unique_ids


class CircularDependencyError(ValueError):
    """Raised when the dependency graph contains a cycle."""


class UnknownDependencyError(ValueError):
    """Raised when a task depends on an id that is not in the task list."""


def topological_sort(tasks: Sequence[Task]) -> list[Task]:
    """Return tasks ordered so every task comes after all of its dependencies.

    Ties are broken by input order, so the result is deterministic. A dependency
    listed more than once is counted once.

    Raises:
        ValueError: On duplicate task ids.
        UnknownDependencyError: If a dependency id does not exist.
        CircularDependencyError: If the graph has a cycle (including a task that
            depends on itself). The message names the tasks that could not be ordered.

    Time O(V + E), space O(V + E).
    """
    validate_unique_ids(tasks)
    by_id: dict[str, Task] = {task.id: task for task in tasks}

    in_degree: dict[str, int] = {task.id: 0 for task in tasks}
    dependents: dict[str, list[str]] = {task.id: [] for task in tasks}
    for task in tasks:
        for dep in dict.fromkeys(task.dependencies):  # de-duplicate, keep order
            if dep not in by_id:
                raise UnknownDependencyError(f"Task {task.id!r} depends on unknown task {dep!r}")
            in_degree[task.id] += 1
            dependents[dep].append(task.id)

    queue = deque(task.id for task in tasks if in_degree[task.id] == 0)
    ordered: list[Task] = []
    while queue:
        current = queue.popleft()
        ordered.append(by_id[current])
        for dependent in dependents[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(ordered) != len(tasks):
        stuck = [task.id for task in tasks if in_degree[task.id] > 0]
        raise CircularDependencyError(
            "Circular dependency detected involving task(s): " + ", ".join(stuck)
        )
    return ordered
