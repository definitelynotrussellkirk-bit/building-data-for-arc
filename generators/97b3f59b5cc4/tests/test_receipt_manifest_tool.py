from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root


TASK = "97b3f59b5cc4"
ROOT = find_root(__file__)
TOOL_PATH = ROOT / "generators" / TASK / "workspace" / "receipt_manifest.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("receipt_manifest_tool", TOOL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_stage(root: Path, stage: str, *, subject: str = "abc123", exit_code: int = 0):
    checks = root / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    prefix = checks / f"{TASK}_after_{stage}"
    prefix.with_suffix(".receipt").write_text(
        json.dumps(
            {
                "exit": exit_code,
                "utc_end": "2026-10-11T00:00:00Z",
                "timed_out": False,
                "subject_sha16": subject,
                "run_id": "test-run",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    prefix.with_suffix(".log").write_text(f"{stage}\n", encoding="utf-8")
    if exit_code == 0:
        prefix.with_suffix(".ok").write_text(subject + "\n", encoding="utf-8")


def test_collects_complete_source_bound_stage_set(tmp_path):
    tool = load_tool()
    lint = tmp_path / "lint"
    selfcheck = tmp_path / "selfcheck"
    write_stage(lint, "lint")
    write_stage(selfcheck, "selfcheck")

    report = tool.collect_receipts(
        task=TASK,
        phase="after",
        source_dirs=[lint, selfcheck],
        stages=("lint", "selfcheck"),
    )

    assert report["complete"] is True
    assert report["subject_sha16"] == "abc123"
    assert report["missing_stages"] == []
    assert [row["stage"] for row in report["selected"]] == ["lint", "selfcheck"]
    assert all(len(row["receipt_sha256"]) == 64 for row in report["selected"])
    assert report["official_next_step"].startswith("Run the official battery --resume")


def test_rejects_mixed_subjects_and_failed_receipts(tmp_path):
    tool = load_tool()
    lint = tmp_path / "lint"
    selfcheck = tmp_path / "selfcheck"
    write_stage(lint, "lint", subject="subject-a")
    write_stage(selfcheck, "selfcheck", subject="subject-b", exit_code=2)

    report = tool.collect_receipts(
        task=TASK,
        phase="after",
        source_dirs=[lint, selfcheck],
        stages=("lint", "selfcheck"),
    )

    assert report["complete"] is False
    assert report["missing_stages"]
    assert report["problems"]
    assert not report["selected"] or all(row["exit"] == 0 for row in report["selected"])
