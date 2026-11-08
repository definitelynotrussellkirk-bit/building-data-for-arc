"""Regression tests for the crossing-band task generator.

The helpers in this file deliberately infer task structure independently of the
production generator so a shared implementation bug cannot make the tests pass.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "7b0cb3b9a618"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))
CANONICAL_PROFILES = {
    (3, 3, 3),
    (8, 12, 5),
    (9, 11, 5),
    (11, 11, 6),
    (11, 12, 6),
    (11, 13, 5),
}


def _clean_rows(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, row[0])
        for r, row in enumerate(grid)
        if row[0] != 0 and len(set(row)) == 1
    ]


def _clean_cols(grid: list[list[int]]) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    result = []
    for c in range(w):
        values = [grid[r][c] for r in range(h)]
        if values[0] != 0 and len(set(values)) == 1:
            result.append((c, values[0]))
    return result


def _orientation_and_answer(grid: list[list[int]]) -> tuple[str, int]:
    rows = _clean_rows(grid)
    if rows:
        assert len({color for _, color in rows}) == 1
        return "horizontal", rows[0][1]
    cols = _clean_cols(grid)
    assert len(cols) == 1
    return "vertical", cols[0][1]


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


@pytest.mark.parametrize(
    "pair",
    CANONICAL,
    ids=[f"{p['split']}{p['pair_index']}" for p in CANONICAL],
)
def test_accepts_every_canonical_crossing_band_input(pair):
    assert GEN.self_check(pair["input"]) == []
    _, answer = _orientation_and_answer(pair["input"])
    assert pair["output"] == [[answer]]


def test_declares_the_active_rule_hash_and_strict_validator():
    assert GEN.RULE_HASH == "20196c190154"
    assert GEN.strict_canonical_like is GEN.self_check


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_is_deterministic_profile_exact_and_teaches_both_orientations(band):
    orientations = []
    seen_profiles = set()
    for sample_index in range(24):
        grid = GEN.generate(190807, sample_index, difficulty=band)
        assert grid == GEN.generate(190807, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert _profile(grid) in CANONICAL_PROFILES
        seen_profiles.add(_profile(grid))
        orientations.append(_orientation_and_answer(grid)[0])

    assert seen_profiles == CANONICAL_PROFILES
    for start in range(0, 21):
        assert set(orientations[start : start + 4]) == {"horizontal", "vertical"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_clean_color_override_is_exact_and_observable_in_every_band(band):
    for sample_index in range(12):
        grid = GEN.generate(77, sample_index, difficulty=band, clean_color=9)
        assert GEN.self_check(grid) == []
        assert _orientation_and_answer(grid)[1] == 9
        assert GEN.observe_overrides(grid) == {"clean_color": 9}


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"clean_color": 0},
        {"clean_color": 10},
        {"clean_color": True},
        {"clean_color": "3"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


def test_semantic_contract_contains_a_real_vertical_counterexample():
    grid = GEN.generate(712, 1, clean_color=9)
    orientation, answer = _orientation_and_answer(grid)
    assert orientation == "vertical"
    assert GEN.SEMANTIC_WITNESSES["vertical_clean_band"](grid)
    rival = GEN.SEMANTIC_RIVALS["uniform_row_only"](grid)
    assert rival != [[answer]]


@pytest.mark.parametrize("sample_index", [0, 1])
def test_validator_rejects_damage_to_the_unique_clean_band(sample_index):
    grid = GEN.generate(314, sample_index)
    orientation, _ = _orientation_and_answer(grid)
    broken = deepcopy(grid)
    if orientation == "horizontal":
        row = _clean_rows(grid)[0][0]
        # Pick a cell whose column is background outside the horizontal band.
        col = next(c for c in range(len(grid[0])) if any(grid[r][c] == 0 for r in range(len(grid))))
        broken[row][col] = 0
    else:
        col = _clean_cols(grid)[0][0]
        # Pick a background row outside all horizontal bands.
        row = next(r for r in range(len(grid)) if any(v == 0 for v in grid[r]))
        broken[row][col] = 0
    assert GEN.self_check(broken)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True]]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert GEN.self_check(bad)
