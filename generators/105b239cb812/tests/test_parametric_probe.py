from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_parametric_probe_runs_protected_racket_and_writes_owner_replay_witness(tmp_path):
    task_dir = Path(__file__).resolve().parents[1]
    repo_root = task_dir.parents[1]
    script = task_dir / "workspace" / "parametric" / "probe.py"
    assert script.is_file(), f"missing {script}"
    report_path = tmp_path / "authoring.json"
    witness_path = tmp_path / "witness.json"
    qualification_path = tmp_path / "qualification.json"
    source_binding = {
        "task_id": "105b239cb812",
        "generator_sha256": "fixture",
        "files": [{"path": "fixture.py", "sha256": "0" * 64}],
    }
    qualification_path.write_text(
        json.dumps(
            {
                "schema": "arcpuzzles-parametric-qualification-v1",
                "status": "qualified",
                "task_id": "105b239cb812",
                "source_binding": source_binding,
            }
        )
    )
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
            "--witness",
            str(witness_path),
            "--qualification",
            str(qualification_path),
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
    witness = json.loads(witness_path.read_text())
    assert report["schema"] == "105b239cb812-parametric-authoring-v1"
    assert report["task_id"] == "105b239cb812"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert len(report["jobs"]) == 2
    assert {row["application"] for row in report["jobs"]} == {"direct", "inverse"}
    assert all(row["survivors"] == [row["application"]] for row in report["jobs"])
    assert all(row["all_python_labels_match_racket"] for row in report["jobs"])
    assert all(row["public_projection"]["query_answers_hidden"] for row in report["jobs"])
    assert all(row["public_projection"]["private_mutation_id_stable"] for row in report["jobs"])
    assert all(row["query_shapes"][-1] == [9, 29] for row in report["jobs"])
    assert all(
        {"local_crop_direct", "local_crop_inverse"} <= set(row["rivals_refuted"])
        for row in report["jobs"]
    )
    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["task_id"] == "105b239cb812"
    assert witness["source_binding"] == source_binding
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert witness["cases"]
    case = witness["cases"][0]
    assert case["ablation"] == "wrong_intermediate"
    assert case["output"] != case["counterfactual_output"]
