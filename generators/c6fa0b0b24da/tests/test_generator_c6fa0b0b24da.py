"""Focused base-generator review for c6fa0b0b24da."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "c6fa0b0b24da"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("_test_c6fa0b0b24da_generator", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_all_original_labels_match_independent_python_rule():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_generation_is_valid_nontrivial_and_deterministic(difficulty):
    for index in range(64):
        first = GEN.generate(81, index, difficulty=difficulty)
        second = GEN.generate(81, index, difficulty=difficulty)
        assert first == second
        assert first is not second
        assert GEN.self_check(first, difficulty=difficulty) == []
        out = GEN.rule_mirror(first)
        assert out != first
        assert any(v == 0 for row in out for v in row)


def test_public_axes_are_strict_and_observable():
    for palette, color in GEN.PALETTE_WITNESSES.items():
        grid = GEN.generate(
            22, 5, difficulty="hard", grid_h=16, grid_w=18,
            palette_kind=palette, color=color, num_cells=7,
        )
        assert GEN.observe_overrides(grid) == {
            "grid_h": 16,
            "grid_w": 18,
            "palette_kind": palette,
            "color": color,
            "num_cells": 7,
        }
        assert GEN.self_check(grid) == []
    for bad in [
        {"typo_axis": 1}, {"grid_h": True}, {"grid_w": 3},
        {"color": 0}, {"num_cells": 1}, {"palette_kind": "bad"},
        {"palette_kind": "warm", "color": GEN.PALETTE_WITNESSES["cool"]},
    ]:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 0, **bad)


def test_generation_does_not_touch_global_random_state():
    random.seed(5519)
    state = random.getstate()
    GEN.generate(7, 8, difficulty="medium")
    assert random.getstate() == state
