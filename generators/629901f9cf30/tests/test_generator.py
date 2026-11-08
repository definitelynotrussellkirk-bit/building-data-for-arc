"""Focused regressions for the 629901f9cf30 generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    first_three_seeds_output,
    load_generator,
    lowest_color_on_ties_output,
    observed,
    reference_output,
    tie_cells,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def pair(grid):
    return {"input": grid, "output": reference_output(grid)}


@pytest.mark.parametrize("pair_data", canonical_pairs())
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair_data):
    source = deepcopy(pair_data["input"])
    assert gen.RULE_HASH == "96013a689278"
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert reference_output(source) == pair_data["output"]
    assert gen.rule_mirror(source) == pair_data["output"]
    assert tie_cells(source)
    assert source == pair_data["input"]


def test_axis_contract_contains_only_observable_controls():
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_seeds"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 4, "grid_w": 18, "n_seeds": 2},
        {"grid_h": 18, "grid_w": 4, "n_seeds": 6},
    ],
)
def test_every_advertised_override_is_exact_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert tie_cells(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 3), ("grid_h", 19), ("grid_h", True), ("grid_h", "4"),
        ("grid_w", 3), ("grid_w", 19), ("grid_w", 4.0),
        ("n_seeds", 1), ("n_seeds", 7), ("n_seeds", False), ("n_seeds", "3"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["extreme", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_every_generated_grid_contains_a_real_tie_and_matches_oracle():
    for band in (None, "easy", "medium", "hard"):
        for index in range(128):
            grid = gen.generate(6000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert tie_cells(grid)
            assert gen.rule_mirror(grid) == reference_output(grid)
            assert gen.SEMANTIC_WITNESSES["tie_cells_remain_zero"](grid)
            assert gen.SEMANTIC_RIVALS["lowest_color_on_ties"](grid) == lowest_color_on_ties_output(grid)
            assert gen.SEMANTIC_RIVALS["lowest_color_on_ties"](grid) != gen.rule_mirror(grid)


def test_schedule_refutes_first_three_seed_shortcut_in_every_three_demo_window():
    rival = gen.CANONICAL_SHORTCUTS["first_three_seeds_only"]
    assert rival is gen.SEMANTIC_RIVALS["first_three_seeds_only"]
    assert rival is gen.LESSON_COMPETITORS["first_three_seeds_only"]
    assert all(rival(item["input"]) == item["output"] for item in canonical_pairs())
    for band in (None, "easy", "medium", "hard"):
        for start in range(9):
            demos = [gen.generate(47, start + offset, difficulty=band) for offset in range(gen.EXAMPLES_NEEDED)]
            assert any(gen.SEMANTIC_WITNESSES["more_than_three_seeds"](grid) for grid in demos)
            assert any(rival(grid) != gen.rule_mirror(grid) for grid in demos)
            query = gen.generate(47, start + gen.EXAMPLES_NEEDED, difficulty=band)
            assert gen.lesson_identifiable([pair(grid) for grid in demos], pair(query)) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_valid_deterministic_and_nontrivial(band):
    seen = set()
    values = {name: set() for name in gen.AXES}
    for index in range(96):
        grid = gen.generate(2000 + index, index, difficulty=band)
        assert grid == gen.generate(2000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        for name, value in stats.items():
            values[name].add(value)
        seen.add(repr(grid))
    assert len(seen) > 90
    assert values["n_seeds"] == {3, 4, 6}
    assert len(values["grid_h"]) >= 3
    assert len(values["grid_w"]) >= 3


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 4 for _ in range(4)], [[10] * 4 for _ in range(4)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_duplicate_seed_colors_and_no_tie_scene():
    duplicate = [[0] * 4 for _ in range(4)]
    duplicate[0][0] = 1
    duplicate[0][2] = 1
    assert gen.self_check(duplicate)

    no_tie = [[0] * 4 for _ in range(4)]
    no_tie[0][0] = 1
    no_tie[0][1] = 2
    assert not tie_cells(no_tie)
    assert gen.self_check(no_tie)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
