import pytest

from scheduler import TaskPriorityQueue
from tests.helpers import make_task


def test_orders_by_deadline_then_higher_profit():
    queue = TaskPriorityQueue(
        [
            make_task("late", deadline=5, profit=100),
            make_task("early_low", deadline=1, profit=10),
            make_task("early_high", deadline=1, profit=50),
        ]
    )
    assert [t.id for t in queue.drain()] == ["early_high", "early_low", "late"]


def test_full_ties_are_stable_in_insertion_order():
    queue = TaskPriorityQueue([make_task("a"), make_task("b"), make_task("c")])
    assert [t.id for t in queue.drain()] == ["a", "b", "c"]


def test_push_pop_len_and_bool():
    queue = TaskPriorityQueue()
    assert len(queue) == 0 and not queue
    queue.push(make_task("a", deadline=2))
    queue.push(make_task("b", deadline=1))
    assert len(queue) == 2 and queue
    assert queue.pop().id == "b"
    assert queue.pop().id == "a"


def test_pop_from_empty_raises_index_error():
    with pytest.raises(IndexError):
        TaskPriorityQueue().pop()


def test_drain_empties_the_queue():
    queue = TaskPriorityQueue([make_task("a")])
    queue.drain()
    assert len(queue) == 0 and queue.drain() == []
