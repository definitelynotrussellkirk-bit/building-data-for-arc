"""Task-local regression tests for the keyed prototype dictionary sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    FIXED_CANONICAL_PATTERNS,
    canonical_pairs,
    fixed_dictionary_output,
    load_generator,
    observed,
    pinned_profile_seed,
    profile,
    racket_outputs,
    stamp_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {profile(pair["input"]) for pair in canonical_pairs()}


def test_contract_metadata_is_pinned():
    assert gen.RULE_HASH == "46157a601fce"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {
        "grid_h", "grid_w", "n_panels", "marker_count", "motif_size", "color_count"
    }


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_accepted_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert stamp_output(pair["input"]) == pair["output"]
    assert fixed_dictionary_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_real_in_every_band(band):
    options = {
        "grid_h": 10,
        "grid_w": 15,
        "n_panels": 4,
        "marker_count": 5,
        "motif_size": 5,
        "color_count": 9,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9), ("grid_h", 15),
        ("grid_w", 14), ("grid_w", 21),
        ("n_panels", 2), ("n_panels", 5),
        ("marker_count", 3), ("marker_count", 6),
        ("motif_size", 2), ("motif_size", 6),
        ("color_count", 7), ("color_count", 10),
        ("grid_h", True), ("grid_w", 15.0), ("motif_size", "4"),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_profile_floor_has_an_exact_hit_in_each_band():
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(20):
            seed = pinned_profile_seed(band, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profiles.append(profile(grid))
        assert CANONICAL_PROFILES.intersection(profiles), (band, profiles)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_are_lawful_deterministic_and_refute_memorization(band):
    seen = set()
    for index in range(80):
        grid = gen.generate(8100 + index, index * 13 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(8100 + index, index * 13 + 5, difficulty=band)
        assert observed(grid) == gen.observe_overrides(grid)
        intended = stamp_output(grid)
        rival = fixed_dictionary_output(grid)
        assert intended != rival
        assert gen.SEMANTIC_WITNESSES["fixed_dictionary_counterexample"](grid)
        assert gen.SEMANTIC_RIVALS["fixed_canonical_dictionary"](grid) == rival
        seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) >= 76


def test_declared_shortcut_fits_every_canonical_pair_and_is_lesson_scored():
    name = "fixed_canonical_dictionary"
    assert gen.CANONICAL_SHORTCUTS[name] is gen.SEMANTIC_RIVALS[name]
    assert gen.LESSON_COMPETITORS[name] is gen.SEMANTIC_RIVALS[name]
    assert gen.WITNESS_RIVALS == {"fixed_dictionary_counterexample": [name]}
    assert all(gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"]
               for pair in canonical_pairs())


@pytest.mark.parametrize(
    "mutation",
    [
        "erase_divider", "duplicate_key", "unknown_body_color",
        "disconnect_prototype", "duplicate_divider", "ragged",
    ],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(42, 7, grid_h=12, grid_w=16, n_panels=3,
                        marker_count=4, motif_size=4, color_count=8)
    if mutation == "erase_divider":
        grid[4][0] = 0
    elif mutation == "duplicate_key":
        # Turn one decoration in the first panel into a second minimum/key.
        nonzero = [(r, c) for r in range(4) for c in range(len(grid[0]))
                   if grid[r][c] not in (0, 9)]
        key = min(grid[r][c] for r, c in nonzero if c < next(
            c for c in range(len(grid[0])) if all(grid[rr][c] == 9 for rr in range(4))))
        target = next((r, c) for r, c in nonzero if grid[r][c] != key)
        grid[target[0]][target[1]] = key
    elif mutation == "unknown_body_color":
        body_cell = next((r, c) for r in range(5, len(grid)) for c in range(len(grid[0]))
                         if grid[r][c] != 0)
        grid[body_cell[0]][body_cell[1]] = 8
    elif mutation == "disconnect_prototype":
        # Add a nonzero cell separated from the first compact motif.
        sep = next(c for c in range(len(grid[0])) if all(grid[r][c] == 9 for r in range(4)))
        occupied = {(r, c) for r in range(4) for c in range(sep) if grid[r][c] != 0}
        cell = next((r, c) for r in range(4) for c in range(sep)
                    if grid[r][c] == 0 and all((r + dr, c + dc) not in occupied
                    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1))))
        grid[cell[0]][cell[1]] = 8
    elif mutation == "duplicate_divider":
        grid[5] = [9] * len(grid[0])
    elif mutation == "ragged":
        grid[-1].pop()
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 15 for _ in range(10)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert results[0] == results[1]


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3])
                 for index in range(36))
    assert racket_outputs(grids) == [stamp_output(grid) for grid in grids]
