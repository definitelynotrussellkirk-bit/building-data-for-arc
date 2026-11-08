from __future__ import annotations

from copy import deepcopy

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.8cfb4420a8f1.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_owned_and_solved() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.rule_mirror(deepcopy(pair["input"])) == pair["output"]


def test_self_check_rejects_four_semantic_impostors() -> None:
    base = gen.generate(4101, 5, difficulty="medium")
    marker_col = next(c for c, value in enumerate(base[0]) if value != 0)
    marker_color = base[0][marker_col]

    no_marker = deepcopy(base)
    no_marker[0][marker_col] = 0

    two_markers = deepcopy(base)
    extra_col = 0 if marker_col != 0 else 1
    two_markers[0][extra_col] = 9 if marker_color != 9 else 8

    marker_absent_below = deepcopy(base)
    for r in range(1, len(marker_absent_below)):
        for c in range(len(marker_absent_below[0])):
            if marker_absent_below[r][c] == marker_color:
                marker_absent_below[r][c] = 0

    no_distractor = deepcopy(base)
    for r in range(1, len(no_distractor)):
        for c in range(len(no_distractor[0])):
            if no_distractor[r][c] not in (0, marker_color):
                no_distractor[r][c] = marker_color

    for impostor in (no_marker, two_markers, marker_absent_below, no_distractor):
        assert gen.self_check(impostor)


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(7, 0, difficulty="easy", typo_axis=1)


def test_exact_override_round_trip() -> None:
    expected = {
        "grid_h": 8,
        "grid_w": 12,
        "marker_position": "right",
        "marker_color": 9,
        "marked_cells": 4,
        "primary_distractor_count": 6,
        "n_distinct_colors": 4,
    }
    grid = gen.generate(991, 17, difficulty="hard", **expected)
    assert gen.observe_overrides(grid) == expected
    assert gen.self_check(grid) == []


def test_every_three_demo_sliding_window_is_identifiable() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            pairs = [
                _pair(8000 + band_index * 100 + index, index, band)
                for index in range(start, start + 4)
            ]
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_declared_semantic_witnesses_fire_in_every_band() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            gen.generate(12000 + band_index * 100 + i, i, difficulty=band)
            for i in range(12)
        ]
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert any(predicate(grid) for grid in grids), name
