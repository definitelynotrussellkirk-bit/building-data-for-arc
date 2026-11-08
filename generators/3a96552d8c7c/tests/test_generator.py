"""Regression frontier for the horizontal exact-two-fives span task."""
from __future__ import annotations

import copy
import os
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import analyze, has_one_zero_span, independent_rule, load_generator

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
TASK = "3a96552d8c7c"
EXPECTED_AXES = {"grid_h", "grid_w", "n_fill_rows", "span_style", "negative_mode"}


def _pairs():
    return canonical_pairs(TASK, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_axis_contract_are_explicit_and_exact():
    assert gen.RULE_HASH == "91ba1164c014"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("pair", _pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_every_canonical_pair_is_owned_and_mirrored_exactly(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert independent_rule(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=6, grid_w=8, n_fill_rows=2, span_style="short", negative_mode="none"),
        dict(grid_h=7, grid_w=10, n_fill_rows=3, span_style="long", negative_mode="blocked"),
        dict(grid_h=8, grid_w=11, n_fill_rows=4, span_style="mixed", negative_mode="three_fives"),
        dict(grid_h=9, grid_w=12, n_fill_rows=2, span_style="short", negative_mode="wrong_color"),
        dict(grid_h=10, grid_w=14, n_fill_rows=4, span_style="mixed", negative_mode="mixed"),
    ],
)
def test_every_exact_override_is_pixel_observable_in_every_band(band, options):
    grid = gen.generate(20261004, 97, difficulty=band, **options)
    assert gen.self_check(grid) == []
    independent = analyze(grid)
    assert {key: independent[key] for key in options} == options
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) == independent_rule(grid)


def test_minimum_legal_one_zero_span_is_generated_not_only_accepted():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(941, index, difficulty=band) for index in range(12)]
        assert all(has_one_zero_span(grid) for grid in grids)
        assert all(independent_rule(grid) != grid for grid in grids)


def test_declared_witnesses_really_refute_their_named_rivals():
    grid = gen.generate(
        707,
        1,
        grid_h=6,
        grid_w=8,
        n_fill_rows=2,
        span_style="mixed",
        negative_mode="mixed",
    )
    expected = independent_rule(grid)
    assert gen.self_check(grid) == []
    assert set(gen.SEMANTIC_WITNESSES) == {
        "one_zero_span", "blocked_pair", "three_five_row", "wrong_color_pair"
    }
    for witness, rival_names in gen.WITNESS_RIVALS.items():
        assert gen.SEMANTIC_WITNESSES[witness](grid), witness
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected, (witness, rival_name)


def test_canonical_shortcuts_fit_canonical_but_default_teaching_refutes_them():
    pairs = _pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    for band in ("easy", "medium", "hard"):
        teaching = gen.generate(1234, 1, difficulty=band)
        expected = independent_rule(teaching)
        assert all(rival(teaching) != expected for rival in gen.CANONICAL_SHORTCUTS.values())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_scheduled_pairs_remain_identifiable_after_any_query_rotation(band):
    for start in range(12):
        pairs = [_pair(gen.generate(8000 + start, start + offset, difficulty=band)) for offset in range(4)]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band, start, query_index, name
                )


def test_canonical_profiles_have_scheduled_support_in_every_band():
    profiles = {(6, 8, 2), (7, 9, 2), (8, 10, 2)}
    for band in ("easy", "medium", "hard"):
        seen = set()
        for index in range(60):
            grid = gen.generate(77, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            if profile in profiles:
                seen.add(profile)
        assert seen == profiles


def test_validation_determinism_freshness_and_global_rng_isolation():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)
    for bad in (True, "3", 3.0):
        with pytest.raises(ValueError):
            gen.generate(0, 0, n_fill_rows=bad)
    with pytest.raises(ValueError):
        gen.generate(0, 0, span_style="tiny")
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="extreme")

    random.seed(991)
    state = random.getstate()
    a = gen.generate(123, 8, difficulty="hard")
    b = gen.generate(123, 8, difficulty="hard")
    assert a == b and a is not b and all(x is not y for x, y in zip(a, b))
    assert random.getstate() == state


def test_self_check_rejects_malformed_or_off_grammar_inputs():
    bad_grids = [
        [],
        [[0, 0], [0]],
        [[0] * 8 for _ in range(6)],
        [[5, 0, 5, 0, 5, 0, 0, 0], *([[0] * 8] * 5)],
        [[5, 0, 4, 0, 5, 0, 0, 0], *([[0] * 8] * 5)],
        [[5, 0, 5, 0, 0, 0, 0, 10], *([[0] * 8] * 5)],
    ]
    for grid in bad_grids:
        assert gen.self_check(grid), grid
