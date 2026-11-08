"""Task-local regression tests for the reviewed 79a30e61d332 sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    bridge_axes,
    canonical_pairs,
    canonical_record,
    first_two_keys_rival,
    grid_hash,
    horizontal_only_rival,
    intended_output,
    key_positions,
    keys_only_rival,
    load_generator,
    observed,
    output_diff_cells,
    racket_outputs,
    row_sum_collision_positions,
    row_sums_only_rival,
    seed_lines_only_rival,
    selected_record,
    tile_mask,
    tile_positions,
    vertical_only_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_pins_authority_and_advertises_only_constructive_controls():
    assert gen.RULE_HASH == "0b623466d0bd"
    assert gen.VERSION == "4.0.2"
    assert set(gen.AXES) == {"layout_profile", "n_keys", "key_cells"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == ("horizontal", "vertical", "mixed")
    assert set(gen.CANONICAL_SHORTCUTS) == {"row_sums_only"}
    assert {
        "row_sums_only",
        "horizontal_only",
        "vertical_only",
        "seed_lines_only",
        "first_two_keys",
        "keys_only",
    } <= set(gen.LESSON_COMPETITORS)


def test_selected_target_text_is_exact_canonical_authority():
    assert selected_record()["racket_target"]["target_code"] == canonical_record()["program_solution"]


@pytest.mark.parametrize(
    "pair", canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_strongest_plausible_shortcut_fits_every_canonical_pair():
    pairs = canonical_pairs()
    assert pairs
    assert all(row_sums_only_rival(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("layout_profile", ["horizontal", "vertical", "mixed"])
@pytest.mark.parametrize("n_keys,key_cells", [(3, 3), (3, 8), (6, 3), (6, 8)])
def test_exact_overrides_are_constructive_observable_and_deterministic(
    band, layout_profile, n_keys, key_cells
):
    options = {
        "layout_profile": layout_profile,
        "n_keys": n_keys,
        "key_cells": key_cells,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)
    assert intended_output(grid) != row_sums_only_rival(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("layout_profile", "diagonal"),
        ("layout_profile", 3),
        ("n_keys", 2),
        ("n_keys", 7),
        ("key_cells", 2),
        ("key_cells", 9),
        ("n_keys", True),
        ("n_keys", 4.0),
        ("key_cells", "5"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["", "__invalid_difficulty__", "expert", 1, True])
def test_rejects_invalid_difficulty_values(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_rejects_noninteger_seed_values(seed):
    with pytest.raises(TypeError):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "0"])
def test_rejects_invalid_sample_index_values(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index)


def _structural_counts(grid):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    component_sizes = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        todo = [start]
        size = 0
        while todo:
            row, col = todo.pop()
            size += 1
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    todo.append(neighbor)
        component_sizes.append(size)
    return len(component_sizes), sum(size == 1 for size in component_sizes)


def test_periodic_hard_example_reproduces_canonical_topology_support():
    canonical_signatures = {_structural_counts(pair["input"]) for pair in canonical_pairs()}
    assert (24, 4) in canonical_signatures

    anchor = gen.generate(991, 5, difficulty="hard")
    assert _structural_counts(anchor) == (24, 4)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_varied_and_refutes_row_sum_shortcut(band):
    inputs = set()
    masks = set()
    profiles = set()
    key_counts = set()
    for index in range(60):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert len([pos for pos in tile_positions() if any(tile_mask(grid, *pos))]) == 24
        assert row_sum_collision_positions(grid)
        assert row_sums_only_rival(grid) != intended_output(grid)
        values = observed(grid)
        profiles.add(values["layout_profile"])
        key_counts.add(values["n_keys"])
        masks.add(tile_mask(grid, key_positions(grid)[0][0], key_positions(grid)[0][1]))
        inputs.add(grid_hash(grid))
    assert profiles == {"horizontal", "vertical", "mixed"}
    assert len(key_counts) >= 2
    assert len(masks) >= 16
    assert len(inputs) >= 58


def test_three_step_schedule_makes_every_four_pair_query_rotation_identifiable():
    competitors = {
        "row_sums_only": row_sums_only_rival,
        "horizontal_only": horizontal_only_rival,
        "vertical_only": vertical_only_rival,
        "seed_lines_only": seed_lines_only_rival,
        "first_two_keys": first_two_keys_rival,
        "keys_only": keys_only_rival,
    }
    for band in ("easy", "medium", "hard"):
        for start in range(30):
            grids = [gen.generate(8100 + start, start + offset, difficulty=band) for offset in range(4)]
            assert [gen.schedule_profile(0, start + offset, band) for offset in range(4)] == [
                ("horizontal", "vertical", "mixed")[(start + offset) % 3]
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [
                    {"input": grid, "output": intended_output(grid)}
                    for i, grid in enumerate(grids)
                    if i != query_index
                ]
                query_grid = grids[query_index]
                query = {"input": query_grid, "output": intended_output(query_grid)}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in competitors.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


@pytest.mark.parametrize("index", range(18))
def test_difficulty_bands_change_pixels_and_composition(index):
    grids = {
        band: gen.generate(12345, index, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert grids["easy"] != grids["medium"] != grids["hard"]
    values = {band: observed(grid) for band, grid in grids.items()}
    assert values["easy"]["n_keys"] in {3, 4}
    assert values["medium"]["n_keys"] in {4, 5}
    assert values["hard"]["n_keys"] in {5, 6}
    assert values["easy"]["key_cells"] in {3, 4}
    assert values["medium"]["key_cells"] in {5, 6}
    assert values["hard"]["key_cells"] in {7, 8}
    assert all(gen.self_check(grid) == [] for grid in grids.values())


def test_each_profile_has_the_claimed_bridge_axis_and_nonseed_bridge_witness():
    for profile in ("horizontal", "vertical", "mixed"):
        for n_keys in range(3, 7):
            grid = gen.generate(913, 17, layout_profile=profile, n_keys=n_keys, key_cells=5)
            axes = bridge_axes(grid)
            expected = {
                "horizontal": {"horizontal"},
                "vertical": {"vertical"},
                "mixed": {"horizontal", "vertical"},
            }[profile]
            assert axes == expected
            assert gen.SEMANTIC_WITNESSES["nonseed_pair_bridge"](grid)


def test_generated_counterexample_has_exact_row_sum_collision_and_output_delta():
    grid = gen.generate(20261007, 2, difficulty="hard", layout_profile="mixed", n_keys=6, key_cells=8)
    collisions = row_sum_collision_positions(grid)
    assert collisions
    intended = intended_output(grid)
    rival = row_sums_only_rival(grid)
    diff = output_diff_cells(intended, rival)
    assert diff
    assert all(any(tile_mask(grid, *pos)) for pos in collisions)
    assert gen.SEMANTIC_WITNESSES["exact_mask_not_row_totals"](grid)
    assert gen.SEMANTIC_RIVALS["row_sums_only"](grid) == rival


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 25 for _ in range(17)],
        [[0] * 25 for _ in range(17)],
    ],
)
def test_self_check_rejects_malformed_or_rule_vacuous_inputs(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_structural_and_color_mutations():
    base = gen.generate(77, 5, layout_profile="mixed", n_keys=5, key_cells=6)
    mutations = []

    wrong_gap = deepcopy(base)
    wrong_gap[0][1] = 1
    mutations.append(wrong_gap)

    second_seed = deepcopy(base)
    for tr, tc in tile_positions():
        if (tr, tc) not in key_positions(base):
            for dr in range(3):
                for dc in range(3):
                    r, c = 1 + 4 * tr + dr, 1 + 4 * tc + dc
                    if second_seed[r][c] == 1:
                        second_seed[r][c] = 8
                        break
                else:
                    continue
                break
            break
    mutations.append(second_seed)

    empty_tile = deepcopy(base)
    tr, tc = next(pos for pos in tile_positions() if pos not in key_positions(base))
    for dr in range(3):
        for dc in range(3):
            empty_tile[1 + 4 * tr + dr][1 + 4 * tc + dc] = 0
    mutations.append(empty_tile)

    illegal_color = deepcopy(base)
    illegal_color[1][1] = 2
    mutations.append(illegal_color)

    for grid in mutations:
        assert gen.self_check(grid)


def test_real_racket_authority_matches_oracle_for_canonical_and_samples():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(101, index, difficulty="medium") for index in range(18))
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_mixed_profile_has_independent_horizontal_and_vertical_effects_regression():
    """Semantic-gate rotation #11 exposed a mixed layout whose vertical bridge
    was wholly overlapped by a horizontal bridge, so horizontal_only survived."""
    grid = gen.generate(84165169887915, 35, difficulty="hard")
    assert gen.schedule_profile(84165169887915, 35, "hard") == "mixed"
    intended = intended_output(grid)
    assert horizontal_only_rival(grid) != intended
    assert vertical_only_rival(grid) != intended
