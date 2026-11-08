from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "audit_replay.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ticket_audit_replay", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rival_differs_only_on_query_decoy_cross():
    module = load_module()
    grid = [
        [0, 3, 0],
        [4, 4, 4],
        [0, 3, 0],
    ]
    assert module.same_color_targets(grid) == []
    assert module.occupancy_targets(grid) == [(1, 1)]
    assert module.paint_targets(grid, module.same_color_targets(grid)) == [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    assert module.paint_targets(grid, module.occupancy_targets(grid)) == [
        [0, 0, 0],
        [0, 8, 0],
        [0, 0, 0],
    ]


def test_pinned_record_hash_is_canonical_json():
    module = load_module()
    assert module.canonical_json_sha256({"b": 2, "a": 1}) == (
        "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    )
