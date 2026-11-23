"""Min-heap wrapper that orders tasks by earliest deadline, then highest profit."""

from __future__ import annotations

import heapq
from collections.abc import Iterable
from itertools import count

from .models import Task


class TaskPriorityQueue:
    """Binary min-heap keyed by ``(deadline, -profit, insertion order)``.

    The insertion counter makes ordering stable and avoids ever comparing
    ``Task`` objects. ``push`` and ``pop`` are O(log n).
    """

    def __init__(self, tasks: Iterable[Task] = ()) -> None:
        self._heap: list[tuple[int, float, int, Task]] = []
        self._counter = count()
        for task in tasks:
            self.push(task)

    def push(self, task: Task) -> None:
        heapq.heappush(self._heap, (task.deadline, -task.profit, next(self._counter), task))

    def pop(self) -> Task:
        """Remove and return the highest-priority task. Raises ``IndexError`` when empty."""
        if not self._heap:
            raise IndexError("pop from an empty TaskPriorityQueue")
        return heapq.heappop(self._heap)[-1]

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    def drain(self) -> list[Task]:
        """Pop every task, returning them in priority order. O(n log n)."""
        return [self.pop() for _ in range(len(self))]
