"""Focused regressions for the key-gallery and exact override contracts."""
from __future__ import annotations

import json
import random
from pathlib import Path
import sys

import pytest

for parent in Path(__file__).resolve().parents:
    support = next(
        (
            p
            for p in (
                parent / "reviewer_support.py",
                parent / "shared/runtime/reviewer_support.py",
            )
            if p.is_file()
        ),
        None,
    )
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break

from reviewer_support import find_root, load_selected_generator

GEN, SOURCE, SOURCE_SHA = load_selected_generator(
    "25c140f9307d", root=find_root(__file__)
)


def components(grid, *, color=None, eight_connected=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if eight_connected:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for sr in range(h):
        for sc in range(w):
            value = grid[sr][sc]
            wanted = value != 0 if color is None else value == color
            if not wanted or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in steps:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    nv = grid[nr][nc]
                    matches = nv != 0 if color is None else nv == color
                    if matches:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def shape_signature(cells):
    points = {(r, c) for r, c in cells}
    variants = []
    for _ in range(4):
        min_r = min(r for r, _ in points)
        min_c = min(c for _, c in points)
        normalized = tuple(sorted((r - min_r, c - min_c) for r, c in points))
        variants.append(normalized)
        points = {(c, -r) for r, c in points}
    return min(variants)


def scene_facts(grid):
    red = sorted(components(grid, color=2), key=len, reverse=True)
    assert red
    r0, c0, r1, c1 = bbox(red[0])
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    holes = sorted(components(crop, color=0, eight_connected=True), key=len)
    objects = sorted(components(grid, eight_connected=True), key=len, reverse=True)
    return {
        "plate_shape": (r1 - r0 + 1, c1 - c0 + 1),
        "holes": holes,
        "objects": objects,
    }


def test_key_gallery_objects_are_separate_and_match_hole_count():
    grid = GEN.generate(
        3749515847903219250,
        0,
        difficulty="medium",
        rect_size=9,
        n_keys=3,
    )
    facts = scene_facts(grid)
    assert facts["plate_shape"] == (9, 9)
    assert [len(hole) for hole in facts["holes"]] == [4, 4, 4]
    assert len(facts["objects"]) == 4  # plate + three detached key objects
    hole_signatures = {shape_signature(hole) for hole in facts["holes"]}
    key_signatures = {
        shape_signature([(r, c) for r, c in key if grid[r][c] == 2])
        for key in facts["objects"][1:]
    }
    assert len(hole_signatures) == 3
    assert key_signatures == hole_signatures
    for key in facts["objects"][1:]:
        values = [grid[r][c] for r, c in key]
        assert values.count(2) == 4
        assert len([v for v in values if v not in (0, 2)]) == 2
        r0, c0, r1, c1 = bbox(key)
        assert (r1 - r0 + 1, c1 - c0 + 1) == (3, 3)
    assert GEN.self_check(grid, difficulty="medium") == []


@pytest.mark.parametrize("size", [9, 11, 14])
def test_rect_size_is_an_exact_observable_square_override(size):
    grid = GEN.generate(20261024, size, rect_size=size, n_keys=4)
    facts = scene_facts(grid)
    assert facts["plate_shape"] == (size, size)
    assert len(facts["holes"]) == 4
    assert len(facts["objects"]) == 5
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("bad", [8, 15, True, 9.0, "9"])
def test_rect_size_rejects_values_outside_the_supported_strict_domain(bad):
    with pytest.raises((TypeError, ValueError), match="rect_size"):
        GEN.generate(1, 0, rect_size=bad)


@pytest.mark.parametrize("n_keys", [2, 3, 4])
def test_n_keys_is_exact_and_observable(n_keys):
    grid = GEN.generate(99173, n_keys, rect_size=9, n_keys=n_keys)
    facts = scene_facts(grid)
    assert len(facts["holes"]) == n_keys
    assert len(facts["objects"]) == n_keys + 1
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("bad", [1, 5, True, 2.0, "2"])
def test_n_keys_rejects_values_outside_the_supported_strict_domain(bad):
    with pytest.raises((TypeError, ValueError), match="n_keys"):
        GEN.generate(1, 0, n_keys=bad)


def test_default_generation_is_valid_deterministic_fresh_and_rng_pure():
    random.seed(314159)
    before = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        for sample_index in range(20):
            grid = GEN.generate(7000 + sample_index, sample_index, difficulty=band)
            again = GEN.generate(7000 + sample_index, sample_index, difficulty=band)
            assert grid == again
            assert grid is not again
            assert all(a is not b for a, b in zip(grid, again))
            assert GEN.self_check(grid, difficulty=band) == []
            facts = scene_facts(grid)
            assert 2 <= len(facts["holes"]) <= 4
            assert len(facts["objects"]) == len(facts["holes"]) + 1
    assert random.getstate() == before


def test_self_check_rejects_a_gallery_bridge_between_two_keys():
    grid = GEN.generate(8080, 0, rect_size=9, n_keys=3)
    facts = scene_facts(grid)
    assert len(facts["objects"]) == 4
    keys = sorted(facts["objects"][1:], key=lambda cells: bbox(cells)[0])
    first = bbox(keys[0])
    second = bbox(keys[1])
    bridged = [row[:] for row in grid]
    c = first[1]
    for r in range(first[2] + 1, second[0]):
        bridged[r][c] = 2
    errors = GEN.self_check(bridged)
    assert any("detached key" in error for error in errors)


def test_every_canonical_input_is_owned_by_the_structural_validator():
    canonical_path = find_root(__file__) / "shared/data/canonical/puzzles.jsonl"
    pairs = None
    for line in canonical_path.open():
        row = json.loads(line)
        if row.get("task_id") == "25c140f9307d":
            pairs = [*row["train"], *row["test"]]
            break
    assert pairs is not None and len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
