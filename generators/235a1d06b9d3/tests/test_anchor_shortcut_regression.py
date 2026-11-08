"""Regression for the row-1/background-anchor domain collapse."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import canonical_path, find_root  # noqa: E402

TASK_ID = "235a1d06b9d3"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"
SPEC = importlib.util.spec_from_file_location("anchor_repair_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _canonical_pairs():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task missing")


def test_row1_anchor_shortcut_is_declared_and_really_fits_all_canonical_pairs():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"row1_col1_background"}
    rival = GEN.CANONICAL_SHORTCUTS["row1_col1_background"]
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_exact_anchor_discriminator_is_valid_and_refutes_shortcut():
    grid = [
        [3, 0, 3, 0, 0],
        [7, 0, 3, 3, 3],
        [3, 3, 3, 3, 3],
    ]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == [
        [3, 0, 3, 0, 0],
        [7, 0, 3, 3, 3],
        [3, 6, 3, 6, 6],
    ]
    assert GEN.CANONICAL_SHORTCUTS["row1_col1_background"](grid) == [
        [3, 0, 3, 0, 0],
        [7, 0, 3, 3, 3],
        [6, 0, 6, 0, 0],
    ]
    assert GEN.SEMANTIC_WITNESSES["row1_col1_is_not_the_background"](grid)
    assert GEN.WITNESS_RIVALS["row1_col1_is_not_the_background"] == [
        "row1_col1_background"
    ]


def test_every_general_profile_carries_a_row1_signal_decoy_and_refutes_shortcut():
    rival = GEN.CANONICAL_SHORTCUTS["row1_col1_background"]
    for profile in GEN.GENERAL_PROFILES:
        for seed in range(20):
            grid = GEN.generate(1000 + seed, seed * 7 + 3, scene_profile=profile)
            info = GEN._analysis(grid)
            assert info["errors"] == []
            assert info["scene_profile"] == profile
            assert grid[1][1] == info["signal"]
            assert grid[1][1] != info["background"]
            assert info["row1_decoy_count"] >= 1
            assert rival(grid) != GEN.rule_mirror(grid)


def test_public_profiles_remain_exact_linked_morphologies_without_decoys():
    for profile in GEN.PUBLIC_PROFILES:
        for seed in range(20):
            grid = GEN.generate(2000 + seed, seed * 11 + 5, scene_profile=profile)
            info = GEN._analysis(grid)
            assert info["errors"] == []
            assert GEN.canonical_profile_signature(grid) == profile
            assert info["row1_decoy_count"] == 0
            assert grid[1][1] == info["background"]


def test_signal_decoys_are_only_allowed_in_row1_not_lower_context():
    grid = GEN.generate(41, 73, scene_profile="distinct_cue_color")
    info = GEN._analysis(grid)
    assert GEN.self_check(grid) == []
    lower = [row[:] for row in grid]
    lower[2][2] = info["signal"]
    assert GEN.self_check(lower)


def test_distribution_change_is_versioned():
    assert GEN.VERSION == "3.1.0"
