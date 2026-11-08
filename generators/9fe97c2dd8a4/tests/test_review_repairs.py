from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

TASK_ID = "9fe97c2dd8a4"
HERE = Path(__file__).resolve()


def _load_generator():
    source = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"review_repairs_{TASK_ID}", source
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_non_integer_scalars(bad):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(bad, 0, difficulty="easy")


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1"])
def test_sample_index_rejects_non_integer_scalars(bad):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.generate(991, bad, difficulty="easy")


def test_sample_index_rejects_negative_values():
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        gen.generate(991, -1, difficulty="easy")


@pytest.mark.parametrize("bad", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_difficulty_rejects_values_outside_declared_bands(bad):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(991, 0, difficulty=bad)


@pytest.mark.parametrize("axis,control", [
    ("grid_h", 4),
    ("grid_w", 8),
    ("marker_col", 5),
    ("bar_count", 3),
])
@pytest.mark.parametrize("bad_factory", [
    lambda value: str(value),
    lambda value: float(value),
    lambda value: value + 0.75,
])
def test_integer_overrides_reject_scalar_coercion(axis, control, bad_factory):
    with pytest.raises(TypeError, match=axis):
        gen.generate(991, 0, difficulty="easy", **{axis: bad_factory(control)})


def test_bar_count_rejects_bool_override():
    with pytest.raises(TypeError, match="bar_count"):
        gen.generate(991, 0, difficulty="easy", bar_count=True)


def test_row_start_conditioned_duplicate_rule_is_declared_and_refuted():
    name = "duplicate_adjustment_only_when_bars_start_row_1"
    assert name in gen.LESSON_COMPETITORS
    rival = gen.LESSON_COMPETITORS[name]

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(5):
                demos = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {
                    "input": query_grid,
                    "output": gen.rule_mirror(query_grid),
                }

                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (difficulty, seed, start)
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    seed,
                    start,
                )


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _profile_floor_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_each_band_has_exact_canonical_profile_support_in_pinned_census():
    canonical_profiles = {
        (profile["grid_h"], profile["grid_w"], profile["palette_size"])
        for profile in gen._CANONICAL_PROFILES
    }

    for band in ("easy", "medium", "hard"):
        exact_hits = 0
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            exact_hits += _profile(grid) in canonical_profiles
        assert exact_hits >= 1, (band, exact_hits)
