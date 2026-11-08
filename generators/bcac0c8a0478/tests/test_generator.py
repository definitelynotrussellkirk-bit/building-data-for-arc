"""Task-local regressions for the portal/checkpoint curriculum."""
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
    direct_to_goal_output,
    goal_first_output,
    ignore_portals_output,
    intended_output,
    load_generator,
    observed,
    positions,
    profile,
    racket_outputs,
    used_portal_colors,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(7, 9, 6), (7, 10, 6), (8, 11, 7)}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_selected_rule_and_validator_accept_all_canonical_pairs(pair):
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []


def test_goal_first_shortcut_fits_every_canonical_pair():
    assert all(goal_first_output(pair["input"]) == pair["output"] for pair in canonical_pairs())


def test_metadata_and_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "076228df68df"
    assert set(gen.AXES) == {"grid_h", "grid_w", "use_portal_6", "use_portal_7"}
    assert set(gen.SEMANTIC_RIVALS) >= {"goal_first_then_checkpoint", "direct_to_goal", "ignore_portals"}
    assert gen.CANONICAL_SHORTCUTS["goal_first_then_checkpoint"] is gen.SEMANTIC_RIVALS["goal_first_then_checkpoint"]
    assert "goal_first_counterexample" in gen.SEMANTIC_WITNESSES
    assert "goal_first_then_checkpoint" in gen.WITNESS_RIVALS["goal_first_counterexample"]
    assert set(gen.LESSON_COMPETITORS) >= set(gen.CANONICAL_SHORTCUTS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 9, "use_portal_6": 0, "use_portal_7": 0},
        {"grid_h": 8, "grid_w": 11, "use_portal_6": 1, "use_portal_7": 0},
        {"grid_h": 10, "grid_w": 13, "use_portal_6": 0, "use_portal_7": 1},
        {"grid_h": 13, "grid_w": 16, "use_portal_6": 1, "use_portal_7": 1},
    ],
)
def test_exact_observable_overrides_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert used_portal_colors(grid) == {
        color for color, key in ((6, "use_portal_6"), (7, "use_portal_7")) if options[key]
    }
    assert intended_output(grid) != goal_first_output(grid)
    assert intended_output(grid) != direct_to_goal_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"__override_contract_unknown_axis__": 1},
        {"grid_h": 6},
        {"grid_h": 14},
        {"grid_w": 8},
        {"grid_w": 17},
        {"use_portal_6": -1},
        {"use_portal_7": 2},
        {"grid_h": True},
        {"grid_w": 9.5},
        {"use_portal_6": "1"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_dense_deterministic_and_teaches_order(band):
    exact = 0
    unique = set()
    modes = set()
    for index in range(48):
        seed = 40_000 + index * 19
        grid = gen.generate(seed, index * 13 + 7, difficulty=band)
        assert grid == gen.generate(seed, index * 13 + 7, difficulty=band)
        assert gen.self_check(grid) == []
        assert intended_output(grid) != goal_first_output(grid)
        assert intended_output(grid) != direct_to_goal_output(grid)
        assert intended_output(grid) != ignore_portals_output(grid)
        assert used_portal_colors(grid) == {
            color for color in (6, 7) if len(positions(grid, color)) == 2
        }
        interior = [
            grid[r][c]
            for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
        ]
        assert interior.count(8) / len(interior) >= 0.20
        assert any(value == 0 for value in interior)
        assert sum(value == 4 for row in intended_output(grid) for value in row) >= 3
        exact += profile(grid) in CANONICAL_PROFILES
        modes.add((observed(grid)["use_portal_6"], observed(grid)["use_portal_7"]))
        unique.add(tuple(tuple(row) for row in grid))
    assert exact >= 36
    assert len(unique) >= 45
    assert {(1, 0), (0, 1), (1, 1)} <= modes


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_exercises_broad_dimension_branch(band):
    shapes = {
        tuple(map(len, (grid, grid[0])))
        for sample_index in range(1, 21)
        for grid in [gen.generate(sample_index, sample_index, difficulty=band)]
    }
    assert any(height > 8 or width > 11 for height, width in shapes)


def test_semantic_witnesses_are_real_output_disagreements():
    witnessed = set()
    for index in range(80):
        grid = gen.generate(72_000 + index, index * 7 + 1)
        authoritative = intended_output(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witnessed.add(name)
                for rival_name in gen.WITNESS_RIVALS.get(name, []):
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != authoritative
    assert set(gen.SEMANTIC_WITNESSES) <= witnessed


def test_generated_three_demo_lesson_refutes_every_declared_competitor():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(88_100 + index, index, difficulty="medium")
        demos.append({"input": grid, "output": intended_output(grid)})
    query_grid = gen.generate(88_900, 19, difficulty="medium")
    query = {"input": query_grid, "output": intended_output(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for competitor in gen.LESSON_COMPETITORS.values():
        assert any(competitor(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)]],
)
def test_malformed_grid_returns_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_rule_application_does_not_mutate_input():
    grid = gen.generate(99, 3)
    original = deepcopy(grid)
    intended_output(grid)
    goal_first_output(grid)
    direct_to_goal_output(grid)
    ignore_portals_output(grid)
    assert grid == original


def test_real_racket_rule_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(24)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
