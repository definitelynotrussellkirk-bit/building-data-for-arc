from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


TASK_DIR = Path(__file__).resolve().parents[1]
PROBE = TASK_DIR / "workspace" / "review_probe.py"
REPO_ROOT = TASK_DIR.parents[1]


def test_review_probe_runs_complete_contract(tmp_path: Path) -> None:
    report_path = tmp_path / "probe.json"
    result = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            "--samples-per-band",
            "6",
            "--json-out",
            str(report_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    stdout_report = json.loads(result.stdout)
    file_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert stdout_report == file_report
    assert stdout_report["status"] == "pass"
    assert stdout_report["canonical"]["pairs_checked"] == 3
    assert stdout_report["randomized"]["cases_checked"] == 18
    assert stdout_report["randomized"]["two_demo_windows_checked"] == 15
    assert stdout_report["randomized"]["easy_hard_contrasts_checked"] == 6
    assert stdout_report["randomized"]["easy_hard_differences"] == 6
    assert stdout_report["overrides"]["boundary_cases_checked"] == 64
    assert stdout_report["overrides"]["unknown_override_rejected"] is True
    assert stdout_report["failures"] == []


def test_review_probe_rejects_nonpositive_sample_count() -> None:
    result = subprocess.run(
        [sys.executable, str(PROBE), "--samples-per-band", "0"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert result.returncode != 0
    assert "positive integer" in result.stderr
