import pytest

from scheduler import CircularDependencyError, UnknownDependencyError, topological_sort
from tests.helpers import make_task


def ids(tasks):
    return [t.id for t in tasks]


def assert_valid_order(tasks, ordered):
    position = {t.id: i for i, t in enumerate(ordered)}
    assert sorted(position) == sorted(t.id for t in tasks)
    for task in tasks:
        for dep in task.dependencies:
            assert position[dep] < position[task.id]


def test_empty_input():
    assert topological_sort([]) == []


def test_independent_tasks_keep_input_order():
    tasks = [make_task("c"), make_task("a"), make_task("b")]
    assert ids(topological_sort(tasks)) == ["c", "a", "b"]


def test_chain_is_ordered_even_when_given_reversed():
    tasks = [make_task("c", deps=["b"]), make_task("b", deps=["a"]), make_task("a")]
    assert ids(topological_sort(tasks)) == ["a", "b", "c"]


def test_diamond_dependencies():
    tasks = [
        make_task("deploy", deps=["backend", "frontend"]),
        make_task("backend", deps=["design"]),
        make_task("frontend", deps=["design"]),
        make_task("design"),
    ]
    ordered = topological_sort(tasks)
    assert_valid_order(tasks, ordered)
    assert ids(ordered)[0] == "design" and ids(ordered)[-1] == "deploy"


def test_duplicate_dependency_entries_are_counted_once():
    tasks = [make_task("b", deps=["a", "a"]), make_task("a")]
    assert ids(topological_sort(tasks)) == ["a", "b"]


def test_does_not_mutate_input():
    tasks = [make_task("b", deps=["a"]), make_task("a")]
    topological_sort(tasks)
    assert ids(tasks) == ["b", "a"]


def test_unknown_dependency():
    with pytest.raises(UnknownDependencyError, match="ghost"):
        topological_sort([make_task("a", deps=["ghost"])])


def test_self_dependency_is_a_cycle():
    with pytest.raises(CircularDependencyError, match="a"):
        topological_sort([make_task("a", deps=["a"])])


def test_two_task_cycle_names_both_tasks():
    tasks = [make_task("x", deps=["y"]), make_task("y", deps=["x"])]
    with pytest.raises(CircularDependencyError) as info:
        topological_sort(tasks)
    assert "x" in str(info.value) and "y" in str(info.value)


def test_cycle_is_detected_even_when_other_tasks_are_fine():
    tasks = [make_task("ok"), make_task("x", deps=["y"]), make_task("y", deps=["x"]), make_task("z", deps=["x"])]
    with pytest.raises(CircularDependencyError) as info:
        topological_sort(tasks)
    assert "ok" not in str(info.value)


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        topological_sort([make_task("a"), make_task("a")])


def test_errors_are_value_errors():
    assert issubclass(CircularDependencyError, ValueError)
    assert issubclass(UnknownDependencyError, ValueError)


def test_long_chain_does_not_hit_recursion_limit():
    n = 5000
    tasks = [make_task(f"t{i}", deps=[f"t{i - 1}"] if i else []) for i in range(n)]
    assert len(topological_sort(tasks)) == n
