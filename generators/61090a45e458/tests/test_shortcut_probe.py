"""Regression tests for the reusable declared-rival witness probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_DIR / "workspace" / "shortcut_probe.py"
SPEC = importlib.util.spec_from_file_location("shortcut_probe_61090a45e458", PROBE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_pins_canonical_fit_witness_and_all_query_rotations():
    report = PROBE.run_probe(starts=6, seeds=[17])

    assert report["status"] == "pass"
    assert report["canonical_demonstrations"] == 3
    fit = report["canonical_shortcut_fit"]["top_left_target_only"]
    assert fit == {"pairs": 3, "fits": 3, "mismatch_indices": []}

    witness = report["witness_by_rival"]["top_left_target_only"]
    assert witness["self_check"] == []
    assert witness["different_cells"]
    assert "target_not_top_left" in witness["semantic_witnesses"]
    assert witness["intended_output"] != witness["rival_output"]

    assert report["production"]["lessons"] == 18
    assert report["production"]["ambiguities"] == 0
    assert report["rotations"]["queries"] == 54
    assert report["rotations"]["ambiguities"] == 0
