"""Semantic generator for ARC task cbf77aa253ac.

For every 8-connected multicolor component containing yellow guide cells and
non-yellow payload, infer a reflection axis from the guide span and rounded
mean.  Clear the payload, choose its modal-color denser side (ties favor
above/left), and mirror all guide/payload colors from that side.  Components
without both roles remain unchanged.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "cbf77aa253ac"
TASK_ID = "cbf77aa253ac"
VERSION = "3.0.0"
RULE_HASH = "356b20c90964"
SUMMARY = "Mirror each guided multicolor component from its modal-payload denser side across the rounded yellow-guide axis."
INVARIANTS = [
    "literal color 0 is the background and color 4 identifies guide cells",
    "multicolor objects use 8-connectivity",
    "only components containing both guide and payload cells are processed",
    "guide column span greater than row span selects a horizontal axis; ties select vertical",
    "the axis is the half-up rounded mean guide row or column",
    "modal-payload count ties select above or left",
    "all payload colors are cleared before selected-side cells are restored and mirrored with clipping",
    "components lacking either role remain unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "horizontal_above_dense",
    "horizontal_below_dense",
    "horizontal_tie_above",
    "vertical_left_dense",
    "vertical_right_dense",
    "vertical_tie_left",
    "guide_span_tie_vertical",
    "irregular_guide_rounding",
    "multicolor_payload",
    "payload_on_axis",
    "clipped_reflection",
    "unaffected_decoys",
    "multiple_components",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "three exact-public and thirteen observable guide/reflection lessons", "valid": "|".join(SCENE_PROFILES)}}

_PUBLIC_ROWS = {
    "public_1": "00000000000000/00030303333000/00033300330000/00333343300000/00033343333000/00033343333000/00003343430000/00003343300000/00033343333000/00030343333000/00000000000000/00000000000000/00000000000000/00000000000000",
    "public_2": "0000000000000000000/0001101000000000000/0111141100000000000/0111111110000000000/0044444440000000000/0111111100000000000/0000111000000000000/0000000000000000000/0000000000000000000/0000000220020000000/0000002222422200000/0000002242422220000/0000022222422200000/0000002222422220000/0000022002022200000/0000000000002200000/0000000000000000000",
    "public_3": "0000000000000000000000000000/0000000000000000000000000000/0000022420000000000800000000/0000222222000000088848000000/0000044444000000884848000000/0000002220000000888848000000/0000020022200000088848880000/0000000000000000888848080000/0000000000000000000800000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000333300000000000000000/0000033333330000000041410000/0000033333330000000111411000/0000044444444000000011400000/0000333333333000000000000000/0000003334333300000000000000/0000003333330000000000000000/0000000300330000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000",
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
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        seed = min(unseen)
        stack = [seed]
        cells = set()
        while stack:
            row, col = stack.pop()
            if (row, col) not in unseen:
                continue
            unseen.remove((row, col))
            cells.add((row, col))
            stack.extend((row + dr, col + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc) and (row + dr, col + dc) in unseen)
        result.append(cells)
    return result


def _mode(values):
    counts = Counter(values)
    best = max(counts.values())
    return next(value for value in values if counts[value] == best)


def _avg_round(values):
    return (2 * sum(values) + len(values)) // (2 * len(values))


def _component_plan(grid, cells):
    guide = {cell for cell in cells if grid[cell[0]][cell[1]] == 4}
    payload = cells - guide
    if not guide or not payload:
        return None
    payload_values = [grid[r][c] for r, c in sorted(payload)]
    main_color = _mode(payload_values)
    row_span = max(r for r, _ in guide) - min(r for r, _ in guide)
    col_span = max(c for _, c in guide) - min(c for _, c in guide)
    horizontal = col_span > row_span
    axis = _avg_round([r for r, _ in guide] if horizontal else [c for _, c in guide])
    if horizontal:
        negative = sum(grid[r][c] == main_color and r < axis for r, c in payload)
        positive = sum(grid[r][c] == main_color and r > axis for r, c in payload)
        choose_negative = negative >= positive
        source = {cell for cell in cells if cell[0] == axis or (cell[0] < axis if choose_negative else cell[0] > axis)}
        reflected = {(2 * axis - r, c) for r, c in source}
    else:
        negative = sum(grid[r][c] == main_color and c < axis for r, c in payload)
        positive = sum(grid[r][c] == main_color and c > axis for r, c in payload)
        choose_negative = negative >= positive
        source = {cell for cell in cells if cell[1] == axis or (cell[1] < axis if choose_negative else cell[1] > axis)}
        reflected = {(r, 2 * axis - c) for r, c in source}
    return {
        "cells": cells, "guide": guide, "payload": payload, "payload_colors": set(payload_values), "main_color": main_color,
        "row_span": row_span, "col_span": col_span, "horizontal": horizontal, "orientation": "horizontal" if horizontal else "vertical",
        "axis": axis, "negative_count": negative, "positive_count": positive, "choose_negative": choose_negative,
        "source": source, "reflected": reflected,
    }


def _execute(grid, plans):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    clipped = []
    for plan in plans:
        for row, col in plan["payload"]:
            output[row][col] = 0
        for row, col in sorted(plan["source"]):
            value = grid[row][col]
            for rr, cc in ((row, col), ((2 * plan["axis"] - row, col) if plan["horizontal"] else (row, 2 * plan["axis"] - col))):
                if 0 <= rr < height and 0 <= cc < width:
                    output[rr][cc] = value
                else:
                    clipped.append((rr, cc, value))
    return output, clipped


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    plans = [plan for cells in _components(grid) if (plan := _component_plan(grid, cells)) is not None]
    return _execute(grid, plans)[0]


def _straight(guide):
    return len({r for r, _ in guide}) == 1 or len({c for _, c in guide}) == 1


def _general_profile(plans, ignored, clipped):
    if len(plans) > 1:
        return "multiple_components"
    plan = plans[0]
    if ignored:
        return "unaffected_decoys"
    if clipped:
        return "clipped_reflection"
    if len(plan["payload_colors"]) > 1:
        return "multicolor_payload"
    if any((r == plan["axis"] if plan["horizontal"] else c == plan["axis"]) for r, c in plan["payload"]):
        return "payload_on_axis"
    if not _straight(plan["guide"]):
        return "guide_span_tie_vertical" if plan["row_span"] == plan["col_span"] else "irregular_guide_rounding"
    if plan["row_span"] == plan["col_span"]:
        return "guide_span_tie_vertical"
    if plan["horizontal"]:
        if plan["negative_count"] == plan["positive_count"]:
            return "horizontal_tie_above"
        return "horizontal_above_dense" if plan["choose_negative"] else "horizontal_below_dense"
    if plan["negative_count"] == plan["positive_count"]:
        return "vertical_tie_left"
    return "vertical_left_dense" if plan["choose_negative"] else "vertical_right_dense"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    components = _components(grid)
    plans = []
    ignored = []
    for cells in components:
        plan = _component_plan(grid, cells)
        (plans if plan is not None else ignored).append(plan if plan is not None else cells)
    if not 1 <= len(plans) <= 5:
        errors.append(f"expected 1..5 guided payload components; got {len(plans)}")
        return result
    if len(components) > 7:
        errors.append("expected at most seven total nonzero components")
        return result
    if any(len(plan["guide"]) < 3 or len(plan["payload"]) < 2 for plan in plans):
        errors.append("each processed component needs at least three guide and two payload cells")
        return result
    output, clipped = _execute(grid, plans)
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(plans, ignored, clipped)
    if profile not in SCENE_PROFILES:
        errors.append("guided component geometry does not match a declared profile")
    result.update({"components": components, "plans": plans, "ignored_components": ignored, "clipped": clipped, "output": output, "scene_profile": profile, "errors": errors})
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


def _standard_cells(relation, color, secondary=None):
    guide = {(4, col, 4) for col in range(2, 9)}
    above = [(3, 3), (3, 4), (2, 4), (3, 5), (2, 5)]
    below = [(5, 7), (6, 7)]
    if relation == "below":
        positions = [(8 - row, col) for row, col in above + below]
    elif relation == "tie":
        above = [(3, 3), (3, 4), (2, 4)]
        below = [(5, 6), (5, 7), (6, 7)]
        positions = above + below
    else:
        positions = above + below
    payload = {(r, c, color) for r, c in positions}
    if secondary is not None:
        payload = {(r, c, secondary if (r, c) in set(positions[-2:]) else color) for r, c in positions}
    return guide | payload


def _transpose(cells):
    return {(col, row, value) for row, col, value in cells}


def _shift(cells, top, left):
    return {(row + top, col + left, value) for row, col, value in cells}


def _paint(grid, cells):
    for row, col, value in cells:
        grid[row][col] = value


def _safe_shift(cells, height, width, rng, forbidden=()):
    """Place a local lesson with both its input and full reflection in bounds."""
    local_height = max(row for row, _, _ in cells) + 1
    local_width = max(col for _, col, _ in cells) + 1
    local = [[0 for _ in range(local_width)] for _ in range(local_height)]
    _paint(local, cells)
    plan = _component_plan(local, {(row, col) for row, col, _ in cells})
    footprint = {(row, col) for row, col, _ in cells} | plan["reflected"]
    min_row = min(row for row, _ in footprint)
    max_row = max(row for row, _ in footprint)
    min_col = min(col for _, col in footprint)
    max_col = max(col for _, col in footprint)
    candidates = []
    for top in range(-min_row, height - max_row):
        for left in range(-min_col, width - max_col):
            translated = {(row + top, col + left) for row, col in footprint}
            if not any(abs(row - rr) <= 1 and abs(col - cc) <= 1 for row, col in translated for rr, cc in forbidden):
                candidates.append((top, left))
    if not candidates:
        raise AssertionError("no noninteracting placement for lesson geometry")
    top, left = rng.choice(candidates)
    return _shift(cells, top, left)


def _general_scene(ctx, profile):
    ranges = {None: (16, 24), "easy": (14, 18), "medium": (18, 24), "hard": (24, 30)}
    low, high = ranges[ctx.difficulty]
    # Keep every lesson's changed-cell footprint visible.  The small
    # tie/axis/clipping templates would otherwise become near-no-ops on a
    # 30x30 field even though their geometry remained semantically valid.
    max_side = {
        "horizontal_tie_above": 24,
        "vertical_tie_left": 24,
        "guide_span_tie_vertical": 19,
        "payload_on_axis": 19,
        "clipped_reflection": 19,
        "irregular_guide_rounding": 28,
        "multiple_components": 30,
    }.get(profile, 26)
    high = min(high, max_side)
    low = min(low, max(14, high - 2))
    height = ctx.draw_int("canvas_height", low, high)
    width = ctx.draw_int("canvas_width", low, high)
    rng = ctx.draw_rng("geometry")
    colors = rng.sample([1, 2, 3, 5, 6, 7, 8, 9], 4)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    relation = "above"
    vertical = False
    if profile == "horizontal_below_dense": relation = "below"
    elif profile == "horizontal_tie_above": relation = "tie"
    elif profile == "vertical_left_dense": vertical = True
    elif profile == "vertical_right_dense": vertical, relation = True, "below"
    elif profile == "vertical_tie_left": vertical, relation = True, "tie"

    if profile == "guide_span_tie_vertical":
        cells = {(2, 2, 4), (3, 3, 4), (4, 4, 4), (5, 5, 4), (3, 2, colors[0]), (4, 2, colors[0]), (5, 3, colors[0]), (4, 6, colors[0])}
    elif profile == "irregular_guide_rounding":
        cells = {(3, 2, 4), (3, 3, 4), (4, 4, 4), (4, 5, 4), (4, 6, 4), (3, 7, 4), (2, 3, colors[0]), (2, 4, colors[0]), (3, 4, colors[0]), (2, 5, colors[0]), (5, 6, colors[0])}
    elif profile == "payload_on_axis":
        cells = {(4, col, 4) for col in range(2, 9) if col != 5} | {(4, 5, colors[0]), (3, 4, colors[0]), (3, 5, colors[0]), (2, 5, colors[0]), (5, 7, colors[0])}
    elif profile == "multicolor_payload":
        cells = _standard_cells("above", colors[0], colors[1])
    elif profile == "clipped_reflection":
        cells = {(1, col, 4) for col in range(2, 9)} | {(2, 3, colors[0]), (2, 4, colors[0]), (3, 4, colors[0]), (2, 5, colors[0]), (3, 5, colors[0]), (0, 7, colors[0])}
    else:
        cells = _standard_cells(relation, colors[0])
        if vertical:
            cells = _transpose(cells)

    if profile == "clipped_reflection":
        _paint(grid, cells)
        return grid

    decoys = set()
    if profile == "unaffected_decoys":
        decoys = {(height - 2, width - 2, colors[2]), (height - 2, width - 1, colors[2]), (height - 1, width - 2, colors[2]), (0, width - 1, 4), (0, width - 2, 4), (1, width - 1, 4)}
    shifted = _safe_shift(cells, height, width, rng, {(row, col) for row, col, _ in decoys})
    _paint(grid, shifted)

    if profile == "unaffected_decoys":
        _paint(grid, decoys)
    elif profile == "multiple_components":
        compact = {(2, col, 4) for col in range(1, 5)} | {(1, 2, colors[1]), (1, 3, colors[1]), (3, 4, colors[1])}
        second = _shift(_transpose(compact), height - 7, width - 7)
        if any(abs(r - rr) <= 1 and abs(c - cc) <= 1 for r, c, _ in shifted for rr, cc, _ in second):
            shifted = _shift(cells, 0, 0)
            grid = [[0 for _ in range(width)] for _ in range(height)]
            _paint(grid, shifted)
        _paint(grid, second)
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
