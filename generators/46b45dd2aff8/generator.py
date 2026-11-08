"""Generator for ARC task a2d730bd / task id 46b45dd2aff8.

The modal color is background.  Every other color owns one solid rectangle and
one or more isolated dots.  A dot is actionable only when it is horizontally
or vertically aligned with the rectangle of the *same color*.  The output
replaces the dot by four petals, grows a one-cell-wide stem toward the matching
rectangle, and adds a three-cell cap immediately outside the rectangle.

The curriculum deliberately varies one to three colors, one to three dots per
color, all four approach directions, non-zero and zero backgrounds, and the
four canonical (height, width, palette-size) profiles.  Six slots in each
eight-sample schedule add a wrong-color rectangle that is nearer to a dot than
its same-color rectangle.  Consequently every three-pair lesson contains two
counterexamples to the color-blind "connect to the nearest aligned rectangle"
rule, so every one-pair query rotation leaves a decisive demonstration.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "46b45dd2aff8"
TASK_ID = "46b45dd2aff8"
VERSION = "3.0.1"
RULE_HASH = "95e121aa05f4"

SUMMARY = (
    "For each isolated dot, use color identity to select its solid rectangle. "
    "When the dot lies beyond one side while remaining inside that side's row "
    "or column span, erase the dot center, paint its four cardinal petals, "
    "continue a stem toward the rectangle, and place a perpendicular 3-cell "
    "cap immediately outside the rectangle. Preserve all other cells and the "
    "input dimensions."
)

INVARIANTS = [
    "the unique modal majority color is background",
    "each active color has exactly one solid rectangular component",
    "each active color has one to three isolated same-color dots",
    "every dot is outside and axis-aligned with its same-color rectangle",
    "every same-color dot-to-rectangle gap is at least two background cells",
    "the output has the same dimensions and keeps unchanged scene cells",
]

# Only exact, grid-observable knobs are declared.  Pedagogical profiles are a
# deterministic sample_index schedule rather than an override axis.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "13..30"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "13..30"},
    "background": {"type": "color", "default": "rng from canonical modes", "valid": "0..9"},
    "n_colors": {"type": "int", "default": "difficulty/profile schedule", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = ("horizontal", "color_trap", "vertical")
LESSON_SCHEDULE = (
    "horizontal",
    "color_trap",
    "color_trap",
    "color_trap",
    "vertical",
    "color_trap",
    "color_trap",
    "color_trap",
)
LESSON_SCHEDULE_PERIOD = len(LESSON_SCHEDULE)
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.10
_CANONICAL_PROFILES = {(13, 16, 2), (22, 16, 2), (22, 16, 3), (30, 30, 4)}
_CANONICAL_BACKGROUNDS = {1, 3, 4, 8}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Keep every three-pair window safe under any one-pair query rotation."""
    del seed, difficulty
    return LESSON_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")


