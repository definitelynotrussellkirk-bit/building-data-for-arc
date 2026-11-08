"""Task-local regressions for the directional-ray count-map sampler."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    has_downward_wall_witness,
    load_generator,
    observed,
    racket_outputs,
    ray_output,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_every_canonical_pair_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert ray_output(pair["input"]) == pair["output"]


def test_declares_exact_canonical_rule_hash():
    assert getattr(gen, "RULE_HASH", None) == "c3e717030acc"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 8, "n_emitters": 7, "n_walls": 4},
        {"grid_h": 10, "grid_w": 10, "n_emitters": 10, "n_walls": 6},
        {"grid_h": 8, "grid_w": 9, "n_emitters": 9, "n_walls": 5},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 11),
        ("grid_w", 7),
        ("grid_w", 11),
        ("n_emitters", 6),
        ("n_emitters", 11),
        ("n_walls", 3),
        ("n_walls", 7),
        ("grid_h", True),
        ("grid_w", 8.0),
        ("n_emitters", "7"),
        ("n_walls", None),  # None is the documented no-override convention; see separate test.
    ],
)
def test_rejects_invalid_overrides(key, value):
    if value is None:
        pytest.skip("None intentionally means no override")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("sample_index", [-1, True, 1.5, "2"])
def test_rejects_invalid_sample_index(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


def test_none_override_preserves_default_draw_contract():
    assert gen.generate(31, 4, grid_h=None) == gen.generate(31, 4)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_guarantees_the_missing_semantic_branch(band):
    shapes, inputs = set(), set()
    for index in range(128):
        grid = gen.generate(2100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(2100 + index, index * 11, difficulty=band)
        assert has_downward_wall_witness(grid)
        assert ray_output(grid) != ray_output(grid, down_ignores_walls=True)
        assert max(max(row) for row in ray_output(grid)) >= 2
        assert {1, 2, 3, 4} <= {value for row in grid for value in row}
        assert 7 <= observed(grid)["n_emitters"] <= 10
        assert 4 <= observed(grid)["n_walls"] <= 6
        shapes.add((len(grid), len(grid[0])))
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert {(7, 9), (8, 8), (8, 9)} & shapes
    assert len(shapes) >= 6
    assert len(inputs) >= 120


def test_strongest_canonical_shortcut_fits_all_canonical_pairs_but_witness_refutes_it():
    assert all(
        ray_output(pair["input"], down_ignores_walls=True) == pair["output"]
        for pair in canonical_pairs()
    )
    grid = witness_input()
    assert gen.self_check(grid) == []
    intended = ray_output(grid)
    rival = ray_output(grid, down_ignores_walls=True)
    assert intended != rival
    assert has_downward_wall_witness(grid)
    assert getattr(gen, "CANONICAL_SHORTCUTS", {}).get("downward_ignores_walls") is not None
    assert gen.CANONICAL_SHORTCUTS["downward_ignores_walls"](grid) == rival


@pytest.mark.parametrize(
    "mutation",
    [
        "bad_shape",
        "unknown_color",
        "missing_direction",
        "too_few_emitters",
        "too_few_walls",
        "no_interaction",
    ],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = witness_input()
    if mutation == "bad_shape":
        grid = [row[:-1] for row in grid]
    elif mutation == "unknown_color":
        grid[0][7] = 9
    elif mutation == "missing_direction":
        grid = [[1 if value == 4 else value for value in row] for row in grid]
    elif mutation == "too_few_emitters":
        removed = 0
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value in (1, 2, 3, 4) and removed < 3:
                    grid[r][c] = 0
                    removed += 1
    elif mutation == "too_few_walls":
        removed = 0
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 5 and removed < 2:
                    grid[r][c] = 0
                    removed += 1
    elif mutation == "no_interaction":
        grid = [[0] * 8 for _ in range(7)]
        # Every ray points immediately out of bounds, so no two rays cross and
        # no emitter reaches a wall or another emitter.
        for r, c, value in (
            (0, 0, 1), (0, 2, 1),
            (6, 1, 3), (6, 3, 3),
            (1, 0, 4), (4, 0, 4),
            (2, 7, 2), (5, 7, 2),
            (1, 2, 5), (2, 2, 5), (4, 5, 5), (5, 5, 5),
        ):
            grid[r][c] = value
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(7)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import sys,json;sys.path.insert(0,sys.argv[1]);"
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


def test_semantic_declarations_are_executable_and_refute_the_rival():
    assert gen.WITNESS_RIVALS["downward_wall_stop"] == ["downward_ignores_walls"]
    for index in range(32):
        grid = gen.generate(712, index)
        original = deepcopy(grid)
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES["downward_wall_stop"](grid)
        rival = gen.SEMANTIC_RIVALS["downward_ignores_walls"](grid)
        assert rival == ray_output(grid, down_ignores_walls=True)
        assert rival != ray_output(grid)
        assert grid == original


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(319, index) for index in range(16)]
    assert racket_outputs(grids) == [ray_output(grid) for grid in grids]
