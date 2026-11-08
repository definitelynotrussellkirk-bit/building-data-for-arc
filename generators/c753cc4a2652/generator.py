"""Semantic generator for ARC task c753cc4a2652.

Select the first non-red component cardinally touching the first row-major
red marker.  Return a blank canvas with only that component's cardinal
perimeter painted red.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "c753cc4a2652"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9fffa90f1037"
SUMMARY = "Outline in red the first non-red component touching the first red marker, clearing markers, interiors, and distractors."
INVARIANTS = [
    "literal color 0 is the background and color 2 marks selection/output",
    "the first row-major color-2 cell is the active marker",
    "at least one non-red monochrome component cardinally touches that marker",
    "the first touching component in object discovery order is selected",
    "only target cells missing a cardinal target neighbor are painted color 2",
    "the output otherwise clears the canvas to zero",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "solid_rectangle",
    "concave_target",
    "holed_target",
    "thin_target",
    "edge_target",
    "distractor_objects",
    "same_color_distractor",
    "multiple_touching_candidates",
    "marker_decoys",
    "large_interior",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten observable selection/perimeter lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "0000000000/0002000000/0066660000/0066660000/0066660000/0000000000/0000007700/0000007700/0000000000/0000000000",
    "public_2": "00000000000/00000007777/00000007777/00000007777/25500000000/05550000000/00550000000/00000000000/00000000000",
    "public_3": "0000020000/0000080000/0000088000/0000088800/0000000000/0000000000/0666600000/0666600000/0666600000/0000000000",
    "public_4": "000000000/066000000/066000000/000002000/000077700/000077700/000007000/000000000/000000000",
    "public_5": "00000000000/00000000770/00020000770/00066000000/00066600000/00006600000/00000000000/05000000000/05500000000/00000000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


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
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            result.append({"color": color, "cells": cells, "size": len(cells), "r1": r1, "c1": c1, "r2": r2, "c2": c2, "height": r2 - r1 + 1, "width": c2 - c1 + 1, "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1)})
    return result


def _touches(marker, cells):
    row, col = marker
    return any((row + dr, col + dc) in cells for dr, dc in _CARDINAL)


def _perimeter(cells):
    return {cell for cell in cells if any((cell[0] + dr, cell[1] + dc) not in cells for dr, dc in _CARDINAL)}


def _paint_output(height, width, cells):
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in cells:
        output[row][col] = 2
    return output


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not markers:
        raise ValueError("expected at least one color-2 marker")
    touching = [obj for obj in _components(grid) if obj["color"] != 2 and _touches(markers[0], obj["cells"])]
    if not touching:
        raise ValueError("expected a non-red component touching the first marker")
    return _paint_output(len(grid), len(grid[0]), _perimeter(touching[0]["cells"]))


def _has_hole(obj):
    cells = obj["cells"]
    gaps = {(r, c) for r in range(obj["r1"], obj["r2"] + 1) for c in range(obj["c1"], obj["c2"] + 1) if (r, c) not in cells}
    if not gaps:
        return False
    boundary = {cell for cell in gaps if cell[0] in (obj["r1"], obj["r2"]) or cell[1] in (obj["c1"], obj["c2"])}
    reachable = set(boundary)
    stack = list(boundary)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, col + dc)
            if neighbor in gaps and neighbor not in reachable:
                reachable.add(neighbor)
                stack.append(neighbor)
    return bool(gaps - reachable)


def _general_profile(markers, component_records, touching, target, perimeter):
    nonred = [obj for obj in component_records if obj["color"] != 2]
    if len(markers) > 1:
        return "marker_decoys"
    if len(touching) > 1:
        return "multiple_touching_candidates"
    colors = [obj["color"] for obj in nonred]
    if len(colors) != len(set(colors)):
        return "same_color_distractor"
    if len(nonred) > 1:
        return "distractor_objects"
    if any(r in (0, target["grid_height"] - 1) or c in (0, target["grid_width"] - 1) for r, c in target["cells"]):
        return "edge_target"
    if _has_hole(target):
        return "holed_target"
    if target["height"] == 1 or target["width"] == 1:
        return "thin_target"
    interior = target["size"] - len(perimeter)
    if target["size"] == target["bbox_area"]:
        return "large_interior" if interior >= 6 else "solid_rectangle"
    return "concave_target"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not 1 <= len(markers) <= 4:
        errors.append(f"expected 1..4 color-2 marker cells; got {len(markers)}")
        return result
    marker_set = set(markers)
    if any((row + dr, col + dc) in marker_set for row, col in markers for dr, dc in _CARDINAL):
        errors.append("color-2 markers must remain 4-disconnected cells")
        return result
    component_records = _components(grid)
    nonred = [obj for obj in component_records if obj["color"] != 2]
    if not 1 <= len(nonred) <= 5:
        errors.append(f"expected 1..5 non-red components; got {len(nonred)}")
        return result
    if any(obj["size"] < 3 for obj in nonred):
        errors.append("every non-red component must contain at least three cells")
        return result
    touching = [obj for obj in nonred if _touches(markers[0], obj["cells"])]
    if not touching:
        errors.append("first marker must cardinally touch a non-red component")
        return result
    target = dict(touching[0])
    target["grid_height"] = len(grid)
    target["grid_width"] = len(grid[0])
    perimeter = _perimeter(target["cells"])
    output = _paint_output(len(grid), len(grid[0]), perimeter)
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(markers, component_records, touching, target, perimeter)
    if profile not in SCENE_PROFILES:
        errors.append("marker/object geometry does not match a declared profile")
    result.update({"markers": markers, "active_marker": markers[0], "objects": component_records, "nonred_objects": nonred, "touching": touching, "target": target, "perimeter": perimeter, "interior": target["cells"] - perimeter, "output": output, "scene_profile": profile, "errors": errors})
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


def _rectangle(height, width):
    return {(row, col) for row in range(height) for col in range(width)}


def _ring(height=5, width=5):
    return {(row, col) for row in range(height) for col in range(width) if row in (0, height - 1) or col in (0, width - 1)}


def _shape_for(profile, rng):
    if profile == "solid_rectangle":
        return _rectangle(rng.randint(3, 4), rng.randint(3, 4))
    if profile in ("distractor_objects", "same_color_distractor"):
        return _rectangle(rng.randint(3, 4), rng.randint(3, 5))
    if profile == "concave_target":
        height, width = rng.randint(4, 6), rng.randint(4, 6)
        notch_h, notch_w = rng.randint(1, height - 2), rng.randint(1, width - 2)
        return _rectangle(height, width) - {(row, col) for row in range(height - notch_h, height) for col in range(width - notch_w, width)}
    if profile == "holed_target":
        return _ring(rng.randint(4, 6), rng.randint(4, 7))
    if profile == "thin_target":
        length = rng.randint(3, 7)
        return {(0, index) for index in range(length)} if rng.choice((False, True)) else {(index, 0) for index in range(length)}
    if profile == "large_interior":
        return _rectangle(rng.randint(5, 7), rng.randint(5, 8))
    return _rectangle(rng.randint(3, 5), rng.randint(3, 6))


def _translate(shape, top, left):
    return {(top + row, left + col) for row, col in shape}


def _target_and_marker(rng, shape, height, width, *, edge=False):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(200):
        if edge:
            side = rng.choice(("top", "bottom", "left", "right"))
            top = 0 if side == "top" else height - sh if side == "bottom" else rng.randint(1, height - sh - 1)
            left = 0 if side == "left" else width - sw if side == "right" else rng.randint(1, width - sw - 1)
        else:
            top = rng.randint(1, height - sh - 1)
            left = rng.randint(1, width - sw - 1)
        cells = _translate(shape, top, left)
        outside = []
        for row, col in cells:
            for dr, dc in _CARDINAL:
                candidate = (row + dr, col + dc)
                if 0 <= candidate[0] < height and 0 <= candidate[1] < width and candidate not in cells:
                    if not (top <= candidate[0] < top + sh and left <= candidate[1] < left + sw):
                        outside.append(candidate)
        if outside:
            return cells, rng.choice(sorted(set(outside)))
    raise AssertionError("could not place target and external marker")


def _place_distractor(rng, grid, shape, color, forbidden):
    height, width = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [(top, left) for top in range(height - sh + 1) for left in range(width - sw + 1)]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = _translate(shape, top, left)
        ring = {(r + dr, c + dc) for r, c in cells for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if ring.intersection(forbidden):
            continue
        for row, col in cells:
            grid[row][col] = color
        return cells
    raise AssertionError("could not place isolated distractor")


def _general_scene(ctx, profile):
    ranges = {None: (12, 22), "easy": (12, 15), "medium": (16, 22), "hard": (23, 30)}
    low, high = ranges[ctx.difficulty]
    height = ctx.draw_int("canvas_height", low, high)
    width = ctx.draw_int("canvas_width", low, high)
    rng = ctx.draw_rng("geometry")
    palette = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], 5)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    if profile == "multiple_touching_candidates":
        mr, mc = height // 2, width // 2
        first_h, second_h, span = rng.randint(1, 3), rng.randint(1, 3), rng.randint(3, 5)
        left = mc - span // 2
        first = {(r, c) for r in range(mr - first_h, mr) for c in range(left, left + span)}
        second = {(r, c) for r in range(mr + 1, mr + second_h + 1) for c in range(left, left + span)}
        for cells, color in ((first, palette[0]), (second, palette[1])):
            for row, col in cells:
                grid[row][col] = color
        grid[mr][mc] = 2
        return grid

    if profile == "marker_decoys":
        target_h, target_w = rng.randint(3, 5), rng.randint(3, 6)
        target = {(r, c) for r in range(2, 2 + target_h) for c in range(3, 3 + target_w)}
        distractor = {(r, c) for r in range(height - 5, height - 2) for c in range(width - 7, width - 3)}
        for cells, color in ((target, palette[0]), (distractor, palette[1])):
            for row, col in cells:
                grid[row][col] = color
        grid[2][2] = 2
        grid[height - 3][width - 3] = 2
        return grid

    shape = _shape_for(profile, rng)
    target, marker = _target_and_marker(rng, shape, height, width, edge=profile == "edge_target")
    for row, col in target:
        grid[row][col] = palette[0]
    grid[marker[0]][marker[1]] = 2
    forbidden = set(target) | {marker}

    if profile in ("distractor_objects", "same_color_distractor"):
        count = 2 if profile == "distractor_objects" else 1
        for index in range(count):
            distractor_shape = _rectangle(2, rng.randint(2, 3))
            color = palette[index + 1] if profile == "distractor_objects" else palette[0]
            cells = _place_distractor(rng, grid, distractor_shape, color, forbidden)
            forbidden.update(cells)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
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
