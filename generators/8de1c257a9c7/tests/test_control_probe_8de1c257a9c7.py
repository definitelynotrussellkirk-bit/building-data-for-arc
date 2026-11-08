"""Regression test for the reusable exact-control contract probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "8de1c257a9c7"
ROOT = find_root(__file__)
PROBE_PATH = ROOT / f"generators/{TASK_ID}/workspace/probe_controls.py"
_RUNTIME_GENERATOR = ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
_LIBRARY_GENERATOR = ROOT / f"generators/{TASK_ID}/generator.py"
GENERATOR_PATH = (
    _RUNTIME_GENERATOR if _RUNTIME_GENERATOR.is_file() else _LIBRARY_GENERATOR
)


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "probe_controls_8de1c257a9c7", PROBE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_control_probe_passes_the_full_schedule_contract():
    probe = _load_probe()
    report = probe.run_probe(GENERATOR_PATH, seeds=(17, 421))
    assert report["status"] == "pass", report
    assert report["schedule_slots_checked"] == 16
    assert report["checks"]["none_override_noop"] == 80
    assert report["checks"]["same_value_override_identity"] == 64
    assert report["checks"]["dimension_override_axis_isolation"] == 32
    assert report["checks"]["invalid_integer_rejection"] == 7
    assert report["failures"] == []


def test_source_tree_runtime_bootstrap_candidate(tmp_path):
    probe = _load_probe()
    generator = tmp_path / "generators/8de1c257a9c7/generator.py"
    generator.parent.mkdir(parents=True)
    generator.write_text("# fixture\n", encoding="utf-8")
    runtime = tmp_path / "shared/runtime"
    (runtime / "puzzle_generators").mkdir(parents=True)
    assert probe.runtime_search_paths(generator) == (runtime,)
