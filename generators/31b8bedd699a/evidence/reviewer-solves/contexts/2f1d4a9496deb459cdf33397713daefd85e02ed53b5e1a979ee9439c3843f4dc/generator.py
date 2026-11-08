"""Sample separated hollow frames for the unchanged, fixed-token Racket rule.

Select frames, compare their TOP-LEFT coordinate ranges (ties horizontal), sort
along the selected axis, and redraw every frame as a 4x4 outline. The Python
mirror below is for diagnostics/rivals only; production labels come from Racket.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect, draw_rect_outline

GENERATOR_ID = "31b8bedd699a"
TASK_ID = "31b8bedd699a"
RULE_HASH = "ca3b9033626d"
VERSION = "3.0.0"
SUMMARY = (
    "On a black canvas, retain 2..5 separated monochrome hollow rectangular "
    "frames and discard 0..3 solid rectangles. Compare the ranges of frame "
    "top-left rows and columns; use a column iff row range is strictly greater, "
    "otherwise a row. Sort along that axis and redraw each frame as a fixed "
    "4x4 outline of its color, including repeated colors."
)
INVARIANTS = [
    "integer colors 0..9 on a rectangular canvas no larger than 30x30; background 0",
    "2..5 complete hollow rectangular outlines, each dimension 3..8",
    "0..3 solid rectangular distractors, each dimension 3..8",
    "every two object bounding boxes have at least one background cell between them",
    "frame colors need not be distinct; input frame dimensions do not set output dimensions",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles or broad 15..30", "valid": "15..30"},
    "grid_w": {"type": "int", "default": "canonical profiles or broad 15..30", "valid": "15..30"},
    "n_frames": {"type": "int", "default": "phase-dependent 2..5", "valid": "2..5"},
    "n_solids": {"type": "int", "default": "phase-dependent 0..3", "valid": "0..3"},
}
# All tuples in the four advertised domains are constructively supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 6
SCHEDULE_PROFILES = (
    "canonical_vertical", "broad_vertical", "canonical_horizontal",
    "broad_horizontal", "canonical_tie", "broad_tie",
)
MIN_STRICT_FRAC = 0.45


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic branch cycle for ordinary, unoverridden production draws."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _components(grid):
    """Row-major, monochrome four-connected components with exact cell support."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            cells = {(r, c)}
            seen.add((r, c))
            pending = [(r, c)]
            while pending:
                y, x = pending.pop()
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (0 <= yy < h and 0 <= xx < w and (yy, xx) not in seen
                            and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        cells.add((yy, xx))
                        pending.append((yy, xx))
            top = min(y for y, _ in cells)
            left = min(x for _, x in cells)
            bottom = max(y for y, _ in cells)
            right = max(x for _, x in cells)
            components.append({"top": top, "left": left, "bottom": bottom, "right": right,
                            "height": bottom - top + 1, "width": right - left + 1,
                            "color": color, "cells": cells,
                            "frame": len(cells) < (bottom - top + 1) * (right - left + 1)})
    return components


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        return ["canvas exceeds 30x30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be Python integers in 0..9 (not booleans)"]
    components = _components(grid)
    errors = []
    frames = [obj for obj in components if obj["frame"]]
    if not 2 <= len(frames) <= 5:
        errors.append(f"expected 2..5 hollow frames, found {len(frames)}")
    if not 0 <= len(components) - len(frames) <= 3:
        errors.append("expected 0..3 solid distractors")
    for obj in components:
        if not (3 <= obj["height"] <= 8 and 3 <= obj["width"] <= 8):
            errors.append("object dimensions must be 3..8")
            continue
        rectangle = {(r, c) for r in range(obj["top"], obj["bottom"] + 1)
                     for c in range(obj["left"], obj["right"] + 1)}
        outline = {(r, c) for r, c in rectangle
                   if r in (obj["top"], obj["bottom"]) or c in (obj["left"], obj["right"])}
        if obj["cells"] != (outline if obj["frame"] else rectangle):
            errors.append("each object must be a complete outline or a solid rectangle")
    for i, a in enumerate(components):
        for b in components[i + 1:]:
            if not (a["bottom"] + 1 < b["top"] or b["bottom"] + 1 < a["top"]
                    or a["right"] + 1 < b["left"] or b["right"] + 1 < a["left"]):
                errors.append("object boxes must have at least one background cell between them")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if any(obj["height"] != 4 or obj["width"] != 4 for obj in _components(grid)):
        return ["strict canonical components are all 4x4"]
    return []


def observe_overrides(grid):
    components = _components(grid)
    frames = sum(obj["frame"] for obj in components)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_frames": frames, "n_solids": len(components) - frames}


def _axis(ctx, name, lo, hi, default):
    # Canonical phase defaults are exact, not post-draw clipping. Explicit
    # controls use the complete declared interval independently of difficulty.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


@lru_cache(maxsize=1024)
def _patterns(n_frames, row_step, col_step, orientation):
    slots = tuple((r, c) for r in range(3) for c in range(3))
    candidates = []
    for chosen in combinations(slots, n_frames):
        dr = (max(r for r, _ in chosen) - min(r for r, _ in chosen)) * row_step
        dc = (max(c for _, c in chosen) - min(c for _, c in chosen)) * col_step
        actual = "vertical" if dr > dc else ("horizontal" if dc > dr else "tie")
        if actual != orientation:
            continue
        primary = 0 if orientation == "vertical" else 1
        if n_frames <= 3 and len({p[primary] for p in chosen}) != n_frames:
            continue
        # Horizontal/tie core scenes also distinguish coordinate order from
        # row-major extraction order, without fixing any numeric color role.
        if orientation != "vertical" and list(chosen) == sorted(chosen, key=lambda p: p[1]):
            continue
        candidates.append(chosen)
    return tuple(candidates)


def _lattice_boxes(h, w, nf, ns, orientation, broad, rng):
    """Nine separated slots guarantee every 15..30 / 2..5 / 0..3 tuple."""
    rs = rng.randint(5, (h - 4) // 2)
    cs = rng.randint(5, (w - 4) // 2)
    if orientation == "tie":
        rs = cs = min(rs, cs)
    patterns = _patterns(nf, rs, cs, orientation)
    if not patterns:
        rs = cs = min(rs, cs)
        patterns = _patterns(nf, rs, cs, orientation)
    if not patterns:
        raise RuntimeError("constructive frame-slot invariant failed")
    frame_slots = rng.choice(patterns)
    spare = [(r, c) for r in range(3) for c in range(3) if (r, c) not in frame_slots]
    solid_slots = rng.sample(spare, ns)
    max_h = min(8, rs - 1, h - 2 * rs)
    max_w = min(8, cs - 1, w - 2 * cs)
    boxes = []
    for i, (r, c) in enumerate((*frame_slots, *solid_slots)):
        bh = rng.randint(3, max_h) if broad else 4
        bw = rng.randint(3, max_w) if broad else 4
        if broad and i == 0:
            bh = bw = 3  # a guaranteed non-12-cell, non-4x4 normalization witness
        boxes.append([r * rs, c * cs, bh, bw, i < nf])
    dr = rng.randint(0, h - max(r + bh for r, c, bh, bw, hollow in boxes))
    dc = rng.randint(0, w - max(c + bw for r, c, bh, bw, hollow in boxes))
    return [[r + dr, c + dc, bh, bw, hollow] for r, c, bh, bw, hollow in boxes]


def _separated(a, b):
    r, c, h, w = a[:4]
    y, x, bh, bw = b[:4]
    return r + h < y or y + bh < r or c + w < x or x + bw < c


def _contrast_boxes(h, w, ns, orientation, rng):
    """Unequal sizes make top-left spread disagree with centers and extents."""
    vertical = orientation == "vertical"
    hh, ww = (h, w) if vertical else (w, h)
    side = rng.choice((7, 8))
    row_gap = rng.randint(11, min(16, hh - 3, ww - side + 1))
    col_gap = row_gap - 1
    r = rng.randint(0, hh - row_gap - 4)
    c = rng.randint(0, ww - col_gap - side)
    boxes = [[r, c + col_gap, side, side, True],
             [r + row_gap, c, 3, 3, True]]
    # The far-right distractor shares the bottom frame's top row. It changes
    # only the all-object column range, so using solids selects the wrong axis.
    boxes.append([r + row_gap, ww - 4, 4, 4, False])
    if not vertical:
        boxes = [[c, r, bw, bh, hollow] for r, c, bh, bw, hollow in boxes]
    candidates = [(r, c, 4, 4, False) for r in range(h - 3) for c in range(w - 3)]
    def preserves_axis_witness(candidate):
        extended = [*boxes, candidate]
        dr = max(box[0] for box in extended) - min(box[0] for box in extended)
        dc = max(box[1] for box in extended) - min(box[1] for box in extended)
        return (dr > dc) != vertical
    for _ in range(ns - 1):
        legal = [box for box in candidates if all(_separated(box, used) for used in boxes)
                 and preserves_axis_witness(box)]
        if not legal:
            raise RuntimeError("contrast scene cannot place its requested distractors")
        boxes.append(list(rng.choice(legal)))
    return boxes


def _paint(h, w, boxes, profile, rng):
    nf = sum(box[4] for box in boxes)
    # Distinct component colors in core profiles preserve exact palette support.
    colors = rng.sample(list(range(1, 10)), len(boxes))
    if profile.startswith("broad"):
        # Repetition in both broad directional scenes survives a query rotation;
        # broad_tie also supplies mixed repeated/distinct frame colors.
        colors[1] = colors[0]
    frames = boxes[:nf]
    dr = max(b[0] for b in frames) - min(b[0] for b in frames)
    dc = max(b[1] for b in frames) - min(b[1] for b in frames)
    key = 0 if dr > dc else 1
    order = sorted(range(nf), key=lambda i: (frames[i][key], frames[i][1 - key]))
    if not profile.startswith("broad") and nf >= 3:
        ordered = [colors[i] for i in order]
        if ordered == sorted(ordered) or ordered == sorted(ordered, reverse=True):
            a, b = order[:2]
            colors[a], colors[b] = colors[b], colors[a]
    grid = full_grid(h, w, 0)
    for (r, c, bh, bw, hollow), color in zip(boxes, colors):
        if hollow:
            draw_rect_outline(grid, r, c, bh, bw, color)
        else:
            draw_rect(grid, r, c, bh, bw, color)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout")
    if profile == "canonical_vertical":
        defaults = ctx.draw_choice("canonical_shape", ((21, 16, 2, 2), (18, 17, 2, 2)))
    elif profile == "canonical_horizontal":
        defaults = (24, 22, 3, 3)
    elif profile == "canonical_tie":
        defaults = (22, 21, 3, 2)
    elif profile == "broad_vertical":
        defaults = (24, 28, 2, ctx.draw_int_diff("contrast_solids", 1, 3))
    elif profile == "broad_horizontal":
        defaults = (28, 24, 2, ctx.draw_int_diff("contrast_solids", 1, 3))
    else:
        defaults = (ctx.draw_int_diff("broad_height", 15, 30), ctx.draw_int_diff("broad_width", 15, 30),
                    ctx.draw_int_diff("broad_frames", 3, 5), ctx.draw_int_diff("broad_solids", 0, 3))
    h = _axis(ctx, "grid_h", 15, 30, defaults[0])
    w = _axis(ctx, "grid_w", 15, 30, defaults[1])
    nf = _axis(ctx, "n_frames", 2, 5, defaults[2])
    ns = _axis(ctx, "n_solids", 0, 3, defaults[3])
    orientation = profile.rsplit("_", 1)[1]
    custom = any(value is not None for value in overrides.values())
    if profile in ("broad_vertical", "broad_horizontal") and not custom:
        boxes = _contrast_boxes(h, w, ns, orientation, rng)
    else:
        boxes = _lattice_boxes(h, w, nf, ns, orientation, profile.startswith("broad"), rng)
    return _paint(h, w, boxes, profile, ctx.draw_rng("colors"))


def _pack(frames, vertical):
    if not frames:
        return [[0]]
    out = full_grid(4 * len(frames) if vertical else 4, 4 if vertical else 4 * len(frames), 0)
    for i, frame in enumerate(frames):
        draw_rect_outline(out, 4 * i if vertical else 0, 0 if vertical else 4 * i,
                          4, 4, frame["color"])
    return out


def _prediction(grid, mode="correct"):
    components = _components(grid)
    frames = [obj for obj in components if obj["frame"]]
    if mode == "size12":
        frames = [obj for obj in components if len(obj["cells"]) == 12]
    elif mode == "keep_solids":
        frames = list(components)
    if not frames:
        return [[0]]
    support = components if mode == "solid_axis" else frames
    def position(obj):
        if mode == "centers":
            return ((obj["top"] + obj["bottom"]) / 2, (obj["left"] + obj["right"]) / 2)
        return obj["top"], obj["left"]
    points = [position(obj) for obj in support]
    dr = max(p[0] for p in points) - min(p[0] for p in points)
    dc = max(p[1] for p in points) - min(p[1] for p in points)
    if mode == "extents":
        dr = max(obj["bottom"] for obj in frames) - min(obj["top"] for obj in frames)
        dc = max(obj["right"] for obj in frames) - min(obj["left"] for obj in frames)
    if mode == "canvas":
        dr, dc = len(grid), len(grid[0])
    vertical = dr >= dc if mode == "vertical_ties" else dr > dc
    if mode == "always_horizontal":
        vertical = False
    elif mode == "always_vertical":
        vertical = True
    if mode != "row_major":
        frames = sorted(frames, key=lambda obj: position(obj)[0 if vertical else 1])
    if mode == "color_ascending":
        frames = sorted(frames, key=lambda obj: obj["color"])
    elif mode == "color_descending":
        frames = sorted(frames, key=lambda obj: -obj["color"])
    if mode == "deduplicate_colors":
        seen = set()
        frames = [obj for obj in frames if obj["color"] not in seen and not seen.add(obj["color"])]
    if mode == "crop":
        # A well-formed size-preserving crop rival: align panels at top/left and
        # pad shorter panels with black, avoiding a malformed-ragged-grid rival.
        height = sum(obj["height"] for obj in frames) if vertical else max(obj["height"] for obj in frames)
        width = max(obj["width"] for obj in frames) if vertical else sum(obj["width"] for obj in frames)
        out = full_grid(height, width, 0)
        offset = 0
        for obj in frames:
            for r, c in obj["cells"]:
                rr, cc = r - obj["top"], c - obj["left"]
                out[rr + (offset if vertical else 0)][cc + (0 if vertical else offset)] = obj["color"]
            offset += obj["height"] if vertical else obj["width"]
        return out
    return _pack(frames, vertical)


def rule_mirror(grid):
    """Diagnostic Python mirror; never used to supply production labels."""
    return _prediction(grid)


def _crop(grid): return _prediction(grid, "crop")
def _centers(grid): return _prediction(grid, "centers")
def _extents(grid): return _prediction(grid, "extents")
def _vertical_ties(grid): return _prediction(grid, "vertical_ties")
def _deduplicate(grid): return _prediction(grid, "deduplicate_colors")
def _size12(grid): return _prediction(grid, "size12")
def _solid_axis(grid): return _prediction(grid, "solid_axis")
def _keep_solids(grid): return _prediction(grid, "keep_solids")
def _always_horizontal(grid): return _prediction(grid, "always_horizontal")
def _always_vertical(grid): return _prediction(grid, "always_vertical")
def _row_major(grid): return _prediction(grid, "row_major")
def _canvas(grid): return _prediction(grid, "canvas")
def _color_ascending(grid): return _prediction(grid, "color_ascending")
def _color_descending(grid): return _prediction(grid, "color_descending")

CANONICAL_SHORTCUTS = {
    "crop_instead_of_normalize": _crop, "centers_instead_of_top_left": _centers,
    "bbox_extents_instead_of_top_left": _extents, "vertical_on_equal_ranges": _vertical_ties,
    "deduplicate_frame_colors": _deduplicate, "select_twelve_cell_objects": _size12,
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "include_solids_in_axis": _solid_axis, "keep_solid_rectangles": _keep_solids,
    "always_horizontal": _always_horizontal, "always_vertical": _always_vertical,
    "row_major_order": _row_major, "canvas_shape_axis": _canvas,
    "ascending_color_order": _color_ascending, "descending_color_order": _color_descending,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _witness(mode):
    def predicate(grid):
        return _prediction(grid, mode) != rule_mirror(grid)
    return predicate

SEMANTIC_WITNESSES = {
    "normalization": _witness("crop"), "top_left_not_center": _witness("centers"),
    "top_left_not_extent": _witness("extents"), "equal_ranges_horizontal": _witness("vertical_ties"),
    "repeat_frame_colors": _witness("deduplicate_colors"), "not_cell_count": _witness("size12"),
    "solid_filter": _witness("keep_solids"), "vertical_output": _witness("always_horizontal"),
    "horizontal_output": _witness("always_vertical"), "spatial_order": _witness("row_major"),
    "distractors_do_not_set_axis": _witness("solid_axis"),
}
WITNESS_RIVALS = {
    "normalization": ["crop_instead_of_normalize"],
    "top_left_not_center": ["centers_instead_of_top_left"],
    "top_left_not_extent": ["bbox_extents_instead_of_top_left"],
    "equal_ranges_horizontal": ["vertical_on_equal_ranges"],
    "repeat_frame_colors": ["deduplicate_frame_colors"],
    "not_cell_count": ["select_twelve_cell_objects"],
    "solid_filter": ["keep_solid_rectangles"],
    "vertical_output": ["always_horizontal"],
    "horizontal_output": ["always_vertical"],
    "spatial_order": ["row_major_order"],
    "distractors_do_not_set_axis": ["include_solids_in_axis"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, including honest reports for custom lessons."""
    errors = []
    for name, solve in LESSON_COMPETITORS.items():
        if all(solve(pair["input"]) == pair["output"] for pair in demos):
            if solve(query["input"]) != query["output"]:
                errors.append(f"{name} fits demonstrations but changes the query")
    return errors
