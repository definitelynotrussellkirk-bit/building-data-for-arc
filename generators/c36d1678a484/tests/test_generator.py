"""Regression tests for the single-7-row generator contract."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("c36d1678a484_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def reference(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        nonzero = [value for value in row if value != 0]
        if nonzero == [7]:
            out[r] = [7] * len(row)
    return out


def features(grid):
    rows = [[value for value in row if value != 0] for row in grid]
    return {
        "target": any(values == [7] for values in rows),
        "multi_seven": any(values.count(7) >= 2 and len(values) < len(grid[0]) for values in rows),
        "nonseven_singleton": any(len(values) == 1 and values[0] != 7 for values in rows),
        "mixed_seven": any(values.count(7) == 1 and any(value != 7 for value in values) for values in rows),
    }


@pytest.mark.parametrize("pair", canonical_pairs("c36d1678a484", root=find_root(__file__)))
def test_accepts_canonical_inputs_and_matches_authority(pair):
    assert gen.self_check(pair["input"]) == []
    assert reference(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    wanted = {"grid_h": 5, "grid_w": 3, "target_rows": 2, "palette_kind": "contrast"}
    grid = gen.generate(17, 9, difficulty=band, **wanted)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == wanted


@pytest.mark.parametrize(
    "bad",
    [
        {"typo": 1},
        {"grid_h": 4},
        {"grid_h": 13},
        {"grid_w": 2},
        {"grid_w": 15},
        {"target_rows": 0},
        {"target_rows": 3},
        {"palette_kind": "unknown"},
        {"grid_h": True},
        {"target_rows": 1.0},
    ],
)
def test_invalid_overrides_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **bad)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_draw_contains_all_semantic_witnesses(band):
    for index in range(32):
        grid = gen.generate(700 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        assert features(grid) == {
            "target": True,
            "multi_seven": True,
            "nonseven_singleton": True,
            "mixed_seven": True,
        }
        assert grid == gen.generate(700 + index, index * 11, difficulty=band)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_retains_a_pinned_canonical_profile(band):
    canonical_profiles = {(5, 6, 2), (5, 7, 2), (6, 7, 3)}
    observed = set()
    for index in range(20):
        digest = hashlib.sha256(
            f"profile-floor:v1:c36d1678a484:{band}:{index}".encode()
        ).hexdigest()
        seed = int(digest[:12], 16)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        colors = {value for row in grid for value in row}
        observed.add((len(grid), len(grid[0]), len(colors)))
    assert observed & canonical_profiles


def test_declared_rivals_are_real_counterexamples_on_every_draw():
    expected = {"any_seven", "any_singleton", "one_seven_anywhere"}
    assert expected <= set(gen.SEMANTIC_RIVALS)
    assert expected <= set(gen.LESSON_COMPETITORS)
    for index in range(32):
        grid = gen.generate(3100, index)
        truth = reference(grid)
        for name in expected:
            original = [row[:] for row in grid]
            assert gen.SEMANTIC_RIVALS[name](grid) != truth
            assert grid == original


def test_lesson_hook_accepts_all_single_query_rotations():
    pairs = []
    for index in range(4):
        grid = gen.generate(4200, index)
        pairs.append({"input": grid, "output": reference(grid)})
    for query_index in range(len(pairs)):
        demos = [pair for i, pair in enumerate(pairs) if i != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []
