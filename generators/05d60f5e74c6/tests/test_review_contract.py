"""Task-local regressions; run explicitly from the source repository."""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("review_generator_05d60f5e74c6", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid, diagonal=False):
    """Independent flood fill used to assert the observed scene, not draw intent."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        points, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc) or (not diagonal and abs(dr) + abs(dc) != 1):
                        continue
                    p = r + dr, c + dc
                    if p in remaining and grid[p[0]][p[1]] == color:
                        remaining.remove(p)
                        points.add(p)
                        todo.append(p)
        r0, r1 = min(r for r, c in points), max(r for r, c in points)
        c0, c1 = min(c for r, c in points), max(c for r, c in points)
        result.append({"color": color, "cells": points, "bbox": (r0, c0, r1, c1),
                       "h": r1-r0+1, "w": c1-c0+1,
                       "solid": len(points) == (r1-r0+1)*(c1-c0+1)})
    return result


def oracle(grid):
    out = [[0]*len(grid[0]) for _ in grid]
    for obj in components(grid):
        if obj["solid"]:
            r0, c0, r1, c1 = obj["bbox"]
            for r, c in {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}:
                out[r][c] = obj["color"]
    return out


def canonical_pairs():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == "05d60f5e74c6":
            return row["train"] + row["test"]
    raise AssertionError("missing canonical task")


@pytest.mark.parametrize("texture", ["blob", "thin", "l_merge"])
def test_forced_texture_never_silently_disappears(texture):
    for seed in range(100):
        grid = gen.generate(seed, 0, difficulty="easy", texture=texture)
        objs = components(grid)
        if texture == "thin":
            assert any(o["solid"] and min(o["h"], o["w"]) == 1 and len(o["cells"]) >= 3 for o in objs), seed
            assert any(len(o["cells"]) == 1 for o in objs), seed
        else:
            assert any(not o["solid"] for o in objs), seed


@pytest.mark.parametrize("axis,value", [("grid_h", 20), ("grid_w", 22), ("rectangles", 6)])
def test_declared_maximum_override_is_accepted_and_realized(axis, value):
    grid = gen.generate(0, 0, **{axis: value})
    if axis == "grid_h":
        assert len(grid) == value
    elif axis == "grid_w":
        assert len(grid[0]) == value
    else:
        assert sum(o["solid"] and min(o["h"], o["w"]) >= 2 for o in components(grid)) == value


def test_unknown_axis_and_bad_values_are_rejected():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, textrue="blob")
    for args in ({"texture": "typo"}, {"grid_h": True}, {"grid_w": 9.5}, {"rectangles": "3"}):
        with pytest.raises((ValueError, TypeError)):
            gen.generate(0, 0, **args)


def test_validator_does_not_accept_identity_only_or_invalid_palette_scenes():
    tiny = [[0]*9 for _ in range(8)]
    for r in range(2):
        for c in range(2):
            tiny[r][c] = 2
    assert gen.self_check(tiny), "a lone 2x2 is an identity, not a teaching witness"
    grid = gen.generate(0, 0)
    for value in (-1, 10, True, "2", 2.5):
        damaged = [row[:] for row in grid]
        damaged[-1][-1] = value
        assert gen.self_check(damaged), value
    for malformed in ([], [[]], [[0], [0, 1]], None, "123"):
        assert gen.self_check(malformed), malformed


def test_canonical_rule_pin_and_independent_oracle():
    assert gen.RULE_HASH == "a74660ace2a2"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]
        assert gen.expected_output(pair["input"]) == pair["output"]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in pairs), name


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_cross_boundary_matrix_and_observed_exact_axes(difficulty):
    for h in (8, 20):
        for w in (9, 22):
            for count in (1, 2, 6):
                for texture in ("plain", "blob", "thin", "l_merge"):
                    kw = dict(grid_h=h, grid_w=w, rectangles=count, texture=texture)
                    grid = gen.generate(17, 9, difficulty=difficulty, **kw)
                    assert gen.self_check(grid) == [], kw
                    assert gen.observe_overrides(grid) == kw
                    assert gen.expected_output(grid) == oracle(grid)
                    assert oracle(grid) != grid


def test_all_cyclic_lesson_starts_refute_actual_declared_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            grids = [gen.generate(seed, i, difficulty=difficulty) for i in range(9)]
            for start in range(len(gen.SCHEDULE_PROFILES)):
                demos = [{"input": g, "output": oracle(g)} for g in grids[start:start+gen.EXAMPLES_NEEDED]]
                query_g = grids[start+gen.EXAMPLES_NEEDED]
                query = {"input": query_g, "output": oracle(query_g)}
                assert gen.lesson_identifiable(demos, query) == [], (seed, start, difficulty)
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(p["input"]) != p["output"] for p in demos), (name, seed, start, difficulty)


def test_replay_global_random_purity_and_no_aliased_rows():
    random.seed(314159)
    state = random.getstate()
    a, b = gen.generate(101, 12), gen.generate(101, 12)
    assert state == random.getstate()
    assert a == b and a is not b
    assert len({id(row) for row in a}) == len(a)
    a[0][0] = (a[0][0] + 1) % 10
    assert a != b


def test_negative_fixtures_are_explicitly_outside_teaching_domain():
    for texture in gen.DEGENERATE_TEXTURES:
        assert gen.self_check(gen.generate(3, 1, texture=texture)), texture
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_constructive_fallback_supports_every_minimum_canvas_axis_combination():
    for h, w in ((8, 9), (20, 22)):
        for count in range(1, 7):
            for texture in gen.HELPFUL_TEXTURES:
                for seed in range(4):
                    grid = gen._fallback(h, w, count, texture, [1, 2, 3, 4, 5, 6], random.Random(seed))
                    assert gen.observe_overrides(grid) == dict(grid_h=h, grid_w=w, rectangles=count, texture=texture)
                    assert gen.expected_output(grid) == oracle(grid)
                    if texture == "l_merge" and count >= 2:
                        assert gen.SEMANTIC_RIVALS["eight_connected_objects"](grid) != oracle(grid)


def test_plain_phase_preserves_canonical_morphology_in_every_difficulty_band():
    profiles = {(len(p["input"]), len(p["input"][0]), len({v for row in p["input"] for v in row}))
                for p in canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            index = next(i for i in range(4) if gen.schedule_profile(seed, i, band) == "plain")
            grid = gen.generate(seed, index, difficulty=band)
            profile = len(grid), len(grid[0]), len({v for row in grid for v in row})
            assert profile in profiles, (band, seed, profile)
