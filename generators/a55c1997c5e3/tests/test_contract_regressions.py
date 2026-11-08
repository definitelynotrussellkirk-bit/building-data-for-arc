"""Behavioral guards for public scalar and canonical-shortcut contracts.

Removing recipe-identity validation must fail the scalar cases. Declaring a rival
that mispredicts a labeled canonical example must fail that rival's case.
"""
from __future__ import annotations

import copy

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a55c1997c5e3"
ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


@pytest.mark.parametrize(
    "seed", [True, 1.25, "314159", None], ids=["true", "float", "string", "none"]
)
def test_generate_rejects_noninteger_seed(seed):
    with pytest.raises(ValueError, match=r"^seed must be an integer"):
        gen.generate(seed, 3, difficulty="medium")


def test_generate_accepts_negative_integer_seed():
    grid = gen.generate(-7, 3, difficulty="medium")
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "sample_index",
    [True, False, 1.25, "3", -1],
    ids=["true", "false", "float", "string", "negative"],
)
def test_generate_rejects_noninteger_or_negative_sample_index(sample_index):
    with pytest.raises(ValueError, match=r"^sample_index must be a nonnegative integer"):
        gen.generate(314159, sample_index, difficulty="medium")


@pytest.mark.parametrize("name", sorted(gen.CANONICAL_SHORTCUTS))
def test_declared_canonical_shortcut_fits_every_labeled_pair(name):
    assert PAIRS, "no labeled canonical examples: shortcut claim was not checked"
    shortcut = gen.CANONICAL_SHORTCUTS[name]
    assert callable(shortcut), f"{name}: canonical shortcut is not callable"
    for pair in PAIRS:
        predicted = shortcut(copy.deepcopy(pair["input"]))
        assert predicted == pair["output"], (
            f"{name} does not fit canonical variant {pair['variant']} "
            f"{pair['split']} pair {pair['pair_index']}"
        )
