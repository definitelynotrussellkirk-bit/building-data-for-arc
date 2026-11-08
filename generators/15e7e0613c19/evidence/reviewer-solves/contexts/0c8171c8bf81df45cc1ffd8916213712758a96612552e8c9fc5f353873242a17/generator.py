"""Crop monochrome 4-connected objects and pack them horizontally, top aligned.

Sort by (pixel count, bbox height, bbox width, numeric color); keep one zero
column between crops. Zero is background; all colors 1..9 can be foreground.
The five exact axes are observable. palette_size and n_distinct_colors are
aliases counting ALL realized colors, including zero; require colors <= n+1.

Default teaching phases separate pixel count from bbox area, height/width ties,
and color ties/repeated-color segmentation. Six consecutive labeled pairs give
two of every phase; EXAMPLES_NEEDED=5 permits each pair to be held out once.
This only distinguishes the declared finite rivals, not all possible rules.
Default packed outputs shrink in both dimensions, as in the canonical pairs.
Count overrides outside the phase's n/colors use a lawful general sampler and
are outside that curriculum guarantee. Dimension overrides retain the phases.
"""
from __future__ import annotations

from itertools import permutations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "15e7e0613c19"
VERSION = "1.2.0"
RULE_HASH = "1f1935df6364"
SUMMARY = "Horizontal gallery sorted by pixel count, height, width, then color."
INVARIANTS = [
    "zero background is a strict majority; nonzero integer colors are 1..9",
    "2..5 monochrome 4-connected motifs, each 1..5 pixels, separated by background",
    "cropped horizontal output has at most 30 rows and columns",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles or rng 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "canonical profiles or rng 9..16", "valid": "9..16"},
    "n": {"type": "int", "default": "3 or 4 by teaching phase", "valid": "2..5"},
    "n_distinct_colors": {"type": "int", "default": "4 including zero", "valid": "2..6"},
    "palette_size": {"type": "int", "default": "alias of n_distinct_colors, including zero", "valid": "2..6"},
}
# These tuples may be rejected only when aliases differ or colors > n+1.
# Structured exceptions also retain the specific conflicting axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("palette_size", "n_distinct_colors"), ("n", "palette_size"), ("n", "n_distinct_colors"),
]
EXAMPLES_NEEDED = 5
SCHEDULE_PROFILES = (0, 1, 2)
# Only the semantic profile repeats: palettes/layouts/sizes do not have period 3.


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["expected a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["expected nonempty list rows"]
    if len({len(row) for row in grid}) != 1:
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["input dimensions exceed 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["colors must be integer values 0..9, excluding bool"]
    return []


def _objects(grid, *, merge_colors=False):
    """Independent Python mirror of the canonical row-major monochrome scan."""
    h, w = len(grid), len(grid[0])
    seen, objects = set(), []
    by_color = {}
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            cells, todo = [], [(r, c)]
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            if merge_colors:
                by_color.setdefault(color, []).extend(cells)
            else:
                objects.append((color, cells))
    if merge_colors:
        objects = list(by_color.items())
    result = []
    for color, cells in objects:
        top, left = min(r for r, _ in cells), min(c for _, c in cells)
        height = max(r for r, _ in cells) - top + 1
        width = max(c for _, c in cells) - left + 1
        pattern = [[0] * width for _ in range(height)]
        for r, c in cells:
            pattern[r - top][c - left] = color
        result.append({"color": color, "cells": cells, "area": len(cells),
                       "height": height, "width": width, "pattern": pattern})
    return result


def _key(obj):
    return obj["area"], obj["height"], obj["width"], obj["color"]


def _pack(objects, key=_key):
    objects = sorted(objects, key=key)
    if not objects:
        return [[0]]
    height = max(o["height"] for o in objects)
    width = sum(o["width"] for o in objects) + len(objects) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for obj in objects:
        for r, row in enumerate(obj["pattern"]):
            out[r][left:left + len(row)] = row
        left += obj["width"] + 1
    return out


def solve_reference(grid):
    """Authoring/test mirror only; runtime labels still come from unchanged Racket."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _pack(_objects(grid))


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    objects = _objects(grid)
    if not 2 <= len(objects) <= 5:
        errors.append("expected 2..5 connected motifs")
    if sum(v == 0 for row in grid for v in row) <= h * w // 2:
        errors.append("zero background must be a strict majority")
    if any(not 1 <= o["area"] <= 5 for o in objects):
        errors.append("motif pixel counts must be 1..5")
    owner = {cell: i for i, obj in enumerate(objects) for cell in obj["cells"]}
    if any((r + dr, c + dc) in owner and owner[r + dr, c + dc] != i
           for (r, c), i in owner.items() for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
        errors.append("distinct motifs must have a background moat")
    if objects and (max(o["height"] for o in objects) > 30
                    or sum(o["width"] for o in objects) + len(objects) - 1 > 30):
        errors.append("packed output dimensions exceed 30")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in ((7, 9), (7, 10), (8, 11)):
        return ["outside observed canonical input profiles"]
    if len({v for row in grid for v in row}) != 4:
        return ["canonical profiles use four colors including background"]
    return []


def observe_overrides(grid):
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    colors = len({v for row in grid for v in row})
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n": len(_objects(grid)),
            "n_distinct_colors": colors, "palette_size": colors}


def rival_bbox_area(grid):
    return _pack(_objects(grid), lambda o: (o["height"] * o["width"], o["height"], o["width"], o["color"]))


def rival_ignore_height(grid):
    return _pack(_objects(grid), lambda o: (o["area"], o["width"], o["color"]))


def rival_ignore_width(grid):
    return _pack(_objects(grid), lambda o: (o["area"], o["height"], o["color"]))


def rival_ignore_color(grid):
    return _pack(_objects(grid), lambda o: (o["area"], o["height"], o["width"]))


def rival_merge_by_color(grid):
    return _pack(_objects(grid, merge_colors=True))


CANONICAL_SHORTCUTS = {
    "bbox_area": rival_bbox_area, "ignore_height": rival_ignore_height,
    "ignore_width": rival_ignore_width, "ignore_color": rival_ignore_color,
    "merge_by_color": rival_merge_by_color,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def _witness(grid, rival, condition):
    if self_check(grid):
        return False
    objects = _objects(grid)
    return bool(condition(objects) and solve_reference(grid) != rival(grid))


def witness_pixel_bbox(grid):
    return _witness(grid, rival_bbox_area, lambda obs: any(
        (a["area"] - b["area"]) * (a["height"] * a["width"] - b["height"] * b["width"]) < 0
        for a in obs for b in obs))


def witness_height_tie(grid):
    return _witness(grid, rival_ignore_height, lambda obs: any(
        a["area"] == b["area"] and a["height"] != b["height"] for a in obs for b in obs))


def witness_width_tie(grid):
    return _witness(grid, rival_ignore_width, lambda obs: any(
        (a["area"], a["height"]) == (b["area"], b["height"]) and a["width"] != b["width"]
        for a in obs for b in obs))


def witness_color_tie(grid):
    return _witness(grid, rival_ignore_color, lambda obs: any(
        (a["area"], a["height"], a["width"]) == (b["area"], b["height"], b["width"])
        and a["color"] != b["color"] for a in obs for b in obs))


def witness_repeated_color(grid):
    return _witness(grid, rival_merge_by_color, lambda obs: len({o["color"] for o in obs}) < len(obs))


SEMANTIC_WITNESSES = {
    "pixel_bbox": witness_pixel_bbox, "height_tie": witness_height_tie,
    "width_tie": witness_width_tie, "color_tie": witness_color_tie,
    "repeated_color": witness_repeated_color,
}
WITNESS_RIVALS = {"pixel_bbox": ["bbox_area"], "height_tie": ["ignore_height"],
                  "width_tie": ["ignore_width"], "color_tie": ["ignore_color"],
                  "repeated_color": ["merge_by_color"]}


def lesson_identifiable(demos, query):
    """Check only declared rivals; finite evidence is not universal induction."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(p["input"]) == p["output"] for p in demos) and rival(query["input"]) != query["output"]:
            reasons.append("surviving declared rival: " + name)
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return sample_index % 3


def _reflect(shape, rng):
    height, width = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
    flip_r, flip_c = rng.choice((False, True)), rng.choice((False, True))
    return [(height - 1 - r if flip_r else r, width - 1 - c if flip_c else c) for r, c in shape]


def _place(shapes, colors, h, w, rng, required):
    """Bounded randomized bbox placement with exact, nonclipping fallback."""
    sizes = [(max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1) for shape in shapes]
    for _ in range(80):
        grid = [[0] * w for _ in range(h)]
        order = sorted(range(len(shapes)), key=lambda i: sizes[i][0] * sizes[i][1], reverse=True)
        for index in order:
            sh, sw = sizes[index]
            locations = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
            rng.shuffle(locations)
            for top, left in locations:
                if any(grid[r][c] for r in range(max(0, top - 1), min(h, top + sh + 1))
                       for c in range(max(0, left - 1), min(w, left + sw + 1))):
                    continue
                for r, c in shapes[index]:
                    grid[top + r][left + c] = colors[index]
                break
            else:
                break
        else:
            answer = solve_reference(grid)
            if all(SEMANTIC_RIVALS[name](grid) != answer for name in required):
                return grid
    # All available motifs admit a shelf layout within the minimum 7x9 grid.
    # Enumerate spatial orders so the color-tie witness also has a guaranteed
    # non-sorted order. This fallback never relaxes counts or clips objects.
    orders = list(permutations(range(len(shapes))))
    rng.shuffle(orders)
    for order in orders:
        grid = [[0] * w for _ in range(h)]
        top = left = row_height = 0
        for index in order:
            sh, sw = sizes[index]
            if left + sw > w:
                top, left, row_height = top + row_height + 1, 0, 0
            if top + sh > h:
                break
            for r, c in shapes[index]:
                grid[top + r][left + c] = colors[index]
            left += sw + 1
            row_height = max(row_height, sh)
        else:
            answer = solve_reference(grid)
            if all(SEMANTIC_RIVALS[name](grid) != answer for name in required):
                return grid
    raise ValueError("incompatible motif layout; no lawful teaching placement")


def _axis(ctx, name, default_options, lo, hi):
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, default_options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed and nonnegative sample_index must be integers")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override axes: " + ", ".join(sorted(unknown)))
    for name, value in overrides.items():
        lo, hi = (int(v) for v in AXES[name]["valid"].split(".."))
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if ("palette_size" in overrides and "n_distinct_colors" in overrides
            and overrides["palette_size"] != overrides["n_distinct_colors"]):
        raise IncompatibleOverrides("palette_size and n_distinct_colors must agree (both include zero)",
                                    ("palette_size", "n_distinct_colors"))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    phase = schedule_profile(seed, sample_index, difficulty)
    preferred_colors = overrides.get("n_distinct_colors", overrides.get("palette_size", 4))
    n = _axis(ctx, "n", (max(4 if phase == 2 else 3, preferred_colors - 1),), 2, 5)
    default_colors = min(preferred_colors, n + 1) if not any(k in overrides for k in ("palette_size", "n_distinct_colors")) else preferred_colors
    colors_n = _axis(ctx, "n_distinct_colors", (default_colors,), 2, 6)
    palette_n = _axis(ctx, "palette_size", (colors_n,), 2, 6)
    if colors_n != palette_n or colors_n > n + 1:
        raise IncompatibleOverrides("n permits at most n+1 colors including zero; color aliases must agree",
                                    tuple(k for k in ("n", "n_distinct_colors", "palette_size") if k in overrides))
    canonical_profile = ctx.draw_choice("profile:" + band, ((7, 9), (7, 10), (8, 11)))
    broad = ctx.draw_choice("broad:" + band, (False, False, False, True))
    h = _axis(ctx, "grid_h", tuple(range(7, 15)) if broad else (canonical_profile[0],), 7, 14)
    w = _axis(ctx, "grid_w", tuple(range(9, 17)) if broad else (canonical_profile[1],), 9, 16)
    rng = ctx.draw_rng("layout:" + band)
    palette = sorted(rng.sample(range(1, 10), colors_n - 1))
    curriculum = colors_n == 4 and n == (4 if phase == 2 else 3)
    if curriculum and phase == 0:
        shapes = [[(0, 0), (1, 0), (2, 0), (2, 1)], [(r, 0) for r in range(5)], [(0, 0)]]
        colors, required = palette, ("bbox_area",)
    elif curriculum and phase == 1:
        shapes = [[(r, 0) for r in range(4)], [(0, 0), (0, 1), (1, 0), (1, 1)],
                  [(0, 0), (1, 0), (1, 1), (1, 2)]]
        colors, required = [palette[1], palette[2], palette[0]], ("ignore_height", "ignore_width")
    elif curriculum:
        shapes = [[(0, 0), (1, 0)] for _ in range(4)]
        colors, required = [palette[2], palette[1], palette[0], palette[2]], ("ignore_color", "merge_by_color")
    else:
        motifs = [[(0, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 0)],
                  [(0, 0), (1, 0), (1, 1)], [(0, 0), (0, 1), (1, 0), (1, 1)]]
        shapes = [rng.choice(motifs) for _ in range(n)]
        colors = palette + [rng.choice(palette) for _ in range(n - len(palette))]
        rng.shuffle(colors)
        required = ()
    shapes = [_reflect(shape, rng) for shape in shapes]
    return _place(shapes, colors, h, w, rng, required)
