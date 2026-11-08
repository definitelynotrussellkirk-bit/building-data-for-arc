"""Regression tests for measuring an aligned endpoint segment as a cyan bar."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "a338acade0b5"
HOME = Path(__file__).resolve().parents[1]
ORIENTATIONS = ("horizontal", "vertical", "diag_down", "diag_up")
BANDS = (None, "easy", "medium", "hard")


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_a338acade0b5", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
CANONICAL = canonical_pairs(TASK, root=find_root(__file__))
CANONICAL_PROFILES = {
    (len(item["input"]), len(item["input"][0]), len({v for row in item["input"] for v in row}))
    for item in CANONICAL
}


def _endpoints(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def _intended_output(grid):
    points = _endpoints(grid)
    assert len(points) == 2
    (r1, c1, _), (r2, c2, _) = points
    length = max(abs(r2 - r1), abs(c2 - c1)) + 1
    return [[8] * length]


def _profile(grid):
    return (len(grid), len(grid[0]), len({v for row in grid for v in row}))


def _is_vertical(grid):
    points = _endpoints(grid)
    return len(points) == 2 and points[0][1] == points[1][1]


@pytest.mark.parametrize(
    "item",
    CANONICAL,
    ids=lambda item: f"{item['split']}{item['pair_index']}",
)
def test_canonical_inputs_are_owned_and_match_independent_oracle(item):
    assert gen.RULE_HASH == "5661890ac5fd"
    assert gen.self_check(item["input"]) == []
    assert gen.strict_canonical_like(item["input"]) == []
    assert _intended_output(item["input"]) == item["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("orientation", ORIENTATIONS)
@pytest.mark.parametrize("length", (2, 7, 14))
def test_exact_controls_cover_full_length_domain_in_every_band(band, orientation, length):
    expected = {
        "segment_length": length,
        "orientation": orientation,
        "endpoint_color": 9,
    }
    grid = gen.generate(73, 11, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert _intended_output(grid) == [[8] * length]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"segment_length": 1},
        {"segment_length": 15},
        {"segment_length": True},
        {"segment_length": 3.5},
        {"endpoint_color": 0},
        {"endpoint_color": 10},
        {"endpoint_color": "2"},
        {"orientation": "diagonal"},
        {"orientation": 1},
    ],
)
def test_invalid_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True))
def test_invalid_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", BANDS)
def test_every_four_pair_lesson_keeps_a_vertical_counterexample_after_any_holdout(band):
    for seed in (0, 17, 91):
        for start in range(8):
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            assert sum(_is_vertical(grid) for grid in grids) >= 2
            for held_out in range(4):
                demos = [
                    {"input": grid, "output": _intended_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != held_out
                ]
                query = {
                    "input": grids[held_out],
                    "output": _intended_output(grids[held_out]),
                }
                assert gen.lesson_identifiable(demos, query) == []
                assert any(_is_vertical(item["input"]) for item in demos)


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_has_canonical_profile_anchors_in_every_band(band):
    grids = [gen.generate(109, index, difficulty=band) for index in range(12)]
    assert any(_profile(grid) in CANONICAL_PROFILES for grid in grids)
    assert all(gen.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_covers_both_diagonal_directions_in_every_band(band):
    orientations = {
        gen.observe_overrides(gen.generate(211, index, difficulty=band))["orientation"]
        for index in range(gen.LESSON_SCHEDULE_PERIOD)
    }
    assert {"diag_down", "diag_up"} <= orientations


def test_declared_vertical_witness_refutes_column_span_shortcut():
    grid = gen.generate(
        31,
        5,
        orientation="vertical",
        segment_length=7,
        endpoint_color=2,
    )
    intended = _intended_output(grid)
    rival = gen.SEMANTIC_RIVALS["column_span_only"](grid)
    assert intended == [[8] * 7]
    assert rival == [[8]]
    assert gen.SEMANTIC_WITNESSES["vertical_segment"](grid) is True
    assert rival != intended
    assert gen.WITNESS_RIVALS["vertical_segment"] == ["column_span_only"]
    assert set(gen.LESSON_COMPETITORS) == {"column_span_only"}


def test_validator_rejects_structure_destroying_mutations():
    base = gen.generate(7, 3, orientation="diag_up", segment_length=7, endpoint_color=4)
    assert gen.self_check(base) == []

    extra = deepcopy(base)
    extra[0][0] = 4

    different_colors = deepcopy(base)
    points = _endpoints(different_colors)
    r, c, _ = points[-1]
    different_colors[r][c] = 5

    non_aligned = [[0] * 8 for _ in range(8)]
    non_aligned[1][1] = 2
    non_aligned[5][6] = 2

    for changed in (extra, different_colors, non_aligned, [], [[]], [[0], [0, 2]]):
        assert gen.self_check(changed)


def test_generation_is_deterministic_and_purely_observable():
    kwargs = {"orientation": "diag_down", "segment_length": 11, "endpoint_color": 8}
    first = gen.generate(412, 111, difficulty="hard", **kwargs)
    before = deepcopy(first)
    assert gen.generate(412, 111, difficulty="hard", **kwargs) == first
    assert gen.observe_overrides(first) == kwargs
    assert first == before


def test_standard_episode_probe_covers_complete_declared_output_alphabet():
    outputs = {
        tuple(_intended_output(gen.generate(ep * 101, sample_index))[0])
        for ep in range(24)
        for sample_index in range(6)
    }
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 13
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN
    assert {len(output) for output in outputs} == set(range(2, 15))
