import itertools
import random

import pytest

from scheduler import knapsack_allocate
from tests.helpers import make_task


def bruteforce(tasks, budget):
    best = 0.0
    for size in range(len(tasks) + 1):
        for subset in itertools.combinations(tasks, size):
            if sum(t.resource_cost for t in subset) <= budget:
                best = max(best, sum(t.profit for t in subset))
    return best


def test_empty_tasks():
    assert knapsack_allocate([], 10) == ([], 0.0)


def test_budget_smaller_than_every_cost_gives_empty_allocation():
    assert knapsack_allocate([make_task("a", cost=5), make_task("b", cost=7)], 4) == ([], 0.0)


def test_zero_budget_still_takes_free_tasks():
    selected, profit = knapsack_allocate([make_task("free", profit=4, cost=0), make_task("paid", profit=9, cost=1)], 0)
    assert [t.id for t in selected] == ["free"] and profit == 4.0


def test_classic_knapsack():
    tasks = [make_task("a", profit=60, cost=10), make_task("b", profit=100, cost=20), make_task("c", profit=120, cost=30)]
    selected, profit = knapsack_allocate(tasks, 50)
    assert [t.id for t in selected] == ["b", "c"] and profit == 220.0


def test_greedy_by_ratio_would_be_wrong_here():
    tasks = [make_task("small", profit=10, cost=1), make_task("big", profit=18, cost=10)]
    selected, profit = knapsack_allocate(tasks, 10)
    assert [t.id for t in selected] == ["big"] and profit == 18.0


def test_selection_respects_budget_and_keeps_input_order():
    tasks = [make_task(f"t{i}", profit=float(i + 1), cost=i % 4 + 1) for i in range(9)]
    selected, profit = knapsack_allocate(tasks, 7)
    assert sum(t.resource_cost for t in selected) <= 7
    assert profit == sum(t.profit for t in selected)
    order = [tasks.index(t) for t in selected]
    assert order == sorted(order)


def test_budget_larger_than_total_cost_takes_everything():
    tasks = [make_task("a", profit=1, cost=2), make_task("b", profit=2, cost=3)]
    selected, profit = knapsack_allocate(tasks, 10**9)
    assert len(selected) == 2 and profit == 3.0


@pytest.mark.parametrize("budget", [-1, 2.5, "5", None, True])
def test_invalid_budget_raises_value_error(budget):
    with pytest.raises(ValueError, match="budget"):
        knapsack_allocate([make_task("a")], budget)


def test_matches_bruteforce_on_random_inputs():
    rng = random.Random(99)
    for _ in range(200):
        n = rng.randint(0, 9)
        tasks = [make_task(f"t{i}", profit=float(rng.randint(0, 40)), cost=rng.randint(0, 8)) for i in range(n)]
        budget = rng.randint(0, 25)
        selected, profit = knapsack_allocate(tasks, budget)
        assert sum(t.resource_cost for t in selected) <= budget
        assert profit == bruteforce(tasks, budget)
        assert profit == sum(t.profit for t in selected)
