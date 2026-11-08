"""Semantic generator for ARC task b7e4aaffabac.

Find the two solid monochrome rectangles.  If their columns are disjoint,
fill their column gap with color 8 on the interior of their shared row span.
Otherwise fill their row gap on the interior of their shared column span.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "b7e4aaffabac"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "ac5d2330da57"
SUMMARY = "Bridge two separated solid rectangles with color 8 inside the shrunken overlap of their facing spans."
INVARIANTS = [
    "the literal background is color 0",
    "there are exactly two solid monochrome 4-connected rectangles",
    "rectangle colors are distinct and exclude 0 and 8",
    "the rectangles are separated on exactly one axis and overlap by at least three cells on the other",
    "the output changes exactly the nonempty rectangular bridge region to color 8",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "horizontal_aligned",
    "horizontal_offset",
    "horizontal_edge",
    "vertical_aligned",
    "vertical_offset",
    "vertical_edge",
    "minimal_overlap",
    "wide_gap",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and eight observable bridge geometries",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "0000000000/0444000000/0444000000/0444000666/0444000666/0444000666/0444000666/0444000666/0444000000/0000000000",
    "public_2": "0000000000/0222200000/0222200000/0222200000/0000000000/0000000000/0000000000/7777770000/7777770000/7777770000",
    "public_3": "3333333330/3333333330/3333333330/0000000000/0000000000/0000000000/0000000000/0000000000/0009999990/0009999990",
    "public_4": "1111000000/1111000222/1111000222/1111000222/1111000222/1111000222/1111000222/1111000000/0000000000/0000000000",
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


def _objects(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        seed = min(unseen)
        color = grid[seed[0]][seed[1]]
        stack = [seed]
        cells = set()
        while stack:
            row, col = stack.pop()
            if (row, col) not in unseen or grid[row][col] != color:
                continue
            unseen.remove((row, col))
            cells.add((row, col))
            stack.extend(
                (rr, cc)
                for rr, cc in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if (rr, cc) in unseen
            )
        result.append({"color": color, "cells": cells})
    return result


def _feature(obj):
    rows = [row for row, _ in obj["cells"]]
    cols = [col for _, col in obj["cells"]]
    r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
    rectangle = {(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)}
    return {
        "color": obj["color"],
        "cells": obj["cells"],
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "height": r2 - r1 + 1,
        "width": c2 - c1 + 1,
        "solid": obj["cells"] == rectangle,
    }


def _bridge_geometry(first, second):
    columns_disjoint = first["c2"] < second["c1"] or second["c2"] < first["c1"]
    rows_disjoint = first["r2"] < second["r1"] or second["r2"] < first["r1"]
    if columns_disjoint:
        left, right = sorted((first, second), key=lambda item: item["c1"])
        lo, hi = max(left["r1"], right["r1"]) + 1, min(left["r2"], right["r2"]) - 1
        start, end = left["c2"] + 1, right["c1"] - 1
        cells = {(row, col) for row in range(lo, hi + 1) for col in range(start, end + 1)}
        return {
            "orientation": "horizontal",
            "ordered": (left, right),
            "gap": end - start + 1,
            "raw_overlap": min(left["r2"], right["r2"]) - max(left["r1"], right["r1"]) + 1,
            "aligned": (left["r1"], left["r2"]) == (right["r1"], right["r2"]),
            "rows_disjoint": rows_disjoint,
            "cells": cells,
        }
    top, bottom = sorted((first, second), key=lambda item: item["r1"])
    lo, hi = max(top["c1"], bottom["c1"]) + 1, min(top["c2"], bottom["c2"]) - 1
    start, end = top["r2"] + 1, bottom["r1"] - 1
    cells = {(row, col) for row in range(start, end + 1) for col in range(lo, hi + 1)}
    return {
        "orientation": "vertical",
        "ordered": (top, bottom),
        "gap": end - start + 1,
        "raw_overlap": min(top["c2"], bottom["c2"]) - max(top["c1"], bottom["c1"]) + 1,
        "aligned": (top["c1"], top["c2"]) == (bottom["c1"], bottom["c2"]),
        "rows_disjoint": rows_disjoint,
        "cells": cells,
    }


def _paint_bridge(grid, cells):
    output = [list(row) for row in grid]
    for row, col in cells:
        output[row][col] = 8
    return output


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    features = [_feature(obj) for obj in _objects(grid)]
    if len(features) < 2:
        raise ValueError("expected at least two nonzero objects")
    geometry = _bridge_geometry(features[0], features[1])
    return _paint_bridge(grid, geometry["cells"])


def _general_profile(geometry, edge_touch):
    if geometry["raw_overlap"] == 3:
        return "minimal_overlap"
    if geometry["gap"] >= 4:
        return "wide_gap"
    prefix = geometry["orientation"]
    if edge_touch:
        return f"{prefix}_edge"
    return f"{prefix}_{'aligned' if geometry['aligned'] else 'offset'}"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    if not any(value == 0 for row in grid for value in row):
        errors.append("expected literal-zero background")
    features = [_feature(obj) for obj in _objects(grid)]
    if len(features) != 2:
        errors.append(f"expected exactly two nonzero objects; got {len(features)}")
        return result
    if any(not feature["solid"] for feature in features):
        errors.append("both objects must be solid rectangles")
    colors = [feature["color"] for feature in features]
    if len(set(colors)) != 2 or any(color in (0, 8) for color in colors):
        errors.append("rectangle colors must be distinct and exclude 0 and 8")
    geometry = _bridge_geometry(*features)
    columns_disjoint = features[0]["c2"] < features[1]["c1"] or features[1]["c2"] < features[0]["c1"]
    rows_disjoint = geometry["rows_disjoint"]
    if columns_disjoint == rows_disjoint:
        errors.append("rectangles must be separated on exactly one axis")
    if geometry["gap"] < 1:
        errors.append("rectangle gap must contain at least one cell")
    if geometry["raw_overlap"] < 3 or not geometry["cells"]:
        errors.append("facing spans must overlap by at least three cells")
    height, width = len(grid), len(grid[0])
    edge_touch = any(
        feature["r1"] == 0 or feature["c1"] == 0 or feature["r2"] == height - 1 or feature["c2"] == width - 1
        for feature in features
    )
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(geometry, edge_touch)
    if profile not in SCENE_PROFILES:
        errors.append("bridge geometry does not match a declared scene profile")
    output = _paint_bridge(grid, geometry["cells"])
    result.update(
        {
            "features": features,
            "orientation": geometry["orientation"],
            "ordered": geometry["ordered"],
            "gap": geometry["gap"],
            "raw_overlap": geometry["raw_overlap"],
            "band_span": geometry["raw_overlap"] - 2,
            "aligned": geometry["aligned"],
            "edge_touch": edge_touch,
            "bridge_cells": geometry["cells"],
            "bridge_area": len(geometry["cells"]),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
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


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _horizontal_scene(rng, height, width, profile, colors):
    minimal = profile == "minimal_overlap"
    wide = profile == "wide_gap"
    edge = profile == "horizontal_edge"
    aligned = profile == "horizontal_aligned" or (profile in ("horizontal_edge", "wide_gap") and rng.choice((True, False)))
    if aligned:
        overlap = 3 if minimal else rng.randint(4, min(8, height - 2))
        span = overlap
        union = span
        extra_left = extra_right = 0
    else:
        extra_left, extra_right = rng.randint(1, 2), rng.randint(1, 2)
        overlap = 3 if minimal else rng.randint(4, min(8, height - extra_left - extra_right - 2))
        union = overlap + extra_left + extra_right
    row_margin = rng.randint(1, max(1, height - union - 1))
    if aligned:
        first_rows = second_rows = (row_margin, row_margin + overlap - 1)
    else:
        first_rows = (row_margin, row_margin + overlap + extra_left - 1)
        second_rows = (row_margin + extra_left, row_margin + union - 1)

    gap = rng.randint(4, min(7, width - 6)) if wide else rng.randint(1, 3)
    max_total = width if edge else width - 2
    left_width = rng.randint(2, min(6, max_total - gap - 2))
    right_width = rng.randint(2, min(6, max_total - gap - left_width))
    total = left_width + gap + right_width
    if edge:
        start = 0 if rng.choice((True, False)) else width - total
    else:
        start = rng.randint(1, width - total - 1)
    left_cols = start, start + left_width - 1
    right_cols = left_cols[1] + gap + 1, left_cols[1] + gap + right_width

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, rows, cols in ((colors[0], first_rows, left_cols), (colors[1], second_rows, right_cols)):
        for row in range(rows[0], rows[1] + 1):
            for col in range(cols[0], cols[1] + 1):
                grid[row][col] = color
    return grid


def _general_scene(ctx, profile):
    ranges = {
        None: (12, 22),
        "easy": (12, 16),
        "medium": (16, 23),
        "hard": (23, 30),
    }
    lo, hi = ranges[ctx.difficulty]
    height = ctx.draw_int("canvas_height", lo, hi)
    width = ctx.draw_int("canvas_width", lo, hi)
    colors = ctx.draw_distinct_colors("rectangle_colors", n=2, exclude={0, 8})
    rng = ctx.draw_rng("geometry")
    if profile.startswith("vertical_"):
        horizontal = profile.replace("vertical_", "horizontal_", 1)
        return _transpose(_horizontal_scene(rng, width, height, horizontal, colors))
    if profile in ("minimal_overlap", "wide_gap") and rng.choice((True, False)):
        return _transpose(_horizontal_scene(rng, width, height, profile, colors))
    return _horizontal_scene(rng, height, width, profile, colors)


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
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal invalid scene: {errors}")
    if observe_overrides(grid) != {"scene_profile": profile}:
        raise AssertionError(f"profile construction drift for {profile}")
    return grid
