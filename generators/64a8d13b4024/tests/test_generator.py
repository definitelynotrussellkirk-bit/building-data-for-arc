"""Focused regressions for the 64a8d13b4024 generator repair."""
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
    capped_five_output,
    canonical_pairs,
    load_generator,
    observed,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def pair(grid):
    return {"input": grid, "output": reference_output(grid)}


@pytest.mark.parametrize("pair_data", canonical_pairs())
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair_data):
    source = deepcopy(pair_data["input"])
    assert gen.RULE_HASH == "e9d7e0db9b8a"
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert reference_output(source) == pair_data["output"]
    assert gen.rule_mirror(source) == pair_data["output"]
    assert source == pair_data["input"]


def test_axis_contract_contains_only_observable_controls():
    assert set(gen.AXES) == {"grid_h", "grid_w", "n1", "n2", "n3"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 8, "grid_w": 14, "n1": 2, "n2": 2, "n3": 2},
        {"grid_h": 14, "grid_w": 8, "n1": 6, "n2": 1, "n3": 6},
    ],
)
def test_every_advertised_override_is_exact_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7), ("grid_h", 15), ("grid_h", True), ("grid_h", "8"),
        ("grid_w", 7), ("grid_w", 15), ("grid_w", 8.0),
        ("n1", 0), ("n1", 7), ("n1", False),
        ("n2", 0), ("n2", 7), ("n2", "2"),
        ("n3", 0), ("n3", 7), ("n3", 2.5),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["extreme", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_equal_counts_are_lawful_and_never_silently_rewritten():
    grid = gen.generate(12, 4, grid_h=10, grid_w=11, n1=3, n2=3, n3=3)
    assert observed(grid) == {"grid_h": 10, "grid_w": 11, "n1": 3, "n2": 3, "n3": 3}
    assert reference_output(grid) == gen.rule_mirror(grid)


def test_every_query_rotation_keeps_a_count_six_witness_in_the_demonstrations():
    rival = gen.CANONICAL_SHORTCUTS["cap_bars_at_five"]
    for band in (None, "easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            episode = [
                gen.generate(71, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query_grid in enumerate(episode):
                demos = [pair(grid) for index, grid in enumerate(episode) if index != query_index]
                assert any(rival(item["input"]) != item["output"] for item in demos)
                assert gen.lesson_identifiable(demos, pair(query_grid)) == []


def test_count_six_schedule_refutes_canonical_fitting_cap_five_rival():
    rival = gen.CANONICAL_SHORTCUTS["cap_bars_at_five"]
    assert rival is gen.SEMANTIC_RIVALS["cap_bars_at_five"]
    assert rival is gen.LESSON_COMPETITORS["cap_bars_at_five"]
    assert all(rival(item["input"]) == item["output"] for item in canonical_pairs())
    for band in (None, "easy", "medium", "hard"):
        for start in range(9):
            demos = [gen.generate(44, start + offset, difficulty=band) for offset in range(gen.EXAMPLES_NEEDED)]
            assert any(gen.SEMANTIC_WITNESSES["count_reaches_six"](grid) for grid in demos)
            assert any(rival(grid) != gen.rule_mirror(grid) for grid in demos)
            query = gen.generate(44, start + gen.EXAMPLES_NEEDED, difficulty=band)
            assert gen.lesson_identifiable([pair(grid) for grid in demos], pair(query)) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_valid_deterministic_and_nontrivial(band):
    seen = set()
    values = {name: set() for name in gen.AXES}
    for index in range(96):
        grid = gen.generate(2000 + index, index, difficulty=band)
        assert grid == gen.generate(2000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == reference_output(grid)
        stats = observed(grid)
        for name, value in stats.items():
            values[name].add(value)
        seen.add(repr(grid))
    assert len(seen) > 80
    assert 6 in values["n1"] | values["n2"] | values["n3"]
    assert all(len(values[name]) >= 3 for name in values)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(8)],
        [[4] + [0] * 7 for _ in range(8)],
        [[0] * 8 for _ in range(8)],
    ],
)
def test_malformed_or_out_of_manifold_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_count_above_six_and_preserves_input():
    grid = gen.generate(3, 2, grid_h=8, grid_w=8, n1=6, n2=2, n3=1)
    changed = deepcopy(grid)
    zero = next((r, c) for r, row in enumerate(changed) for c, value in enumerate(row) if value == 0)
    changed[zero[0]][zero[1]] = 1
    snapshot = deepcopy(changed)
    assert gen.self_check(changed)
    assert changed == snapshot


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
