"""Contract tests for the reusable canonical-shortcut probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE = Path(__file__).with_name("probe_canonical_shortcuts.py")


def _load_probe():
    assert PROBE.is_file(), "canonical-shortcut probe has not been implemented"
    spec = importlib.util.spec_from_file_location("probe_canonical_shortcuts", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_exposes_reusable_pure_helpers():
    probe = _load_probe()
    assert callable(probe.cell_differences)
    assert callable(probe.scheduled_cases)
    assert callable(probe.rotation_summaries)


def test_cell_differences_reports_shape_and_value_disagreements():
    probe = _load_probe()
    assert probe.cell_differences([[1, 0], [0, 2]], [[1, 3], [0, 2]]) == [
        {"row": 0, "column": 1, "intended": 0, "rival": 3}
    ]


def test_scheduled_cases_cover_every_index_needed_by_sliding_windows():
    probe = _load_probe()
    cases = probe.scheduled_cases(seed=7, starts=3, window=5, difficulties=(None, "easy"))
    assert [(case["difficulty"], case["sample_index"]) for case in cases] == [
        (None, 0), (None, 1), (None, 2), (None, 3), (None, 4), (None, 5), (None, 6),
        ("easy", 0), ("easy", 1), ("easy", 2), ("easy", 3), ("easy", 4),
        ("easy", 5), ("easy", 6),
    ]

def test_rotation_summaries_check_every_leave_one_out_query():
    probe = _load_probe()
    checked = {}
    for sample_index in range(6):
        checked[(None, sample_index)] = {
            "sample_index": sample_index,
            "shortcuts": {
                "rival": {"matches_reference": sample_index not in {1, 4}}
            },
        }
    rotations = probe.rotation_summaries(
        checked,
        ["rival"],
        starts=1,
        window=5,
        difficulties=(None,),
    )
    assert len(rotations) == 6
    assert all(rotation["shortcut_refuted"] == {"rival": True} for rotation in rotations)
    assert [rotation["query_sample_index"] for rotation in rotations] == list(range(6))
