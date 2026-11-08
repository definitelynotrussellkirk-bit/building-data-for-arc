"""Task-local regressions; run explicitly (the repository suite omits these)."""
from __future__ import annotations

import importlib.util
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("review_f2dbde875127", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def frames(grid):
    """Independent frame reader, not the generator's validator."""
    left = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1}
    result = []
    while left:
        todo = [min(left)]
        cells = set()
        while todo:
            p = todo.pop()
            if p not in left:
                continue
            left.remove(p)
            cells.add(p)
            r, c = p
            todo.extend([(r-1, c), (r+1, c), (r, c-1), (r, c+1)])
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        r1, c1 = max(r for r, c in cells), max(c for r, c in cells)
        keys = [(r0-1, c, grid[r0-1][c]) for c in range(c0, c1+1) if grid[r0-1][c] in (2, 3, 4, 5)]
        points = {(r-r0-1, c-c0-1) for r in range(r0+1, r1) for c in range(c0+1, c1) if grid[r][c]}
        result.append(((r0, c0, r1, c1), keys, points))
    return sorted(result)


def norm(points):
    r0, c0 = min(r for r, c in points), min(c for r, c in points)
    return frozenset((r-r0, c-c0) for r, c in points)


def orbit(points):
    current = norm(points)
    states = []
    for _ in range(4):
        states.append(current)
        current = norm({(c, -r) for r, c in current})
    return states


def canonical():
    return next(x for x in map(json.loads, (REPO / "shared/data/canonical/puzzles.jsonl").open()) if x["task_id"] == gen.TASK_ID)


def test_all_canonical_inputs_are_semantically_valid():
    for split in ("train", "test"):
        for i, pair in enumerate(canonical()[split]):
            assert gen.self_check(pair["input"]) == [], (split, i)


def test_all_four_keys_and_rectangles_have_default_support():
    keys = Counter()
    rectangles = 0
    for seed in range(64):
        grid = gen.generate(seed, 0, difficulty="medium")
        for (r0, c0, r1, c1), kk, points in frames(grid):
            keys.update(k[2] for k in kk)
            rectangles += (r1-r0 != c1-c0)
    assert set(keys) == {2, 3, 4, 5}, keys
    assert rectangles > 0


def test_normal_objects_distinguish_all_four_rotations():
    for seed in range(64):
        for box, keys, points in frames(gen.generate(seed, 0, difficulty="medium")):
            assert len(set(orbit(points))) == 4, (seed, box, keys)


@pytest.mark.parametrize("key", [2, 3, 4, 5])
def test_explicit_key_is_realized_and_key2_moves(key):
    for seed in range(8):
        grid = gen.generate(seed, 0, key=key)
        assert not gen.self_check(grid)
        for (r0, c0, r1, c1), kk, points in frames(grid):
            assert [k[2] for k in kk] == [key]
            if key == 2:
                shape = norm(points)
                oh = max(r for r, c in shape)+1
                ow = max(c for r, c in shape)+1
                target = {((r1-r0-1-oh)//2+r, (c1-c0-1-ow)//2+c) for r, c in shape}
                assert points != target


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_determinism_validity_and_validator_purity(difficulty):
    for seed in range(20):
        grid = gen.generate(seed, 7, difficulty=difficulty)
        assert grid == gen.generate(seed, 7, difficulty=difficulty)
        before = deepcopy(grid)
        assert not gen.self_check(grid, difficulty=difficulty)
        assert grid == before


def test_realized_geometry_overrides():
    for seed in range(8):
        grid = gen.generate(seed, 0, grid_h=24, grid_w=26, n_frames=3, interior_h=4, interior_w=5)
        assert (len(grid), len(grid[0])) == (24, 26)
        ff = frames(grid)
        assert len(ff) == 3
        assert all((b[2]-b[0]-1, b[3]-b[1]-1) == (4, 5) for b, _, _ in ff)


@pytest.mark.parametrize("overrides", [{"unknown_axis": 1}, {"key": 6}, {"key": True}, {"n_frames": 0}, {"grid_h": 8}, {"interior_w": "4"}, {"texture": "warm"}])
def test_bad_or_formerly_ignored_overrides_raise(overrides):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(0, 0, **overrides)


def test_impossible_geometry_raises_instead_of_underfilling():
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, grid_h=9, grid_w=10, n_frames=3, interior_h=7, interior_w=7)
    assert set(exc.value.incompatible_axes) >= {"grid_h", "grid_w", "n_frames"}


@pytest.mark.parametrize("name", ["no_key", "no_frame", "no_object"])
def test_negative_fixtures_remain_rejected(name):
    assert gen.self_check(gen.generate(0, 0, texture=name))


def test_disconnected_object_is_rejected():
    grid = gen.generate(0, 0, n_frames=1, interior_h=5, interior_w=5)
    (r0, c0, r1, c1), _, _ = frames(grid)[0]
    for r in range(r0+1, r1):
        for c in range(c0+1, c1):
            grid[r][c] = 0
    grid[r0+1][c0+1] = 7
    grid[r1-1][c1-1] = 7
    assert any("connected" in error for error in gen.self_check(grid))


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 0]], [[-1]], [[10]], [[True]], [[1.5]], None])
def test_malformed_inputs_return_findings_without_crashing(grid):
    assert gen.self_check(grid)


