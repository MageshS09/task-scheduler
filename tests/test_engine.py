import json
from pathlib import Path

import pytest

from scheduler import CircularDependencyError, Task, UnknownDependencyError, run_engine
from tests.helpers import make_task

ROOT = Path(__file__).resolve().parent.parent


def sample_tasks(key="tasks"):
    data = json.loads((ROOT / "sample_tasks.json").read_text(encoding="utf-8"))
    return [Task(**raw) for raw in data[key]], data


def test_empty_task_list():
    result = run_engine([], resource_budget=10)
    assert result.topological_order == [] and result.final_selected == [] and result.total_profit == 0.0


def test_stages_are_reported():
    tasks = [make_task("b", deadline=2, profit=5, cost=1, deps=["a"]), make_task("a", deadline=1, profit=9, cost=1)]
    result = run_engine(tasks, resource_budget=5)
    assert result.topological_order == ["a", "b"]
    assert result.priority_order == ["a", "b"]
    assert [t.id for t in result.greedy_selected] == ["a", "b"]
    assert [t.id for t in result.final_selected] == ["a", "b"]
    assert result.total_profit == 14.0


def test_budget_limits_final_selection_but_not_greedy_selection():
    tasks = [make_task("a", deadline=1, profit=10, cost=6), make_task("b", deadline=2, profit=8, cost=6)]
    result = run_engine(tasks, resource_budget=6)
    assert len(result.greedy_selected) == 2
    assert [t.id for t in result.final_selected] == ["a"]
    assert result.total_profit == 10.0


def test_final_selection_is_always_a_subset_of_greedy_selection():
    tasks, data = sample_tasks()
    result = run_engine(tasks, resource_budget=data["resource_budget"])
    assert {t.id for t in result.final_selected} <= {t.id for t in result.greedy_selected}
    assert sum(t.resource_cost for t in result.final_selected) <= data["resource_budget"]


def test_sample_file_expected_result():
    tasks, data = sample_tasks()
    result = run_engine(tasks, resource_budget=data["resource_budget"])
    assert sorted(t.id for t in result.final_selected) == ["backend", "deploy", "frontend"]
    assert result.total_profit == 360.0


def test_circular_demo_set_raises():
    tasks, _ = sample_tasks("circular_dependency_demo")
    with pytest.raises(CircularDependencyError):
        run_engine(tasks, resource_budget=12)


def test_unknown_dependency_raises():
    with pytest.raises(UnknownDependencyError):
        run_engine([make_task("a", deps=["nope"])], resource_budget=1)


def test_duplicate_ids_raise_before_scheduling():
    with pytest.raises(ValueError, match="Duplicate"):
        run_engine([make_task("a"), make_task("a")], resource_budget=1)


def test_negative_budget_raises():
    with pytest.raises(ValueError, match="budget"):
        run_engine([make_task("a")], resource_budget=-1)


def test_known_limitation_dependencies_are_not_enforced_in_selection():
    # Documented in the README: a selected task's prerequisites may be dropped by later stages.
    tasks = [make_task("base", deadline=1, profit=1, cost=5), make_task("top", deadline=2, profit=50, cost=5, deps=["base"])]
    result = run_engine(tasks, resource_budget=5)
    assert [t.id for t in result.final_selected] == ["top"]


def test_input_is_not_mutated():
    tasks = [make_task("b", deps=["a"]), make_task("a")]
    run_engine(tasks, resource_budget=3)
    assert [t.id for t in tasks] == ["b", "a"] and tasks[0].dependencies == ["a"]
