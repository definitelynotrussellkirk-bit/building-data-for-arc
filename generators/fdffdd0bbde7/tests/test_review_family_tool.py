"""Checks for the reusable bounded parametric-family reviewer."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from reviewer_support import find_root


TASK_ID = "fdffdd0bbde7"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
TOOL_PATH = PARAMETRIC / "tools/review_family.py"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_seed_report_covers_supported_boundaries_and_stress_case():
    prototype = _load("review_family_test_prototype", PROTOTYPE_PATH)
    tool = _load("review_family_test_tool", TOOL_PATH)
    report = tool.collect_seed_report(
        prototype,
        seed=11,
        demo_counts=(2, 6),
        query_counts=(1, 4),
    )
    assert report["seed"] == 11
    assert report["combinations"] == 4
    assert report["episodes"] == 8
    assert report["labeled_pairs_checked"] == 52
    assert report["matched_input_instances"] == 26
    assert report["distinct_inputs"] == 10
    assert report["setting_disagreements"] == 26
    assert report["stress_30x30"] == 2
    assert report["teaching_failures"] == []
    assert report["determinism_failures"] == []
    assert report["branch_failures"] == []


def test_display_path_accepts_outputs_outside_repo(tmp_path):
    tool = _load("review_family_test_tool_display", TOOL_PATH)
    outside = tmp_path / "review.json"
    assert tool.display_path(outside) == str(outside)
    assert tool.display_path(ROOT / "inside.json") == "inside.json"


def test_build_review_supports_batched_seed_ranges_and_racket_only_runs():
    tool = _load("review_family_test_tool_batches", TOOL_PATH)
    batch = tool.build_review(seed_start=9, seed_count=1, racket_seeds=())
    assert [row["seed"] for row in batch["seed_reports"]] == [9]
    assert batch["racket"]["calls"] == 0
    racket_only = tool.build_review(seed_start=20, seed_count=0, racket_seeds=())
    assert racket_only["seed_reports"] == []
    assert racket_only["totals"]["episodes"] == 0
