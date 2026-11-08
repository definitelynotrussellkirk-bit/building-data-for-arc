"""Rooted-template sampler with exact controls and disjoint stamp rectangles.

The selected Racket rule is the label authority. The Python stamping routines
below are explicitly rival/contract probes, never the generation label path.
Ordinary three-demo/one-query lessons alternate canonical-size cases with
joint extraction witnesses. Explicit overrides need not preserve that schedule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "2fb8d019f6ca"
TASK_ID = GENERATOR_ID
RULE_HASH = "b1a2d9fb3e21"
VERSION = "3.0.0"
SUMMARY = (
    "Extract the four-connected non-{0,8} component rooted at (0,0), clear the "
    "canvas, and stamp its colored cells at every color-8 anchor. Samples mix "
    "canonical-size templates with longer templates, diagonal distractors and "
    "three/four anchors; source and stamped bounding boxes stay disjoint."
)
INVARIANTS = [
    "rectangular 8..16 by 10..16 grid with integer colors 0..9",
    "3..8 non-{0,8} template cells form the four-connected component at (0,0)",
    "template fits 3x3, 2x4 or 4x2; 1..4 color-8 anchors remain in bounds",
    "source and stamp bounding boxes are pairwise disjoint",
    "0..1 disconnected distractor uses an existing template color and is not copied",
    "palette_size is the exact nonzero color count, including reserved anchor color 8",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile/wide mixture", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical-profile/wide mixture", "valid": "10..16"},
    "n_anchors": {"type": "int", "default": "2 in core; 3..4 in witness", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "3 in core; 2..4 in witness", "valid": "2..4"},
    "template_cells": {"type": "int", "default": "4..6 in core; 5..8 in witness", "valid": "3..8"},
    "n_distractors": {"type": "int", "default": "0 in core; 1 in witness", "valid": "0..1"},
}
# One supported compatibility name, not an extra independent sampling axis.
OVERRIDE_ALIASES = {"n_distinct_colors": "palette_size"}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical_core", "extraction_witness")
_CANONICAL_PROFILES = ((10, 12), (11, 13), (10, 14), (12, 12))
_LIMITS = {"grid_h": (8, 16), "grid_w": (10, 16), "n_anchors": (1, 4),
           "palette_size": (2, 4), "template_cells": (3, 8), "n_distractors": (0, 1)}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _draw_axis(ctx, name, defaults):
    lo, hi = _LIMITS[name]
    # Overrides use the same documented domain in every band/profile. Defaults
    # remain schedule-specific; their exact values are recorded by GenCtx.
    choices = tuple(range(lo, hi+1)) if ctx.overrides.get(name) is not None else defaults
    return ctx.draw_choice(name, choices)


def _template(rng, count, wide):
    if wide and count >= 5:
        cells = {(0, c) for c in range(4)} | {(1, 3)}
        cells.update(rng.sample([(1, 0), (1, 1), (1, 2)], count-5))
        if rng.choice((False, True)):
            cells = {(c, r) for r, c in cells}
        return sorted(cells)
    # Connected growth supports all canonical motifs instead of selecting from
    # the predecessor's six-shape bank. Sorted frontiers keep hash-seed stability.
    cells = {(0, 0)}
    while len(cells) < count:
        frontier = {(rr, cc) for r, c in cells
                    for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                    if 0 <= rr < 3 and 0 <= cc < 3 and (rr, cc) not in cells}
        cells.add(rng.choice(sorted(frontier)))
    return sorted(cells)


def _contains(anchor, h, w, point):
    return anchor[0] <= point[0] < anchor[0]+h and anchor[1] <= point[1] < anchor[1]+w


@lru_cache(maxsize=256)
def _band_starts(size, width):
    count, slack = divmod(size, width)
    return tuple((0,) + tuple(v + j*(width-1) for j, v in enumerate(rest, 1))
                 for rest in combinations(range(1, count+slack), count-1))


def _place_anchors(h, w, th, tw, count, distractor, rng):
    # Exhaust a finite set of non-overlapping rectangular tilings. This cannot
    # silently return a shortened anchor list as the old 80-attempt loop did.
    layouts = list(product(_band_starts(h, th), _band_starts(w, tw)))
    rng.shuffle(layouts)
    for rows, cols in layouts:
        slots = [p for p in product(rows, cols) if p != (0, 0)
                 and (distractor is None or not _contains(p, th, tw, distractor))]
        if len(slots) < count:
            continue
        if distractor is None:
            return rng.sample(slots, count)
        feasible = []
        for first in slots:
            extra = (first[0]+distractor[0], first[1]+distractor[1])
            if extra[0] >= h or extra[1] >= w:
                continue
            remaining = [p for p in slots if p != first and not _contains(p, th, tw, extra)]
            if len(remaining) >= count-1:
                feasible.append((first, remaining))
        if feasible:
            first, remaining = rng.choice(feasible)
            return [first] + rng.sample(remaining, count-1)
    raise ValueError("requested template and anchor count cannot be packed without collision")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a Python integer, not bool/float/string")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES) - set(OVERRIDE_ALIASES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    overrides = dict(overrides)
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a Python integer, not bool/float/string")
    alias = overrides.pop("n_distinct_colors", None)
    if alias is not None:
        if overrides.get("palette_size") is not None and overrides["palette_size"] != alias:
            raise ValueError("n_distinct_colors aliases palette_size; conflicting requests")
        overrides["palette_size"] = alias
    for name, value in overrides.items():
        lo, hi = _LIMITS[name]
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = schedule_profile(seed, sample_index, difficulty) == "canonical_core"
    profile_h, profile_w = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    h = _draw_axis(ctx, "grid_h", (profile_h,) if core else tuple(range(8, 17)))
    w = _draw_axis(ctx, "grid_w", (profile_w,) if core else tuple(range(10, 17)))
    anchor_defaults = (3, 3, 4) if difficulty == "easy" else ((3, 4, 4) if difficulty == "hard" else (3, 4))
    count = _draw_axis(ctx, "n_anchors", (2,) if core else anchor_defaults)
    colors = _draw_axis(ctx, "palette_size", (3,) if core else (2, 3, 4))
    size = _draw_axis(ctx, "template_cells", (4, 5, 6) if core else (5, 6, 7, 8))
    noise = _draw_axis(ctx, "n_distractors", (0,) if core else (1,))
    cells = _template(ctx.draw_rng("template_shape"), size, not core)
    th, tw = max(r for r, c in cells)+1, max(c for r, c in cells)+1
    distractor = (th, tw) if noise else None
    palette = random_palette(ctx.draw_rng("palette"), colors-1, exclude={8})
    color_rng = ctx.draw_rng("template_colors")
    painted = list(palette) + [color_rng.choice(palette) for _ in range(size-len(palette))]
    color_rng.shuffle(painted)
    grid = full_grid(h, w, 0)
    for (r, c), value in zip(cells, painted):
        grid[r][c] = value
    if distractor is not None:
        grid[distractor[0]][distractor[1]] = color_rng.choice(palette)
    for r, c in _place_anchors(h, w, th, tw, count, distractor, ctx.draw_rng("anchors")):
        grid[r][c] = 8
    return grid


def _component(grid, diagonal=False):
    seen, pending = set(), [(0, 0)]
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while pending:
        r, c = pending.pop()
        if (r, c) in seen or not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            continue
        if grid[r][c] in (0, 8):
            continue
        seen.add((r, c))
        pending.extend((r+dr, c+dc) for dr, dc in steps)
    return seen


def _anchors(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]


def observe_overrides(grid):
    root = _component(grid)
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "n_anchors": len(_anchors(grid)),
        "palette_size": len({v for row in grid for v in row} - {0}),
        "template_cells": len(root),
        "n_distractors": sum(v not in (0, 8) and (r, c) not in root
                             for r, row in enumerate(grid) for c, v in enumerate(row)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be Python integer colors 0..9, not bool/float/string"]
    if grid[0][0] in (0, 8):
        return ["(0,0) must be a non-{0,8} template root"]
    root = _component(grid)
    th, tw = max(r for r, c in root)+1, max(c for r, c in root)+1
    observed = observe_overrides(grid)
    errors = [f"{name}={observed[name]} outside {lo}..{hi}"
              for name, (lo, hi) in _LIMITS.items() if not lo <= observed[name] <= hi]
    if not ((th <= 3 and tw <= 3) or (th <= 2 and tw <= 4) or (th <= 4 and tw <= 2)):
        errors.append("template must fit 3x3, 2x4 or 4x2")
    colors = {grid[r][c] for r, c in root}
    noise = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v not in (0, 8) and (r, c) not in root}
    if any(grid[r][c] not in colors for r, c in noise):
        errors.append("distractor must reuse a template color")
    occupied = {(r, c) for r in range(th) for c in range(tw)}
    for ar, ac in _anchors(grid):
        footprint = {(ar+r, ac+c) for r in range(th) for c in range(tw)}
        if ar+th > len(grid) or ac+tw > len(grid[0]):
            errors.append("stamp bounding box extends out of bounds")
        if footprint & occupied:
            errors.append("source/stamp bounding boxes overlap")
        if footprint & noise:
            errors.append("stamp bounding box contains an input distractor")
        occupied.update(footprint)
    return errors


def strict_canonical_like(grid):
    """Declared lawful template-stamping manifold, not an exact-size predicate."""
    return self_check(grid)


def _stamp_probe(grid, cells, anchors=None):
    """Prediction helper for explicit rivals; real labels still come from Racket."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for ar, ac in _anchors(grid) if anchors is None else anchors:
        for r, c in sorted(cells):
            if ar+r < len(grid) and ac+c < len(grid[0]):
                out[ar+r][ac+c] = grid[r][c]
    return out


