"""Focused regressions for the repaired path-extension generator."""
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
    analyze_scene,
    canonical_pairs,
    load_generator,
    observed,
    racket_outputs,
    reference_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{len(pair['input'])}x{len(pair['input'][0])}")
def test_canonical_inputs_are_lawful_and_reference_matches_labels(pair):
    assert GEN.self_check(pair["input"]) == []
    if pair.get("output") is not None:
        assert reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((1, True), {}),
        ((1, -1), {}),
        ((1, 0.0), {}),
        ((1, "0"), {}),
        ((1, 0), {"difficulty": True}),
        ((1, 0), {"difficulty": "invalid"}),
        ((1, 0), {"typo_axis": 1}),
        ((1, 0), {"grid_h": True}),
        ((1, 0), {"grid_w": 14.0}),
        ((1, 0), {"grid_h": 13}),
        ((1, 0), {"grid_w": 31}),
        ((1, 0), {"palette_kind": 3}),
        ((1, 0), {"palette_kind": "not-a-palette"}),
        ((1, 0), {"texture": "no_path"}),
    ],
)
def test_rejects_invalid_call_contract(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


def test_negative_fixtures_are_not_lawful_or_advertised():
    assert "texture" not in GEN.AXES
    assert GEN.self_check([[0] * 14 for _ in range(14)])
    singleton = [[0] * 14 for _ in range(14)]
    singleton[5][8] = 4
    assert GEN.self_check(singleton)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("palette_kind", ["warm", "cool", "broad", "primary"])
def test_exact_overrides_are_observable_in_every_band(band, palette_kind):
    requested = {"grid_h": 14, "grid_w": 30, "palette_kind": palette_kind}
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    seen = GEN.observe_overrides(grid)
    assert {key: seen[key] for key in requested} == requested
    assert seen["n_paths"] == seen["n_markers"] == 2
    assert seen["marker_distances"][0] in (2, 3)
    assert seen["marker_distances"][1] in (4, 5, 6, 7)


def test_observer_and_independent_probe_agree_on_geometry():
    for index in range(64):
        grid = GEN.generate(2100 + index, index * 11, difficulty=("easy", "medium", "hard")[index % 3])
        public = GEN.observe_overrides(grid)
        independent = observed(grid)
        for key in ("grid_h", "grid_w", "path_sizes", "marker_distances", "extension_counts", "turn_counts"):
            assert public[key] == independent[key]


def test_distribution_covers_canonical_path_sizes_and_marker_distances():
    path_sizes = set()
    distances = set()
    dimensions = set()
    turn_counts = set()
    for index in range(320):
        band = ("easy", "medium", "hard")[index % 3]
        grid = GEN.generate(4000 + index, index, difficulty=band)
        assert grid == GEN.generate(4000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        stats = observed(grid)
        path_sizes.update(stats["path_sizes"])
        distances.update(stats["marker_distances"])
        turn_counts.update(stats["turn_counts"])
        dimensions.add((stats["grid_h"], stats["grid_w"]))
        assert stats["marker_distances"][0] in (2, 3)
        assert stats["marker_distances"][1] in (4, 5, 6, 7)
    assert {7, 8, 12, 13, 16} <= path_sizes
    assert set(range(2, 8)) <= distances
    assert {(20, 20), (30, 30)} <= dimensions
    assert {1, 2, 3} <= turn_counts


def test_declared_shortcut_fits_canonical_but_generated_witness_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["far_markers_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs() if pair.get("output") is not None)
    for index in range(24):
        grid = GEN.generate(5010 + index, index)
        intended = reference_output(grid)
        assert GEN.SEMANTIC_WITNESSES["near_marker"](grid)
        assert rival(grid) != intended


def test_lesson_contract_rejects_an_uninformative_demo_set():
    pair = next(pair for pair in canonical_pairs() if pair.get("output") is not None)
    grid = GEN.generate(6001, 1)
    query = {"input": grid, "output": reference_output(grid)}
    reasons = GEN.lesson_identifiable([deepcopy(pair)], query)
    assert reasons and "far_markers_only" in " ".join(reasons)
    informative = {"input": grid, "output": reference_output(grid)}
    assert GEN.lesson_identifiable([informative], query) == []


def test_validator_accepts_multiturn_paths_but_rejects_a_branch():
    multiturn = max(
        (pair["input"] for pair in canonical_pairs()),
        key=lambda grid: max(path["turn_count"] for path in analyze_scene(grid)["paths"]),
    )
    assert max(path["turn_count"] for path in analyze_scene(multiturn)["paths"]) >= 3
    assert GEN.self_check(multiturn) == []

    grid = GEN.generate(7, 2)
    scene = analyze_scene(grid)
    path = scene["paths"][0]
    # Add a side cell to an interior path cell, creating a degree-3 branch.
    for r, c in path["order"][1:-1]:
        candidates = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        target = next(
            (point for point in candidates if 0 <= point[0] < len(grid) and 0 <= point[1] < len(grid[0]) and grid[point[0]][point[1]] == 0),
            None,
        )
        if target is not None:
            grid[target[0]][target[1]] = path["color"]
            break
    else:
        pytest.skip("no free branch cell in this deterministic draw")
    assert GEN.self_check(grid)


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


def test_real_racket_matches_independent_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(GEN.generate(7100 + index, index) for index in range(20))
    outputs = racket_outputs(grids)[0]
    assert outputs == [reference_output(grid) for grid in grids]
