"""Regression tests for strict public scalar controls in generator 126da449328f."""
from __future__ import annotations

import importlib

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.126da449328f.generator"
)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", -1])
def test_sample_index_must_be_a_nonnegative_literal_integer(bad):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.schedule_profile(991, bad, "easy")
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(991, bad, difficulty="easy")


@pytest.mark.parametrize("bad", [True, False, 1.0, "1"])
def test_seed_must_be_a_literal_integer(bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(bad, 0, difficulty="easy")


@pytest.mark.parametrize(
    ("axis", "bad"),
    [
        ("grid_h", 7.0),
        ("grid_h", "7"),
        ("grid_w", 7.0),
        ("grid_w", "7"),
        ("seed_count", 3.0),
        ("seed_count", "3"),
    ],
)
def test_integer_overrides_reject_coercible_nonintegers(axis, bad):
    with pytest.raises((TypeError, ValueError), match=axis):
        gen.generate(991, 0, difficulty="easy", **{axis: bad})


def test_right_over_left_tie_shortcut_fits_canonical_but_not_generation():
    rival = gen.CANONICAL_SHORTCUTS["right_over_left_ties"]
    root = find_root(__file__)
    pairs = canonical_pairs(gen.TASK_ID, root=root, labeled_only=True)
    assert pairs
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    grid = gen.generate(126_449, 4, difficulty="medium")
    assert gen.semantic_observables(grid)["scene_profile"] == "left_over_right"
    assert rival(grid) != gen.rule_mirror(grid)
    assert "right_over_left_ties" in gen.WITNESS_RIVALS["left_over_right"]
