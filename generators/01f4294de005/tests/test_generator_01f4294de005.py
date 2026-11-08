"""Focused regression tests for the canonical 01f4294de005 generator."""
from __future__ import annotations

import copy
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "01f4294de005"
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_generation_breaks_the_blank_row_one_shortcut():
    contacts = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(96):
            grid = gen.generate(50_000 + seed, seed, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) != grid
            contacts.append(any(value != 0 for value in grid[1]))
    assert any(contacts), "no generated body reaches the row immediately below the legend"
    assert not all(contacts), "row-one contact became a new constant morphology shortcut"


def test_declared_overrides_are_strict_observable_and_unknown_keys_fail():
    grid = gen.generate(
        177,
        3,
        difficulty="hard",
        grid_h=14,
        grid_w=14,
        n_legend=5,
        n_blobs=5,
        decoy=1,
        top_contact=1,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 14,
        "grid_w": 14,
        "n_legend": 5,
        "n_blobs": 5,
        "decoy": 1,
        "top_contact": 1,
    }

    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, n_blobs=True)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, decoy="yes")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, typo_axis=1)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(9182)
    state = random.getstate()
    first = gen.generate(8123, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(8123, 9, difficulty="hard")
    assert state == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_self_check_rejects_malformed_and_rule_crashing_inputs():
    valid = gen.generate(91, 1, n_legend=3, n_blobs=3)
    assert gen.self_check(valid) == []

    bad_bool = copy.deepcopy(valid)
    bad_bool[1][0] = False
    assert gen.self_check(bad_bool)

    no_legend = copy.deepcopy(valid)
    no_legend[0] = [0] * len(no_legend[0])
    assert gen.self_check(no_legend)

    oversized = [[0] * 9 for _ in range(7)]
    oversized[0][0:2] = [2, 4]
    oversized[2][2:5] = [7, 7, 7]
    assert gen.self_check(oversized)


@pytest.mark.parametrize(
    ("seed", "sample_index"),
    [
        (True, 0),
        (False, 0),
        (1.0, 0),
        ("1", 0),
        (1, True),
        (1, False),
        (1, 1.0),
        (1, "1"),
        (1, -1),
    ],
)
def test_seed_and_sample_index_are_strict_nonnegative_integers(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_redundant_texture_axis_is_removed_and_rejected():
    assert "texture" not in gen.AXES
    with pytest.raises((TypeError, ValueError)):
        gen.generate(810, 3, texture="plain")


def test_small_canvas_max_blob_count_is_constructively_supported():
    grid = gen.generate(
        25,
        25 * 17 + 3,
        difficulty="easy",
        grid_h=6,
        n_blobs=5,
        top_contact=0,
    )
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed["grid_h"] == 6
    assert observed["n_blobs"] == 5
    assert observed["top_contact"] == 0
