"""Regression tests for the repaired 9e47b59d6afc input sampler."""
from __future__ import annotations

import copy
import json
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "9e47b59d6afc"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def _intended(grid):
    red = _normalize({(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2})
    green = _normalize({(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3})
    cells = red | green
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in cells:
        out[r][c] = 8 if (r, c) in red and (r, c) in green else (2 if (r, c) in red else 3)
    return out


def _manual(red_shape, green_shape, *, height=10, width=12):
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in red_shape:
        grid[1 + r][1 + c] = 2
    for r, c in green_shape:
        grid[height - 4 + r][width - 4 + c] = 3
    return grid


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def test_rule_pin_and_all_canonical_pairs_match_independent_oracle():
    assert GEN.RULE_HASH == "cc8053a66713"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _intended(pair["input"]) == pair["output"]
        assert GEN.expected_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 9, "grid_w": 11, "placement": "red_nw"},
        {"grid_h": 13, "grid_w": 15, "placement": "red_se"},
        {"grid_h": 10, "grid_w": 12, "placement": "red_ne"},
        {"grid_h": 11, "grid_w": 13, "placement": "red_sw"},
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, requested):
    grid = GEN.generate(17, 5, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert set(value for row in GEN.expected_output(grid) for value in row) >= {2, 3, 8}


@pytest.mark.parametrize(
    "args,overrides",
    [
        ((0, True), {}),
        ((0, 1.0), {}),
        ((0, "1"), {}),
        ((0, -1), {}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"grid_w": 12.0}),
        ((0, 0), {"placement": 1}),
        ((0, 0), {"grid_h": 8}),
        ((0, 0), {"grid_w": 16}),
        ((0, 0), {"shape_pair": 0}),
        ((0, 0), {"placement": "middle"}),
        ((0, 0), {"texture": "warm"}),
        ((0, 0), {"typo_axis": 1}),
    ],
)
def test_invalid_retired_or_unknown_controls_fail_loudly(args, overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **overrides)


def test_constructive_sampler_never_returns_partial_or_semantically_weak_grids():
    for band in (None, "easy", "medium", "hard"):
        for sample_index in range(64):
            grid = GEN.generate(1000 + sample_index, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            output = GEN.expected_output(grid)
            colors = {value for row in output for value in row}
            assert {2, 3, 8} <= colors
            assert _intended(grid) == output


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_contains_canonical_size_palette_support_and_all_profiles(band):
    grids = [GEN.generate(3000 + i, i, difficulty=band) for i in range(24)]
    canonical_sizes = {(9, 11), (10, 12), (11, 13)}
    assert any((len(g), len(g[0])) in canonical_sizes for g in grids)
    assert all({v for row in g for v in row} == {0, 2, 3} for g in grids)
    observed = [GEN.observe_overrides(g) for g in grids]
    assert len({GEN.observe_profile(g) for g in grids}) >= 12
    assert {row["placement"] for row in observed} == {
        "red_nw", "red_ne", "red_sw", "red_se"
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_shape_profiles_vary_across_seeds_at_fixed_sample_index(band):
    profiles = {
        GEN.observe_profile(GEN.generate(seed, 0, difficulty=band))
        for seed in range(144)
    }
    assert len(profiles) >= 80


def test_shape_profile_bank_has_144_distinct_semantic_outputs():
    assert len(GEN._SHAPE_PAIRS) == 144
    signatures = {GEN._overlay_signature(red, green) for red, green in GEN._SHAPE_PAIRS}
    assert len(signatures) == 144


def test_self_check_rejects_structural_and_semantic_impostors():
    valid = GEN.generate(41, 2, placement="red_nw")
    assert GEN.self_check(valid) == []

    blank = [[0] * 12 for _ in range(10)]

    bad_color = copy.deepcopy(valid)
    bad_color[0][0] = 9

    disconnected_red = copy.deepcopy(valid)
    for r in range(len(disconnected_red) - 1, -1, -1):
        for c in range(len(disconnected_red[0]) - 1, -1, -1):
            if disconnected_red[r][c] == 0:
                disconnected_red[r][c] = 2
                break
        else:
            continue
        break

    identical = _manual(
        {(0, 0), (1, 0), (1, 1)},
        {(0, 0), (1, 0), (1, 1)},
    )
    one_sided_exclusive = _manual(
        {(0, 0)},
        {(0, 0), (1, 0), (1, 1)},
    )
    no_normalized_overlap = _manual(
        {(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)},
        {(0, 0), (0, 1), (1, 0), (1, 1)},
    )

    for damaged in (
        blank,
        bad_color,
        disconnected_red,
        identical,
        one_sided_exclusive,
        no_normalized_overlap,
    ):
        assert GEN.self_check(damaged), damaged


def test_retained_baseline_fallback_counterexample_is_rejected():
    counterexample_path = HOME / "counterexamples" / "baseline_forced_exhaustion_blank.json"
    record = json.loads(counterexample_path.read_text())
    assert record["baseline_generator_sha256"] == (
        "2a53250135a1a1d046d297c5de436e9b4b8c9acf74b7215d6c2cde88fdc0de96"
    )
    errors = GEN.self_check(record["grid"])
    for fragment in record["current_self_check_fragments"]:
        assert fragment in errors



def test_generation_and_oracle_are_deterministic_fresh_and_global_rng_pure():
    random.seed(9981)
    state = random.getstate()
    first = GEN.generate(123, 9, difficulty="hard")
    second = GEN.generate(123, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    before = copy.deepcopy(first)
    assert GEN.expected_output(first) == _intended(first)
    assert first == before


def test_every_declared_semantic_witness_has_a_real_disagreeing_rival():
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for sample_index in range(16):
        grid = GEN.generate(5000 + sample_index, sample_index)
        truth = GEN.expected_output(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert witness(grid), witness_name
            rival_names = GEN.WITNESS_RIVALS[witness_name]
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


def test_three_pair_windows_identify_the_rule_under_every_query_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for offset in range(4):
                grid = GEN.generate(7000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.expected_output(grid)})
            for held_out, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                assert GEN.lesson_identifiable(demos, query) == []
