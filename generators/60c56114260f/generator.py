"""Semantic generator for ARC task 60c56114260f.

Sort the nonzero objects by top row then left column.  Output an N by N
matrix whose entry is cyan 8 exactly when the corresponding cropped binary
shapes are equivalent under a rotation or reflection, and zero otherwise.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "60c56114260f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "10e74a39671a"
SUMMARY = "Build the pairwise dihedral-equivalence matrix of sorted objects."
INVARIANTS = [
    "background is zero and every object is monochrome",
    "objects are spatially isolated and use distinct nonzero colors",
    "objects are ordered by bounding-box top row and then left column",
    "the output is a symmetric N by N cyan/zero equivalence matrix with cyan diagonal",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_train_4", "public_test_1",
)
GENERAL_LESSONS = {
    "three_trominoes": (3, 3),
    "three_tetrominoes": (3, 4),
    "three_pentominoes": (3, 5),
    "four_trominoes": (4, 3),
    "four_tetrominoes": (4, 4),
    "four_pentominoes": (4, 5),
    "five_trominoes": (5, 3),
    "five_tetrominoes": (5, 4),
    "six_trominoes": (6, 3),
    "six_tetrominoes": (6, 4),
    "six_pentominoes": (6, 5),
}
GENERAL_PROFILES = tuple(GENERAL_LESSONS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng over public layouts and equivalence partitions",
        "valid": "public_train_1|public_train_2|public_train_3|public_train_4|public_test_1|three_trominoes|three_tetrominoes|three_pentominoes|four_trominoes|four_tetrominoes|four_pentominoes|five_trominoes|five_tetrominoes|six_trominoes|six_tetrominoes|six_pentominoes",
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "00000000000000", "02220033000000", "02000003000000", "00000003000000",
        "00000000000000", "00000000004440", "00000000000400", "00000000000000",
        "00000000000000",
    ),
    "public_train_2": (
        "0000000000000", "0220000000000", "0022000000000", "0000000550000",
        "0000005500000", "0000000000660", "0000000000660", "0000000000000",
    ),
    "public_train_3": (
        "000000000000000", "000000000000000", "033000044000000", "033000044000000",
        "030000004000000", "000000000007770", "000000000000770", "000000000000000",
        "000000000000000", "000000000000000",
    ),
    "public_train_4": (
        "00000000000000", "02220000000000", "02020000550000", "02220000550000",
        "00000000000000", "00000000000660", "00000000000660", "00000000000000",
        "00000000000000",
    ),
    "public_test_1": (
        "000000000000000", "022000000000000", "020000000000000", "000000440000000",
        "000000040000000", "000000000000000", "000000000077700", "000000000070700",
        "000000000000000", "000000000000000",
    ),
}
_PUBLIC_INPUTS = {name: [[int(cell) for cell in row] for row in rows]
                  for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}

_SHAPE_CLASSES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
)
_SHAPES_BY_SIZE = {
    size: tuple(shape for shape in _SHAPE_CLASSES if len(shape) == size)
    for size in (3, 4, 5)
}


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate(cells):
    norm = _normalize(cells)
    height = max(r for r, _ in norm) + 1
    return _normalize((c, height - 1 - r) for r, c in norm)


def _reflect(cells):
    norm = _normalize(cells)
    width = max(c for _, c in norm) + 1
    return _normalize((r, width - 1 - c) for r, c in norm)


def _variants(cells):
    result = set()
    current = _normalize(cells)
    for _ in range(4):
        result.add(current); result.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(result))


def _shape_key(cells):
    return min(_variants(cells))


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors"], h, w
    return [], h, w


def _extract_components(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while remaining:
        start = min(remaining)
        cells, stack = {start}, [start]
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor); cells.add(neighbor); stack.append(neighbor)
        result.append({
            "cells": frozenset(cells), "norm": _normalize(cells),
            "r1": min(r for r, _ in cells), "c1": min(c for _, c in cells),
            "colors": frozenset(grid[r][c] for r, c in cells),
        })
    return sorted(result, key=lambda obj: (obj["r1"], obj["c1"]))


def _partition(keys):
    labels, seen = [], {}
    for key in keys:
        if key not in seen:
            seen[key] = len(seen)
        labels.append(seen[key])
    return tuple(labels)


_LESSON_TO_PROFILE = {lesson: profile for profile, lesson in GENERAL_LESSONS.items()}


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors:
        return result
    parts = _extract_components(grid)
    if not 3 <= len(parts) <= 6:
        errors.append("exactly three through six isolated objects are required")
    colors = []
    for obj in parts:
        if len(obj["colors"]) != 1:
            errors.append("every object must be monochrome")
        else:
            colors.append(next(iter(obj["colors"])))
    if len(colors) != len(set(colors)):
        errors.append("object colors must be distinct")
    keys = tuple(_shape_key(obj["norm"]) for obj in parts)
    partition = _partition(keys)
    output = [[8 if keys[r] == keys[c] else 0 for c in range(len(keys))]
              for r in range(len(keys))]
    signature = tuple(map(tuple, grid))
    sizes = {len(obj["cells"]) for obj in parts}
    general_lesson = (len(keys), next(iter(sizes))) if len(sizes) == 1 else None
    profile = _PUBLIC_SIGNATURES.get(signature) or _LESSON_TO_PROFILE.get(general_lesson)
    if profile not in SCENE_PROFILES:
        errors.append("object equivalence partition does not match a declared lesson")
    result.update({"parts": parts, "colors": tuple(colors), "shape_keys": keys,
                   "partition": partition, "output": output,
                   "scene_profile": profile, "errors": errors})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid); profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _dimensions(rng, band):
    bounds = {"easy": ((9, 11), (15, 17)), "medium": ((10, 13), (17, 20)),
              "hard": ((13, 16), (20, 24))}
    (h1, h2), (w1, w2) = bounds[band]
    return rng.randint(h1, h2), rng.randint(w1, w2)


def _general_grid(rng, profile, band):
    object_count, shape_size = GENERAL_LESSONS[profile]
    class_pool = _SHAPES_BY_SIZE[shape_size]
    class_count = rng.randint(2, min(object_count, len(class_pool)))
    labels = list(range(class_count)) + [rng.randrange(class_count) for _ in range(object_count - class_count)]
    rng.shuffle(labels)
    partition = _partition(labels)
    h, w = _dimensions(rng, band)
    classes = rng.sample(class_pool, class_count)
    shapes = [rng.choice(_variants(classes[group])) for group in partition]
    colors = rng.sample(range(1, 10), len(shapes))
    grid = [[0 for _ in range(w)] for _ in range(h)]
    columns = (0, w // 2 - 2, w - 4)
    rows = (0, h - 4)
    for index, (shape, color) in enumerate(zip(shapes, colors)):
        slot_row, slot_col = divmod(index, 3)
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        r0 = rows[slot_row]
        c0 = columns[slot_col]
        for dr, dc in shape:
            grid[r0 + dr][c0 + dc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=band, overrides=overrides)
    weighted = list(PUBLIC_PROFILES) + [profile for profile in GENERAL_PROFILES for _ in range(4)]
    profile = ctx.draw_choice("scene_profile", weighted)
    rng = ctx.draw_rng("layout")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_grid(rng, profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    if info["errors"]:
        return list(info["errors"])
    output = info["output"]
    n = len(info["parts"])
    if len(output) != n or any(len(row) != n for row in output):
        return ["output must be square with one row and column per object"]
    if any(output[i][i] != 8 for i in range(n)):
        return ["equivalence matrix diagonal must be cyan"]
    if any(output[r][c] != output[c][r] for r in range(n) for c in range(n)):
        return ["equivalence matrix must be symmetric"]
    return []
