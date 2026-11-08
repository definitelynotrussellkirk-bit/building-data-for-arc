"""Task-local regression tests for the reviewed 7de2798953a7 sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    any_two_nonzero_rival,
    canonical_pairs,
    intended_output,
    mismatched_rows,
    observed,
    pair_rows,
    racket_outputs,
    right_phase_rival,
    shortcut_witness,
    solid_fill_rival,
    load_generator,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_pins_authority_and_advertises_only_exact_controls():
    assert gen.RULE_HASH == "3bca54d68914"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_pairs"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == ("canonical", "contrast")
    assert set(gen.CANONICAL_SHORTCUTS) == {"any_two_nonzero"}
    assert {"solid_fill", "right_phase", "any_two_nonzero"} <= set(gen.LESSON_COMPETITORS)


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


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 4, "grid_w": 7, "n_pairs": 1},
        {"grid_h": 4, "grid_w": 14, "n_pairs": 4},
        {"grid_h": 10, "grid_w": 7, "n_pairs": 4},
        {"grid_h": 10, "grid_w": 14, "n_pairs": 1},
    ],
)
def test_exact_overrides_are_constructive_observable_and_deterministic(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 3),
        ("grid_h", 11),
        ("grid_w", 6),
        ("grid_w", 15),
        ("n_pairs", 0),
        ("n_pairs", 5),
        ("grid_h", True),
        ("grid_w", 8.5),
        ("n_pairs", "2"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_varied_and_has_phase_witness(band):
    shapes = set()
    pair_counts = set()
    colors = set()
    inputs = set()
    for index in range(120):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        pairs = pair_rows(grid)
        assert pairs
        assert any((right - left) % 2 == 1 for _, _, left, right in pairs)
        assert solid_fill_rival(grid) != intended_output(grid)
        assert right_phase_rival(grid) != intended_output(grid)
        shapes.add((len(grid), len(grid[0])))
        pair_counts.add(len(pairs))
        colors.update(color for _, color, _, _ in pairs)
        inputs.add(tuple(tuple(row) for row in grid))
    assert {(6, 7), (5, 8), (4, 9), (4, 8)} <= shapes
    assert {2, 3} <= pair_counts
    assert len(colors) >= 7
    assert len(inputs) >= 110


def test_contrast_schedule_survives_every_query_rotation():
    """Every four consecutive pairs leave a mismatch witness in any 3 demos."""
    for band in ("easy", "medium", "hard"):
        for start in range(36):
            grids = [gen.generate(8100 + start, start + offset, difficulty=band) for offset in range(4)]
            flags = [bool(mismatched_rows(grid)) for grid in grids]
            assert sum(flags) >= 2, (band, start, flags)
            for query_index in range(4):
                demos = [grid for i, grid in enumerate(grids) if i != query_index]
                assert any(mismatched_rows(grid) for grid in demos)
                assert all(
                    any_two_nonzero_rival(grid) != intended_output(grid)
                    for grid in demos
                    if mismatched_rows(grid)
                )
                demo_pairs = [
                    {"input": grid, "output": intended_output(grid)} for grid in demos
                ]
                query_grid = grids[query_index]
                assert gen.lesson_identifiable(
                    demo_pairs,
                    {"input": query_grid, "output": intended_output(query_grid)},
                ) == []


def test_named_shortcut_fits_canonical_but_generated_contrast_refutes_it():
    assert all(any_two_nonzero_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = shortcut_witness()
    assert gen.self_check(witness) == []
    intended = intended_output(witness)
    rival = any_two_nonzero_rival(witness)
    assert intended != rival
    assert [(r, c) for r in range(4) for c in range(8) if intended[r][c] != rival[r][c]] == [
        (1, 2),
        (1, 4),
    ]
    for index in range(1, 18):
        if index % 3 == 0:
            continue
        grid = gen.generate(9200, index, difficulty="medium")
        assert mismatched_rows(grid)
        assert gen.SEMANTIC_WITNESSES["same_colour_required"](grid)
        assert gen.SEMANTIC_RIVALS["any_two_nonzero"](grid) != intended_output(grid)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 7 for _ in range(4)],
        [[0] * 7 for _ in range(4)],
    ],
)
def test_self_check_rejects_malformed_or_rule_vacuous_inputs(grid):
    assert gen.self_check(grid)


def test_real_racket_authority_matches_oracle_for_canonical_witness_and_samples():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [shortcut_witness()]
    grids.extend(gen.generate(101, index, difficulty="medium") for index in range(12))
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]

@pytest.mark.parametrize("index", range(12))
def test_difficulty_bands_change_pixels_without_changing_exact_profile(index):
    grids = {
        band: gen.generate(12345, index, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert grids["easy"] != grids["hard"]
    assert len({(len(grid), len(grid[0]), len(pair_rows(grid))) for grid in grids.values()}) == 1
    assert all(gen.self_check(grid) == [] for grid in grids.values())
