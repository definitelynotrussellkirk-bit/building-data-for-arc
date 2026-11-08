"""Semantic generator for ARC task c464f6b94fbb.

Extract every nonzero monochrome 4-connected component, sort components by
decreasing cell count with top-row and left-column tie breaks, crop each
component's raw bounding box, and stack the crops top-aligned with one zero
column between neighbors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "c464f6b94fbb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "48e84ae04028"
SUMMARY = "Sort nonzero component crops by (-size, top, left), then stack their raw bounding boxes left-to-right with one zero-column gap."
INVARIANTS = [
    "literal color 0 is the background",
    "there are two to five isolated monochrome 4-connected components",
    "sorting uses the exact key (-cell count, top row, left column)",
    "each crop preserves every cell in the component's raw input bounding box",
    "crops are top-aligned and separated by exactly one zero column",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "distinct_sizes",
    "tie_by_row",
    "tie_by_column",
    "two_objects",
    "five_objects",
    "same_color_objects",
    "internal_holes",
    "varied_heights",
    "single_cell_member",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three exact-public and nine observable sorting/cropping lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "000000000000000/022000003330000/022000000300000/020000003330000/000000000000000/000000000000000/000004444000000/000000000000000/000000000000000/000000000000000",
    "public_2": "0000000000000000/0055000000000000/0055000000666000/0050000000060000/0000000000666000/0000000000000000/0000000000000000/0000000000000000/0000007770000000/0000000000000000/0000000000000000",
    "public_3": "00000000000000000/08800000000000000/08800000022220000/08000000000000000/00000000000000000/00000000000000000/00000000000000000/00000000000033300/00000000000003000/00000000000033300/00000000000000000/00000000000000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid):
    """Return monochrome 4-connected components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            crop = [list(input_row[c1:c2 + 1]) for input_row in grid[r1:r2 + 1]]
            result.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
                "crop": crop,
            })
    return result


def _stack_crops(components):
    ordered = sorted(components, key=lambda obj: (-obj["size"], obj["r1"], obj["c1"]))
    out_height = max(obj["height"] for obj in ordered)
    out_width = sum(obj["width"] for obj in ordered) + len(ordered) - 1
    output = [[0 for _ in range(out_width)] for _ in range(out_height)]
    left = 0
    for obj in ordered:
        for row, values in enumerate(obj["crop"]):
            output[row][left:left + len(values)] = values
        left += obj["width"] + 1
    return ordered, output


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _components(grid)
    if not components:
        raise ValueError("expected at least one nonzero component")
    return _stack_crops(components)[1]


