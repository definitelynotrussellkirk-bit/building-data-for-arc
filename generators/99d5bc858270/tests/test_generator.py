"""Regression tests for the canonical-domain and curriculum repair."""
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
    geometry_output,
    has_shared_projection_gap,
    light_position,
    load_generator,
    observed,
    racket_outputs,
    shared_projection_gap_lengths,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_every_canonical_input_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("position", range(8))
def test_exact_overrides_work_in_every_band(band, position):
    requested = {"grid_h": 6, "grid_w": 9, "light_position": position}
    grid = gen.generate(117 + position, 31, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert {key: observed(grid)[key] for key in requested} == requested
    assert gen.observe_overrides(grid) == requested
    assert geometry_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5),
        ("grid_h", 16),
        ("grid_w", 6),
        ("grid_w", 17),
        ("light_position", -1),
        ("light_position", 8),
        ("grid_h", True),
        ("grid_w", 9.0),
        ("light_position", "4"),
    ],
)
def test_rejects_invalid_or_unknown_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_curriculum_covers_canonical_scale_corners_and_all_directions(band):
    positions = set()
    exact_profiles = 0
    distinct = set()
    for index in range(192):
        grid = gen.generate(4000 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(4000 + index, index * 11, difficulty=band)
        assert has_shared_projection_gap(grid)
        assert gen.SEMANTIC_WITNESSES["shared_projection_gap"](grid)
        assert gen.SEMANTIC_RIVALS["farthest_caster_per_projection"](grid) != geometry_output(grid)
        positions.add(light_position(grid))
        palette = len({value for row in grid for value in row})
        exact_profiles += (len(grid), len(grid[0]), palette) in {(6, 9, 3), (6, 9, 4)}
        distinct.add(tuple(tuple(row) for row in grid))
    assert positions == set(range(8))
    assert exact_profiles >= 8
    assert len(distinct) >= 180



def test_witness_geometry_is_not_a_single_fixed_gap_template():
    minimum_gap_lengths = set()
    for index in range(768):
        grid = gen.generate(9300 + index, index * 17, difficulty="easy",
                            grid_h=6, grid_w=7, light_position=index % 8)
        lengths = shared_projection_gap_lengths(grid)
        assert lengths
        minimum_gap_lengths.add(min(lengths))
    assert {2, 3}.issubset(minimum_gap_lengths)

def test_named_rival_fits_no_generated_demonstration_window():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(8):
            grid = gen.generate(7100 + index, index, difficulty=band)
            pairs.append({"input": grid, "output": geometry_output(grid)})
        for start in range(6):
            demos = pairs[start : start + 2]
            query = pairs[start + 2]
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(6)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_extra_light_border_caster_and_empty_scene():
    grid = gen.generate(91, 7, grid_h=6, grid_w=9, light_position=4)

    extra_light = deepcopy(grid)
    extra_light[-1][-1] = 4
    assert gen.self_check(extra_light)

    border_caster = deepcopy(grid)
    border_caster[-1][4] = 3
    assert gen.self_check(border_caster)

    empty = [[0] * 9 for _ in range(6)]
    empty[0][0] = 4
    assert gen.self_check(empty)


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(800 + index, index, light_position=index % 8)
        for index in range(24)
    ]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]
