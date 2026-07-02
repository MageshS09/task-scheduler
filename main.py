"""CLI entry point: loads tasks (hardcoded sample or a JSON file), runs the
scheduling engine, and prints the results.

Usage:
    python main.py                                   # built-in sample, budget 12
    python main.py --input sample_tasks.json          # load tasks from a file
    python main.py --input sample_tasks.json --budget 20
    python main.py --verbose                          # show every pipeline stage
    python main.py --demo-circular                    # show CircularDependencyError handling
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

from scheduler import (
    CircularDependencyError,
    EngineResult,
    Task,
    UnknownDependencyError,
    run_engine,
)

DEFAULT_RESOURCE_BUDGET = 12
DEFAULT_INPUT_FILE = Path(__file__).parent / "sample_tasks.json"


def build_sample_tasks() -> list[Task]:
    """A small project-planning scenario with real dependency chains."""
    return [
        Task(id="requirements", name="Gather Requirements", deadline=1, profit=40.0, resource_cost=2),
        Task(
            id="design",
            name="System Design",
            deadline=2,
            profit=70.0,
            resource_cost=3,
            dependencies=["requirements"],
        ),
        Task(
            id="backend",
            name="Build Backend",
            deadline=4,
            profit=120.0,
            resource_cost=5,
            dependencies=["design"],
        ),
        Task(
            id="frontend",
            name="Build Frontend",
            deadline=4,
            profit=90.0,
            resource_cost=4,
            dependencies=["design"],
        ),
        Task(
            id="integration_tests",
            name="Integration Tests",
            deadline=5,
            profit=60.0,
            resource_cost=3,
            dependencies=["backend", "frontend"],
        ),
        Task(
            id="docs",
            name="Write Documentation",
            deadline=3,
            profit=15.0,
            resource_cost=1,
            dependencies=["requirements"],
        ),
        Task(
            id="deploy",
            name="Deploy to Production",
            deadline=6,
            profit=150.0,
            resource_cost=6,
            dependencies=["integration_tests"],
        ),
    ]


def _task_from_dict(raw: dict) -> Task:
    return Task(
        id=raw["id"],
        name=raw["name"],
        deadline=raw["deadline"],
        profit=raw["profit"],
        resource_cost=raw["resource_cost"],
        dependencies=raw.get("dependencies", []),
    )


def load_tasks_from_file(
    path: Path, use_circular_demo: bool = False
) -> Tuple[List[Task], Optional[int]]:
    """Load tasks (and an optional resource_budget) from a JSON file.

    Expected shape: ``{"resource_budget": <int>, "tasks": [ {...}, ... ]}``.
    A file may also carry an inert ``circular_dependency_demo`` list of tasks
    that intentionally forms a cycle; pass ``use_circular_demo=True`` to load
    that list instead, for demonstrating error handling on request.

    Raises:
        ValueError: If the file is missing the requested task list.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with path.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)

    key = "circular_dependency_demo" if use_circular_demo else "tasks"
    raw_tasks = data.get(key)
    if raw_tasks is None:
        raise ValueError(f"Input file {path} has no {key!r} key")

    tasks = [_task_from_dict(raw) for raw in raw_tasks]
    budget = data.get("resource_budget")
    return tasks, budget


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_verbose_stages(result: EngineResult, budget: int) -> None:
    print_section("1. Topological Order (dependency-respecting)")
    print(" -> ".join(result.topological_order) or "(no tasks)")

    print_section("2. Priority Queue Order (earliest deadline, ties by higher profit)")
    print(" -> ".join(result.priority_order) or "(no tasks)")

    print_section("3. Greedy Schedule (max profit under deadlines only)")
    for slot_index, task in enumerate(result.greedy_schedule, start=1):
        label = f"{task.name} (id={task.id}, profit={task.profit})" if task else "-- empty --"
        print(f"  slot {slot_index}: {label}")
    greedy_profit = sum(t.profit for t in result.greedy_selected)
    print(f"  Greedy-selected tasks: {[t.id for t in result.greedy_selected]}")
    print(f"  Greedy total profit (ignores resource budget): {greedy_profit}")

    print_section(f"4. DP Resource Allocation (budget = {budget})")
    total_cost = sum(t.resource_cost for t in result.final_selected)
    print(f"  Final selected tasks: {[t.id for t in result.final_selected]}")
    print(f"  Total resource cost used: {total_cost} / {budget}")
    print(f"  Final total profit: {result.total_profit}")


def print_results_table(tasks: List[Task], result: EngineResult) -> None:
    selected_ids = {t.id for t in result.final_selected}
    order_index = {task_id: i for i, task_id in enumerate(result.topological_order)}
    rows = sorted(tasks, key=lambda t: order_index.get(t.id, len(order_index)))

    headers = ["id", "name", "deadline", "profit", "selected"]
    table = [
        [
            task.id,
            task.name,
            str(task.deadline),
            f"{task.profit:g}",
            "yes" if task.id in selected_ids else "no",
        ]
        for task in rows
    ]

    widths = [
        max(len(headers[col]), *(len(row[col]) for row in table)) if table else len(headers[col])
        for col in range(len(headers))
    ]

    def format_row(cells: List[str]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths))

    print()
    print(format_row(headers))
    print("  ".join("-" * width for width in widths))
    for row in table:
        print(format_row(row))

    print()
    print(f"Total resource cost used: {sum(t.resource_cost for t in result.final_selected)}")
    print(f"Total profit: {result.total_profit:g}")


def run_circular_demo(input_path: Path) -> None:
    print_section("Demo: Circular Dependency Detection")
    print(f"Loading 'circular_dependency_demo' tasks from {input_path} ...")
    tasks, _ = load_tasks_from_file(input_path, use_circular_demo=True)
    try:
        run_engine(tasks, resource_budget=DEFAULT_RESOURCE_BUDGET)
        print("  No error raised -- the demo task set is not actually circular.")
    except CircularDependencyError as exc:
        print(f"  Caught expected CircularDependencyError: {exc}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Multi-Constraint Task Scheduler & Resource Allocator (CLI demo)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to a JSON file of tasks (default: built-in sample tasks)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=None,
        help="Resource budget (default: value from --input file, or 12)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print step-by-step: topological order -> greedy selection -> DP allocation",
    )
    parser.add_argument(
        "--demo-circular",
        action="store_true",
        help=(
            "Load the inert 'circular_dependency_demo' task set from --input "
            "(or the bundled sample_tasks.json) and show CircularDependencyError handling"
        ),
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    print("Multi-Constraint Task Scheduler & Resource Allocator")
    print("=" * 55)

    if args.demo_circular:
        input_path = args.input if args.input is not None else DEFAULT_INPUT_FILE
        try:
            run_circular_demo(input_path)
        except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
            print(f"Error loading {input_path}: {exc}", file=sys.stderr)
            sys.exit(1)
        print()
        print("Done.")
        return

    file_budget: Optional[int] = None
    if args.input is not None:
        try:
            tasks, file_budget = load_tasks_from_file(args.input)
        except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
            print(f"Error loading {args.input}: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        tasks = build_sample_tasks()

    budget = args.budget if args.budget is not None else (
        file_budget if file_budget is not None else DEFAULT_RESOURCE_BUDGET
    )

    try:
        result = run_engine(tasks, resource_budget=budget)
    except (CircularDependencyError, UnknownDependencyError, ValueError) as exc:
        print(f"Scheduling failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print_verbose_stages(result, budget)
        print()

    print_results_table(tasks, result)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
