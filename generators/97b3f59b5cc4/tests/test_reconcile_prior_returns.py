from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root


TASK = "97b3f59b5cc4"
ROOT = find_root(__file__)
TOOL_PATH = ROOT / "generators" / TASK / "workspace" / "reconcile_prior_returns.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("reconcile_prior_returns", TOOL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_report_binds_current_source_and_preserves_both_prior_return_improvements():
    tool = load_tool()
    report = tool.build_report(
        ROOT,
        exact_sample_indexes=(0, 1),
        exact_difficulties=(None,),
        ordinary_seeds=(0, 1),
        ordinary_difficulties=(None, "easy"),
        ordinary_sample_count=8,
    )

    assert report["status"] == "reconciled_current_source"
    assert report["task_id"] == TASK
    assert report["generator_sha256"] == report["retained_counterexample"]["generator_sha256"]
    assert {row["return_id"] for row in report["prior_returns"]} == {
        "review-abe8247bc7f3032c:v0001",
        "review-30f42b66093700f5:v0001",
    }
    assert report["canonical"]["failures"] == []
    assert report["exact_controls"]["failures"] == []
    assert report["exact_controls"]["cases"] == 2048
    assert report["retired_controls"]["all_rejected"] is True
    assert report["teaching_windows"]["failures"] == []
    assert report["retained_counterexample"]["replayed_exactly"] is True
    assert report["retained_counterexample"]["rival_differs"] is True


def test_report_marks_a_source_binding_conflict_instead_of_claiming_reconciliation(tmp_path):
    import json
    import shutil

    task_root = tmp_path / "generators" / TASK
    (task_root / "counterexamples").mkdir(parents=True)
    shutil.copy2(ROOT / "generators" / TASK / "generator.py", task_root / "generator.py")
    counterexample_path = task_root / "counterexamples" / "shared-color-opposite-fates.json"
    record = json.loads(
        (ROOT / "generators" / TASK / "counterexamples" / "shared-color-opposite-fates.json").read_text()
    )
    record["generator_sha256"] = "0" * 64
    counterexample_path.write_text(json.dumps(record))

    canonical_path = tmp_path / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_path.parent.mkdir(parents=True)
    canonical_path.symlink_to(ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl")

    tool = load_tool()
    report = tool.build_report(
        tmp_path,
        exact_sample_indexes=(0,),
        exact_difficulties=(None,),
        ordinary_seeds=(0,),
        ordinary_difficulties=(None,),
        ordinary_sample_count=3,
    )

    assert report["status"] == "conflict_detected"
    assert report["retained_counterexample"]["source_bound"] is False


def test_cli_exits_nonzero_when_report_detects_a_conflict(tmp_path):
    import json
    import shutil

    task_root = tmp_path / "generators" / TASK
    (task_root / "counterexamples").mkdir(parents=True)
    shutil.copy2(ROOT / "generators" / TASK / "generator.py", task_root / "generator.py")
    counterexample_path = task_root / "counterexamples" / "shared-color-opposite-fates.json"
    record = json.loads(
        (ROOT / "generators" / TASK / "counterexamples" / "shared-color-opposite-fates.json").read_text()
    )
    record["generator_sha256"] = "0" * 64
    counterexample_path.write_text(json.dumps(record))

    canonical_path = tmp_path / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_path.parent.mkdir(parents=True)
    canonical_path.symlink_to(ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl")

    tool = load_tool()
    out = tmp_path / "conflict-report.json"
    exit_code = tool.main(
        [
            "--root",
            str(tmp_path),
            "--out",
            str(out),
            "--exact-sample-indexes",
            "0",
            "--exact-difficulties",
            "none",
            "--ordinary-seeds",
            "0",
            "--ordinary-difficulties",
            "none",
            "--ordinary-sample-count",
            "3",
        ]
    )

    assert exit_code == 1
    assert json.loads(out.read_text())["status"] == "conflict_detected"
