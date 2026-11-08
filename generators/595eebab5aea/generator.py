"""Inputs for area ranking, positional tie breaks, recoloring and centered stacking.

Labels belong to the unchanged Racket authority. The prediction functions below
are executable rival diagnostics, never an output-label source. See notes.md for
the bounded input domain and the five-demonstration lesson contract.
"""
from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "595eebab5aea"
TASK_ID = GENERATOR_ID
RULE_HASH = "5e9e9e076193"
VERSION = "3.0.2"
SUMMARY = (
    "Read three distinct rank colors left-to-right in row 0. Rank three "
    "separated monochrome body components by descending area, then bounding-box "
    "top and left ascending. Recolor their crops in rank order and stack with "
    "one blank row, centered with floor((maximum width - piece width)/2). "
    "Ties, narrow and wide crops, shape variation, and positional tie witnesses "
    "are ordinary generated inputs."
)
INVARIANTS = [
    "rectangular integer 0..9 grid, height 11..18 and width 12..18, background 0",
    "row 0 contains exactly three distinct rank colors; row 1 is blank",
    "exactly three distinct non-rank-colored, four-connected body components",
    "each body has 2..10 cells and a bounding box at most 5 by 5",
    "body bounding boxes have at least one blank row or column between them",
    "equal areas are lawful: ties use bounding-box top, then left, ascending",
]
_AREA_PATTERNS = ("distinct", "pair_tie", "all_tied")
_ALIGNMENT_PROFILES = ("narrow_gap", "wide_gap")
_POSITIONS = ("staggered", "paired_top", "same_top")
AXES = {
    "grid_h": {"type": "int", "default": "11..18; canonical anchor every third draw", "valid": "11..18"},
    "grid_w": {"type": "int", "default": "12..18; canonical anchor every third draw", "valid": "12..18"},
    "area_pattern": {"type": "str", "default": "scheduled, with all three patterns in the varied profile", "valid": "|".join(_AREA_PATTERNS)},
    "alignment_profile": {"type": "str", "default": "narrow_gap, wide_gap, wide_gap", "valid": "|".join(_ALIGNMENT_PROFILES)},
    "position_bias": {"type": "str", "default": "varied, staggered, same_top", "valid": "|".join(_POSITIONS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("varied", "center_and_area", "tie_breaks")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _choice(ctx, name, options, scheduled=None):
    # A scheduled default is a deterministic singleton choice. Explicit controls
    # still draw from their entire advertised domain and are never overwritten.
    choices = options if ctx.overrides.get(name) is not None or scheduled is None else (scheduled,)
    return ctx.draw_choice(name, choices)


def _polyomino(rng, area, width):
    """Grow a connected shape with exact area/width and height at most five."""
    cells = {(rng.randrange(5), 0)}
    while len(cells) < area:
        right = max(c for _, c in cells)
        missing_columns = width - right - 1
        if area - len(cells) == missing_columns:
            candidates = [(r, right + 1) for r, c in cells if c == right]
        else:
            candidates = {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= r + dr < 5 and 0 <= c + dc < width
                and (r + dr, c + dc) not in cells
            }
        cells.add(rng.choice(sorted(candidates)))
    top = min(r for r, _ in cells)
    return tuple(sorted((r - top, c) for r, c in cells))


def _general_shapes(ctx, area_pattern, alignment, width):
    rng = ctx.draw_rng("areas")
    if area_pattern == "distinct":
        areas = rng.sample(range(2, 11), 3)
    elif area_pattern == "pair_tie":
        tied = rng.randint(2, 10)
        areas = [tied, tied, rng.choice([n for n in range(2, 11) if n != tied])]
        rng.shuffle(areas)
    else:
        tied = rng.randint(3 if alignment == "wide_gap" else 2, 10)
        areas = [tied] * 3
    legal_widths = [range((n + 4) // 5, min(n, 5) + 1) for n in areas]
    widths = [ws for ws in product(*legal_widths)
              if sum(ws) + 2 <= width
              and ((max(ws) - min(ws) >= 2) == (alignment == "wide_gap"))]
    if not widths:
        raise RuntimeError("internal shape-domain error: no constructive width tuple")
    chosen = ctx.draw_rng("shape_widths").choice(widths)
    return [_polyomino(ctx.draw_rng(f"shape_{i}"), n, w)
            for i, (n, w) in enumerate(zip(areas, chosen))]


def _shapes(ctx, profile, area_pattern, alignment, position, width):
    # Profiles are witnessed in pixels, not merely tagged in a schedule.
    if (profile == "center_and_area" and area_pattern == "distinct"
            and alignment == "wide_gap" and position == "staggered"):
        rng = ctx.draw_rng("areas")
        areas = (rng.randint(2, 4), rng.randint(7, 10), rng.randint(5, 6))
        widths = (1, 4, rng.choice((2, 3)))
        return ([_polyomino(ctx.draw_rng(f"shape_{i}"), n, w)
                 for i, (n, w) in enumerate(zip(areas, widths))], "area_witness")
    if (profile == "tie_breaks" and area_pattern == "all_tied"
            and alignment == "wide_gap" and position == "same_top"):
        # Equal cell areas; left-to-right heights 3,5,2, widths 2,1,4,
        # and bounding-box areas 6,5,8 are all nonmonotone. Geometry cannot
        # silently substitute for the left-position tie rule in this scene.
        compact = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))
        elbow = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0))
        shapes = [compact, tuple((r, 0) for r in range(5)), elbow]
        for i in (0, 2):
            rng = ctx.draw_rng(f"shape_{i}")
            h, w = _dimensions(shapes[i])
            flip_rows, flip_columns = rng.randrange(2), rng.randrange(2)
            shapes[i] = tuple(sorted((h - 1 - r if flip_rows else r,
                                      w - 1 - c if flip_columns else c)
                                     for r, c in shapes[i]))
        return shapes, "tie_witness"
    return _general_shapes(ctx, area_pattern, alignment, width), None


def _dimensions(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _tops(ctx, shapes, position, mode, height):
    safe = list(range(2, height - max(_dimensions(s)[0] for s in shapes) + 1))
    rng = ctx.draw_rng("body_rows")
    if position == "same_top":
        return [rng.choice(safe)] * 3
    if position == "staggered":
        rows = rng.sample(safe, 3)
        return sorted(rows) if mode == "area_witness" else rows
    first, second = rng.sample(safe, 2)
    rows = [first, first, second]
    rng.shuffle(rows)
    return rows


def _separated(a, b):
    r, c, h, w = a
    rr, cc, hh, ww = b
    return r + h < rr or rr + hh < r or c + w < cc or cc + ww < c


def _columns(ctx, shapes, tops, width, mode):
    """Finite constructive search; no silently dropped shapes or retry cutoff."""
    dims = [_dimensions(s) for s in shapes]
    rng = ctx.draw_rng("body_columns")
    candidates = [rng.sample(range(width - w + 1), width - w + 1) for _, w in dims]
    order = sorted(range(3), key=lambda i: -dims[i][1])
    placed = {}

    def visit(depth):
        if depth == 3:
            return [placed[i][1] for i in range(3)]
        i = order[depth]
        h, w = dims[i]
        for col in candidates[i]:
            box = (tops[i], col, h, w)
            if any(not _separated(box, other) for other in placed.values()):
                continue
            placed[i] = box
            tie_order_ok = (mode != "tie_witness" or all(
                placed[a][1] < placed[b][1]
                for a in placed for b in placed if a < b))
            if tie_order_ok:
                result = visit(depth + 1)
                if result is not None:
                    return result
            del placed[i]
        return None

    result = visit(0)
    if result is None:
        # The width tuple admits a side-by-side packing with two blank columns,
        # so reaching this branch indicates an implementation defect.
        raise RuntimeError("constructive placement failed; refusing an incomplete grid")
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer, not bool")
    for name in ("area_pattern", "alignment_profile", "position_bias"):
        if overrides.get(name) is not None and type(overrides[name]) is not str:
            raise ValueError(f"{name} must be a string")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    anchor = ctx.draw_rng("canonical_dimensions").choice(((13, 14), (14, 15), (14, 16), (13, 15)))
    heights = tuple(range(11, 19))
    widths = tuple(range(12, 19))
    if profile != "varied":
        heights += ((11, 12, 13) if difficulty == "easy" else
                    (16, 17, 18) if difficulty == "hard" else (13, 14, 15)) * 2
        widths += ((12, 13, 14) if difficulty == "easy" else
                   (16, 17, 18) if difficulty == "hard" else (14, 15, 16)) * 2
    h = _choice(ctx, "grid_h", heights, anchor[0] if profile == "varied" else None)
    w = _choice(ctx, "grid_w", widths, anchor[1] if profile == "varied" else None)
    area = _choice(ctx, "area_pattern", _AREA_PATTERNS,
                   "distinct" if profile == "center_and_area" else
                   "all_tied" if profile == "tie_breaks" else None)
    alignment = _choice(ctx, "alignment_profile", _ALIGNMENT_PROFILES,
                        "narrow_gap" if profile == "varied" else "wide_gap")
    position = _choice(ctx, "position_bias", _POSITIONS,
                       "staggered" if profile == "center_and_area" else
                       "same_top" if profile == "tie_breaks" else None)
    shapes, mode = _shapes(ctx, profile, area, alignment, position, w)
    tops = _tops(ctx, shapes, position, mode, h)
    columns = _columns(ctx, shapes, tops, w, mode)
    colors = ctx.draw_rng("palette").sample(range(1, 10), 6)
    rank_colors = colors[:3]
    if profile != "varied" and rank_colors == sorted(rank_colors):
        rank_colors[0], rank_colors[1] = rank_colors[1], rank_colors[0]
    body_colors = colors[3:]
    if mode == "tie_witness" and body_colors in (sorted(body_colors), sorted(body_colors, reverse=True)):
        body_colors[0], body_colors[1] = body_colors[1], body_colors[0]
    rank_slots = sorted(ctx.draw_rng("rank_columns").sample(range(w - 2), 3))
    g = full_grid(h, w, 0)
    for i, color in enumerate(rank_colors):
        g[0][rank_slots[i] + i] = color
    for i, shape in enumerate(shapes):
        for dr, dc in shape:
            g[tops[i] + dr][columns[i] + dc] = body_colors[i]
    return g


def _body_components(grid):
    seen, components = set(), []
    h, w = len(grid), len(grid[0])
    for r in range(2, h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = rr + dr, cc + dc
                    if (2 <= p[0] < h and 0 <= p[1] < w and p not in seen
                            and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        stack.append(p)
            top, left = min(x[0] for x in cells), min(x[1] for x in cells)
            bottom, right = max(x[0] for x in cells), max(x[1] for x in cells)
            components.append({"color": color, "cells": cells, "area": len(cells),
                               "top": top, "left": left, "bottom": bottom,
                               "height": bottom - top + 1, "width": right - left + 1})
    return components


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be literal integer colors 0..9"]
    h, w = len(grid), len(grid[0])
    if not (11 <= h <= 18 and 12 <= w <= 18):
        return ["outside bounded canvas domain: height 11..18, width 12..18"]
    ranks = [v for v in grid[0] if v]
    errors = []
    if len(ranks) != 3 or len(set(ranks)) != 3:
        errors.append("row 0 must contain exactly three distinct rank-color cells")
    if any(grid[1]):
        errors.append("row 1 must be a blank separator")
    bodies = _body_components(grid)
    if len(bodies) != 3:
        errors.append(f"expected three body components, got {len(bodies)}")
    body_colors = [o["color"] for o in bodies]
    if len(set(body_colors)) != len(body_colors) or set(body_colors) & set(ranks):
        errors.append("body colors must be distinct and disjoint from rank colors")
    if any(not 2 <= o["area"] <= 10 or o["height"] > 5 or o["width"] > 5 for o in bodies):
        errors.append("each body must have 2..10 cells within a 5 by 5 bounding box")
    boxes = [(o["top"], o["left"], o["height"], o["width"]) for o in bodies]
    if any(not _separated(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:]):
        errors.append("body bounding boxes must have a blank row or column between them")
    return errors


def strict_canonical_like(grid):
    """Lawful inputs in the stated task domain, including all canonical ties."""
    return self_check(grid)


def observe_overrides(grid):
    bodies = _body_components(grid)
    n_areas = len({o["area"] for o in bodies})
    n_tops = len({o["top"] for o in bodies})
    gap = max(o["width"] for o in bodies) - min(o["width"] for o in bodies)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "area_pattern": {3: "distinct", 2: "pair_tie", 1: "all_tied"}[n_areas],
            "alignment_profile": "wide_gap" if gap >= 2 else "narrow_gap",
            "position_bias": {3: "staggered", 2: "paired_top", 1: "same_top"}[n_tops]}


def _predict(grid, *, order="area", alignment="floor", sorted_colors=False):
    """Explanatory task model used only to define/test rivals, never label data."""
    bodies = _body_components(grid)
    raster = lambda o: (o["top"], o["left"])
    area = lambda o: (-o["area"], o["top"], o["left"])
    if order == "rightmost_tie":
        bodies.sort(key=lambda o: (-o["area"], o["top"], -o["left"]))
    elif order == "bottom_tie":
        bodies.sort(key=lambda o: (-o["area"], o["bottom"], o["left"]))
    elif order == "taller_tie":
        bodies.sort(key=lambda o: (-o["area"], o["top"], -o["height"], o["left"]))
    elif order == "narrower_tie":
        bodies.sort(key=lambda o: (-o["area"], o["top"], o["width"], o["left"]))
    elif order == "bbox_descending_tie":
        bodies.sort(key=lambda o: (-o["area"], o["top"],
                                   -o["height"] * o["width"], o["left"]))
    elif order == "area_then_bbox_descending":
        bodies.sort(key=lambda o: (-o["area"], -o["height"] * o["width"],
                                   o["top"], o["left"]))
    elif order == "color_ascending_tie":
        bodies.sort(key=lambda o: (-o["area"], o["top"], o["color"], o["left"]))
    elif order == "color_descending_tie":
        bodies.sort(key=lambda o: (-o["area"], o["top"], -o["color"], o["left"]))
    elif order == "raster":
        bodies.sort(key=raster)
    elif order == "largest_then_raster":
        first = min(bodies, key=area)
        bodies = [first] + sorted([o for o in bodies if o is not first], key=raster)
    elif order == "ascending_area":
        bodies.sort(key=lambda o: (o["area"], o["top"], o["left"]))
    else:
        bodies.sort(key=area)
    ranks = [v for v in grid[0] if v]
    if sorted_colors:
        ranks.sort()
    width = max(o["width"] for o in bodies)
    out = full_grid(sum(o["height"] for o in bodies) + 2, width, 0)
    top = 0
    for obj, color in zip(bodies, ranks):
        gap = width - obj["width"]
        left = 0 if alignment == "left" else gap if alignment == "right" else (
            (gap + 1) // 2 if alignment == "ceil" else gap // 2)
        for r, c in obj["cells"]:
            out[top + r - obj["top"]][left + c - obj["left"]] = color
        top += obj["height"] + 1
    return out


def _left_align(g):
    return _predict(g, alignment="left")


def _tie_rightmost(g):
    return _predict(g, order="rightmost_tie")


def _tie_bottom_first(g):
    return _predict(g, order="bottom_tie")


def _largest_then_raster(g):
    return _predict(g, order="largest_then_raster")


def _tie_taller_first(g):
    return _predict(g, order="taller_tie")


def _tie_narrower_first(g):
    return _predict(g, order="narrower_tie")


def _tie_bbox_area_descending(g):
    return _predict(g, order="bbox_descending_tie")


def _area_then_bbox_descending(g):
    return _predict(g, order="area_then_bbox_descending")


def _tie_color_ascending(g):
    return _predict(g, order="color_ascending_tie")


def _tie_color_descending(g):
    return _predict(g, order="color_descending_tie")


def _raster_order(g):
    return _predict(g, order="raster")


def _ascending_area(g):
    return _predict(g, order="ascending_area")


def _sorted_rank_colors(g):
    return _predict(g, sorted_colors=True)


def _right_align(g):
    return _predict(g, alignment="right")


def _ceil_center(g):
    return _predict(g, alignment="ceil")


CANONICAL_SHORTCUTS = {
    "left_align": _left_align, "tie_rightmost": _tie_rightmost,
    "tie_bottom_first": _tie_bottom_first, "largest_then_raster": _largest_then_raster,
    "tie_taller_first": _tie_taller_first, "tie_narrower_first": _tie_narrower_first,
    "tie_color_ascending": _tie_color_ascending, "tie_color_descending": _tie_color_descending,
    "tie_bbox_area_descending": _tie_bbox_area_descending,
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS, "raster_order": _raster_order,
    "ascending_area": _ascending_area, "sorted_rank_colors": _sorted_rank_colors,
    "right_align": _right_align, "ceil_center": _ceil_center,
    "area_then_bbox_descending": _area_then_bbox_descending,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _witness(rival):
    # The semantic gate independently checks each claimed disagreement against
    # Racket. These predicates alone are not authority evidence.
    return lambda grid: rival(grid) != _predict(grid)


SEMANTIC_WITNESSES = {name: _witness(rival) for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}
