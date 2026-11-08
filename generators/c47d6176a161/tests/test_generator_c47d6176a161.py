"""Focused regression coverage for the c47d6176a161 legend-match generator."""
from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.c47d6176a161 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen._solve(grid)}


def test_canonical_inputs_are_owned_and_python_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen._solve(pair["input"]) == pair["output"]


def test_all_exact_axis_combinations_are_realized_and_observed():
    case_index = 0
    for shape in gen.GRID_SHAPES:
        for profile in gen.SCENE_PROFILES:
            for shared in (1, 2):
                for corner in gen.CORNER_MODES:
                    requested = {
                        "grid_shape": shape,
                        "scene_profile": profile,
                        "shared_colors": shared,
                        "corner_mode": corner,
                    }
                    grid = gen.generate(
                        100_000 + case_index,
                        case_index,
                        difficulty=("easy", "medium", "hard")[case_index % 3],
                        **requested,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested
                    case_index += 1
    assert case_index == 144


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="repeat_top")
    with pytest.raises(ValueError):
        gen.generate(1, 0, shared_colors=0)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_shape="14x14")


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(
        7,
        3,
        grid_shape="5x5",
        scene_profile="repeat_both",
        shared_colors=1,
        corner_mode="background",
    )
    assert gen.self_check(valid) == []

    interior_painted = copy.deepcopy(valid)
    interior_painted[2][2] = 9

    missing_top = copy.deepcopy(valid)
    missing_top[0][1] = 0

    missing_left = copy.deepcopy(valid)
    missing_left[1][0] = 0

    disjoint_headers = copy.deepcopy(valid)
    top_colors = set(disjoint_headers[0][1:])
    absent = [c for c in range(1, 10) if c not in top_colors]
    assert len(absent) >= 2
    for r in range(1, len(disjoint_headers)):
        disjoint_headers[r][0] = absent[(r - 1) % 2]

    bad_corner = copy.deepcopy(valid)
    used = set(bad_corner[0]) | {row[0] for row in bad_corner}
    bad_corner[0][0] = next(c for c in range(1, 10) if c not in used)

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()

    cases = {
        "painted interior": interior_painted,
        "missing top key": missing_top,
        "missing left key": missing_left,
        "disjoint headers": disjoint_headers,
        "unrelated corner key": bad_corner,
        "ragged grid": ragged,
    }
    for name, grid in cases.items():
        assert gen.self_check(grid), name
        assert gen.observe_overrides(grid) == {}, name


def test_every_default_draw_refutes_the_named_core_rivals():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for i in range(40):
            grid = gen.generate(20_000 + band_index * 1_000 + i, i, difficulty=band)
            official = gen._solve(grid)
            assert gen._identity(grid) != official
            assert gen._row_membership(grid) != official
            assert gen._column_membership(grid) != official
            assert gen._diagonal_only(grid) != official
            assert gen._copy_left_rows(grid) != official
            assert gen._copy_top_columns(grid) != official
            for witness in gen.SEMANTIC_WITNESSES.values():
                assert witness(grid)


def test_every_sliding_lesson_window_is_identifiable():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seed = 30_000 + band_index
        for start in range(36):
            pairs = [
                _pair(seed, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    before = random.getstate()
    first = gen.generate(42, 17, difficulty="hard")
    middle = gen.generate(99, 3, difficulty="easy")
    second = gen.generate(42, 17, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert first != middle
    assert before == after
