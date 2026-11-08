from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root
from puzzle_generators.per_puzzle.aad4e3a1d5e3 import generator as gen


def _pairs() -> list[dict]:
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def _find_axes(grid: list[list[int]]) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    rows = [
        r
        for r, row in enumerate(grid)
        if all(value in (5, 6) for value in row)
        and sum(value == 6 for value in row) >= w - 1
    ]
    cols = [
        c
        for c in range(w)
        if all(grid[r][c] in (5, 6) for r in range(h))
        and sum(grid[r][c] == 5 for r in range(h)) >= h - 1
    ]
    assert len(rows) == len(cols) == 1
    return rows[0], cols[0]


def _intended(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python rendering of the selected canonical Racket rule."""
    row_axis, col_axis = _find_axes(grid)
    out = copy.deepcopy(grid)
    interesting = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    for r, c, value in interesting:
        out[r][2 * col_axis - c] = value
    second_pass = [
        (r, c, value)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    for r, c, value in second_pass:
        out[2 * row_axis - r][c] = value
    return out


def test_rule_hash_is_pinned_and_canonical_pairs_match_independent_oracle() -> None:
    assert gen.RULE_HASH == "3fcc1761aea7"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert _intended(source) == pair["output"]
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 10,
            "grid_w": 11,
            "n_cells": 6,
            "source_quadrant": "top_left",
            "layout": "connected",
            "row_axis_position": "center",
            "col_axis_position": "center",
            "intersection_owner": "vertical",
        },
        {
            "grid_h": 12,
            "grid_w": 14,
            "n_cells": 9,
            "source_quadrant": "bottom_right",
            "layout": "split",
            "row_axis_position": "off_center",
            "col_axis_position": "off_center",
            "intersection_owner": "horizontal",
        },
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, requested) -> None:
    grid = gen.generate(811, 17, difficulty=band, **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    assert gen.rule_mirror(grid) == _intended(grid)
    assert gen.rule_mirror(grid) != grid


def test_none_axis_overrides_are_equivalent_to_omission() -> None:
    mismatches = []
    for band in (None, "easy", "medium", "hard"):
        for axis in (*gen.AXES, "all_axes"):
            overrides = (
                {name: None for name in gen.AXES}
                if axis == "all_axes"
                else {axis: None}
            )
            for sample_index in range(gen.LESSON_SCHEDULE_PERIOD):
                expected = gen.generate(24680, sample_index, difficulty=band)
                try:
                    actual = gen.generate(
                        24680, sample_index, difficulty=band, **overrides
                    )
                except Exception as exc:  # a no-op sentinel must never destabilize generation
                    mismatches.append(
                        (band, axis, sample_index, type(exc).__name__, str(exc))
                    )
                    break
                if actual != expected:
                    mismatches.append(
                        (
                            band,
                            axis,
                            sample_index,
                            gen.observe_overrides(expected),
                            gen.observe_overrides(actual),
                        )
                    )
                    break
    assert mismatches == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"palette_kind": "warm"},
        {"grid_h": True},
        {"grid_h": 9},
        {"grid_w": 15},
        {"n_cells": 5},
        {"n_cells": 10},
        {"source_quadrant": "left"},
        {"layout": "other"},
        {"row_axis_position": "edge"},
        {"col_axis_position": "edge"},
        {"intersection_owner": "both"},
    ],
)
def test_invalid_or_retired_overrides_fail_loudly(overrides) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **overrides)


def test_schedule_covers_profiles_and_observable_semantic_axes_in_every_band() -> None:
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]))
        for pair in _pairs()
    }
    assert set(gen.SCHEDULE_PROFILES) == set(range(gen.LESSON_SCHEDULE_PERIOD))
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed = [
            gen.observe_overrides(gen.generate(9000 + band_index, index, difficulty=band))
            for index in range(gen.LESSON_SCHEDULE_PERIOD)
        ]
        assert {(item["grid_h"], item["grid_w"]) for item in observed} == canonical_profiles
        assert {item["source_quadrant"] for item in observed} == {
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        }
        assert {item["layout"] for item in observed} == {"connected", "split"}
        assert {item["row_axis_position"] for item in observed} == {
            "center",
            "off_center",
        }
        assert {item["col_axis_position"] for item in observed} == {
            "center",
            "off_center",
        }
        assert {item["intersection_owner"] for item in observed} == {
            "vertical",
            "horizontal",
        }


def test_every_five_sample_lesson_keeps_a_shortcut_witness_after_any_holdout() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(16):
            grids = [
                gen.generate(12000 + band_index, start + offset, difficulty=band)
                for offset in range(5)
            ]
            assert sum(gen.SEMANTIC_WITNESSES["broken_vertical_guide"](g) for g in grids) >= 2
            for held_out in range(5):
                demos = [
                    {"input": grid, "output": _intended(grid)}
                    for index, grid in enumerate(grids)
                    if index != held_out
                ]
                query = {"input": grids[held_out]}
                assert gen.lesson_identifiable(demos, query) == []


def test_named_shortcut_fits_all_canonical_pairs_but_generated_witness_refutes_it() -> None:
    pairs = _pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {"require_unbroken_vertical_guide"}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    witness = gen.generate(
        440,
        1,
        difficulty="hard",
        intersection_owner="horizontal",
    )
    assert gen.SEMANTIC_WITNESSES["broken_vertical_guide"](witness)
    assert gen.self_check(witness) == []
    assert gen.CANONICAL_SHORTCUTS["require_unbroken_vertical_guide"](witness) != _intended(witness)


def test_declared_mutation_fixtures_are_rejected() -> None:
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 8
    for name, grid in fixtures:
        errors = gen.self_check(grid)
        assert errors, name
        assert all(isinstance(error, str) and error for error in errors)


def test_standard_destructive_mutations_are_rejected() -> None:
    valid = gen.generate(71, 3, difficulty="medium")
    assert gen.self_check(valid) == []

    blank = [[0 for _ in row] for row in valid]
    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    absent_color = copy.deepcopy(valid)
    motif_colors = sorted({value for row in valid for value in row} - {0, 5, 6})
    absent_color = [
        [motif_colors[0] if value == motif_colors[1] else value for value in row]
        for row in absent_color
    ]
    drop_minority = copy.deepcopy(valid)
    counts = {
        color: sum(value == color for row in valid for value in row)
        for color in motif_colors
    }
    minority = min(counts, key=counts.get)
    drop_minority = [
        [0 if value == minority else value for value in row]
        for row in drop_minority
    ]
    for grid in (blank, ragged, absent_color, drop_minority):
        assert gen.self_check(grid)


def test_replay_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(321)
    before = random.getstate()
    first = gen.generate(404, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    snapshot = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert gen.generate(404, 5, difficulty="hard") == snapshot


def test_difficulty_bands_change_default_cell_count_without_changing_task_grammar() -> None:
    observed = {
        band: gen.observe_overrides(gen.generate(818, 0, difficulty=band))
        for band in ("easy", "medium", "hard")
    }
    assert [observed[band]["n_cells"] for band in ("easy", "medium", "hard")] == [6, 7, 8]
    for band in ("easy", "medium", "hard"):
        assert observed[band]["intersection_owner"] == "vertical"
