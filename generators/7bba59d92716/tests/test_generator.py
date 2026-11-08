"""Regression frontier for the repaired exact-component line generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    all_vertical_components,
    branch_witness,
    branched_run5_signatures,
    canonical_pairs,
    changed_cells,
    component_size5_any_shape,
    intended_output,
    load_generator,
    observed,
    off_midpoint_branch_witness,
    run5_ignores_branches,
    run5_skips_midpoint_side_neighbor,
    run5_skips_six_cell_branch,
    vertical_length_at_least5,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {"profile", "n_targets", "decoy_length", "n_distractors"}


def test_contract_surface_is_pinned_and_observable():
    assert gen.RULE_HASH == "0f19aed9b60e"
    assert gen.VERSION == "2.1.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.lesson_identifiable)


def test_all_canonical_pairs_are_accepted_and_independent_oracle_matches():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert intended_output(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(profile="p8x10c4", n_targets=2, decoy_length=3, n_distractors=2),
        dict(profile="p10x13c3", n_targets=3, decoy_length=6, n_distractors=4),
        dict(profile="p9x12c4", n_targets=3, decoy_length=4, n_distractors=3),
    ],
)
def test_exact_overrides_are_realized_in_every_band(band, options):
    grid = gen.generate(20261007, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == gen.observe_overrides(grid) | {
        "branched_run5": True,
        "horizontal5": True,
        "palette": observed(grid)["palette"],
        "component_sizes": observed(grid)["component_sizes"],
    }
    assert gen.observe_overrides(grid) == options
    assert gen.generate(20261007, 9, difficulty=band, **options) == grid


@pytest.mark.parametrize(
    "bad",
    [
        {"unknown_axis": 1},
        {"profile": "p7x7c2"},
        {"n_targets": 1},
        {"n_targets": 4},
        {"decoy_length": 5},
        {"n_distractors": 1},
        {"n_distractors": 5},
        {"n_targets": True},
        {"decoy_length": "3"},
        {"profile": 3},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **bad)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_canonical_profiled_and_counterexample_rich(band):
    grids = [gen.generate(4000 + index, index, difficulty=band) for index in range(30)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    facts = [observed(grid) for grid in grids]
    assert all(row["profile"] in CANONICAL_PROFILES for row in facts)
    assert {row["n_targets"] for row in facts} == {2, 3}
    assert {row["decoy_length"] for row in facts} == {3, 4, 6}
    assert {row["n_distractors"] for row in facts} == {2, 3, 4}
    assert all(row["branched_run5"] for row in facts)
    assert all(row["horizontal5"] for row in facts)
    assert all(run5_ignores_branches(grid) != intended_output(grid) for grid in grids)
    assert all(
        run5_skips_midpoint_side_neighbor(grid) != intended_output(grid)
        for grid in grids
    )
    signatures = [signature for grid in grids for signature in branched_run5_signatures(grid)]
    assert {size for size, _ in signatures} == {6, 7}
    assert all(2 not in offsets for _, offsets in signatures)
    assert any(
        run5_skips_six_cell_branch(grid) != intended_output(grid)
        for grid in grids
    )
    assert all(component_size5_any_shape(grid) != intended_output(grid) for grid in grids)


def test_declared_canonical_shortcuts_fit_canonical_and_generated_witnesses_refute():
    pairs = canonical_pairs()
    assert all(run5_ignores_branches(pair["input"]) == pair["output"] for pair in pairs)
    assert all(
        run5_skips_midpoint_side_neighbor(pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert all(
        run5_skips_six_cell_branch(pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert all(component_size5_any_shape(pair["input"]) == pair["output"] for pair in pairs)

    witness = branch_witness()
    assert gen.strict_canonical_like(witness) == []
    assert changed_cells(intended_output(witness), run5_ignores_branches(witness)) == [
        (3, 2, 1, 2)
    ]

    off_midpoint = off_midpoint_branch_witness()
    assert gen.strict_canonical_like(off_midpoint) == []
    assert changed_cells(
        intended_output(off_midpoint),
        run5_skips_midpoint_side_neighbor(off_midpoint),
    ) == [(3, 2, 1, 2)]

    grid = gen.generate(
        99,
        7,
        profile="p8x10c4",
        n_targets=2,
        decoy_length=6,
        n_distractors=2,
    )
    intended = intended_output(grid)
    assert gen.SEMANTIC_WITNESSES["branched_run5_decoy"](grid)
    assert gen.SEMANTIC_WITNESSES["horizontal_size5_decoy"](grid)
    assert gen.SEMANTIC_WITNESSES["wrong_length_vertical_decoy"](grid)
    assert gen.SEMANTIC_RIVALS["run5_ignores_branches"](grid) != intended
    assert gen.SEMANTIC_RIVALS["run5_skips_midpoint_side_neighbor"](grid) != intended
    assert gen.SEMANTIC_RIVALS["component_size5_any_shape"](grid) != intended
    assert gen.SEMANTIC_RIVALS["all_vertical_components"](grid) != intended
    assert gen.SEMANTIC_RIVALS["vertical_length_at_least5"](grid) != intended


def test_branch_schedule_varies_component_size_and_attachment_rows():
    signatures = []
    for sample_index in range(8):
        grid = gen.generate(66119, sample_index, difficulty="medium")
        rows = branched_run5_signatures(grid)
        assert len(rows) == 1
        signatures.extend(rows)
        assert run5_skips_midpoint_side_neighbor(grid) != intended_output(grid)
    assert {size for size, _ in signatures} == {6, 7}
    assert {offsets for _, offsets in signatures} == {
        (0,),
        (1, 3),
        (4,),
        (0, 4),
    }


def test_materialized_lesson_contract_eliminates_every_declared_competitor():
    pairs = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(77123, index, difficulty="medium")
        pairs.append({"input": grid, "output": intended_output(grid)})
    assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        bad = deepcopy(pairs)
        bad[0]["output"] = rival(bad[0]["input"])
        # At least the untouched genuine demonstrations still expose the rival.
        assert any(rival(pair["input"]) != pair["output"] for pair in bad[1:-1])


def test_self_check_rejects_loss_of_answer_or_semantic_structure():
    grid = gen.generate(
        123,
        4,
        profile="p8x10c4",
        n_targets=2,
        decoy_length=3,
        n_distractors=2,
    )
    assert gen.self_check(grid) == []

    no_targets = deepcopy(grid)
    intended = intended_output(no_targets)
    for r, row in enumerate(intended):
        for c, value in enumerate(row):
            if value == 2:
                no_targets[r][c] = 0
    assert gen.self_check(no_targets)

    output_color_in_input = deepcopy(grid)
    output_color_in_input[0][0] = 2
    assert gen.self_check(output_color_in_input)

    ragged = [row[:] for row in grid]
    ragged[-1].pop()
    assert gen.self_check(ragged)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    state = random.getstate()
    first = gen.generate(314159, 27, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 27, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert gen.generate(314159, 27, difficulty="hard") == second

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_survives_all_query_rotations(band):
    """A held-out long decoy must not be the lesson's only >=5 counterexample."""
    for start in range(8):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(99117, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (
                band,
                start,
                query_index,
                [observed(pair["input"])["decoy_length"] for pair in pairs],
            )
