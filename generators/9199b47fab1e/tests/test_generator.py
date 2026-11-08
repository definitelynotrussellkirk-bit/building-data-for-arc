"""Task-local regression suite for the chamber-distance generator."""
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
    SHAPE_OPTIONS,
    canonical_pairs,
    canonical_rule_source,
    component_signature,
    load_generator,
    nearest_seed_manhattan_ignoring_walls,
    observed,
    racket_outputs,
    rule_output,
    selected_target_code,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {"shape", "n_seeds", "wall_color"}
CANONICAL_SHAPES = {"9x9", "9x13", "10x12", "11x11", "11x13"}


def test_metadata_pins_authority_and_exposes_only_observable_controls():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "b0749d721740"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_accepts_every_canonical_pair_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"shape": "9x9", "n_seeds": 1, "wall_color": 6},
        {"shape": "11x13", "n_seeds": 3, "wall_color": 8},
        {"shape": "18x20", "n_seeds": 2, "wall_color": 9},
    ],
)
def test_exact_overrides_are_observable_and_honored_in_every_band(difficulty, requested):
    grid = gen.generate(17, 9, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert rule_output(grid) != nearest_seed_manhattan_ignoring_walls(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("shape", "8x8"), ("shape", 9),
        ("n_seeds", 0), ("n_seeds", 4), ("n_seeds", True),
        ("n_seeds", 2.5), ("n_seeds", "2"),
        ("wall_color", 5), ("wall_color", 10), ("wall_color", True),
        ("wall_color", "8"),
    ],
)
def test_rejects_unknown_or_invalid_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_distribution_is_valid_diverse_deterministic_and_always_refutes_shortcut(difficulty):
    shapes: set[str] = set()
    seeds: set[int] = set()
    wall_colors: set[int] = set()
    signatures: set[tuple] = set()
    inputs: set[str] = set()
    for index in range(192):
        grid = gen.generate(2100 + index, index * 11, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(2100 + index, index * 11, difficulty=difficulty)
        stats = observed(grid)
        assert gen.observe_overrides(grid) == stats
        shapes.add(str(stats["shape"]))
        seeds.add(int(stats["n_seeds"]))
        wall_colors.add(int(stats["wall_color"]))
        signatures.add(component_signature(grid))
        inputs.add(repr(grid))
        assert rule_output(grid) != nearest_seed_manhattan_ignoring_walls(grid)
    assert shapes <= set(SHAPE_OPTIONS)
    assert shapes & CANONICAL_SHAPES
    assert len(shapes) >= 6
    assert seeds == {1, 2, 3}
    assert wall_colors == {6, 7, 8, 9}
    assert len(signatures) >= 12
    assert len(inputs) >= 180


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_consecutive_three_demo_window_refutes_each_declared_competitor(difficulty):
    assert set(gen.LESSON_COMPETITORS) == {
        "nearest_seed_manhattan_ignoring_walls",
        "color_8_only_barrier",
    }
    for start in range(32):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(700 + start, start + offset, difficulty=difficulty)
            demos.append({"input": grid, "output": rule_output(grid)})
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                difficulty, start, name
            )
        query_grid = gen.generate(
            700 + start,
            start + gen.EXAMPLES_NEEDED,
            difficulty=difficulty,
        )
        assert gen.lesson_identifiable(
            demos,
            {"input": query_grid, "output": rule_output(query_grid)},
        ) == []


def test_wall_blocking_witness_is_a_real_counterexample_on_every_profile():
    assert set(gen.SEMANTIC_WITNESSES) == {
        "wall_blocks_propagation",
        "non_8_wall_color",
    }
    assert set(gen.SEMANTIC_RIVALS) == {
        "nearest_seed_manhattan_ignoring_walls",
        "color_8_only_barrier",
    }
    assert gen.WITNESS_RIVALS == {
        "wall_blocks_propagation": ["nearest_seed_manhattan_ignoring_walls"],
        "non_8_wall_color": ["color_8_only_barrier"],
    }
    for index, shape in enumerate(SHAPE_OPTIONS):
        grid = gen.generate(910, index, shape=shape, n_seeds=(index % 3) + 1)
        assert gen.SEMANTIC_WITNESSES["wall_blocks_propagation"](grid)
        assert gen.SEMANTIC_RIVALS["nearest_seed_manhattan_ignoring_walls"](grid) != rule_output(grid)


def test_declared_color_8_shortcut_fits_every_canonical_pair_but_generated_non_8_walls_refute_it():
    assert set(gen.CANONICAL_SHORTCUTS) == {"color_8_only_barrier"}
    rival = gen.CANONICAL_SHORTCUTS["color_8_only_barrier"]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    counterexample = gen.generate(123, 1, shape="9x9", n_seeds=1, wall_color=6)
    assert gen.SEMANTIC_WITNESSES["non_8_wall_color"](counterexample)
    assert rival(counterexample) != rule_output(counterexample)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_each_four_pair_window_survives_every_query_rotation(difficulty):
    for start in range(32):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(1700 + start, start + offset, difficulty=difficulty)
            pairs.append({"input": grid, "output": rule_output(grid)})
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    difficulty, start, query_index, name
                )
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "mutation",
    ["remove_walls", "remove_seeds", "unknown_color", "extra_wall_color", "solid_wall"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(44, 3, shape="11x13", n_seeds=2, wall_color=8)
    if mutation == "remove_walls":
        grid = [[0 if value == 8 else value for value in row] for row in grid]
    elif mutation == "remove_seeds":
        grid = [[0 if value == 2 else value for value in row] for row in grid]
    elif mutation == "unknown_color":
        grid[0][0] = 1
    elif mutation == "extra_wall_color":
        wall = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8)
        grid[wall[0]][wall[1]] = 7
    elif mutation == "solid_wall":
        grid = [[8 for _ in row] for row in grid]
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_selected_authority_text_is_exactly_synchronized_with_canonical_source():
    assert selected_target_code() == canonical_rule_source()


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3])
        for index in range(24)
    ]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