def _general_profile(components):
    colors = [obj["color"] for obj in components]
    if len(colors) != len(set(colors)):
        return "same_color_objects"
    if any(obj["bbox_area"] > obj["size"] for obj in components):
        return "internal_holes"
    if len(components) == 2:
        return "two_objects"
    if len(components) == 5:
        return "five_objects"
    if any(obj["size"] == 1 for obj in components):
        return "single_cell_member"
    by_size = {}
    for obj in components:
        by_size.setdefault(obj["size"], []).append(obj)
    tied = [group for group in by_size.values() if len(group) > 1]
    if any(len({obj["r1"] for obj in group}) > 1 for group in tied):
        return "tie_by_row"
    if any(len({obj["c1"] for obj in group}) > 1 for group in tied):
        return "tie_by_column"
    if len({obj["height"] for obj in components}) == len(components):
        return "varied_heights"
    return "distinct_sizes"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    components = _components(grid)
    if not 2 <= len(components) <= 5:
        errors.append(f"expected 2..5 nonzero components; got {len(components)}")
        return result
    ordered, output = _stack_crops(components)
    if len(output) > 30 or len(output[0]) > 30:
        errors.append("stacked output dimensions must not exceed 30")
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(components)
    if profile not in SCENE_PROFILES:
        errors.append("component geometry does not match a declared profile")
    result.update({
        "components": components,
        "ordered": ordered,
        "sort_keys": [(-obj["size"], obj["r1"], obj["c1"]) for obj in ordered],
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _line(length, *, vertical=False):
    return {(index, 0) if vertical else (0, index) for index in range(length)}


def _rectangle(height, width):
    return {(row, col) for row in range(height) for col in range(width)}


def _shape_spec(profile):
    if profile == "distinct_sizes":
        return [_line(2), _line(3), _rectangle(2, 2)]
    if profile == "tie_by_row":
        return [_line(4), _rectangle(2, 2), _rectangle(2, 3)]
    if profile == "tie_by_column":
        return [_line(4), _rectangle(2, 2), _rectangle(2, 3)]
    if profile == "two_objects":
        return [_rectangle(2, 2), _rectangle(3, 2)]
    if profile == "five_objects":
        return [_line(2, vertical=True), _line(3), _rectangle(2, 2), _line(5, vertical=True), _rectangle(2, 3)]
    if profile == "same_color_objects":
        return [_rectangle(2, 2), _line(3, vertical=True), _rectangle(2, 3)]
    if profile == "internal_holes":
        return [{(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)}, _rectangle(2, 2), _rectangle(2, 3)]
    if profile == "varied_heights":
        return [_line(2, vertical=True), _rectangle(3, 2), _rectangle(4, 2)]
    if profile == "single_cell_member":
        return [{(0, 0)}, _rectangle(2, 2), _rectangle(3, 2)]
    raise ValueError(f"unknown scene profile: {profile!r}")


def _normalize(shape):
    r0 = min(r for r, _ in shape)
    c0 = min(c for _, c in shape)
    return {(r - r0, c - c0) for r, c in shape}


def _can_place(cells, occupied, height, width):
    if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        return False
    ring = {(r + dr, c + dc) for r, c in cells for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
    return not ring.intersection(occupied)


def _place_random(rng, shape, occupied, height, width, *, required_row=None):
    shape = _normalize(shape)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    rows = [required_row] if required_row is not None else list(range(height - sh + 1))
    candidates = [(row, col) for row in rows for col in range(width - sw + 1)]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = {(top + r, left + c) for r, c in shape}
        if _can_place(cells, occupied, height, width):
            return cells
    return None


def _place_shapes(rng, shapes, profile, height, width):
    for _ in range(80):
        occupied = set()
        placed = []
        common_row = rng.randint(0, height - 1) if profile == "tie_by_column" else None
        forced_rows = None
        if profile == "tie_by_row":
            first = rng.randint(0, max(0, height // 3 - 1))
            second = rng.randint(max(first + 2, 2 * height // 3), height - 1)
            forced_rows = (first, second)
        success = True
        for index, shape in enumerate(shapes):
            required_row = common_row if profile == "tie_by_column" and index < 2 else None
            if forced_rows is not None and index < 2:
                required_row = forced_rows[index]
            cells = _place_random(rng, shape, occupied, height, width, required_row=required_row)
            if cells is None:
                success = False
                break
            placed.append(cells)
            occupied.update(cells)
        if success:
            return placed
    raise AssertionError("canvas cannot fit requested isolated components")


def _general_scene(ctx, profile):
    ranges = {
        None: ((10, 18), (14, 22)),
        "easy": ((10, 12), (14, 17)),
        "medium": ((12, 17), (16, 22)),
        "hard": ((16, 24), (20, 30)),
    }
    (hlo, hhi), (wlo, whi) = ranges[ctx.difficulty]
    height = ctx.draw_int("canvas_height", hlo, hhi)
    width = ctx.draw_int("canvas_width", wlo, whi)
    rng = ctx.draw_rng("geometry")
    shapes = _shape_spec(profile)
    placed = _place_shapes(rng, shapes, profile, height, width)
    palette = rng.sample(list(range(1, 10)), len(shapes))
    if profile == "same_color_objects":
        palette[1] = palette[0]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in zip(palette, placed):
        for row, col in cells:
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES + GENERAL_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
