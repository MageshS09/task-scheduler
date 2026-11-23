import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args):
    return subprocess.run([sys.executable, str(ROOT / "main.py"), *args], capture_output=True, text=True, cwd=ROOT, timeout=30, check=False)


def write(tmp_path, content, name="tasks.json"):
    path = tmp_path / name
    path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return str(path)


TASK = {"id": "a", "name": "A", "deadline": 1, "profit": 5, "resource_cost": 1}


def test_default_run_uses_builtin_sample():
    result = run_cli()
    assert result.returncode == 0
    assert "Total profit" in result.stdout and "Done." in result.stdout


def test_input_file_and_budget_precedence(tmp_path):
    path = write(tmp_path, {"resource_budget": 1, "tasks": [TASK, {**TASK, "id": "b", "name": "B", "deadline": 2}]})
    assert "Total resource cost used: 1" in run_cli("--input", path).stdout
    assert "Total resource cost used: 2" in run_cli("--input", path, "--budget", "5").stdout


def test_verbose_shows_every_stage():
    out = run_cli("--input", str(ROOT / "sample_tasks.json"), "--verbose").stdout
    for heading in ("1. Topological Order", "2. Priority Queue Order", "3. Greedy Schedule", "4. DP Resource Allocation"):
        assert heading in out


def test_demo_circular_reports_the_error():
    result = run_cli("--demo-circular")
    assert result.returncode == 0 and "CircularDependencyError" in result.stdout


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        "[1, 2]",
        {"tasks": "nope"},
        {"tasks": [1]},
        {"tasks": [{"id": "a"}]},
        {"tasks": [{**TASK, "deadline": 0}]},
        {"tasks": [{**TASK, "profit": "5"}]},
        {"tasks": [TASK, TASK]},
        {"tasks": [{**TASK, "dependencies": ["ghost"]}]},
        {"tasks": [{**TASK, "dependencies": ["a"]}]},
        {"resource_budget": -3, "tasks": [TASK]},
    ],
)
def test_bad_input_exits_with_error_not_traceback(tmp_path, content):
    result = run_cli("--input", write(tmp_path, content))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert result.stderr.strip()


def test_missing_input_file_is_reported():
    result = run_cli("--input", "does-not-exist.json")
    assert result.returncode == 1 and "Traceback" not in result.stderr
