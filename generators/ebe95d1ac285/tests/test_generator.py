"""Task-local regressions for the ebe95d1ac285 constructive repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    analyze,
    canonical_pairs,
    canonical_rule_hash,
    intended_output,
    load_generator,
    observed,
    symmetry_only_rival,
    touch_only_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "anchor_sym",
    "anchor_touch",
    "match_count",
    "same_touch_distractors",
    "same_sym_distractors",
    "neutral_distractors",
}


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_seed(band, index):
    digest = hashlib.sha256(f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()).hexdigest()
    return int(digest[:12], 16)


def test_rule_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == canonical_rule_hash() == "5aebf983dc54"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    source = deepcopy(pair["input"])
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert intended_output(source) == pair["output"]
    assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("anchor_sym", range(4))
@pytest.mark.parametrize("anchor_touch", [False, True])
def test_minimum_exact_overrides_construct_and_are_observable(band, anchor_sym, anchor_touch):
    requested = {
        "grid_h": 12,
        "grid_w": 16,
        "anchor_sym": anchor_sym,
        "anchor_touch": anchor_touch,
        "match_count": 1,
        "same_touch_distractors": 1,
        "same_sym_distractors": 1,
        "neutral_distractors": 0,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert intended_output(grid) != grid
    assert touch_only_rival(grid) != intended_output(grid)
    assert symmetry_only_rival(grid) != intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_maximum_exact_overrides_construct_and_are_observable(band):
    requested = {
        "grid_h": 24,
        "grid_w": 24,
        "anchor_sym": 3,
        "anchor_touch": True,
        "match_count": 2,
        "same_touch_distractors": 2,
        "same_sym_distractors": 2,
        "neutral_distractors": 1,
    }
    grid = gen.generate(113, 29, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 11),
        ("grid_h", 25),
        ("grid_h", True),
        ("grid_w", "16"),
        ("anchor_sym", -1),
        ("anchor_sym", 4),
        ("anchor_sym", 1.0),
        ("anchor_touch", 1),
        ("anchor_touch", "true"),
        ("match_count", 0),
        ("match_count", 3),
        ("same_touch_distractors", 0),
        ("same_sym_distractors", 3),
        ("neutral_distractors", 2),
    ],
)
def test_invalid_unknown_and_coerced_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_invalid_sample_index_fails_loudly(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


def test_invalid_difficulty_fails_loudly():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_teaches_conjunction(band):
    signatures = set()
    shapes = set()
    for index in range(128):
        seed = 4000 + index
        grid = gen.generate(seed, index * 13, difficulty=band)
        assert grid == gen.generate(seed, index * 13, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        info = analyze(grid)
        assert info["match"]
        assert info["same_touch"]
        assert info["same_sym"]
        assert intended_output(grid) != touch_only_rival(grid)
        assert intended_output(grid) != symmetry_only_rival(grid)
        signatures.add((info["anchor_touch"], info["anchor_sym"]))
        shapes.add((len(grid), len(grid[0]), len(info["objects"])))
    assert signatures == {(touch, sym) for touch in (False, True) for sym in range(4)}
    assert len(shapes) >= 20


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_official_profile_floor_schedule_has_exact_canonical_hit_per_band(band):
    profiles = {_profile(pair["input"]) for pair in canonical_pairs()}
    hits = []
    for index in range(20):
        seed = _pinned_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        if _profile(grid) in profiles:
            hits.append(index)
    assert hits


def test_generation_is_global_rng_isolated_and_returns_fresh_rows():
    random.seed(918273)
    state = random.getstate()
    first = gen.generate(11, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(11, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 16 for _ in range(12)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("mutation", ["remove_anchor", "duplicate_anchor", "input_8", "erase_matches"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(71, 5, grid_h=14, grid_w=18)
    info = analyze(grid)
    if mutation == "remove_anchor":
        for row, col in info["anchor"]["cells"]:
            grid[row][col] = 0
    elif mutation == "duplicate_anchor":
        for row, col in info["same_touch"][0]["cells"]:
            grid[row][col] = 2
    elif mutation == "input_8":
        row, col = min(info["neutral"][0]["cells"]) if info["neutral"] else min(info["same_touch"][0]["cells"])
        grid[row][col] = 8
    else:
        for obj in info["match"]:
            for row, col in obj["cells"]:
                grid[row][col] = 0
    assert gen.self_check(grid)


def test_semantic_contract_names_and_witnesses_are_executable():
    grid = gen.generate(31, 8, difficulty="medium")
    assert set(gen.SEMANTIC_RIVALS) == {"touch_only", "symmetry_only"}
    assert set(gen.SEMANTIC_WITNESSES) == {"same_touch_wrong_sym", "same_sym_wrong_touch"}
    assert gen.SEMANTIC_WITNESSES["same_touch_wrong_sym"](grid)
    assert gen.SEMANTIC_WITNESSES["same_sym_wrong_touch"](grid)
    assert gen.SEMANTIC_RIVALS["touch_only"](grid) == touch_only_rival(grid)
    assert gen.SEMANTIC_RIVALS["symmetry_only"](grid) == symmetry_only_rival(grid)
    assert gen.SEMANTIC_RIVALS["touch_only"](grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["symmetry_only"](grid) != intended_output(grid)
