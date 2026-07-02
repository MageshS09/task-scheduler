# Multi-Constraint Task Scheduler & Resource Allocator

A dependency-light Python project demonstrating four classic algorithm
families — **greedy algorithms**, **dynamic programming**, **graph
traversal**, and **heaps** — composed into a single, coherent scheduling
pipeline. Built as an interview portfolio project (Infosys Specialist
Programmer / Digital Specialist Engineer).

## Problem

Given a set of tasks, each with a deadline, a profit, a resource cost, and
zero or more dependencies on other tasks, decide:

1. What order must tasks run in, given their dependencies?
2. Which tasks can realistically be completed by their own deadline while
   maximizing profit?
3. Of those, which subset fits inside a shared, limited resource budget
   while still maximizing profit?

## Architecture

```
scheduler/
├── models.py              # Task dataclass + validation
├── dependency_graph.py     # Kahn's algorithm (BFS topological sort)
├── priority_queue.py       # Min-heap wrapper, orders by (deadline, -profit)
├── greedy_scheduler.py     # Classic job-sequencing-with-deadlines greedy
├── dp_allocator.py         # 0/1 knapsack DP for the resource budget
└── engine.py                # Orchestrates all four stages

main.py                    # CLI demo (argparse) over the scheduler package
demo/                       # Flask web demo (isolated, imports scheduler only)
api/, vercel.json           # Deployment-only shim so demo/ can be hosted on Vercel
```

`demo/` and `api/` are demo layers on top of the core engine — they only
*import* `scheduler`, never modify it, and none of the tests in `tests/`
depend on them.

### Pipeline (`engine.run_engine`)