def test_key_contrast_probe_masks_the_changed_marker():
    path = HOME / "workspace/key_contrast_probe.py"
    assert path.is_file(), "the reusable key-contrast probe is missing"
    ss = importlib.util.spec_from_file_location("key_probe", path)
    probe = importlib.util.module_from_spec(ss)
    ss.loader.exec_module(probe)
    grid = gen.generate(4, 0, n_frames=1, key=3)
    variants = probe.key_family(grid)
    assert [v["key"] for v in variants] == [2, 3, 4, 5]
    # A do-nothing oracle changes the output key marker, but must NOT be credited
    # with four distinct semantic outcomes. Only the selected interior counts.
    assert len({probe.interior_signature(v["input"], v["box"]) for v in variants}) == 1
    assert len({probe.interior_signature(probe.python_transform(v["input"]), v["box"]) for v in variants}) == 4
    for variant in variants:
        assert len([1 for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != variant["input"][r][c]]) <= 1


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_band_keeps_novel_canonical_scale_support(difficulty):
    profile_set = {(len(p["input"]), len(p["input"][0]), len({v for row in p["input"] for v in row}))
                   for split in ("train", "test") for p in canonical()[split]}
    grids = [gen.generate(seed, 0, difficulty=difficulty) for seed in range(64)]
    hits = [g for g in grids if (len(g), len(g[0]), len({v for row in g for v in row})) in profile_set]
    assert len(hits) >= 3
    originals = [p["input"] for split in ("train", "test") for p in canonical()[split]]
    assert all(grid not in originals for grid in hits)
    assert len({(len(g), len(g[0])) for g in grids}) >= 8


def test_stray_nonzero_outside_frames_is_rejected():
    grid = gen.generate(0, 0, n_frames=1, grid_h=24, grid_w=26)
    grid[-1][-1] = 9
    assert any("outside" in message for message in gen.self_check(grid))


def test_default_geometry_and_key_provenance_matches_realized_axes():
    from puzzle_generators.base import set_ctx_observer
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            contexts = []
            set_ctx_observer(contexts.append)
            try:
                grid = gen.generate(seed, 0, difficulty=band)
            finally:
                set_ctx_observer(None)
            recorded = contexts[-1].recorded_draws()
            observed = gen.observe_overrides(grid)
            for axis in gen.AXES:
                assert axis in recorded, (band, seed, axis)
                assert axis in observed, (band, seed, axis)
                assert recorded[axis] == observed[axis], (band, seed, axis, recorded, observed)