def _draw_int(ctx, label: str, global_lo: int, global_hi: int, lo: int, hi: int) -> int:
    """Honor the full declared range under overrides; otherwise use a band."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, global_lo, global_hi)
    return ctx.draw_int(label, lo, hi)


def _scheduled_defaults(ctx, sample_index: int, difficulty: str | None) -> tuple[int, int, int]:
    profile = schedule_profile(ctx.seed, sample_index, difficulty)
    slot = sample_index % 8
    if difficulty == "easy":
        if slot == 0:
            defaults = (13, 16, 1)  # exact canonical profile
        elif profile == "color_trap":
            defaults = (16, 18, 2)
        else:
            defaults = (15, 17, 1 + (sample_index % 2))
        h = _draw_int(ctx, "grid_h", 13, 30, defaults[0], defaults[0])
        w = _draw_int(ctx, "grid_w", 13, 30, defaults[1], defaults[1])
        n = _draw_int(ctx, "n_colors", 1, 3, defaults[2], defaults[2])
    elif difficulty == "hard":
        if slot == 0:
            defaults = (30, 30, 3)  # exact canonical profile
        elif profile == "color_trap":
            defaults = (27, 29, 3)
        else:
            defaults = (25 + sample_index % 4, 24 + sample_index % 6, 2 + sample_index % 2)
        h_hi = defaults[0] if slot == 0 else min(30, defaults[0] + 1)
        w_hi = defaults[1] if slot == 0 else min(30, defaults[1] + 1)
        h = _draw_int(ctx, "grid_h", 13, 30, defaults[0], h_hi)
        w = _draw_int(ctx, "grid_w", 13, 30, defaults[1], w_hi)
        n = _draw_int(ctx, "n_colors", 1, 3, defaults[2], defaults[2])
    else:
        if slot == 0:
            # Alternate the two 22x16 canonical palette sizes.
            defaults = (22, 16, 1 if (sample_index // 8) % 2 == 0 else 2)
        elif profile == "color_trap":
            defaults = (22, 20, 2 + (sample_index % 2))
        else:
            defaults = (18 + sample_index % 6, 16 + sample_index % 6, 1 + sample_index % 3)
        h_hi = defaults[0] if slot == 0 else min(30, defaults[0] + 1)
        w_hi = defaults[1] if slot == 0 else min(30, defaults[1] + 1)
        h = _draw_int(ctx, "grid_h", 13, 30, defaults[0], h_hi)
        w = _draw_int(ctx, "grid_w", 13, 30, defaults[1], w_hi)
        n = _draw_int(ctx, "n_colors", 1, 3, defaults[2], defaults[2])
    return h, w, n


def _background(ctx) -> int:
    if "background" in ctx.overrides and ctx.overrides["background"] is not None:
        return ctx.draw_int("background", 0, 9)
    return ctx.draw_choice("background", (1, 3, 4, 8))


def _active_colors(ctx, bg: int, n_colors: int) -> list[int]:
    rng = ctx.draw_rng("active_colors")
    return rng.sample([color for color in range(10) if color != bg], n_colors)


def _bands(length: int, count: int) -> list[tuple[int, int]]:
    """Partition an axis into count contiguous bands, each at least four."""
    cuts = [round(i * length / count) for i in range(count + 1)]
    return [(cuts[i], cuts[i + 1] - 1) for i in range(count)]


def _horizontal_scene(h: int, w: int, bg: int, colors: list[int], rng, sample_index: int) -> list[list[int]]:
    grid = full_grid(h, w, bg)
    for index, (color, (top, bottom)) in enumerate(zip(colors, _bands(h, len(colors)))):
        band_h = bottom - top + 1
        rect_h = 3 if band_h >= 6 and (sample_index + index) % 3 == 0 else 2
        # Canonical rectangles reach 33 cells.  Preserve that scale on large
        # boards while retaining four columns of clearance for dots/caps.
        rect_w = min(11, max(2, w - 8))
        r1 = top + max(1, (band_h - rect_h) // 2)
        r1 = min(r1, bottom - rect_h)
        c1 = max(4, (w - rect_w) // 2 + rng.choice((-1, 0, 1)))
        c1 = min(c1, w - rect_w - 4)
        draw_rect(grid, r1, c1, rect_h, rect_w, color)
        rows = [r1, r1 + rect_h - 1]
        # One, two, or three dots, with every dot remaining a singleton.
        dot_mode = (sample_index + index) % 4
        spots = [(rows[0], 1)] if dot_mode == 0 else [(rows[0], 1), (rows[-1], w - 2)]
        if dot_mode == 3 and rect_h >= 3:
            spots.append((r1 + 2, 1))
        for r, c in spots:
            grid[r][c] = color
    return grid


def _vertical_scene(h: int, w: int, bg: int, colors: list[int], rng, sample_index: int) -> list[list[int]]:
    grid = full_grid(h, w, bg)
    for index, (color, (left, right)) in enumerate(zip(colors, _bands(w, len(colors)))):
        band_w = right - left + 1
        rect_w = 3 if band_w >= 6 and (sample_index + index) % 3 == 1 else 2
        # Canonical rectangles reach 33 cells.  Preserve that scale on large
        # boards while retaining four rows of clearance for dots/caps.
        rect_h = min(11, max(2, h - 8))
        c1 = left + max(1, (band_w - rect_w) // 2)
        c1 = min(c1, right - rect_w)
        r1 = max(4, (h - rect_h) // 2 + rng.choice((-1, 0, 1)))
        r1 = min(r1, h - rect_h - 4)
        draw_rect(grid, r1, c1, rect_h, rect_w, color)
        cols = [c1, c1 + rect_w - 1]
        dot_mode = (sample_index + index) % 4
        spots = [(1, cols[0])] if dot_mode == 0 else [(1, cols[0]), (h - 2, cols[-1])]
        if dot_mode == 3 and rect_w >= 3:
            spots.append((1, c1 + 2))
        for r, c in spots:
            grid[r][c] = color
    return grid


def _color_trap_scene(h: int, w: int, bg: int, colors: list[int], rng, sample_index: int) -> list[list[int]]:
    """Make color identity decisive against the nearest-aligned shortcut."""
    if len(colors) < 2:
        return _horizontal_scene(h, w, bg, colors, rng, sample_index)
    grid = full_grid(h, w, bg)
    a, b = colors[:2]

    # B rectangle is nearer to A's central dot, but A's matching rectangle is
    # on the opposite side.  The true rule grows right; the rival grows left.
    draw_rect(grid, 2, 1, 2, 2, b)
    draw_rect(grid, 2, w - 4, 2, 2, a)
    grid[2][4] = a

    # Vertical dots make the orientation branch decisive too.  They are kept
    # on separated columns so their stems cannot overwrite another rectangle.
    grid[min(h - 3, 7)][w - 3] = a
    grid[min(h - 3, 8)][1] = b

    # A third color occupies a bottom band, preserving the same grammar.
    if len(colors) == 3:
        c = colors[2]
        r1 = h - 4
        c1 = max(5, w // 2 - 1)
        c1 = min(c1, w - 7)
        draw_rect(grid, r1, c1, 2, 2, c)
        grid[r1][1] = c
        grid[r1 + 1][w - 2] = c
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        task_id=TASK_ID,
        version=VERSION,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_colors = _scheduled_defaults(ctx, sample_index, difficulty)
    bg = _background(ctx)
    colors = _active_colors(ctx, bg, n_colors)
    rng = ctx.draw_rng("layout")
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "color_trap" and n_colors >= 2:
        grid = _color_trap_scene(h, w, bg, colors, rng, sample_index)
    elif profile == "vertical":
        grid = _vertical_scene(h, w, bg, colors, rng, sample_index)
    else:
        grid = _horizontal_scene(h, w, bg, colors, rng, sample_index)
    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _DIR4:
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    queue.append(q)
        result.append(sorted(cells))
    return result


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": ["grid colors must be integers in 0..9"]}

    h = len(grid)
    counts = Counter(value for row in grid for value in row)
    ranked = counts.most_common()
    bg, bg_count = ranked[0]
    errors: list[str] = []
    if len(ranked) > 1 and ranked[1][1] == bg_count:
        errors.append("background mode must be unique")
    if bg_count <= h * w // 2:
        errors.append("background must be a strict majority")

    by_color: dict[int, dict[str, Any]] = {}
    for color in sorted(value for value in counts if value != bg):
        comps = _components(grid, color)
        rects: list[dict[str, Any]] = []
        dots: list[tuple[int, int]] = []
        malformed: list[int] = []
        for cells in comps:
            if len(cells) == 1:
                dots.append(cells[0])
                continue
            r1, c1, r2, c2 = _bbox(cells)
            if set(cells) != {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}:
                malformed.append(len(cells))
            else:
                rects.append({"bbox": (r1, c1, r2, c2), "cells": cells})
        by_color[color] = {"components": comps, "rects": rects, "dots": sorted(dots), "malformed": malformed}
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "background": bg,
        "background_count": bg_count,
        "counts": counts,
        "by_color": by_color,
    }


def _dot_direction(dot: tuple[int, int], rect: tuple[int, int, int, int]) -> tuple[str, int] | None:
    r, c = dot
    r1, c1, r2, c2 = rect
    if c < c1 and r1 <= r <= r2:
        return "right", c1 - c - 1
    if c > c2 and r1 <= r <= r2:
        return "left", c - c2 - 1
    if r < r1 and c1 <= c <= c2:
        return "down", r1 - r - 1
    if r > r2 and c1 <= c <= c2:
        return "up", r - r2 - 1
    return None


def observe_overrides(grid) -> dict[str, int]:
    info = _scene_facts(grid)
    if info.get("errors"):
        return {}
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "background": info["background"],
        "n_colors": len(info["by_color"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _scene_facts(grid)
    errors = list(info.get("errors", []))
    if "by_color" not in info:
        return errors
    if not 1 <= len(info["by_color"]) <= 3:
        errors.append(f"expected one to three active colors, got {len(info['by_color'])}")
    h, w = info["height"], info["width"]
    for color, facts in info["by_color"].items():
        if facts["malformed"]:
            errors.append(f"color {color} has non-rectangular multi-cell component(s) {facts['malformed']}")
        if len(facts["rects"]) != 1:
            errors.append(f"color {color} must have exactly one solid rectangle; got {len(facts['rects'])}")
            continue
        if not 1 <= len(facts["dots"]) <= 3:
            errors.append(f"color {color} must have one to three isolated dots; got {len(facts['dots'])}")
        rect = facts["rects"][0]["bbox"]
        r1, c1, r2, c2 = rect
        if r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1:
            errors.append(f"color {color} rectangle must leave room for its external cap")
        for dot in facts["dots"]:
            r, c = dot
            if r in (0, h - 1) or c in (0, w - 1):
                errors.append(f"color {color} dot {dot} must leave room for four petals")
                continue
            direction = _dot_direction(dot, rect)
            if direction is None:
                errors.append(f"color {color} dot {dot} is not axis-aligned outside its rectangle")
            elif direction[1] < 2:
                errors.append(f"color {color} dot {dot} has only {direction[1]} background cells to rectangle; need >=2")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        requested.update({name: meta[name] for name in AXES if name in meta})
    observed = observe_overrides(grid)
    for name, expected in requested.items():
        if name in AXES and expected is not None and observed.get(name) != expected:
            errors.append(f"override {name}={expected!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    profile = (observed["grid_h"], observed["grid_w"], observed["n_colors"] + 1)
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}")
    if observed["background"] not in _CANONICAL_BACKGROUNDS:
        errors.append(f"background {observed['background']} is outside canonical modes {sorted(_CANONICAL_BACKGROUNDS)}")
    return errors


def _paint(grid: list[list[int]], cells, color: int) -> None:
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            grid[r][c] = color


def _transform_dot(out: list[list[int]], bg: int, color: int, dot: tuple[int, int], rect: tuple[int, int, int, int]) -> bool:
    relation = _dot_direction(dot, rect)
    if relation is None:
        return False
    direction, _ = relation
    dr, dc = dot
    r1, c1, r2, c2 = rect
    out[dr][dc] = bg
    _paint(out, ((dr - 1, dc), (dr + 1, dc), (dr, dc - 1), (dr, dc + 1)), color)
    if direction == "right":
        cap = c1 - 1
        _paint(out, ((dr, c) for c in range(dc + 2, cap + 1)), color)
        _paint(out, ((dr - 1, cap), (dr + 1, cap)), color)
    elif direction == "left":
        cap = c2 + 1
        _paint(out, ((dr, c) for c in range(cap, dc - 1)), color)
        _paint(out, ((dr - 1, cap), (dr + 1, cap)), color)
    elif direction == "down":
        cap = r1 - 1
        _paint(out, ((r, dc) for r in range(dr + 2, cap + 1)), color)
        _paint(out, ((cap, dc - 1), (cap, dc + 1)), color)
    else:  # up
        cap = r2 + 1
        _paint(out, ((r, dc) for r in range(cap, dr - 1)), color)
        _paint(out, ((cap, dc - 1), (cap, dc + 1)), color)
    return True


def _rects_and_dots(grid: list[list[int]]) -> tuple[int, dict[int, tuple[int, int, int, int]], dict[int, list[tuple[int, int]]]]:
    info = _scene_facts(grid)
    bg = info["background"]
    rects: dict[int, tuple[int, int, int, int]] = {}
    dots: dict[int, list[tuple[int, int]]] = {}
    for color, facts in info["by_color"].items():
        if facts["rects"]:
            rects[color] = facts["rects"][0]["bbox"]
        dots[color] = facts["dots"]
    return bg, rects, dots


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    bg, rects, dots = _rects_and_dots(grid)
    for color in sorted(dots):
        rect = rects.get(color)
        if rect is None:
            continue
        for dot in sorted(dots[color]):
            _transform_dot(out, bg, color, dot, rect)
    return out


def _first_dot_per_color(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    bg, rects, dots = _rects_and_dots(grid)
    for color in sorted(dots):
        if color in rects and dots[color]:
            _transform_dot(out, bg, color, sorted(dots[color])[0], rects[color])
    return out


def _horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    bg, rects, dots = _rects_and_dots(grid)
    for color in sorted(dots):
        rect = rects.get(color)
        if rect is None:
            continue
        for dot in sorted(dots[color]):
            relation = _dot_direction(dot, rect)
            if relation and relation[0] in {"left", "right"}:
                _transform_dot(out, bg, color, dot, rect)
    return out


def _nearest_aligned_ignoring_color(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    bg, rects, dots = _rects_and_dots(grid)
    all_rects = sorted((color, rect) for color, rect in rects.items())
    for dot_color in sorted(dots):
        for dot in sorted(dots[dot_color]):
            candidates = []
            for rect_color, rect in all_rects:
                relation = _dot_direction(dot, rect)
                if relation is not None:
                    candidates.append((relation[1], rect, rect_color))
            if candidates:
                _, rect, _ = min(candidates)
                _transform_dot(out, bg, dot_color, dot, rect)
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_dot_per_color": _first_dot_per_color,
    "horizontal_only": _horizontal_only,
    "nearest_aligned_ignoring_color": _nearest_aligned_ignoring_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "nearest_aligned_ignoring_color": _nearest_aligned_ignoring_color,
}


def _rival_differs(name: str, grid: list[list[int]]) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "multiple_dots_require_all_instances": lambda grid: _rival_differs("first_dot_per_color", grid),
    "vertical_branch_required": lambda grid: _rival_differs("horizontal_only", grid),
    "color_identity_beats_nearest_rectangle": lambda grid: _rival_differs("nearest_aligned_ignoring_color", grid),
}
WITNESS_RIVALS = {
    "multiple_dots_require_all_instances": ["first_dot_per_color"],
    "vertical_branch_required": ["horizontal_only"],
    "color_identity_beats_nearest_rectangle": ["nearest_aligned_ignoring_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    findings: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is malformed")
            continue
        if rule_mirror(pair["input"]) != [list(row) for row in pair["output"]]:
            findings.append(f"pair {index} output disagrees with the canonical dot-to-rectangle rule")
    if findings:
        return findings
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            findings.append(f"demonstrations do not refute competitor {name!r}")
    return findings
