"""Task-local regression tests for ad9405621c3d."""
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
    independent_output,
    load_generator,
    outer_two_ring_output,
    path_features,
    racket_outputs,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_inputs_are_owned_and_python_mirror_matches(pair):
    before = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert independent_output(pair["input"]) == pair["output"]
    assert GEN.expected_output(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_outer_two_ring_shortcut_fits_every_canonical_pair():
    assert all(
        outer_two_ring_output(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(6, 7), (6, 9), (9, 7), (9, 9)])
@pytest.mark.parametrize("color", [2, 9])
def test_exact_overrides_are_observable_in_every_band(band, height, width, color):
    grid = GEN.generate(
        17,
        9,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        endpoint_color=color,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "endpoint_color": color,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"grid_h": 5},
        {"grid_h": 10},
        {"grid_w": 6},
        {"grid_w": 10},
        {"endpoint_color": 0},
        {"endpoint_color": 5},
        {"endpoint_color": True},
        {"grid_h": 6.0},
        {"grid_w": "7"},
        {"difficulty": "expert"},
    ],
)
def test_invalid_calls_reject_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("start", range(8))
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_demo_window_refutes_the_canonical_shortcut(start, band):
    grids = [GEN.generate(701, start + offset, difficulty=band) for offset in range(4)]
    profiles = {GEN.schedule_profile(701, start + offset, difficulty=band) for offset in range(4)}
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert any(
        outer_two_ring_output(grid) != independent_output(grid)
        for grid in grids
    )
    demos = [{"input": grid, "output": independent_output(grid)} for grid in grids]
    query_grid = GEN.generate(701, start + 4, difficulty=band)
    query = {"input": query_grid, "output": independent_output(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []


def test_declared_witness_is_a_real_rival_disagreement():
    hits = 0
    for index in range(80):
        grid = GEN.generate(900 + index, index, difficulty="medium")
        intended = independent_output(grid)
        assert GEN.expected_output(grid) == intended
        fires = GEN.SEMANTIC_WITNESSES["interior_route"](grid)
        if fires:
            hits += 1
            rival = GEN.SEMANTIC_RIVALS["outer_two_ring_only"](grid)
            assert rival == outer_two_ring_output(grid)
            assert rival != intended
            assert path_features(grid)["max_boundary_depth"] >= 2
    assert hits >= 40


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_is_deterministic_valid_diverse_and_nontrivial(band):
    inputs = set()
    profiles = set()
    colors = set()
    deep = 0
    exact_profiles = {(6, 7, 3), (7, 7, 3), (8, 8, 3), (9, 9, 3)}
    observed_profiles = set()
    for index in range(160):
        seed = 10_000 + index
        grid = GEN.generate(seed, index * 13 + 5, difficulty=band)
        assert grid == GEN.generate(seed, index * 13 + 5, difficulty=band)
        assert GEN.self_check(grid) == []
        intended = independent_output(grid)
        assert intended != grid
        assert GEN.expected_output(grid) == intended
        inputs.add(tuple(map(tuple, grid)))
        profiles.add(GEN.schedule_profile(seed, index * 13 + 5, difficulty=band))
        stats = GEN.observe_overrides(grid)
        colors.add(stats["endpoint_color"])
        observed_profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        deep += path_features(grid)["max_boundary_depth"] >= 2
    assert len(inputs) >= 150
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert colors == {2, 3, 4, 6, 7, 8, 9}
    assert deep >= 75
    assert observed_profiles <= exact_profiles
    assert observed_profiles == exact_profiles


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[0] * 7 for _ in range(6)],
        [[5] * 7 for _ in range(6)],
        [[2] + [0] * 6 for _ in range(6)],
        [[True] * 7 for _ in range(6)],
    ],
)
def test_malformed_and_structural_impostors_are_rejected(grid):
    assert GEN.self_check(grid)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for value in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=value, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [GEN.generate(319, index, difficulty="hard") for index in range(24)]
    assert racket_outputs(grids) == [independent_output(grid) for grid in grids]
