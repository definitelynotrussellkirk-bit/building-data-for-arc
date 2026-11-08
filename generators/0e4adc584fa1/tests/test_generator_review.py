from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "0e4adc584fa1"
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_review", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _labelled(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_every_canonical_pair_are_owned_and_mirrored():
    assert gen.RULE_HASH == "314b2cc8cd15"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_any_four_consecutive_defaults_cover_all_control_codes():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 19, 2026):
            for start in range(8):
                codes = []
                for sample_index in range(start, start + 4):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    assert gen.self_check(grid) == []
                    codes.append(gen.observe_overrides(grid)["control_code"])
                assert set(codes) == {1, 2, 3, 4}


def test_every_advertised_axis_is_exact_observable_and_unknown_keys_reject():
    requested = {
        "grid_h": 8,
        "grid_w": 9,
        "control_code": 4,
        "shape_profile": "large_4x4",
        "shape_colors": 3,
        "marker_order": "after",
    }
    grid = gen.generate(91, 17, difficulty="hard", **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested

    requested = {
        "grid_h": 12,
        "grid_w": 14,
        "control_code": 1,
        "shape_profile": "canonical_3x3",
        "shape_colors": 1,
        "marker_order": "before",
    }
    grid = gen.generate(91, 18, difficulty="easy", **requested)
    assert gen.observe_overrides(grid) == requested

    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(1, 0, misspelled_axis="accepted silently")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, shape_profile="not_a_profile")


def test_control_axis_changes_only_marker_and_gives_four_distinct_outputs():
    common = {
        "grid_h": 10,
        "grid_w": 12,
        "shape_profile": "canonical_3x3",
        "shape_colors": 2,
        "marker_order": "before",
    }
    grids = [gen.generate(707, 11, control_code=code, **common) for code in range(1, 5)]
    marker_positions = []
    normalized = []
    outputs = []
    for code, grid in enumerate(grids, 1):
        observed = gen.observe_overrides(grid)
        assert observed["control_code"] == code
        marker = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == code
            and all(
                not (0 <= r + dr < len(grid) and 0 <= c + dc < len(row))
                or grid[r + dr][c + dc] == 0
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
        )
        marker_positions.append(marker)
        clone = copy.deepcopy(grid)
        clone[marker[0]][marker[1]] = 0
        normalized.append(clone)
        outputs.append(gen.rule_mirror(grid))
    assert len(set(marker_positions)) == 1
    assert all(grid == normalized[0] for grid in normalized[1:])
    assert len({tuple(map(tuple, output)) for output in outputs}) == 4


def test_declared_size_shortcut_fits_canonical_but_generated_witness_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["canonical_size_to_code"]
    for pair in _pairs():
        assert shortcut(pair["input"]) == pair["output"]

    witnesses = []
    for sample_index in range(16):
        grid = gen.generate(123, sample_index, difficulty="medium")
        if gen.SEMANTIC_WITNESSES["size_code_decoupled"](grid):
            witnesses.append(grid)
    assert witnesses
    assert all(shortcut(grid) != gen.rule_mirror(grid) for grid in witnesses)


def test_every_five_pair_window_is_identifiable_in_production_and_rotated_queries():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [_labelled(555, index, band) for index in range(start, start + 5)]
            assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
            for query_index in range(5):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_default_distribution_retains_canonical_like_support_in_every_band():
    for band in ("easy", "medium", "hard"):
        strict = 0
        for sample_index in range(24):
            grid = gen.generate(811, sample_index, difficulty=band)
            strict += not gen.strict_canonical_like(grid)
        assert strict >= 8


def test_replay_is_fresh_deterministic_and_global_rng_neutral():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(17, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(17, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_declared_mutation_fixtures_are_rejected_without_input_mutation():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        snapshot = copy.deepcopy(grid)
        assert gen.self_check(grid), name
        assert grid == snapshot
