"""Tests for the retained source-bound structural/shortcut probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "7842d7d91514"
ROOT = find_root(__file__)
PROBE = Path(__file__).resolve().parents[1] / "workspace" / "shape_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("shape_probe_7842d7d91514", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grid_hash_is_stable_and_shape_sensitive():
    probe = _load_probe()
    grid = [[0, 5], [2, 0]]
    assert probe.grid_hash(grid) == probe.grid_hash([[0, 5], [2, 0]])
    assert probe.grid_hash(grid) != probe.grid_hash([[0, 5, 2, 0]])


def test_scan_reports_lawful_unique_counterexamples_in_every_band():
    probe = _load_probe()
    generator, _, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    report = probe.scan(generator, per_band=8, seed_base=700_000)

    assert report["task_id"] == TASK_ID
    assert report["generator_sha256"] == source_hash
    assert report["draws"] == 24
    assert report["lawful_draws"] == 24
    assert report["unique_inputs"] >= 22
    assert report["canonical_profile_hits"] > 0
    assert report["palette_failures"] == 0
    assert report["same_size_dihedral_witnesses"] == 24
    assert all(count == 24 for count in report["rival_disagreements"].values())
    assert set(report["bands"]) == {"easy", "medium", "hard"}
    assert all(row["lawful"] == 8 for row in report["bands"].values())
    assert all(row["dihedral_witnesses"] == 8 for row in report["bands"].values())