1. **Topological sort** (`dependency_graph.py`, Kahn's algorithm) validates
   the dependency graph is a DAG and produces a dependency-respecting task
   order. Raises `CircularDependencyError` immediately if there's a cycle —
   nothing downstream is meaningful over an inconsistent task set.
   **Time: O(V + E). Space: O(V + E).**
2. **Priority queue** (`priority_queue.py`, binary min-heap) drains the
   topologically-ordered tasks by `(deadline, -profit)` to produce a
   recommended earliest-deadline-first execution order (reporting/utility
   output). **Push/pop: O(log n) each, O(n log n) to drain n tasks.**
3. **Greedy scheduler** (`greedy_scheduler.py`, classic "Job Sequencing
   With Deadlines") picks the profit-maximizing subset of tasks that can
   each finish by their own deadline, ignoring resource cost entirely.
   **Time: O(n log n + n·d)** where `d` = max deadline (slot search); the
   `n log n` term is the profit sort.
4. **DP allocator** (`dp_allocator.py`, 0/1 knapsack) takes the greedy
   stage's output and picks the optimal sub-subset that fits the shared
   resource budget. **Time: O(n · budget). Space: O(n · budget).**

Total pipeline complexity: `O(V + E) + O(n log n) + O(n log n + n·d) + O(n · budget)`.

## Running it

```bash
pip install -r requirements.txt
python main.py            # run the demo end-to-end
python -m pytest tests/ -v  # run the test suite
```

## CLI Reference

`main.py` is a thin demo layer over the `scheduler` package — it doesn't
change any of the tested engine logic, it just gives you a way to drive it.

```bash
python main.py                                          # built-in 7-task sample, budget 12
python main.py --input sample_tasks.json                # load tasks from a JSON file
python main.py --input sample_tasks.json --budget 25    # override the resource budget
python main.py --input sample_tasks.json --verbose      # show every pipeline stage, not just the final table
python main.py --demo-circular                          # trigger CircularDependencyError on request
```

| Flag | Effect |
|---|---|
| `--input <file.json>` | Load tasks (and optionally a `resource_budget`) from a JSON file instead of the hardcoded sample. Expected shape: `{"resource_budget": 15, "tasks": [ {"id", "name", "deadline", "profit", "resource_cost", "dependencies"}, ... ]}`. |
| `--budget <int>` | Set/override the resource budget. Precedence: `--budget` > `resource_budget` in the input file > default of `12`. |
| `--verbose` | Print each pipeline stage: topological order → priority queue order → greedy selection → DP allocation, before the final table. |
| `--demo-circular` | Ignores the normal task list and loads the inert `circular_dependency_demo` task pair from `--input` (or the bundled `sample_tasks.json`), which intentionally cycles, to show the engine's error handling on request. |

`sample_tasks.json` ships with 10 varied tasks, including a multi-level
dependency chain (`requirements → design → backend/frontend →
integration_tests → deploy`) and a `circular_dependency_demo` block that is
inert during a normal run and only used when `--demo-circular` is passed.

## Interview Talking Points

**Why isn't greedy alone enough here?**
The classic job-sequencing greedy algorithm (sort by profit, place each job
in the latest free slot at or before its deadline) is *provably optimal* —
but only for its own narrow objective: maximizing profit subject to
per-task deadlines, with no other constraints. Its optimality proof relies
on an exchange argument that only holds when jobs are otherwise
independent. The moment you introduce **dependencies** ("task B can't start
until task A is done") or a **shared resource budget**, that exchange
argument breaks down:

- A dependency can force a low-profit task to run *before* a high-profit
  one, even though pure profit-greedy would rather skip the low-profit task
  entirely. Greedy has no mechanism to "look ahead" and account for what a
  task unlocks.
- Greedy job-sequencing also has zero awareness of resource cost — it will
  happily schedule two tasks that are individually feasible but jointly
  exceed the available budget, because deadline-feasibility and
  budget-feasibility are different constraints.

That's why this project runs **topological sort first**: it's the only way
to guarantee a task ordering that is even *valid* before profit
optimization is attempted, and it's what surfaces circular dependencies
early with a clear error instead of an infinite loop or silently wrong
schedule.

**Why is DP needed for the resource-constrained allocation step?**
Choosing the best subset of tasks under a single shared budget is the 0/1
knapsack problem, which is **NP-hard in general** — there is no known
greedy exchange rule that is always safe, because the "best" choice at a
given remaining budget depends on the best solutions to *smaller* budgets
(optimal substructure), and the same sub-budget is reused across many
choices (overlapping subproblems). That's exactly the signature that makes
a problem a good fit for dynamic programming: build up `dp[i][b]` = best
achievable profit using the first `i` tasks and budget `b`, and reuse those
answers instead of recomputing them. The DP here runs in pseudo-polynomial
time `O(n · budget)`, which is efficient in practice for realistic budgets,
even though the general knapsack problem is NP-hard.

**Why compose them this way instead of one big algorithm?**
Each stage solves a genuinely different sub-problem with a genuinely
different tool, and keeping them as separate, independently testable
modules mirrors how you'd actually explain (and defend) a system design in
an interview: graph validity first, then a fast greedy filter for the
easy constraint (deadlines), then DP for the hard constraint (a shared,
non-separable budget). It's also a natural teaching example of *when greedy
is optimal vs. when it silently isn't* — a very common interview question
in its own right.

**Known limitation (and a good follow-up question to expect):**
Neither the greedy stage nor the DP stage enforces that a task's
dependencies are *also* in the final selection — each stage optimizes its
own constraint in isolation (deadlines, then budget) rather than solving
one combined "dependency + deadline + budget" objective. Topological sort
guarantees any selected tasks would run in a *valid order relative to each
other*, but not that a selected task's prerequisites survived the later
filtering steps. Enforcing that is the "precedence-constrained knapsack"
problem: for a tree-shaped dependency structure it can be solved with a
tree-knapsack DP (`dp[node][budget]` = best profit in node's subtree using
at most `budget`, combined bottom-up); for a general DAG with shared
prerequisites it's harder still, since a naively-summed cost would
double-count a dependency shared by multiple selected tasks. This project
keeps `dp_allocator.py` as a clean, independently-testable textbook 0/1
knapsack on purpose — the tree-knapsack extension is a natural "what would
you change" answer to have ready.

## Edge Cases Handled

| Case | Behavior |
|---|---|
| Circular dependency | `CircularDependencyError` raised by `topological_sort` / `run_engine`, with the offending task ids named |
| Dependency on unknown task id | `UnknownDependencyError` raised |
| Empty task list | Every function returns an empty/zero result, no error |
| `deadline <= 0` | `ValueError` raised in `Task.__post_init__` |
| `resource_cost < 0` | `ValueError` raised in `Task.__post_init__` |
| `profit < 0` | `ValueError` raised in `Task.__post_init__` |
| Resource budget smaller than every task's cost | `knapsack_allocate` returns `([], 0.0)` — a valid, empty allocation, not an error |
| Duplicate task ids | `ValueError` raised by `validate_unique_ids` / `run_engine` |

## Dependencies

The core `scheduler` package itself imports nothing beyond the standard
library. `requirements.txt` at the repo root additionally lists `pytest`
(for the test suite) and `flask` (for the `demo/` web layer) — `flask` is
there only because Vercel's Python builder reads a single root-level
`requirements.txt` for deployment; `demo/requirements.txt` lists the same
dependency for anyone who wants to install just the web demo on its own.

## Web Demo (Flask)

`demo/app.py` is a minimal Flask app over the same, unmodified `scheduler`
engine:

- `GET /` — a single HTML page (no JS framework, just a form + `fetch()`)
  with "Load Sample Tasks" and "Load Circular-Dependency Example" buttons.
- `POST /schedule` — accepts `{"resource_budget": int, "tasks": [...]}` and
  returns the scheduling result as JSON.

**Run it locally:**

```bash
pip install -r demo/requirements.txt
flask --app demo/app run          # http://127.0.0.1:5000
# or: python demo/app.py
```

**Live deployment:** the same app is deployed on Vercel via a thin
`api/index.py` shim + `vercel.json` at the repo root (deployment plumbing
only — it imports `demo/app.py`, nothing under `scheduler/` or `demo/`
changes because of it). See the link at the top of this README, or deploy
your own copy: `vercel --prod` from the repo root (Vercel auto-detects
`api/index.py` as a Python serverless function).

## How to Demo This

**Terminal (CLI):**

```bash
python -m pytest tests/ -v                          # 1. show all 37 tests passing
python main.py --input sample_tasks.json --verbose  # 2. show the full pipeline on a 10-task project
python main.py --demo-circular                      # 3. show error handling on a bad dependency graph
```

**Browser (web demo):** open the deployed link (or run `flask --app demo/app run` locally), click **Load Sample Tasks** → **Schedule** to see the table populate, then click **Load Circular-Dependency Example** → **Schedule** to see the API reject an invalid graph with a clear error instead of hanging.

**What to say:** "This is a four-stage pipeline — topological sort to
validate the dependency graph, a greedy job-sequencing algorithm to pick the
profit-maximizing tasks under deadlines, and a 0/1 knapsack DP to fit those
into a shared resource budget, because greedy alone can't solve a
shared-budget constraint optimally. The web demo and the `--verbose` CLI
flag both call the exact same `scheduler.run_engine()` — nothing about the
core algorithm changes between the terminal and the browser, only how the
result gets presented. The circular-dependency example shows the engine
failing fast with a clear error instead of an infinite loop when the
dependency graph has a cycle."
