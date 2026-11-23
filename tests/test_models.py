import pytest

from scheduler import Task, validate_unique_ids
from tests.helpers import make_task


def test_valid_task_defaults_to_no_dependencies():
    task = Task(id="a", name="A", deadline=1, profit=0, resource_cost=0)
    assert task.dependencies == []


def test_default_dependency_lists_are_not_shared():
    first = Task(id="a", name="A", deadline=1, profit=1, resource_cost=1)
    second = Task(id="b", name="B", deadline=1, profit=1, resource_cost=1)
    first.dependencies.append("x")
    assert second.dependencies == []


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"deadline": 0}, "deadline"),
        ({"deadline": -3}, "deadline"),
        ({"deadline": 1.5}, "deadline"),
        ({"deadline": "2"}, "deadline"),
        ({"deadline": True}, "deadline"),
        ({"profit": -1}, "profit"),
        ({"profit": float("nan")}, "profit"),
        ({"profit": float("inf")}, "profit"),
        ({"profit": "10"}, "profit"),
        ({"resource_cost": -1}, "resource_cost"),
        ({"resource_cost": 2.5}, "resource_cost"),
        ({"resource_cost": None}, "resource_cost"),
        ({"id": ""}, "id"),
        ({"id": 7}, "id"),
        ({"name": None}, "name"),
        ({"dependencies": "a"}, "dependencies"),
        ({"dependencies": [1]}, "dependencies"),
    ],
)
def test_invalid_fields_raise_value_error(kwargs, message):
    base = {"id": "a", "name": "A", "deadline": 1, "profit": 1.0, "resource_cost": 1}
    base.update(kwargs)
    with pytest.raises(ValueError, match=message):
        Task(**base)


def test_zero_profit_and_zero_cost_are_allowed():
    Task(id="a", name="A", deadline=1, profit=0.0, resource_cost=0)


def test_validate_unique_ids_accepts_unique_and_empty():
    validate_unique_ids([])
    validate_unique_ids([make_task("a"), make_task("b")])


def test_validate_unique_ids_names_each_duplicate_once():
    tasks = [make_task("a"), make_task("b"), make_task("a"), make_task("a"), make_task("b")]
    with pytest.raises(ValueError, match="a, b"):
        validate_unique_ids(tasks)
