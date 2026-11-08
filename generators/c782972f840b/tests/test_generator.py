"""Focused semantic and distribution regressions for c782972f840b."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    rows = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        item = json.loads(line)
        if item.get("task_id") != "c782972f840b":
            continue
        for split in ("train", "test"):
            pairs = item.get(split) or []
            if isinstance(pairs, dict):
                pairs = [pairs]
            rows.extend(pairs)
    return rows


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            result.append(cells)
    return result


def _normalize(points):
    points = tuple(points)
    assert points
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return tuple(sorted((r - top, c - left) for r, c in points))


def _rotate(shape):
    turned = [(c, -r) for r, c in shape]
    return _normalize(turned)


def _rotation_key(shape):
    variants = []
    current = _normalize(shape)
    for _ in range(4):
        variants.append(current)
        current = _rotate(current)
    return min(variants)


def _dihedral_key(shape):
    shape = _normalize(shape)
    reflected = _normalize((r, -c) for r, c in shape)
    return min(_rotation_key(shape), _rotation_key(reflected))


def _objects(grid):
    objects = []
    for cells in _components(grid):
        colors = {grid[r][c] for r, c in cells}
        assert len(colors) == 1
        objects.append(
            {
                "bbox": (min(r for r, _ in cells), min(c for _, c in cells)),
                "color": next(iter(colors)),
                "oriented": _normalize(cells),
                "rotation": _rotation_key(cells),
                "dihedral": _dihedral_key(cells),
            }
        )
    return sorted(objects, key=lambda item: item["bbox"])


def _relation_output(grid, *, dihedral=False, exact_orientation=False):
    objects = _objects(grid)
    size = len(objects)
    output = [[0] * size for _ in range(size)]
    for row, left in enumerate(objects):
        for col, right in enumerate(objects):
            if row == col:
                output[row][col] = 9
                continue
            if exact_orientation:
                same_shape = left["oriented"] == right["oriented"]
            elif dihedral:
                same_shape = left["dihedral"] == right["dihedral"]
            else:
                same_shape = left["rotation"] == right["rotation"]
            same_color = left["color"] == right["color"]
            output[row][col] = (
                6 if same_shape and same_color
                else 4 if same_shape
                else 2 if same_color
                else 0
            )
    return output


def test_rule_hash_and_canonical_examples_are_owned():
    assert gen.RULE_HASH == "1f9d3ac91fc0"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert _relation_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "canvas_profile",
    [
        "canonical_12x14x3",
        "canonical_13x15x3",
        "canonical_12x16x4",
        "canonical_14x15x3",
        "canonical_13x14x3",
        "expanded",
    ],
)
@pytest.mark.parametrize("n_objects", [4, 5, 6])
@pytest.mark.parametrize("relation_profile", ["with_duplicate", "without_duplicate"])
def test_every_exact_override_is_realized(canvas_profile, n_objects, relation_profile):
    grid = gen.generate(
        117,
        19,
        difficulty="hard",
        canvas_profile=canvas_profile,
        n_objects=n_objects,
        relation_profile=relation_profile,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "canvas_profile": canvas_profile,
        "n_objects": n_objects,
        "relation_profile": relation_profile,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"canvas_profile": "unknown"},
        {"n_objects": 3},
        {"n_objects": 7},
        {"relation_profile": "unknown"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((KeyError, ValueError)):
        gen.generate(1, 2, **kwargs)


def test_relation_profile_controls_only_same_shape_same_color_duplicates():
    with_dup = gen.generate(
        31,
        4,
        canvas_profile="canonical_12x14x3",
        n_objects=6,
        relation_profile="with_duplicate",
    )
    without_dup = gen.generate(
        31,
        4,
        canvas_profile="canonical_12x14x3",
        n_objects=6,
        relation_profile="without_duplicate",
    )
    assert 6 in {value for row in _relation_output(with_dup) for value in row}
    assert 6 not in {value for row in _relation_output(without_dup) for value in row}
    for grid in (with_dup, without_dup):
        values = {value for row in _relation_output(grid) for value in row}
        assert {0, 2, 4, 9} <= values


def test_rotation_is_equivalent_but_reflection_is_not():
    grid = gen.generate(
        91,
        8,
        canvas_profile="canonical_13x15x3",
        n_objects=6,
        relation_profile="with_duplicate",
    )
    assert gen.SEMANTIC_WITNESSES["mirror_not_rotation"](grid)
    authority = _relation_output(grid)
    assert gen.SEMANTIC_RIVALS["dihedral_equivalence"](grid) == _relation_output(
        grid, dihedral=True
    )
    assert gen.SEMANTIC_RIVALS["dihedral_equivalence"](grid) != authority


def test_default_distribution_is_deterministic_and_covers_controls():
    profiles = set()
    counts = set()
    relations = set()
    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = gen.generate(5000 + index, index * 7, difficulty=band)
            assert grid == gen.generate(5000 + index, index * 7, difficulty=band)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            profiles.add(observed["canvas_profile"])
            counts.add(observed["n_objects"])
            relations.add(observed["relation_profile"])
    assert {
        "canonical_12x14x3",
        "canonical_13x15x3",
        "canonical_12x16x4",
        "canonical_14x15x3",
        "canonical_13x14x3",
    } <= profiles
    assert counts == {4, 5, 6}
    assert relations == {"with_duplicate", "without_duplicate"}


@pytest.mark.parametrize(
    "grid",
    [
        [[0] * 14 for _ in range(12)],
        [[1] * 14 for _ in range(12)],
        [[0] * 14 for _ in range(12)],
        [[0, 0], [0]],
        [[True] * 14 for _ in range(12)],
    ],
)
def test_self_check_rejects_malformed_or_semantically_empty_grids(grid):
    if len(grid) == 12 and len(grid[0]) == 14 and all(v == 0 for row in grid for v in row):
        grid = [row[:] for row in grid]
        grid[5][5] = 3
    assert gen.self_check(grid)


def test_generated_python_oracle_matches_declared_authority_helper():
    for profile in ("with_duplicate", "without_duplicate"):
        for index in range(20):
            grid = gen.generate(700 + index, index, relation_profile=profile)
            assert gen._relation_output(grid) == _relation_output(grid)
