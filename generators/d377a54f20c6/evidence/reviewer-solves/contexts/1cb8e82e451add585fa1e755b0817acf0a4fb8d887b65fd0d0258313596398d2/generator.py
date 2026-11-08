"""Semantic generator for ARC task d377a54f20c6.

Each nonzero 4-connected object is a filled two-color rectangle.  Its
dominant color becomes a frame, while its rarer color draws inward diagonals
and the center-row/center-column extension needed by a non-square interior.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "d377a54f20c6"
TASK_ID = "d377a54f20c6"
VERSION = "3.0.0"
RULE_HASH = "108312a76f48"
SUMMARY = "Redraw every filled two-color object as a dominant-color frame with a rare-color edge-distance X and centered extension."
INVARIANTS = [
    "literal color 0 is background and remains unchanged outside object bounding boxes",
    "nonzero 4-connected components are processed independently",
    "each component fills its rectangular bounding box and uses exactly two colors",
    "the uniquely most frequent color supplies the output frame",
    "the rarer color supplies every interior stroke",
    "interior stroke cells have equal nearest vertical and horizontal edge distance",
    "a wider interior extends the middle row and a taller interior extends the middle column",
    "input marker position and multiplicity do not determine output stroke placement",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "square_odd_side",
    "square_even_side",
    "landscape_center_row",
    "portrait_center_column",
    "extreme_landscape",
    "extreme_portrait",
    "multiple_objects",
    "shared_marker_color",
    "cross_role_palette",
    "border_marker_erased",
    "multiple_marker_pixels",
    "mixed_parities",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve observable frame-and-stroke lessons",
        "valid": "public_1|public_2|public_3|public_4|square_odd_side|square_even_side|landscape_center_row|portrait_center_column|extreme_landscape|extreme_portrait|multiple_objects|shared_marker_color|cross_role_palette|border_marker_erased|multiple_marker_pixels|mixed_parities",
    }
}

_PUBLIC_ROWS = {
    "public_1": "00000000000000/00333333333000/00333333363000/00333333333000/00333333333000/00333333333000/00333333333000/00333333333000/00333333333000/00333333333000/00333333333000/00000000000000/00000000000000",
    "public_2": "000000000000000/022222222000000/021222222000000/022222222000000/022222222000000/022222222000000/022222222000000/022222222000000/000000000000000/000000000000000/000000000000000/000000000000000",
    "public_3": "000000000000000000/001111111003333330/001111111003333230/001111111003333330/001111111003333330/001111111003333330/001111121003333330/001111111000000000/000000000000000000/000000444444444440/000000444444444440/000000444444444440/000000444444444440/000000444444444440/000000434444444440/000000444444444440/000000000000000000",
    "public_4": "000000000000000000000000/033333300000000000000000/033333300000008888888880/033333300000008688888880/033333300000008888888880/031333300000008888888880/033333300000008888888880/000000000000008888888880/000222222222208888888880/000222222222208888888880/000222222222208888888880/000222222222208888888880/000222222222208888888880/000222222222208888888880/000222222222208888888880/000222222222200000000000/000242222222200000000000/000222222222200000000000/000000000000000000000000",
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
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return components


def _object_facts(grid):
    facts = []
    for cells in _components(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        frequencies = Counter(grid[row][col] for row, col in cells)
        ordered = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))
        main = ordered[0][0] if ordered else None
        marker = ordered[1][0] if len(ordered) > 1 else None
        marker_cells = [(row, col) for row, col in cells if marker is not None and grid[row][col] == marker]
        facts.append({
            "cells": cells,
            "bbox": (r1, c1, r2, c2),
            "height": r2 - r1 + 1,
            "width": c2 - c1 + 1,
            "frequencies": frequencies,
            "main": main,
            "marker": marker,
            "marker_cells": marker_cells,
            "fills_bbox": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
            "unique_dominant": len(ordered) >= 2 and ordered[0][1] > ordered[1][1],
        })
    return facts


def _stroke(ir, ic, interior_height, interior_width):
    dr = min(ir, interior_height - 1 - ir)
    dc = min(ic, interior_width - 1 - ic)
    max_dr = (interior_height - 1) // 2
    max_dc = (interior_width - 1) // 2
    return dr == dc or (dr == max_dr and dc >= dr) or (dc == max_dc and dr >= dc)


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for obj in _object_facts(grid):
        if len(obj["frequencies"]) < 2:
            raise ValueError("every object must contain a dominant and marker color")
        r1, c1, r2, c2 = obj["bbox"]
        height, width = obj["height"], obj["width"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                rr, cc = row - r1, col - c1
                if rr in (0, height - 1) or cc in (0, width - 1):
                    output[row][col] = obj["main"]
                else:
                    output[row][col] = obj["marker"] if _stroke(rr - 1, cc - 1, height - 2, width - 2) else 0
    return output


def _general_profile(facts):
    mains = {obj["main"] for obj in facts}
    markers = [obj["marker"] for obj in facts]
    if len(facts) >= 2:
        if mains.intersection(markers):
            return "cross_role_palette"
        if len(set(markers)) < len(markers):
            return "shared_marker_color"
        if len(facts) == 3:
            return "mixed_parities"
        return "multiple_objects"
    obj = facts[0]
    r1, c1, r2, c2 = obj["bbox"]
    if any(row in (r1, r2) or col in (c1, c2) for row, col in obj["marker_cells"]):
        return "border_marker_erased"
    if len(obj["marker_cells"]) > 1:
        return "multiple_marker_pixels"
    delta = obj["width"] - obj["height"]
    if delta >= 5:
        return "extreme_landscape"
    if delta <= -5:
        return "extreme_portrait"
    if delta > 0:
        return "landscape_center_row"
    if delta < 0:
        return "portrait_center_column"
    return "square_odd_side" if obj["height"] % 2 else "square_even_side"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    if all(value != 0 for row in grid for value in row):
        errors.append("expected literal zero background outside the objects")
    facts = _object_facts(grid)
    if not 1 <= len(facts) <= 3:
        errors.append("expected one to three nonzero objects")
    for index, obj in enumerate(facts):
        prefix = f"object {index + 1}"
        if not obj["fills_bbox"]:
            errors.append(f"{prefix} must fill its rectangular bounding box")
        if obj["height"] < 5 or obj["width"] < 5:
            errors.append(f"{prefix} dimensions must both be at least five")
        if len(obj["frequencies"]) != 2:
            errors.append(f"{prefix} must use exactly two colors")
        if not obj["unique_dominant"]:
            errors.append(f"{prefix} must have a unique dominant color")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match a declared semantic profile")
    output = None
    changed = 0
    if not errors:
        output = rule_mirror(grid)
        changed = sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b))
        if not public and changed / (len(grid) * len(grid[0])) < 0.01:
            errors.append("frame-and-stroke lesson must visibly change at least one percent of the canvas")
    result.update({"objects": facts, "output": output, "changed": changed, "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested and analysis["scene_profile"] != requested:
        errors.append(f"scene profile drifted from {requested} to {analysis['scene_profile']}")
    return errors


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _single_dimensions(profile, difficulty, rng):
    bands = {
        None: ((7, 9), (6, 10)),
        "easy": ((5, 7), (5, 8)),
        "medium": ((7, 9), (7, 10)),
        "hard": ((9, 13), (9, 14)),
    }
    square_range, rect_range = bands[difficulty]
    if profile == "square_odd_side":
        choices = [value for value in range(square_range[0], square_range[1] + 1) if value % 2]
        side = rng.choice(choices)
        return side, side
    if profile == "square_even_side":
        choices = [value for value in range(max(6, square_range[0]), square_range[1] + 2) if value % 2 == 0]
        side = rng.choice(choices)
        return side, side
    low, high = rect_range
    short = rng.randint(low, high)
    if profile in {"extreme_landscape", "extreme_portrait"}:
        long = min(22, short + rng.randint(5, 7))
    else:
        long = min(16, short + rng.randint(2, 4))
    return (short, long) if profile in {"landscape_center_row", "extreme_landscape"} else (long, short)


def _multi_dimensions(profile, difficulty, rng):
    bump = 0 if difficulty == "easy" else 1
    if profile == "mixed_parities":
        return [(5 + bump, 5 + bump), (6 + bump, 7 + bump), (7 + bump, 6 + bump)]
    first = (6 + bump, 6 + bump)
    second = (7 + bump, 9 + bump)
    if rng.randrange(2):
        second = second[::-1]
    return [first, second]


def _color_pairs(profile, count, rng):
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if profile == "shared_marker_color":
        return [(palette[index], palette[-1]) for index in range(count)]
    if profile == "cross_role_palette":
        return [(palette[0], palette[1]), (palette[1], palette[2])]
    return [(palette[2 * index], palette[2 * index + 1]) for index in range(count)]


def _place_specs(dimensions, colors, rng):
    count = len(dimensions)
    horizontal = count == 3 or bool(rng.randrange(2))
    gap = 1 if count == 3 else rng.randint(1, 3)
    if horizontal:
        content_h = max(height for height, _ in dimensions)
        content_w = sum(width for _, width in dimensions) + gap * (count - 1)
    else:
        content_h = sum(height for height, _ in dimensions) + gap * (count - 1)
        content_w = max(width for _, width in dimensions)
    margin_high = 2 if count == 3 else 3
    top, bottom, left, right = (rng.randint(1, margin_high) for _ in range(4))
    grid = [[0] * (content_w + left + right) for _ in range(content_h + top + bottom)]
    cursor = left if horizontal else top
    placed = []
    for (height, width), (main, marker) in zip(dimensions, colors):
        if horizontal:
            r1 = top + rng.randint(0, content_h - height)
            c1 = cursor
            cursor += width + gap
        else:
            r1 = cursor
            c1 = left + rng.randint(0, content_w - width)
            cursor += height + gap
        for row in range(r1, r1 + height):
            for col in range(c1, c1 + width):
                grid[row][col] = main
        placed.append((r1, c1, height, width, main, marker))
    return grid, placed


def _mark(grid, placed, profile, rng):
    for r1, c1, height, width, _, marker in placed:
        if profile == "border_marker_erased":
            positions = [(r1, c1 + rng.randint(1, width - 2))]
        else:
            count = rng.randint(2, 3) if profile == "multiple_marker_pixels" else 1
            candidates = [(row, col) for row in range(r1 + 1, r1 + height - 1) for col in range(c1 + 1, c1 + width - 1)]
            positions = rng.sample(candidates, count)
        for row, col in positions:
            grid[row][col] = marker


def _general_scene(ctx, profile):
    rng = ctx.draw_rng("geometry")
    if profile in {"multiple_objects", "shared_marker_color", "cross_role_palette", "mixed_parities"}:
        dimensions = _multi_dimensions(profile, ctx.difficulty, rng)
    else:
        dimensions = [_single_dimensions(profile, ctx.difficulty, rng)]
    colors = _color_pairs(profile, len(dimensions), rng)
    grid, placed = _place_specs(dimensions, colors, rng)
    _mark(grid, placed, profile, rng)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 3)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
