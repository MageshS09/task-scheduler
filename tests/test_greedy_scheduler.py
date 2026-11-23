import itertools
import random

from scheduler import greedy_schedule
from tests.helpers import make_task


def feasible(subset):
    """A unit-time job set is schedulable iff, sorted by deadline, the k-th job has deadline >= k."""
    return all(task.deadline >= k for k, task in enumerate(sorted(subset, key=lambda t: t.deadline), start=1))


def best_profit_bruteforce(tasks):
    best = 0.0
    for size in range(len(tasks) + 1):
        for subset in itertools.combinations(tasks, size):
            if feasible(subset):
                best = max(best, sum(t.profit for t in subset))
    return best


def test_empty():
    assert greedy_schedule([]) == ([], [])


def test_classic_example():
    tasks = [
        make_task("a", deadline=2, profit=100),
        make_task("b", deadline=1, profit=19),
        make_task("c", deadline=2, profit=27),
        make_task("d", deadline=1, profit=25),
        make_task("e", deadline=3, profit=15),
    ]
    slots, selected = greedy_schedule(tasks)
    assert sorted(t.id for t in selected) == ["a", "c", "e"]
    assert sum(t.profit for t in selected) == 142
    assert [t.id for t in slots] == ["c", "a", "e"]


def test_each_selected_task_meets_its_deadline_and_slots_are_unique():
    tasks = [make_task(f"t{i}", deadline=d, profit=p) for i, (d, p) in enumerate([(1, 5), (1, 9), (2, 4), (3, 8), (3, 1)])]
    slots, selected = greedy_schedule(tasks)
    for index, task in enumerate(slots, start=1):
        if task is not None:
            assert index <= task.deadline
    assert len({t.id for t in selected}) == len(selected)


def test_more_tasks_than_slots_drops_lowest_profit():
    tasks = [make_task("low", deadline=1, profit=1), make_task("high", deadline=1, profit=9)]
    _, selected = greedy_schedule(tasks)
    assert [t.id for t in selected] == ["high"]


def test_huge_deadlines_do_not_allocate_huge_tables():
    tasks = [make_task("a", deadline=10**9, profit=1), make_task("b", deadline=10**9, profit=2)]
    slots, selected = greedy_schedule(tasks)
    assert len(slots) <= 2 and len(selected) == 2


def test_gaps_are_possible_and_trailing_gaps_trimmed():
    slots, selected = greedy_schedule([make_task("a", deadline=1, profit=1)])
    assert [t.id for t in slots] == ["a"] and len(selected) == 1


def test_ignores_resource_cost():
    _, selected = greedy_schedule([make_task("a", deadline=1, profit=5, cost=10**6)])
    assert len(selected) == 1


def test_zero_profit_tasks_do_not_displace_others():
    _, selected = greedy_schedule([make_task("zero", deadline=1, profit=0), make_task("real", deadline=1, profit=3)])
    assert [t.id for t in selected] == ["real"]


def test_matches_bruteforce_on_random_inputs():
    rng = random.Random(1234)
    for _ in range(200):
        n = rng.randint(1, 8)
        tasks = [make_task(f"t{i}", deadline=rng.randint(1, 6), profit=float(rng.randint(0, 30))) for i in range(n)]
        _, selected = greedy_schedule(tasks)
        assert feasible(selected)
        assert sum(t.profit for t in selected) == best_profit_bruteforce(tasks)


def test_does_not_mutate_input():
    tasks = [make_task("a", deadline=1, profit=1), make_task("b", deadline=1, profit=2)]
    greedy_schedule(tasks)
    assert [t.id for t in tasks] == ["a", "b"]
