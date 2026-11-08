"""Regression, contract, and semantic tests for ae0d46c67401."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    load_generator,
    observed,
    racket_outputs,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {"size", "cells", "palette_size", "side_profile", "anchor_corner"}


def test_rule_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "2b970065d6a3"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_accepts_all_canonical_inputs_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"size": 5, "cells": 9, "palette_size": 3, "side_profile": "above", "anchor_corner": False},
        {"size": 5, "cells": 3, "palette_size": 1, "side_profile": "mixed", "anchor_corner": True},
        {"size": 14, "cells": 9, "palette_size": 3, "side_profile": "below", "anchor_corner": True},
    ],
)
def test_exact_overrides_are_constructive_and_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert reference_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("size", 4), ("size", 15), ("size", True), ("size", 6.0),
        ("cells", 2), ("cells", 10), ("cells", "3"),
        ("palette_size", 0), ("palette_size", 4), ("palette_size", True),
        ("side_profile", "upper"), ("side_profile", 1),
        ("anchor_corner", 1), ("anchor_corner", "false"),
    ],
)
def test_rejects_invalid_or_unknown_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["trivial", "expert", 1, True])
def test_rejects_unknown_difficulty(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band_index,band", enumerate(("easy", "medium", "hard")))
def test_default_distribution_covers_every_axis_and_canonical_sizes(band_index, band):
    support = {name: set() for name in EXPECTED_AXES}
    unique = set()
    for index in range(140):
        seed = 5000 + band_index * 1000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        facts = observed(grid)
        assert gen.observe_overrides(grid) == facts
        for name, value in facts.items():
            support[name].add(value)
        unique.add(json.dumps(grid, separators=(",", ":")))
        output = reference_output(grid)
        assert output != grid
        assert sum(a != b for ra, rb in zip(grid, output) for a, b in zip(ra, rb)) == facts["cells"]
    assert support["side_profile"] == {"above", "below", "mixed"}
    assert support["anchor_corner"] == {False, True}
    assert support["palette_size"] == {1, 2, 3}
    assert support["cells"] == set(range(3, 10))
    assert {5, 6} <= support["size"]
    assert len(support["size"]) >= 4
    assert len(unique) >= 135


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_twenty_item_window_hits_canonical_size_profile(band):
    for start in range(0, 80, 20):
        sizes = {
            observed(gen.generate(8100 + index, index, difficulty=band))["size"]
            for index in range(start, start + 20)
        }
        assert sizes & {5, 6}


def test_four_item_schedule_survives_every_query_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            grids = [gen.generate(9000 + start, start + offset, difficulty=band) for offset in range(4)]
            profiles = [observed(grid)["side_profile"] for grid in grids]
            assert profiles.count("mixed") >= 2
            outputs = [reference_output(grid) for grid in grids]
            for query_index in range(4):
                demos = [
                    {"input": grids[i], "output": outputs[i]}
                    for i in range(4)
                    if i != query_index
                ]
                query = {"input": grids[query_index], "output": outputs[query_index]}
                assert gen.lesson_identifiable(demos, query) == []


def test_generated_inputs_have_empty_transpose_targets_and_exact_palette():
    for index in range(100):
        grid = gen.generate(11_000 + index, index, difficulty="hard")
        points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        assert all(r != c for r, c in points)
        assert all(grid[c][r] == 0 for r, c in points)
        facts = observed(grid)
        assert len({grid[r][c] for r, c in points}) == facts["palette_size"]


def test_declared_witnesses_refute_their_named_rivals():
    grid = gen.generate(
        12001,
        2,
        size=8,
        cells=7,
        palette_size=3,
        side_profile="mixed",
        anchor_corner=True,
    )
    intended = reference_output(grid)
    for witness, rivals in gen.WITNESS_RIVALS.items():
        assert gen.SEMANTIC_WITNESSES[witness](grid)
        assert any(gen.SEMANTIC_RIVALS[name](grid) != intended for name in rivals)
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize(
    "case",
    ["empty", "ragged", "nonsquare", "bool", "blank", "diagonal", "paired", "four_colors"],
)
def test_self_check_rejects_structural_impostors(case):
    grid = gen.generate(7, 3, size=7, cells=5, palette_size=3, side_profile="mixed", anchor_corner=False)
    if case == "empty":
        bad = []
    elif case == "ragged":
        bad = deepcopy(grid); bad[0].pop()
    elif case == "nonsquare":
        bad = [row[:-1] for row in grid]
    elif case == "bool":
        bad = deepcopy(grid); bad[0][0] = True
    elif case == "blank":
        bad = [[0] * 7 for _ in range(7)]
    elif case == "diagonal":
        bad = deepcopy(grid); bad[3][3] = 1
    elif case == "paired":
        bad = deepcopy(grid)
        r, c = next((r, c) for r, row in enumerate(bad) for c, value in enumerate(row) if value)
        bad[c][r] = 9 if bad[r][c] != 9 else 8
    else:
        bad = deepcopy(grid)
        zeros = [(r, c) for r in range(7) for c in range(r + 1, 7) if bad[r][c] == bad[c][r] == 0]
        for color, (r, c) in zip((1, 2, 3, 4), zeros):
            bad[r][c] = color
    assert gen.self_check(bad)


def test_global_rng_purity_and_fresh_returns():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_real_racket_authority_on_canonical_and_generated_inputs():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty="medium") for index in range(8)]
    try:
        actual = racket_outputs(grids)
    except Exception as exc:
        pytest.skip(f"Racket authority unavailable in this invocation: {exc}")
    assert actual == [reference_output(grid) for grid in grids]
