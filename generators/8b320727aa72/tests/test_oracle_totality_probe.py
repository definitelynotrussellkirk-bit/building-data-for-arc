from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root


TASK_ID = "8b320727aa72"
ROOT = find_root(__file__)
PROBE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "probes" / "oracle_totality_probe.py"
)
SPEC = importlib.util.spec_from_file_location("oracle_totality_probe", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_novel_background_substitution_separates_total_rule_from_erasure_shortcut():
    case = probe.build_counterexample(root=ROOT)

    assert case["base_generator_domain_errors"] == []
    assert "anomaly changes a consensus background cell" in case["counterexample_domain_errors"]
    assert case["intended_python_mirror"] != case["erasure_only_rival_output"]

    row, col = case["local_insertion_coordinate"]
    assert case["intended_python_mirror"][row][col] == 1
    assert case["erasure_only_rival_output"][row][col] == case["background_color"]
    assert case["inserted_color"] not in {
        1,
        case["background_color"],
        case["separator_color"],
    }
    assert case["rival_fits_canonical_erasure_grammar"] is True
    assert case["canonical_rival_fit"]["errors"] == []
    assert case["canonical_rival_fit"]["pairs"] >= 1
    assert case["canonical_rival_fit"]["fits"] == case["canonical_rival_fit"]["pairs"]
    assert case["rival_fits_all_canonical_demonstrations"] is True
