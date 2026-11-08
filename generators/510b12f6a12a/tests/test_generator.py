"""Regression tests for the blocker-aware beam-crossing generator repair."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    beam_output,
    canonical_pairs,
    extra_emitter_counterexample,
    functional_blocker,
    load_generator,
    observed,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_contract_surface_is_pinned_and_only_real_axes_are_advertised():
    assert GEN.RULE_HASH == "8686bcf8a89a"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_v", "n_h", "n_blockers"}


def test_every_canonical_pair_is_accepted_and_matches_independent_rule():
    for pair in canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert beam_output(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"], "validation/rule mirror must not mutate input"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 8, "n_v": 2, "n_h": 2, "n_blockers": 0},
        {"grid_h": 9, "grid_w": 10, "n_v": 4, "n_h": 4, "n_blockers": 6},
    ],
)
def test_exact_override_boundaries_are_realized_in_every_band(band, overrides):
    grid = GEN.generate(911, 7, difficulty=band, **overrides)
    assert GEN.self_check(grid) == []
    assert observed(grid) == overrides
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.rule_mirror(grid) == beam_output(grid)
    assert GEN.generate(911, 7, difficulty=band, **overrides) == grid


@pytest.mark.parametrize(
    "override",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_w": 11},
        {"n_v": 1},
        {"n_v": 5},
        {"n_h": 1},
        {"n_h": 5},
        {"n_blockers": -1},
        {"n_blockers": 7},
        {"grid_h": True},
        {"n_v": 2.5},
        {"n_blockers": "2"},
    ],
)
def test_invalid_overrides_fail_loudly(override):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **override)


def test_default_schedule_covers_canonical_profiles_and_decisive_semantics():
    profiles = set()
    schedule_names = set()
    saw_functional_blocker = False
    saw_extra_emitter_counterexample = False
    for index in range(len(GEN.SCHEDULE_PROFILES) * 3):
        grid = GEN.generate(73, index, difficulty="medium")
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == beam_output(grid)
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        schedule_names.add(GEN.schedule_profile(73, index, difficulty="medium"))
        saw_functional_blocker |= functional_blocker(grid)
        saw_extra_emitter_counterexample |= extra_emitter_counterexample(grid)
    assert {(8, 8, 3), (9, 9, 4), (8, 10, 4)} <= profiles
    assert schedule_names == set(GEN.SCHEDULE_PROFILES)
    assert saw_functional_blocker
    assert saw_extra_emitter_counterexample


def test_difficulty_bands_change_the_default_curriculum():
    signatures = {
        band: [GEN.generate(607, index, difficulty=band) for index in range(8)]
        for band in ("easy", "medium", "hard")
    }
    assert signatures["easy"] != signatures["medium"]
    assert signatures["medium"] != signatures["hard"]
    assert signatures["easy"] != signatures["hard"]


def test_declared_rivals_are_genuine_and_canonical_shortcut_really_fits_canonical():
    shortcut = GEN.CANONICAL_SHORTCUTS["first_two_emitters_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())

    blocker_grid = next(
        grid
        for index in range(64)
        if functional_blocker(grid := GEN.generate(151, index, n_blockers=4))
    )
    assert GEN.SEMANTIC_WITNESSES["functional_blocker"](blocker_grid)
    assert GEN.SEMANTIC_RIVALS["ignore_blockers"](blocker_grid) != beam_output(blocker_grid)

    emitter_grid = next(
        grid
        for index in range(64)
        if extra_emitter_counterexample(
            grid := GEN.generate(211, index, n_v=4, n_h=4, n_blockers=2)
        )
    )
    assert GEN.SEMANTIC_WITNESSES["extra_emitters"](emitter_grid)
    assert shortcut(emitter_grid) != beam_output(emitter_grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]],
)
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "mutation",
    ["origin", "wrong_edge_color", "interior_emitter", "unknown_color", "too_few_vertical"],
)
def test_self_check_rejects_structural_impostors(mutation):
    grid = GEN.generate(301, 5, n_blockers=2)
    if mutation == "origin":
        grid[0][0] = 2
    elif mutation == "wrong_edge_color":
        grid[0][1] = 1
    elif mutation == "interior_emitter":
        grid[2][2] = 2
    elif mutation == "unknown_color":
        grid[2][2] = 9
    elif mutation == "too_few_vertical":
        for c in range(1, len(grid[0])):
            if grid[0][c] == 2:
                grid[0][c] = 0
        grid[0][1] = 2
    assert GEN.self_check(grid)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(41,13,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
