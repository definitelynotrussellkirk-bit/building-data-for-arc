from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


HOME = Path(__file__).resolve().parents[1]
TOOL = HOME / "workspace" / "semantic_census.py"


def test_semantic_census_tool_is_source_bound_and_reproducible(tmp_path: Path) -> None:
    assert TOOL.is_file(), "workspace/semantic_census.py must exist"
    report = tmp_path / "census.json"
    command = [
        sys.executable,
        str(TOOL),
        "--lessons-per-band",
        "3",
        "--json-out",
        str(report),
    ]
    first = subprocess.run(command, check=True, capture_output=True, text=True)
    first_report = json.loads(report.read_text())
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    second_report = json.loads(report.read_text())
    assert first.stdout == second.stdout
    assert first_report == second_report
    assert first_report["status"] == "pass"
    assert first_report["lessons"] == 9
    assert first_report["inputs"] == 36
    assert first_report["invalid_inputs"] == 0
    assert first_report["unidentifiable_lessons"] == 0
    assert first_report["generator_sha256"]
    assert first_report["tool_sha256"]
    assert set(first_report["bands"]) == {"easy", "medium", "hard"}
    assert all(
        count == first_report["inputs"]
        for count in first_report["rival_disagreements"].values()
    )
