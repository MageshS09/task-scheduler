"""Shared helpers for tests."""

from scheduler import Task


def make_task(id: str, deadline: int = 1, profit: float = 10.0, cost: int = 1, deps=None, name: str = "") -> Task:
    return Task(id=id, name=name or id, deadline=deadline, profit=profit, resource_cost=cost, dependencies=list(deps or []))
