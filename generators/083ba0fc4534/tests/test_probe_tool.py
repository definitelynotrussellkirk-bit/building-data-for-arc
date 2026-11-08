from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_probe_tool_reports_source_bound_contract_coverage(tmp_path):
    task_dir = Path(__file__).resolve().parents[1]
    repo_root = task_dir.parents[1]
    script = task_dir / "workspace" / "probe_consensus_contract.py"
    output = tmp_path / "probe.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "shared" / "runtime")
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--per-band",
            "8",
            "--seed-base",
            "7000",
            "--out",
            str(output),
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(output.read_text())
    assert report["task_id"] == "083ba0fc4534"
    assert report["rule_hash"] == "076637306d69"
    assert report["samples"] == 24
    assert report["unique_inputs"] == 24
    assert report["self_check_failures"] == []
    assert report["mirror_mismatches"] == []
    assert report["canonical_shortcuts_fit_all_canonical"] == {
        "first_nonzero_if_two_occupied": True
    }
    assert all(count == 24 for count in report["rival_refutations"].values())
    assert all(count == 24 for count in report["required_branch_firings"].values())
