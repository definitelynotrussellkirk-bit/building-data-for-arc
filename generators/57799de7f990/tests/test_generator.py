"""Focused portable regression suite for the repaired 57799de7f990 sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    axis_local_rival,
    canonical_pairs,
    diamond_centers,
    explicit_witness,
    intended_output,
    load_generator,
    observed,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_pins_authority_and_declares_only_observable_exact_axes():
    assert gen.RULE_HASH == "cd5434186fae"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_diamonds", "three_arm_witness"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.CANONICAL_SHORTCUTS) == {"axis_local_three_arm"}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{len(p['input'])}x{len(p['input'][0])}")
def test_accepts_canonical_inputs_and_independent_oracle_matches_labels(pair):
    grid = deepcopy(pair["input"])
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert intended_output(grid) == pair["output"]
    assert axis_local_rival(grid) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 9, "grid_w": 9, "n_diamonds": 3, "three_arm_witness": True},
        {"grid_h": 9, "grid_w": 9, "n_diamonds": 7, "three_arm_witness": False},
        {"grid_h": 26, "grid_w": 26, "n_diamonds": 7, "three_arm_witness": True},
        {"grid_h": 14, "grid_w": 16, "n_diamonds": 5, "three_arm_witness": False},
    ],
)
def test_exact_overrides_are_constructive_and_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 8}, {"grid_h": 27}, {"grid_h": True}, {"grid_h": 9.0},
        {"grid_w": 8}, {"grid_w": 27}, {"grid_w": "9"},
        {"n_diamonds": 2}, {"n_diamonds": 8}, {"n_diamonds": False},
        {"three_arm_witness": 1}, {"three_arm_witness": "true"},
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,index,difficulty",
    [
        (True, 0, None), (1.5, 0, None), ("1", 0, None),
        (0, True, None), (0, -1, None), (0, 1.5, None),
        (0, 0, "expert"), (0, 0, 0.5),
    ],
)
def test_rejects_invalid_call_scalars(seed, index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, index, difficulty=difficulty)


@pytest.mark.parametrize("n", range(3, 8))
def test_explicit_witness_family_refutes_three_arm_rival(n):
    grid = gen.generate(71, 4, grid_h=9, grid_w=9, n_diamonds=n,
                        three_arm_witness=True)
    assert gen.self_check(grid) == []
    assert len(diamond_centers(grid)) == n
    assert gen.SEMANTIC_WITNESSES["three_arm_false_center"](grid)
    assert gen.SEMANTIC_RIVALS["axis_local_three_arm"](grid) == axis_local_rival(grid)
    assert axis_local_rival(grid) != intended_output(grid)


def test_exact_handmade_counterexample_disagrees_at_expected_cells():
    grid = explicit_witness()
    assert gen.self_check(grid) == []
    intended = intended_output(grid)
    rival = axis_local_rival(grid)
    assert [(r, c) for r in range(9) for c in range(9)
            if intended[r][c] != rival[r][c]] == [(2, 3), (2, 5)]


@pytest.mark.parametrize("n", range(3, 8))
def test_plain_family_has_no_accidental_three_arm_shortcut_witness(n):
    grid = gen.generate(91, n, grid_h=9, grid_w=9, n_diamonds=n,
                        three_arm_witness=False)
    assert gen.self_check(grid) == []
    assert len(diamond_centers(grid)) == n
    assert intended_output(grid) == axis_local_rival(grid)
    assert gen.observe_overrides(grid)["three_arm_witness"] is False


def test_default_schedule_teaches_rival_under_every_rotated_query_window():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(314159, start + offset, difficulty=band)
                lesson.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(len(lesson)):
                query = lesson[query_index]
                demos = lesson[:query_index] + lesson[query_index + 1:]
                assert gen.lesson_identifiable(demos, query) == []
                assert any(axis_local_rival(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)], [[2] * 9 for _ in range(9)]],
)
def test_malformed_or_impostor_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_red_counts_without_lawful_diamond_structure():
    no_alignment = [[0] * 9 for _ in range(9)]
    for r, c in ((2, 2), (6, 6), (2, 6)):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            no_alignment[r + dr][c + dc] = 2
    # Remove the only aligned pair while preserving twelve red cells.
    no_alignment[2][5] = 0
    no_alignment[5][6] = 2
    assert gen.self_check(no_alignment)


def test_default_generation_is_deterministic_diverse_and_always_transforms():
    inputs = set()
    profiles = set()
    witness_values = set()
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(8000 + index, index * 7 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(8000 + index, index * 7 + 3, difficulty=band)
            assert intended_output(grid) != grid
            stats = observed(grid)
            inputs.add(repr(grid))
            profiles.add((stats["grid_h"], stats["grid_w"]))
            witness_values.add(stats["three_arm_witness"])
    assert len(inputs) >= 100
    assert len(profiles) >= 4
    assert witness_values == {False, True}

@pytest.mark.parametrize("shape", [(9, 26), (26, 9), (26, 26)])
@pytest.mark.parametrize("witness", [False, True])
def test_large_canvas_examples_demonstrate_a_nontrivial_connection_fraction(shape, witness):
    h, w = shape
    grid = gen.generate(222, 6, grid_h=h, grid_w=w, n_diamonds=3,
                        three_arm_witness=witness)
    output = intended_output(grid)
    changed = sum(a != b for row_a, row_b in zip(grid, output)
                  for a, b in zip(row_a, row_b))
    assert changed / (h * w) >= 0.02
