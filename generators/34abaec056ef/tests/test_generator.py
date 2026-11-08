"""Regression tests for the source-bound repair of task 34abaec056ef."""
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
    BASES,
    any_nonframe_color_output,
    canonical_pairs,
    color_shortcut_witness,
    frame,
    intended_output,
    load_generator,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=("train0", "train1", "test0"))
def test_canonical_examples_are_accepted_and_independently_reproduced(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_honored_in_every_band(band):
    options = {
        "grid_h": 9,
        "grid_w": 9,
        "orientation": 7,
        "n_markers": 5,
        "n_outer_markers": 4,
        "n_local_distractors": 1,
        "n_exterior_distractors": 4,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 8},
        {"grid_w": 17},
        {"orientation": 8},
        {"n_markers": 0},
        {"n_markers": 6},
        {"n_outer_markers": 5},
        {"n_local_distractors": 2},
        {"n_exterior_distractors": 5},
        {"grid_h": True},
        {"orientation": 1.0},
        {"n_markers": "3"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (0, True, None),
        (0, -1, None),
        (0, 0, True),
        (0, 0, "impossible"),
    ],
)
def test_invalid_call_scalars_are_rejected(seed, index, difficulty):
    with pytest.raises(ValueError):
        gen.generate(seed, index, difficulty=difficulty)


def test_all_generated_frames_are_cardinal_and_reference_lawful():
    for band in (None, "easy", "medium", "hard"):
        for index in range(96):
            grid = gen.generate(7000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert frame(grid)[1:] in BASES
            assert grid == gen.generate(7000 + index, index, difficulty=band)
            assert intended_output(grid) == gen.rule_mirror(grid)


def test_schedule_hits_canonical_profile_and_teaches_color_selection():
    for band in (None, "easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [
                gen.generate(211, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            assert any((len(g), len(g[0]), len({v for row in g for v in row})) == (9, 9, 5) for g in grids)
            assert sum(observed(g)["n_local_distractors"] == 1 for g in grids) >= 2
            pairs = [{"input": g, "output": intended_output(g)} for g in grids]
            query_grid = gen.generate(211, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": intended_output(query_grid)}
            assert gen.lesson_identifiable(pairs, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name


def test_canonical_shortcut_has_exact_generated_counterexample():
    canonical = canonical_pairs()
    assert all(any_nonframe_color_output(pair["input"]) == pair["output"] for pair in canonical)
    witness = color_shortcut_witness()
    assert gen.self_check(witness) == []
    assert intended_output(witness) != any_nonframe_color_output(witness)
    assert gen.CANONICAL_SHORTCUTS["any_nonframe_local_color"](witness) == any_nonframe_color_output(witness)
    assert gen.SEMANTIC_WITNESSES["ignored_local_color"](witness)
    assert any(
        observed(gen.generate(919, i))["n_local_distractors"] == 1
        for i in range(gen.LESSON_SCHEDULE_PERIOD)
    )


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 9 for _ in range(9)],
    ],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_noncardinal_and_duplicate_frames():
    diagonal = [[0] * 9 for _ in range(9)]
    diagonal[4][4] = 2
    diagonal[3][3] = 3
    diagonal[5][3] = 4
    diagonal[3][5] = 8
    assert gen.self_check(diagonal)

    duplicate = color_shortcut_witness()
    duplicate[0][0] = 2
    assert gen.self_check(duplicate)


def test_replay_is_fresh_and_global_rng_pure():
    random.seed(6421)
    expected = [random.random() for _ in range(8)]
    random.seed(6421)
    first = gen.generate(31337, 17, difficulty="hard")
    second = gen.generate(31337, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(31337, 17, difficulty="hard") == second
    assert [random.random() for _ in range(8)] == expected


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [color_shortcut_witness()]
    grids += [gen.generate(812, i, orientation=i % 8) for i in range(32)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_declares_complete_intrinsic_output_codomain():
    import math

    # The frame occupies three of the 3x3 local cells. Production places 1..5
    # markers in the remaining six, so every nonempty/non-full subset is lawful.
    assert gen.EXPECTED_OUTPUT_CODOMAIN == sum(math.comb(6, k) for k in range(1, 6)) == 62


def test_default_lint_horizon_covers_complete_output_codomain():
    outputs = {
        tuple(tuple(row) for row in intended_output(gen.generate(ep * 101, sample_index)))
        for ep in range(24)
        for sample_index in range(6)
    }
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN == 62
