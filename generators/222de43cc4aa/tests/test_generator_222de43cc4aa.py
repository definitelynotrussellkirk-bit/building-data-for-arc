"""Focused regression tests for ARC generator 222de43cc4aa."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "222de43cc4aa"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def test_canonical_inputs_remain_valid_under_the_pinned_rule():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    assert GEN.RULE_HASH == "ce9518b81cf8"
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


def test_unknown_override_key_is_rejected_instead_of_silently_ignored():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(11, 7, bogus_axis=1)


def test_invalid_texture_token_is_rejected_instead_of_treated_as_a_normal_draw():
    with pytest.raises(ValueError, match="texture"):
        GEN.generate(11, 7, texture="bogus")


@pytest.mark.parametrize("texture", GEN.HELPFUL_TEXTURES + GEN.DEGENERATE_TEXTURES)
def test_every_declared_texture_token_still_generates_a_lawful_grid(texture):
    grid = GEN.generate(91, 3, difficulty="medium", texture=texture)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_representative_declared_axis_overrides_round_trip(difficulty):
    requested = {"grid_h": 5, "grid_w": 17, "n_fg_colors": 1}
    grid = GEN.generate(37, 9, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
