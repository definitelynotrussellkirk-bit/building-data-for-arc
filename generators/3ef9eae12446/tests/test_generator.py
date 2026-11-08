"""Focused regression and curriculum tests for 3ef9eae12446."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    intended_output,
    load_generator,
    motif_features,
    observed_profile,
    orthogonal_neighbors_only,
    ring_centers,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = ("cross_guard", "multi_target", "mixed_guard", "filled_guard")


def test_authority_pin_and_canonical_pairs():
    assert gen.RULE_HASH == "ddc9a34d6cd5"
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


def test_strongest_canonical_shortcut_really_fits_all_canonical_pairs():
    assert all(
        orthogonal_neighbors_only(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )


def test_retained_validator_impostor_is_rejected():
    path = HOME / "counterexamples/review-e1437e23da7cb8de-v0001/retained/checks/audit/3ef9eae12446/input.json"
    impostor = json.loads(path.read_text(encoding="utf-8"))
    assert ring_centers(impostor) == {}
    assert gen.self_check(impostor)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 2, 2], [2, 0, 2], [2, 2, 2]],
        [[10, 2, 2], [2, 0, 2], [2, 2, 2]],
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[2, 2, 2], [2, 2, 2], [2, 2, 2]],
    ],
)
def test_malformed_or_rule_inert_grids_are_rejected_without_exception(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
def test_every_exact_override_combination_is_observable_in_every_band(band, profile):
    requested = {"grid_h": 4, "grid_w": 6, "profile": profile}
    grid = gen.generate(19, 7, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert observed_profile(grid) == profile


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 3},
        {"grid_h": 11},
        {"grid_w": 5},
        {"grid_w": 13},
        {"profile": "unknown"},
        {"grid_h": True},
        {"grid_h": 4.0},
        {"grid_w": "6"},
        {"profile": 3},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_override_domain_boundaries_are_jointly_constructive():
    for height in (4, 10):
        for width in (6, 12):
            for profile in PROFILES:
                requested = {"grid_h": height, "grid_w": width, "profile": profile}
                grid = gen.generate(901, height * 100 + width, difficulty="hard", **requested)
                assert len(grid) == height and len(grid[0]) == width
                assert gen.observe_overrides(grid) == requested
                assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "band,expected_shape",
    [("easy", (4, 6)), ("medium", (5, 7)), ("hard", (6, 7))],
)
def test_each_band_has_canonical_size_and_palette_support(band, expected_shape):
    seen = []
    for index in range(20):
        grid = gen.generate(3000 + index, index, difficulty=band)
        seen.append((len(grid), len(grid[0]), len({value for row in grid for value in row})))
    assert (*expected_shape, 3) in seen


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_is_lawful_deterministic_and_nonidentity(band):
    inputs = set()
    profiles = set()
    colors = set()
    for index in range(80):
        seed = 4100 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert intended_output(grid) != grid
        observed = gen.observe_overrides(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        assert observed["profile"] == observed_profile(grid)
        profiles.add(observed["profile"])
        colors.add(tuple(sorted({value for row in grid for value in row if value != 0})))
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert profiles == set(PROFILES)
    assert len(inputs) >= 35
    assert len(colors) >= 10


@pytest.mark.parametrize("profile", PROFILES)
def test_profiles_have_exact_semantic_structure(profile):
    for seed in range(12):
        grid = gen.generate(seed, seed * 5, grid_h=4, grid_w=6, profile=profile)
        features = motif_features(grid)
        if profile == "multi_target":
            assert len(features["targets"]) == 2
            assert not features["crosses"] and not features["mixed"] and not features["occupied"]
        else:
            assert len(features["targets"]) == 1
            assert bool(features["crosses"]) == (profile == "cross_guard")
            assert bool(features["mixed"]) == (profile == "mixed_guard")
            assert bool(features["occupied"]) == (profile == "filled_guard")


def test_explicit_witness_refutes_the_canonical_fitting_shortcut():
    grid = witness_input()
    assert gen.self_check(grid) == []
    intended = intended_output(grid)
    rival = orthogonal_neighbors_only(grid)
    assert intended != rival
    assert [(r, c) for r in range(4) for c in range(6) if intended[r][c] != rival[r][c]] == [(1, 4)]


def test_semantic_contract_names_and_executes_the_real_shortcut():
    assert set(gen.CANONICAL_SHORTCUTS) == {"orthogonal_neighbors_only"}
    assert set(gen.LESSON_COMPETITORS) == {"orthogonal_neighbors_only"}
    assert set(gen.SEMANTIC_RIVALS) == {"orthogonal_neighbors_only"}
    assert gen.WITNESS_RIVALS == {"missing_corners_cross": ["orthogonal_neighbors_only"]}
    grid = gen.generate(8, 0, profile="cross_guard")
    assert gen.SEMANTIC_WITNESSES["missing_corners_cross"](grid)
    assert gen.SEMANTIC_RIVALS["orthogonal_neighbors_only"](grid) == orthogonal_neighbors_only(grid)
    assert gen.SEMANTIC_RIVALS["orthogonal_neighbors_only"](grid) != intended_output(grid)


def test_six_phase_schedule_emits_all_profiles_and_every_four_pair_window_survives_query_rotation():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 6
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "cross_guard", "multi_target", "cross_guard",
        "filled_guard", "cross_guard", "mixed_guard",
    )
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(gen.LESSON_SCHEDULE_PERIOD):
                pairs = []
                for index in range(start, start + 4):
                    grid = gen.generate(seed, index, difficulty=band)
                    assert gen.schedule_profile(seed, index, band) == gen.observe_overrides(grid)["profile"]
                    pairs.append({"input": grid, "output": intended_output(grid)})
                for query_index in range(4):
                    demos = [pair for idx, pair in enumerate(pairs) if idx != query_index]
                    query = pairs[query_index]
                    assert any(gen.SEMANTIC_WITNESSES["missing_corners_cross"](pair["input"]) for pair in demos)
                    assert gen.lesson_identifiable(demos, query) == []


def test_keyed_generation_is_python_hash_seed_independent():
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
