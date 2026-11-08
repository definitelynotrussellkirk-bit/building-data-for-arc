"""Task-local contract tests for f812a7b32f47."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (anywhere_marker_rival, canonical_pairs,
                             canonical_profiles, explicit_witness,
                             intended_output, load_generator, observed,
                             pinned_profile_seed)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def test_rule_hash_is_pinned():
    assert gen.RULE_HASH == "6fdb2408e34a"


@pytest.mark.parametrize("pair", canonical_pairs(),
                         ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_accepts_canonical_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_and_observable(band):
    options = {
        "frame_h": 5,
        "frame_w": 6,
        "frame_color": 9,
        "n_top": 4,
        "n_left": 3,
        "n_distractors": 4,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("frame_h", 4), ("frame_h", 14),
    ("frame_w", 5), ("frame_w", 16),
    ("frame_color", 0), ("frame_color", 2), ("frame_color", 3),
    ("frame_color", 7), ("n_top", 0), ("n_top", 5),
    ("n_left", 0), ("n_left", 4),
    ("n_distractors", 0), ("n_distractors", 5),
    ("frame_h", True), ("n_top", 2.5), ("frame_color", "5"),
])
def test_rejects_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_explicit_off_axis_witness_refutes_strongest_canonical_shortcut():
    grid = explicit_witness()
    intended = intended_output(grid)
    rival = anywhere_marker_rival(grid)
    assert gen.self_check(grid) == []
    assert intended != rival
    assert gen.SEMANTIC_RIVALS["markers_anywhere"](grid) == rival
    assert gen.CANONICAL_SHORTCUTS["markers_anywhere"](grid) == rival
    differences = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
                   if intended[r][c] != rival[r][c]]
    assert differences == [(2, 6), (4, 6), (5, 2), (5, 4), (5, 6)]


def test_shortcut_fits_every_canonical_demonstration():
    assert all(anywhere_marker_rival(pair["input"]) == pair["output"]
               for pair in canonical_pairs())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_always_supplies_rival_witness(band):
    for index in range(96):
        grid = gen.generate(3000 + index, index * 13 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert observed(grid)["n_distractors"] >= 1
        assert intended_output(grid) != anywhere_marker_rival(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_schedule_has_support_in_every_band(band):
    profiles = canonical_profiles()
    hits = 0
    for index in range(20):
        seed = pinned_profile_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        hits += profile in profiles
    assert hits >= 1


def test_distribution_is_deterministic_and_covers_axes():
    heights, widths, colors, tops, lefts, distractors, inputs = set(), set(), set(), set(), set(), set(), set()
    for index in range(384):
        args = (7000 + index, index * 19 + 11)
        grid = gen.generate(*args, difficulty=("easy", "medium", "hard")[index % 3])
        assert grid == gen.generate(*args, difficulty=("easy", "medium", "hard")[index % 3])
        stats = observed(grid)
        heights.add(stats["frame_h"]); widths.add(stats["frame_w"])
        colors.add(stats["frame_color"]); tops.add(stats["n_top"])
        lefts.add(stats["n_left"]); distractors.add(stats["n_distractors"])
        inputs.add(_grid_hash(grid))
    assert {5, 6, 7, 8, 12, 13} <= heights
    assert {6, 7, 8, 9, 14, 15} <= widths
    assert colors == {1, 4, 5, 6, 8, 9}
    assert tops == {1, 2, 3, 4}
    assert lefts == {1, 2, 3}
    assert distractors == {1, 2, 3, 4}
    assert len(inputs) > 360


@pytest.mark.parametrize("mutation", [
    "blank", "ragged", "unknown_color", "erase_top_marker",
    "erase_left_marker", "interior_noise", "broken_border",
])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(31, 7, frame_h=7, frame_w=8, frame_color=5,
                        n_top=2, n_left=2, n_distractors=1)
    if mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "unknown_color":
        grid[0][0] = 10
    else:
        nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        r0 = min(r for r, _ in nonzero); r1 = max(r for r, _ in nonzero)
        c0 = min(c for _, c in nonzero); c1 = max(c for _, c in nonzero)
        if mutation == "erase_top_marker":
            for c in range(c0 + 1, c1):
                if grid[r0][c] == 3:
                    grid[r0][c] = 5
        elif mutation == "erase_left_marker":
            for r in range(r0 + 1, r1):
                if grid[r][c0] == 2:
                    grid[r][c0] = 5
        elif mutation == "interior_noise":
            grid[r0 + 1][c0 + 1] = 4
        elif mutation == "broken_border":
            grid[r1][c0 + 1] = 0
    assert gen.self_check(grid)


def test_intended_and_rival_functions_do_not_mutate_input():
    grid = gen.generate(123, 456)
    original = deepcopy(grid)
    intended_output(grid)
    anywhere_marker_rival(grid)
    gen.SEMANTIC_RIVALS["markers_anywhere"](grid)
    assert grid == original


def test_lesson_contract_uses_at_least_two_demonstrations():
    """A one-example identifiability audit is formally vacuous for rivals."""
    assert gen.EXAMPLES_NEEDED >= 2