def _all_non_anchor_pixels(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)}
    return _stamp_probe(grid, cells)


def _eight_connected_template(grid):
    return _stamp_probe(grid, _component(grid, diagonal=True))


def _first_two_anchors(grid):
    return _stamp_probe(grid, _component(grid), _anchors(grid)[:2])


def _fixed_three_by_three(grid):
    return _stamp_probe(grid, {(r, c) for r, c in _component(grid) if r < 3 and c < 3})


def _joint_witness(grid):
    root = _component(grid)
    extra = _component(grid, diagonal=True) - root
    anchors = _anchors(grid)
    copied = {(ar+r, ac+c) for ar, ac in anchors for r, c in root}
    return (len(anchors) > 2 and any(r >= 3 or c >= 3 for r, c in root)
            and any(ar+r < len(grid) and ac+c < len(grid[0]) and (ar+r, ac+c) not in copied
                    for ar, ac in anchors for r, c in extra))


CANONICAL_SHORTCUTS = {
    "all_non_anchor_pixels": _all_non_anchor_pixels,
    "eight_connected_template": _eight_connected_template,
    "first_two_anchors": _first_two_anchors,
    "fixed_three_by_three": _fixed_three_by_three,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {"rooted_extraction_and_anchor_scope": _joint_witness}
WITNESS_RIVALS = {"rooted_extraction_and_anchor_scope": list(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query):
    """Only a finite declared-rival contract, never universal identification."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
