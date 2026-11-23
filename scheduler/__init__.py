"""Multi-constraint task scheduler: dependencies, deadlines and a resource budget."""

from .dependency_graph import (
    CircularDependencyError,
    UnknownDependencyError,
    topological_sort,
)
from .dp_allocator import knapsack_allocate
from .engine import EngineResult, run_engine
from .greedy_scheduler import greedy_schedule
from .models import Task, validate_unique_ids
from .priority_queue import TaskPriorityQueue

__all__ = [
    "CircularDependencyError",
    "EngineResult",
    "Task",
    "TaskPriorityQueue",
    "UnknownDependencyError",
    "greedy_schedule",
    "knapsack_allocate",
    "run_engine",
    "topological_sort",
    "validate_unique_ids",
]
