"""Regression tests for the repaired corner-marker beam sampler."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import os
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    active_and_inactive_blockers,
    beam_output,
    canonical_pairs,
    load_generator,
    observed,
    profile,
)

gen = load_generator()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_remain_accepted_and_match_authority(pair):
    assert gen.self_check(pair["input"]) == []
    assert beam_output(pair["input"]) == pair["output"]


def test_authority_pin_and_executable_semantic_contract_exist():
    assert gen.RULE_HASH == "46ed28101b5f"
    assert "ignore_blockers" in gen.SEMANTIC_RIVALS
    assert "active_and_inactive_blockers" in gen.SEMANTIC_WITNESSES
    assert gen.WITNESS_RIVALS["active_and_inactive_blockers"] == ["ignore_blockers"]
    assert "ignore_blockers" in gen.LESSON_COMPETITORS


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=6, grid_w=7, n_emitters=4, n_blockers=2,
             emitter_palette_size=2, marker_corner="tl", marker_direction=1),
        dict(grid_h=14, grid_w=16, n_emitters=8, n_blockers=6,
             emitter_palette_size=4, marker_corner="br", marker_direction=4),
        dict(grid_h=9, grid_w=12, n_emitters=6, n_blockers=4,
             emitter_palette_size=3, marker_corner="tr", marker_direction=3),
    ],
)
def test_every_exact_override_is_realized_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    active, inactive = active_and_inactive_blockers(grid)
    assert active and inactive
    assert beam_output(grid) != beam_output(grid, blockers_enabled=False)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 5}, {"grid_h": 15}, {"grid_h": True}, {"grid_h": 6.0},
        {"grid_w": 6}, {"grid_w": 17},
        {"n_emitters": 3}, {"n_emitters": 9},
        {"n_blockers": 1}, {"n_blockers": 7},
        {"emitter_palette_size": 1}, {"emitter_palette_size": 5},
        {"marker_corner": "center"}, {"marker_direction": 0}, {"marker_direction": 5},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("seed", [True, False, 1.0, "1"])
def test_invalid_seed_scalars_are_rejected(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_invalid_sample_index_scalars_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "unknown"])
def test_invalid_difficulty_scalars_are_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_draw_teaches_blocker_semantics_and_retains_irrelevant_blocker(band):
    for index in range(96):
        grid = gen.generate(0xB91A3B0B, index, difficulty=band)
        assert gen.self_check(grid) == []
        active, inactive = active_and_inactive_blockers(grid)
        assert active, (band, index)
        assert inactive, (band, index)
        assert beam_output(grid) != beam_output(grid, blockers_enabled=False)
        assert gen.SEMANTIC_WITNESSES["active_and_inactive_blockers"](grid)
        assert gen.SEMANTIC_RIVALS["ignore_blockers"](grid) == beam_output(
            grid, blockers_enabled=False
        )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_five_demo_cyclic_window_refutes_ignore_blockers(band):
    # Check every cyclic start in a larger bounded schedule, not only the small
    # aggregate lesson smoke test. Holding out any one of six still leaves a
    # blocker-sensitive demonstration because every production draw is a witness.
    grids = [gen.generate(7123, i, difficulty=band) for i in range(48)]
    for start in range(48):
        episode = [grids[(start + offset) % 48] for offset in range(6)]
        for query_index in range(6):
            demos = episode[:query_index] + episode[query_index + 1 :]
            assert any(
                beam_output(grid) != beam_output(grid, blockers_enabled=False)
                for grid in demos
            )


def test_profile_schedule_exceeds_strict_after_floor_in_every_band():
    canonical = {profile(pair["input"]) for pair in canonical_pairs()}
    hs = [p[0] for p in canonical]
    ws = [p[1] for p in canonical]
    ps = [p[2] for p in canonical]
    pooled_exact = pooled_envelope = 0
    for band in ("easy", "medium", "hard"):
        draws = [gen.generate(99173, i, difficulty=band) for i in range(20)]
        exact = sum(profile(grid) in canonical for grid in draws)
        envelope = sum(
            min(hs) <= len(grid) <= max(hs)
            and min(ws) <= len(grid[0]) <= max(ws)
            and min(ps) <= len({v for row in grid for v in row}) <= max(ps)
            for grid in draws
        )
        assert exact >= 1, band
        pooled_exact += exact
        pooled_envelope += envelope
    assert pooled_exact >= 3
    assert pooled_envelope >= 15


def test_self_check_rejects_minimal_impostors_and_destructive_mutations():
    assert gen.self_check([[6, 6], [6, 6]])
    grid = gen.generate(41, 3)
    h, w = len(grid), len(grid[0])
    mutations = []
    no_marker = deepcopy(grid)
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if no_marker[r][c] in {1, 2, 3, 4}:
            no_marker[r][c] = 0
    mutations.append(no_marker)
    second_marker = deepcopy(grid)
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if second_marker[r][c] == 0:
            second_marker[r][c] = 1
            break
    mutations.append(second_marker)
    bad_color = deepcopy(grid)
    bad_color[1][1] = 10
    mutations.append(bad_color)
    no_emitter = deepcopy(grid)
    marker_cells = {(r, c) for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)) if no_emitter[r][c] in {1, 2, 3, 4}}
    for r in range(h):
        for c in range(w):
            if (r, c) not in marker_cells and no_emitter[r][c] not in (0, 5):
                no_emitter[r][c] = 0
    mutations.append(no_emitter)
    assert all(gen.self_check(candidate) for candidate in mutations)


def test_generation_is_deterministic_and_oracle_helpers_are_input_pure():
    first = gen.generate(1234, 55, difficulty="hard")
    assert first == gen.generate(1234, 55, difficulty="hard")
    original = deepcopy(first)
    beam_output(first)
    gen.SEMANTIC_RIVALS["ignore_blockers"](first)
    assert first == original


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
