"""Exercise the retained audit CLI, including its nonzero failure contract."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parents[1]
TOOL = TASK / "workspace/lesson_probe.py"


def load_tool():
    assert TOOL.is_file(), "retain a runnable lesson probe, not just reported counts"
    spec = importlib.util.spec_from_file_location("lesson_probe_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_separates_query_ambiguity_from_harmless_survival():
    tool = load_tool()
    rivals = {"identity": lambda x: x, "always_one": lambda x: [[1]]}
    demos = [{"input": [[1]], "output": [[1]]}]
    result = tool.score_lesson(rivals, demos, {"input": [[2]], "output": [[2]]})
    assert result == {"refuted": [], "survived_all": ["identity"],
                      "query_discriminates": ["always_one"]}
    result = tool.score_lesson(rivals, demos + [{"input": [[2]], "output": [[2]]}],
                               {"input": [[3]], "output": [[3]]})
    assert result["refuted"] == ["always_one"]


def test_cli_report_and_refuses_overwrite(tmp_path):
    load_tool()
    output = tmp_path / "report.json"
    command = [sys.executable, str(TOOL), "--library", str(TASK.parents[1]),
               "--seeds", "2", "--starts", "4", "--out", str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text())
    assert report["population"]["lesson_count"] == 32
    assert report["oracle"] == "python_mirror_not_independent"
    assert report["query_discriminating_lesson_count"] == 0
    assert report["canonical_shortcut_checks"]["public_command_order"]["matched"] == 5
    assert len(report["generator_sha256"]) == 64
    second = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert second.returncode != 0
    assert json.loads(output.read_text()) == report


def test_live_racket_cli_and_actual_runner(tmp_path):
    import os
    import pytest
    if not os.environ.get("RACKET_PATH"):
        pytest.skip("set RACKET_PATH to exercise the independent label runtime")
    load_tool()
    output = tmp_path / "racket.json"
    result = subprocess.run([
        sys.executable, str(TOOL), "--library", str(TASK.parents[1]),
        "--oracle", "racket", "--seeds", "1", "--starts", "4",
        "--bands", "easy", "--runner-lessons", "4", "--out", str(output),
    ], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text())
    assert report["oracle"] == "canonical_racket"
    assert report["actual_runner"]["checked"] == 4
    assert not report["mirror_mismatches"]
