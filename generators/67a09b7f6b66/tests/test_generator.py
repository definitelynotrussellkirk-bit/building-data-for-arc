"""Task-local regression and semantic curriculum tests for 67a09b7f6b66."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    chamber_zero_region_counts,
    has_same_row_dot_pair,
    load_generator,
    observed,
    occupied_rows_output,
    position_only_output,
    retained_degenerate_inputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
COUNT_ORDERS = ("123", "132", "213", "231", "312", "321")
PALETTE_KINDS = ("wall_excluded", "wall_shared")
EXPECTED_AXES = {"ch_h", "ch_w", "palette_kind", "count_order"}


def pair(seed: int, index: int, band: str | None = None) -> dict:
    grid = gen.generate(seed, index, difficulty=band)
    return {"input": grid, "output": rule_output(grid)}


def test_authority_pin_and_honest_public_contract():
    assert gen.RULE_HASH == "100ba25d6ec9"
    assert gen.VERSION == "2.1.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.SEMANTIC_RIVALS) == {"position_only", "occupied_rows"}
    assert set(gen.CANONICAL_SHORTCUTS) == {"position_only", "occupied_rows"}
    assert set(gen.LESSON_COMPETITORS) == {"position_only", "occupied_rows"}
    assert gen.WITNESS_RIVALS == {
        "noncanonical_count_order": ("position_only",),
        "same_row_dot_pair": ("occupied_rows",),
    }


@pytest.mark.parametrize(
    "canonical",
    canonical_pairs(),
    ids=lambda item: f"{item['split']}-{item['pair_index']}",
)
def test_all_canonical_inputs_are_accepted_and_oracle_matches(canonical):
    original = deepcopy(canonical["input"])
    assert gen.self_check(canonical["input"]) == []
    assert gen.strict_canonical_like(canonical["input"]) == []
    assert rule_output(canonical["input"]) == canonical["output"]
    assert gen.rule_mirror(canonical["input"]) == canonical["output"]
    assert canonical["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_every_public_override_combination_is_exact_observable_and_lawful(band):
    for index, (ch_h, ch_w, palette_kind, count_order) in enumerate(
        itertools.product(range(5, 10), range(3, 6), PALETTE_KINDS, COUNT_ORDERS)
    ):
        requested = {
            "ch_h": ch_h,
            "ch_w": ch_w,
            "palette_kind": palette_kind,
            "count_order": count_order,
        }
        grid = gen.generate(50_000 + index, index, difficulty=band, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)
        assert grid == gen.generate(50_000 + index, index, difficulty=band, **requested)


@pytest.mark.parametrize(
    "overrides",
    (
        {"typo_axis": 1},
        {"ch_h": 4}, {"ch_h": 10}, {"ch_w": 2}, {"ch_w": 6},
        {"ch_h": True}, {"ch_h": 6.0}, {"ch_w": "3"},
        {"palette_kind": "default"}, {"palette_kind": 1},
        {"count_order": "111"}, {"count_order": 123},
    ),
)
def test_invalid_and_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True, 2))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_retained_degenerate_counterexamples_are_rejected_even_with_metadata():
    for name, grid in zip(("no_dots", "no_legend", "no_walls"), retained_degenerate_inputs()):
        assert gen.self_check(grid)
        assert gen.self_check(grid, meta={"texture": name})


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_legend", "duplicate_legend", "extra_row0_color", "broken_top_wall",
        "broken_vertical_wall", "illegal_chamber_color", "wrong_counts", "ragged", "bool_cell",
    ),
)
def test_structural_validator_rejects_near_misses(mutation):
    grid = gen.generate(781, 9, ch_h=6, ch_w=3, palette_kind="wall_shared", count_order="231")
    if mutation == "missing_legend":
        grid[0][2] = 0
    elif mutation == "duplicate_legend":
        grid[0][2] = grid[0][1]
    elif mutation == "extra_row0_color":
        grid[0][6] = 4
    elif mutation == "broken_top_wall":
        grid[1][5] = 0
    elif mutation == "broken_vertical_wall":
        grid[4][4] = 0
    elif mutation == "illegal_chamber_color":
        grid[3][2] = 5
    elif mutation == "wrong_counts":
        for row in range(2, len(grid) - 1):
            for col in range(1, 4):
                grid[row][col] = 0
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "bool_cell":
        grid[2][1] = True
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_covers_semantics_and_canonical_profile_in_each_band(band):
    orders = set()
    palettes = set()
    dimensions = set()
    unique = set()
    for index in range(48):
        grid = gen.generate(9_100 + index, index, difficulty=band)
        assert grid == gen.generate(9_100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        state = observed(grid)
        orders.add(state["count_order"])
        palettes.add(state["palette_kind"])
        dimensions.add((state["ch_h"], state["ch_w"]))
        unique.add(tuple(tuple(row) for row in grid))
    assert orders == set(COUNT_ORDERS)
    assert palettes == set(PALETTE_KINDS)
    assert {5, 6, 7, 8, 9} <= {height for height, _ in dimensions}
    assert {3, 4, 5} <= {width for _, width in dimensions}
    assert (6, 3) in {
        (observed(gen.generate(44_000 + index, index, difficulty=band))["ch_h"],
         observed(gen.generate(44_000 + index, index, difficulty=band))["ch_w"])
        for index in range(20)
    }
    assert len(unique) >= 44


def test_generated_inputs_preserve_one_racket_zero_region_per_chamber():
    # This exact old draw isolated cell (2,5) behind two dots, causing the
    # selected Racket rule to color one cell from a separate one-dot region.
    seed = 177050694093610
    grid = gen.generate(seed, 25, difficulty="easy")
    assert chamber_zero_region_counts(grid) == (1, 1, 1)
    assert gen.self_check(grid) == []

    for ch_h, ch_w, count_order in itertools.product(
        range(5, 10), range(3, 6), COUNT_ORDERS
    ):
        grid = gen.generate(7301, ch_h * 100 + ch_w, ch_h=ch_h, ch_w=ch_w, count_order=count_order)
        assert chamber_zero_region_counts(grid) == (1, 1, 1)
        assert gen.self_check(grid) == []


def test_pinned_profile_floor_has_at_least_twenty_five_percent_exact_support():
    canonical_profiles = {(9, 13, 5), (9, 13, 6)}
    total_hits = 0
    for band in ("easy", "medium", "hard"):
        band_hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            band_hits += profile in canonical_profiles
        assert band_hits >= 1
        total_hits += band_hits
    assert total_hits >= 15


def test_position_only_shortcut_fits_every_canonical_pair_but_generated_witness_refutes_it():
    assert all(position_only_output(item["input"]) == item["output"] for item in canonical_pairs())
    witness = gen.generate(
        17,
        1,
        ch_h=6,
        ch_w=3,
        palette_kind="wall_shared",
        count_order="231",
    )
    intended = rule_output(witness)
    rival = position_only_output(witness)
    assert gen.SEMANTIC_WITNESSES["noncanonical_count_order"](witness)
    assert gen.SEMANTIC_RIVALS["position_only"](witness) == rival
    assert rival != intended
    assert gen.rule_mirror(witness) == intended


def test_occupied_rows_shortcut_fits_canonical_but_scheduled_witness_refutes_it():
    assert all(occupied_rows_output(item["input"]) == item["output"] for item in canonical_pairs())
    witness = gen.generate(
        23,
        0,
        ch_h=6,
        ch_w=3,
        palette_kind="wall_excluded",
        count_order="231",
    )
    intended = rule_output(witness)
    rival = occupied_rows_output(witness)
    assert has_same_row_dot_pair(witness)
    assert gen.SEMANTIC_WITNESSES["same_row_dot_pair"](witness)
    assert gen.SEMANTIC_RIVALS["occupied_rows"](witness) == rival
    assert rival != intended
    assert gen.rule_mirror(witness) == intended


@pytest.mark.parametrize("band", BANDS)
def test_every_cyclic_four_pair_window_and_query_rotation_is_identifiable(band):
    for start in range(36):
        lesson = [pair(88_000 + start, start + offset, band) for offset in range(4)]
        for query_index in range(4):
            query = lesson[query_index]
            demos = [item for index, item in enumerate(lesson) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (band, start, query_index)


def test_rule_and_rival_are_pure_and_do_not_mutate_inputs():
    grid = gen.generate(913, 11, count_order="312", palette_kind="wall_shared")
    original = deepcopy(grid)
    assert gen.rule_mirror(grid) == rule_output(grid)
    assert grid == original
    assert gen.SEMANTIC_RIVALS["position_only"](grid) == position_only_output(grid)
    assert grid == original


@pytest.mark.parametrize('location', ('demo', 'query'))
@pytest.mark.parametrize('invalid_color', (False, 0.0))
def test_lesson_rejects_equal_valued_noninteger_output_colors(location, invalid_color):
    lesson = [pair(7651, index) for index in range(4)]
    demos, query = lesson[:3], lesson[3]
    assert gen.lesson_identifiable(demos, query) == []
    target = demos[0] if location == 'demo' else query
    target['output'][0][0] = invalid_color
    assert gen.lesson_identifiable(demos, query), (location, invalid_color)


@pytest.mark.parametrize('rows_are_tuples', (False, True))
def test_rule_mirror_and_lesson_accept_validated_tuple_inputs(rows_are_tuples):
    lesson = [pair(7651, index) for index in range(4)]
    query = lesson[-1]
    query['input'] = tuple(tuple(row) if rows_are_tuples else row for row in query['input'])
    original = deepcopy(query['input'])
    assert gen.self_check(query['input']) == []
    assert gen.rule_mirror(query['input']) == query['output']
    assert gen.lesson_identifiable(lesson[:3], query) == []
    assert query['input'] == original


@pytest.mark.parametrize('tuple_rows', (False, True))
def test_lesson_output_contract_requires_list_grid(tuple_rows):
    lesson = [pair(7651, index) for index in range(4)]
    query = lesson[-1]
    query['output'] = (
        [tuple(row) for row in query['output']] if tuple_rows else tuple(query['output'])
    )
    assert gen.lesson_identifiable(lesson[:3], query)
