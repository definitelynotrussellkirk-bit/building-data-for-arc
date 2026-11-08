from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def test_protected_racket_audit_writes_reusable_causal_case(tmp_path):
    task_dir = Path(__file__).resolve().parents[1]
    repo_root = task_dir.parents[1]
    script = task_dir / "workspace" / "parametric" / "audit.py"
    assert script.is_file(), f"missing {script}"
    report_path = tmp_path / "authoring.json"
    case_path = tmp_path / "audited-case.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "shared" / "runtime")]
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seed",
            "5",
            "--demos",
            "2",
            "--out",
            str(report_path),
            "--case",
            str(case_path),
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(report_path.read_text())
    case = json.loads(case_path.read_text())
    assert report["schema"] == "35368341e72e-parametric-authoring-v1"
    assert report["task_id"] == "35368341e72e"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["matched_inputs_across_settings"] is True
    assert len(report["jobs"]) == 2
    assert {row["assembly"] for row in report["jobs"]} == {
        "query_order",
        "fewest_cells_first",
    }
    assert all(row["declared_survivors"] == [row["assembly"]] for row in report["jobs"])
    assert all(row["tested_harmful_survivors"] == [] for row in report["jobs"])
    assert all(row["all_python_labels_match_racket"] for row in report["jobs"])
    assert all(row["public_projection"]["query_answers_hidden"] for row in report["jobs"])
    assert all(row["public_projection"]["future_queries_hidden"] for row in report["jobs"])
    assert all(row["query_shapes"][-1] == [30, 30] for row in report["jobs"])
    assert case["schema"] == "35368341e72e-audited-causal-case-v1"
    assert case["settings"] == {"assembly": "fewest_cells_first"}
    assert case["program"] != case["counterfactual_program"]
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "skip_a"
    intermediate = case["intermediate_value"]
    assert intermediate["active_cell_counts"] != intermediate["sorted_active_cell_counts"]
    assert intermediate["sorted_active_cell_counts"] == sorted(intermediate["active_cell_counts"])
