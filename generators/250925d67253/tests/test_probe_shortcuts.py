from __future__ import annotations

import importlib.util
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_ROOT / "workspace" / "probe_shortcuts.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("probe_shortcuts_250925d67253", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_records_canonical_fit_and_exact_generated_disagreement():
    probe = _load_probe()
    report = probe.build_report(
        seed=0,
        sample_index=0,
        difficulty="medium",
        overrides={
            "permutation_kind": "mixed_fixed",
            "marker_density": "dense",
            "palette_band": "low",
        },
    )

    assert report["task_id"] == "250925d67253"
    assert report["selected_rival"] == "bounding_box_center"
    assert report["canonical_pair_count"] == 8
    assert report["canonical_fit"]["bounding_box_center"]["matches"] == 8
    assert report["canonical_fit"]["nearest_anchor"]["matches"] == 8
    assert report["canonical_fit"]["median_marker"]["matches"] == 8

    witness = report["generated_witness"]
    assert witness["self_check_errors"] == []
    assert witness["outputs_differ"] is True
    assert witness["differing_cells"]
    first = witness["differing_cells"][0]
    row, column = first["row"], first["column"]
    assert witness["intended_output"][row][column] == first["intended"]
    assert witness["rival_output"][row][column] == first["rival"]
    assert witness["generator_call"] == {
        "seed": 0,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": {
            "permutation_kind": "mixed_fixed",
            "marker_density": "dense",
            "palette_band": "low",
        },
    }
