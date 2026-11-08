"""Semantic generator for ARC task b570c79ec730.

Treat zero as background and extract monochrome 4-connected components.  For
each component, erase only cells that lie strictly inside that component's
bounding box.  Cells on any bbox edge remain unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "b570c79ec730"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "98453598f105"
SUMMARY = "Erase each component's strictly bbox-interior cells while preserving its bbox-edge cells."
INVARIANTS = [
    "background is literal color 0",
    "objects are monochrome 4-connected components",
    "only object cells strictly inside their own bbox are erased",
    "bbox-edge cells, colors, grid dimensions, and background cells are preserved",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "single_rectangle",
    "many_rectangles",
    "tall_and_wide",
    "same_color_separate",
    "thin_with_thick",
    "notched_border",
    "border_touching",
    "mixed_components",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and eight observable component lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "0000000/0222220/0222220/0222220/0222220/0000000/0000000/0000000",
    "public_2": "0000000000000000/0888800000000000/0888800000000000/0888803333333000/0000003333333000/0000003333333000/0000003333333000/0000003333333000/0000000000000000/0000000000000000/0066666660007770/0066666660007770/0066666660007770/0066666660007770/0000000000007770/0000000000000000/0000000000000000/0000000000000000",
    "public_3": "000000000000/005555555500/005555555500/005555555500/005555555500/000000000000/044444400000/044444400000/044444400000/044444400000/000000000000",
    "public_4": "0000000000000000000/0888888000066660000/0888888000066660000/0888888000066660000/0000000000000000000/0044444400000000000/0044444400111111110/0044444400111111110/0044444400111111110/0044444400111111110/0044444400111111110/0044444400111111110/0000000000000000000/0000033333000000000/0000033333000000000/0000033333000000000/0000000000000000000",
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
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        seed = min(unseen)
        color = grid[seed[0]][seed[1]]
        stack = [seed]
        cells = set()
        while stack:
            cell = stack.pop()
            if cell not in unseen or grid[cell[0]][cell[1]] != color:
                continue
            unseen.remove(cell)
            cells.add(cell)
            row, col = cell
            stack.extend(
                neighbor
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if neighbor in unseen
            )
        result.append({"color": color, "cells": cells})
    return result


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _feature(component):
    r1, c1, r2, c2 = _bbox(component["cells"])
    height, width = r2 - r1 + 1, c2 - c1 + 1
    interior = {
        (row, col)
        for row, col in component["cells"]
        if r1 < row < r2 and c1 < col < c2
    }
    boundary = component["cells"] - interior
    perimeter = height * width if height <= 2 or width <= 2 else 2 * height + 2 * width - 4
    return {
        "color": component["color"],
        "cells": component["cells"],
        "bbox": (r1, c1, r2, c2),
        "height": height,
        "width": width,
        "area": height * width,
        "size": len(component["cells"]),
        "solid": len(component["cells"]) == height * width,
        "interior_cells": interior,
        "boundary_cells": boundary,
        "missing_boundary": perimeter - len(boundary),
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for component in _components(grid):
        for row, col in _feature(component)["interior_cells"]:
            output[row][col] = 0
    return output


def _general_profile(features, height, width):
    thin = [feature for feature in features if feature["height"] <= 2 or feature["width"] <= 2]
    notched = [feature for feature in features if feature["missing_boundary"] > 0]
    thick = [feature for feature in features if feature["interior_cells"]]
    colors = [feature["color"] for feature in features]
    touches = any(
        r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1
        for r1, c1, r2, c2 in (feature["bbox"] for feature in features)
    )
    if thin and notched and thick:
        return "mixed_components"
    if thin and thick:
        return "thin_with_thick"
    if notched and thick:
        return "notched_border"
    if touches and thick:
        return "border_touching"
    if len(colors) != len(set(colors)) and thick:
        return "same_color_separate"
    if len(features) >= 3 and all(feature["solid"] for feature in features):
        return "many_rectangles"
    if (
        len(features) == 2
        and any(feature["height"] > feature["width"] for feature in features)
        and any(feature["width"] > feature["height"] for feature in features)
    ):
        return "tall_and_wide"
    if len(features) == 1 and features[0]["solid"] and features[0]["interior_cells"]:
        return "single_rectangle"
    return None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    components = _components(grid)
    features = [_feature(component) for component in components]
    if not any(value == 0 for row in grid for value in row):
        errors.append("expected at least one literal-zero background cell")
    if not features:
        errors.append("expected at least one non-background component")
    if not any(feature["interior_cells"] for feature in features):
        errors.append("expected at least one component with a strictly interior cell")
    height, width = len(grid), len(grid[0])
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(features, height, width)
    if profile not in SCENE_PROFILES:
        errors.append("component structure does not match a declared scene profile")
    output = rule_mirror(grid)
    result.update(
        {
            "components": components,
            "features": features,
            "component_count": len(features),
            "transformed_components": sum(bool(feature["interior_cells"]) for feature in features),
            "unchanged_components": sum(not feature["interior_cells"] for feature in features),
            "erased_cells": sum(len(feature["interior_cells"]) for feature in features),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    return profile if profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _solid(height, width):
    return {(row, col) for row in range(height) for col in range(width)}


def _notched(height, width, rng):
    cells = _solid(height, width)
    options = (
        [(0, col) for col in range(1, width - 1)]
        + [(height - 1, col) for col in range(1, width - 1)]
        + [(row, 0) for row in range(1, height - 1)]
        + [(row, width - 1) for row in range(1, height - 1)]
    )
    cells.remove(rng.choice(options))
    interiors = [(row, col) for row in range(1, height - 1) for col in range(1, width - 1)]
    if len(interiors) > 3 and rng.randrange(2):
        cells.remove(rng.choice(interiors))
    return cells


def _thin(length, vertical, thickness):
    height, width = (length, thickness) if vertical else (thickness, length)
    return _solid(height, width)


def _shape_specs(rng, profile, band):
    limits = {"easy": 6, "medium": 7, "hard": 8}
    maximum = limits[band]
    colors = list(range(1, 10))
    rng.shuffle(colors)

    def rect(low=3, high=maximum):
        return _solid(rng.randint(low, high), rng.randint(low, high))

    if profile == "single_rectangle":
        return [(rect(), colors[0], False)]
    if profile == "many_rectangles":
        count = {"easy": 3, "medium": 4, "hard": 5}[band]
        return [(rect(3, min(5, maximum)), colors[index], False) for index in range(count)]
    if profile == "tall_and_wide":
        long = rng.randint(max(5, maximum - 1), maximum)
        short = rng.randint(3, min(4, maximum))
        return [(_solid(long, short), colors[0], False), (_solid(short, long), colors[1], False)]
    if profile == "same_color_separate":
        count = {"easy": 2, "medium": 3, "hard": 4}[band]
        return [(rect(3, min(5, maximum)), colors[0], False) for _ in range(count)]
    if profile == "thin_with_thick":
        thin = _thin(rng.randint(4, maximum), bool(rng.randrange(2)), rng.randint(1, 2))
        return [(thin, colors[0], False), (rect(4, maximum), colors[1], False)]
    if profile == "notched_border":
        count = {"easy": 1, "medium": 2, "hard": 3}[band]
        result = [(_notched(rng.randint(4, maximum), rng.randint(4, maximum), rng), colors[0], False)]
        result.extend((rect(3, min(5, maximum)), colors[index], False) for index in range(1, count))
        return result
    if profile == "border_touching":
        count = {"easy": 1, "medium": 2, "hard": 3}[band]
        result = [(rect(4, maximum), colors[0], True)]
        result.extend((rect(3, min(5, maximum)), colors[index], False) for index in range(1, count))
        return result
    if profile == "mixed_components":
        notch = _notched(rng.randint(4, maximum), rng.randint(4, maximum), rng)
        thin = _thin(rng.randint(4, maximum), bool(rng.randrange(2)), rng.randint(1, 2))
        return [(notch, colors[0], False), (thin, colors[1], False), (rect(3, min(5, maximum)), colors[2], False)]
    raise ValueError(f"unknown general profile: {profile!r}")


def _shape_bbox(cells):
    return _bbox(cells)


def _place_shapes(rng, height, width, specs):
    grid = [[0] * width for _ in range(height)]
    boxes = []
    for cells, color, force_border in specs:
        local_r1, local_c1, local_r2, local_c2 = _shape_bbox(cells)
        shape_h, shape_w = local_r2 - local_r1 + 1, local_c2 - local_c1 + 1
        positions = [
            (row, col)
            for row in range(height - shape_h + 1)
            for col in range(width - shape_w + 1)
            if (
                (force_border and (row == 0 or col == 0 or row + shape_h == height or col + shape_w == width))
                or (
                    not force_border
                    and row >= 1
                    and col >= 1
                    and row + shape_h < height
                    and col + shape_w < width
                )
            )
        ]
        rng.shuffle(positions)
        placed = False
        for top, left in positions:
            box = top, left, top + shape_h - 1, left + shape_w - 1
            if any(
                not (
                    box[2] + 1 < other[0]
                    or other[2] + 1 < box[0]
                    or box[3] + 1 < other[1]
                    or other[3] + 1 < box[1]
                )
                for other in boxes
            ):
                continue
            for row, col in cells:
                grid[top + row - local_r1][left + col - local_c1] = color
            boxes.append(box)
            placed = True
            break
        if not placed:
            return None
    return grid


def _general(rng, profile, band):
    ranges = {"easy": (12, 15), "medium": (16, 20), "hard": (21, 26)}
    low, high = ranges[band]
    for _ in range(20):
        height, width = rng.randint(low, high), rng.randint(low, high)
        grid = _place_shapes(rng, height, width, _shape_specs(rng, profile, band))
        if grid is not None:
            return grid
    raise ValueError(f"could not place scene profile {profile!r}")


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = requested or ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)],
    )
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
