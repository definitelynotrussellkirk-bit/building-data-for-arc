"""Task-local regressions for the e4351af561ac input sampler."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (RIVALS, canonical_pairs, load_generator, observed,
                             official_output, reflection_allowed, translation_only)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_canonical_pairs_match_independent_oracle_and_validate():
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert official_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_and_pixel_observable(band):
    options = {
        "grid_h": 9,
        "grid_w": 12,
        "template_size": 4,
        "n_match": 2,
        "n_nonmatch": 2,
        "n_other_match": 1,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("name,value", [
    ("unknown_axis", 1),
    ("grid_h", 8), ("grid_h", 17),
    ("grid_w", 11), ("grid_w", 19),
    ("template_size", 2), ("template_size", 6),
    ("n_match", 0), ("n_match", 3),
    ("n_nonmatch", 0), ("n_nonmatch", 3),
    ("n_other_match", -1), ("n_other_match", 2),
    ("n_match", True), ("grid_w", 12.0), ("template_size", "4"),
])
def test_invalid_overrides_are_rejected(name, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{name: value})


@pytest.mark.parametrize("bad_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_is_rejected(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, bad_index)


def test_minimum_canvas_supports_every_count_product():
    for n_match in (1, 2):
        for n_nonmatch in (1, 2):
            for n_other in (0, 1):
                for size in (3, 4, 5):
                    options = dict(grid_h=9, grid_w=12, template_size=size,
                                   n_match=n_match, n_nonmatch=n_nonmatch,
                                   n_other_match=n_other)
                    grid = gen.generate(1300 + size, 10*n_match + 3*n_nonmatch + n_other,
                                        difficulty="hard", **options)
                    assert gen.self_check(grid) == []
                    assert observed(grid) == options


def test_declared_schedule_refutes_every_rival_after_any_single_holdout():
    period = gen.LESSON_SCHEDULE_PERIOD
    assert period == 4
    pairs = []
    for index in range(period):
        grid = gen.generate(711, index, difficulty="hard")
        pairs.append({"input": grid, "output": official_output(grid)})
    for query_index in range(period):
        demos = [pair for i, pair in enumerate(pairs) if i != query_index]
        query = pairs[query_index]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in RIVALS.items():
            assert not (all(rival(pair["input"]) == pair["output"] for pair in demos)
                        and rival(query["input"]) != query["output"]), name


def test_teaching_profile_distinguishes_rotation_and_reflection():
    grid = gen.generate(712, 0, template_size=4, n_match=2,
                        n_nonmatch=1, n_other_match=1)
    intended = official_output(grid)
    assert translation_only(grid) != intended
    assert reflection_allowed(grid) != intended
    assert gen.SEMANTIC_WITNESSES["translation_only"](grid)
    assert gen.SEMANTIC_WITNESSES["reflection_allowed"](grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(9)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_retained_counterexample_refutes_all_declared_rivals():
    case = json.loads((HOME / "counterexamples" / "multi_rival_witness.json").read_text())
    grid = case["input"]
    expected = case["expected_output"]
    assert gen.self_check(grid) == []
    assert official_output(grid) == expected
    assert set(case["refutes"]) == set(RIVALS)
    for name in case["refutes"]:
        assert RIVALS[name](grid) != expected, name
