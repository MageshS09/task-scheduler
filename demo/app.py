"""Minimal Flask demo: a single page plus ``POST /schedule`` over ``scheduler.run_engine``."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, jsonify, request

from scheduler import Task, run_engine

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "sample_tasks.json"
DEFAULT_BUDGET = 12
# The demo may be public, so bound the work a single request can ask for.
MAX_TASKS = 500
MAX_BUDGET = 100_000

app = Flask(__name__)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Task Scheduler Demo</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#1f2937}
textarea{width:100%;height:16rem;font-family:monospace}
button{margin:.25rem .25rem .25rem 0;padding:.4rem .8rem}
table{border-collapse:collapse;margin-top:1rem;width:100%}
th,td{border:1px solid #d1d5db;padding:.3rem .5rem;text-align:left}
.error{color:#b91c1c;font-weight:600}
</style></head><body>
<h1>Multi-Constraint Task Scheduler</h1>
<p>Edit the JSON (<code>resource_budget</code> and <code>tasks</code>) or load an example, then schedule.</p>
<button id="sample">Load Sample Tasks</button>
<button id="circular">Load Circular-Dependency Example</button>
<textarea id="input" aria-label="Tasks JSON">{}</textarea><br>
<button id="run"><strong>Schedule</strong></button>
<div id="out"></div>
<script>
const input = document.getElementById("input"), out = document.getElementById("out");
const show = (el, text) => { el.textContent = text; };
async function load(url) {
  const res = await fetch(url);
  input.value = JSON.stringify(await res.json(), null, 2);
}
document.getElementById("sample").onclick = () => load("/sample");
document.getElementById("circular").onclick = () => load("/sample?circular=1");
document.getElementById("run").onclick = async () => {
  out.replaceChildren();
  let body;
  try { body = JSON.parse(input.value); } catch (e) { const p = document.createElement("p"); p.className = "error"; show(p, "Invalid JSON: " + e.message); out.append(p); return; }
  const res = await fetch("/schedule", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  const data = await res.json();
  if (!res.ok) { const p = document.createElement("p"); p.className = "error"; show(p, data.error); out.append(p); return; }
  const table = document.createElement("table");
  const head = table.insertRow();
  for (const h of ["id", "name", "deadline", "profit", "cost", "selected"]) { const th = document.createElement("th"); show(th, h); head.append(th); }
  for (const t of data.tasks) {
    const row = table.insertRow();
    for (const v of [t.id, t.name, t.deadline, t.profit, t.resource_cost, t.selected ? "yes" : "no"]) show(row.insertCell(), String(v));
  }
  const summary = document.createElement("p");
  show(summary, `Total profit: ${data.total_profit} | resource used: ${data.resource_used} / ${data.resource_budget}`);
  out.append(summary, table);
};
load("/sample");
</script></body></html>
"""


def parse_tasks(raw_tasks: object) -> list[Task]:
    """Build tasks from request JSON, raising ``ValueError`` with a readable message."""
    if not isinstance(raw_tasks, list):
        raise ValueError("'tasks' must be a list")
    if len(raw_tasks) > MAX_TASKS:
        raise ValueError(f"At most {MAX_TASKS} tasks are allowed")
    tasks = []
    for position, raw in enumerate(raw_tasks, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Task #{position} must be an object")
        missing = [key for key in ("id", "name", "deadline", "profit", "resource_cost") if key not in raw]
        if missing:
            raise ValueError(f"Task #{position} is missing: {', '.join(missing)}")
        tasks.append(
            Task(
                id=raw["id"],
                name=raw["name"],
                deadline=raw["deadline"],
                profit=raw["profit"],
                resource_cost=raw["resource_cost"],
                dependencies=raw.get("dependencies", []),
            )
        )
    return tasks


@app.get("/")
def index() -> str:
    return PAGE


@app.get("/sample")
def sample():
    """Serve the bundled example; ``?circular=1`` returns the intentionally cyclic task set."""
    data = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
    if request.args.get("circular"):
        return jsonify({"resource_budget": DEFAULT_BUDGET, "tasks": data["circular_dependency_demo"]})
    return jsonify({"resource_budget": data.get("resource_budget", DEFAULT_BUDGET), "tasks": data["tasks"]})


@app.post("/schedule")
def schedule():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    budget = payload.get("resource_budget", DEFAULT_BUDGET)
    if isinstance(budget, bool) or not isinstance(budget, int) or not 0 <= budget <= MAX_BUDGET:
        return jsonify({"error": f"'resource_budget' must be an integer from 0 to {MAX_BUDGET}"}), 400
    try:
        tasks = parse_tasks(payload.get("tasks"))
        result = run_engine(tasks, resource_budget=budget)
    except ValueError as exc:  # includes circular / unknown-dependency errors
        return jsonify({"error": str(exc)}), 400

    chosen = {task.id for task in result.final_selected}
    return jsonify(
        {
            "resource_budget": budget,
            "resource_used": sum(task.resource_cost for task in result.final_selected),
            "total_profit": result.total_profit,
            "topological_order": result.topological_order,
            "priority_order": result.priority_order,
            "greedy_selected": [task.id for task in result.greedy_selected],
            "final_selected": [task.id for task in result.final_selected],
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "deadline": task.deadline,
                    "profit": task.profit,
                    "resource_cost": task.resource_cost,
                    "selected": task.id in chosen,
                }
                for task in tasks
            ],
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
