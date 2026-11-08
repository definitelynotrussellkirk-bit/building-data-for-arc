"""Focused regression tests for the reviewed 4238cc89338a generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_demonstrations,
    canonical_pairs,
    has_blue_row_gap,
    load_generator,
    observed,
    output,
    shortcut_diff,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_accepted_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert output(pair["input"]) == pair["output"]


def test_metadata_pins_current_authority_and_only_advertises_real_axes():
    assert gen.RULE_HASH == "e8d6ce4b7903"
    assert set(gen.AXES) == {"grid_h", "grid_w", "blue_size", "red_size", "profile_mode"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_override_is_exact_in_every_band(band):
    expected = {
        "grid_h": 10,
        "grid_w": 14,
        "blue_size": 5,
        "red_size": 5,
        "profile_mode": "counterexample",
    }
    grid = gen.generate(17, 9, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert observed(grid) == expected
    assert shortcut_diff(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 9},
        {"grid_w": 13},
        {"blue_size": 4},
        {"red_size": 10},
        {"profile_mode": "unknown"},
        {"grid_h": True},
        {"blue_size": 5.0},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_first_twenty_defaults_cover_each_canonical_canvas_profile(band):
    shapes = {(len(gen.generate(31, i, difficulty=band)), len(gen.generate(31, i, difficulty=band)[0]))
              for i in range(20)}
    assert (10, 18) in shapes
    assert (11, 20) in shapes


def test_default_schedule_repeatedly_emits_real_shortcut_counterexamples():
    grids = [gen.generate(73, i, difficulty="medium") for i in range(12)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert sum(bool(shortcut_diff(grid)) for grid in grids) >= 6
    assert all(has_blue_row_gap(grids[i]) for i in range(0, 12, 2))


def test_blue_row_span_shortcut_fits_canonical_demos_but_not_witnesses():
    rival = gen.SEMANTIC_RIVALS["blue_row_span"]
    assert all(
        rival(pair["input"]) == pair["output"]
        for pair in canonical_demonstrations()
    )
    # The labeled canonical test already distinguishes the shortcut; the
    # generator must nevertheless teach that distinction in ordinary lessons.
    assert any(
        rival(pair["input"]) != pair["output"]
        for pair in canonical_pairs()[len(canonical_demonstrations()):]
    )
    witness = gen.generate(101, 0, profile_mode="counterexample")
    assert gen.SEMANTIC_WITNESSES["blue_row_gap"](witness)
    assert rival(witness) != output(witness)


def test_lesson_hook_requires_a_counterexample_in_the_demonstrations():
    compact = gen.generate(8, 1, profile_mode="compact")
    witness = gen.generate(8, 0, profile_mode="counterexample")
    compact_pair = {"input": compact, "output": output(compact)}
    witness_pair = {"input": witness, "output": output(witness)}
    assert gen.lesson_identifiable([compact_pair], compact_pair)
    assert gen.lesson_identifiable([compact_pair, witness_pair], compact_pair) == []


def test_generation_is_deterministic_and_does_not_mutate_results():
    first = gen.generate(202, 7, difficulty="hard")
    snapshot = deepcopy(first)
    assert gen.generate(202, 7, difficulty="hard") == first
    assert output(first) == output(snapshot)
    assert first == snapshot


@pytest.mark.parametrize("mutation", ["unknown_color", "erase_blue", "split_blue", "ragged"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(44, 0, profile_mode="counterexample")
    if mutation == "unknown_color":
        grid[0][0] = 9
    elif mutation == "erase_blue":
        for row in grid:
            for c, value in enumerate(row):
                if value == 1:
                    row[c] = 0
    elif mutation == "split_blue":
        grid[0][0] = 1
    else:
        grid[0].pop()
    assert gen.self_check(grid)


def test_standard_probe_stream_covers_declared_output_codomain():
    outputs = {
        tuple(tuple(row) for row in output(gen.generate(ep * 101, sample_index)))
        for ep in range(24)
        for sample_index in range(6)
    }
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 39
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN


def test_source_avoids_racket_primitive_identifier_objects():
    import ast

    tree = ast.parse(Path(gen.__file__).read_text())
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    assert "objects" not in names


def test_schedule_has_three_canonical_canvas_slots_without_public_period_claim():
    canonical = {(10, 18), (11, 20)}
    for band in ("easy", "medium", "hard"):
        dimensions = [
            (len(gen.generate(509, index, difficulty=band)),
             len(gen.generate(509, index, difficulty=band)[0]))
            for index in range(10)
        ]
        assert sum(value in canonical for value in dimensions) >= 3
    assert gen._SCHEDULE_PERIOD == 10
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")


def test_placement_is_constructive_without_materialized_pair_cache():
    assert not hasattr(gen, "_placement_pairs")
    for height in (10, 22):
        for width in (14, 22):
            for blue_size in (5, 9):
                for red_size in (5, 9):
                    for mode in gen.PROFILE_MODES:
                        grid = gen.generate(
                            811,
                            blue_size + red_size,
                            grid_h=height,
                            grid_w=width,
                            blue_size=blue_size,
                            red_size=red_size,
                            profile_mode=mode,
                        )
                        assert gen.self_check(grid) == []
