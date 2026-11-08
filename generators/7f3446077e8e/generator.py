"""Generator for ARC task 7f3446077e8e (bank volume 14, M92).

The vector from the unique color-8 marker to the unique color-9 marker is
applied to every cell of the connected color-2 object.  In-bounds translated
cells are painted color 3; out-of-bounds cells are clipped.  Everything else
is retained.

The canonical examples all use diagonal vectors, so this generator deliberately
alternates diagonal and purely axial vectors.  Axial examples are teaching
witnesses against the strongest known canonical-fitting shortcut: "copy only
when both vector components are non-zero".
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7f3446077e8e"
TASK_ID = GENERATOR_ID
RULE_HASH = "5d4c6d9ec409"
VERSION = "3.0.0"
SUMMARY = (
    "A connected color-2 object, one color-8 marker, one color-9 marker, and "
    "a small irrelevant decoration appear on a zero background. Translate the "
    "object by the vector 8→9, paint each in-bounds translated cell color 3, "
    "and clip cells that leave the grid. Axial and diagonal vectors alternate "
    "so short lessons refute a diagonal-only shortcut."
)
INVARIANTS = [
    "9..12 by 10..12 rectangular grid with exactly five colors",
    "one connected color-2 object of 3..9 cells",
    "exactly one color-8 marker and one color-9 marker with nonzero delta",
    "one connected 1..2-cell decoration in a fifth color",
    "the visible translated copy is nonempty and does not overwrite retained cells",
    "copy visibility is either fully in bounds or deliberately clipped",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile cycle", "valid": "9..12"},
    "grid_w": {"type": "int", "default": "canonical-profile cycle", "valid": "10..12"},
    "shape_size": {"type": "int", "default": "3..9 cycle", "valid": "3..9"},
    "decoration_size": {"type": "int", "default": "1..2 cycle", "valid": "1..2"},
    "copy_visibility": {
        "type": "str",
        "default": "full/clipped cycle",
        "valid": "full|clipped",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("axial", "diagonal")

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIMENSION_CYCLE = ((9, 11), (10, 10), (10, 12), (11, 12), (12, 12))
_DECORATION_COLORS = (1, 4, 5, 6, 7)


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive samples contain two axial and two diagonal cases."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % 2]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int, overrides) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _scheduled_choice(ctx, label: str, scheduled: str, options, overrides) -> str:
    if overrides.get(label) is not None:
        return str(ctx.draw_choice(label, tuple(options)))
    return str(ctx.draw_choice(label, (scheduled,)))


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _compact_polyomino(rng, size: int):
    """Grow a connected shape inside 4x4, keeping every prefix connected."""
    cells = {(1, 1)}
    while len(cells) < size:
        frontier = {
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _CARD
            if 0 <= r + dr < 4 and 0 <= c + dc < 4
            and (r + dr, c + dc) not in cells
        }
        if not frontier:  # defensive; a <16-cell connected set always has frontier
            break
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def _fallback_shape(size: int):
    # A spiral ordering whose every prefix is connected and whose bbox is <=3x3.
    order = ((0, 0), (0, 1), (1, 1), (1, 0), (2, 0),
             (2, 1), (2, 2), (1, 2), (0, 2))
    return tuple(sorted(order[:size]))


def _candidate_deltas(h: int, w: int, mode: str, rng):
    if mode == "axial":
        values = []
        for magnitude in range(1, min(6, max(h, w) - 1) + 1):
            values.extend(((magnitude, 0), (-magnitude, 0),
                           (0, magnitude), (0, -magnitude)))
    else:
        values = [
            (sr * dr, sc * dc)
            for dr in range(1, min(5, h - 1) + 1)
            for dc in range(1, min(5, w - 1) + 1)
            for sr in (-1, 1)
            for sc in (-1, 1)
        ]
    rng.shuffle(values)
    return values


def _adjacent_pairs(cells):
    available = set(cells)
    return [
        ((r, c), (r + dr, c + dc))
        for r, c in sorted(available)
        for dr, dc in ((1, 0), (0, 1))
        if (r + dr, c + dc) in available
    ]


def _place_layout(h: int, w: int, shape, delta, visibility: str,
                  decoration_size: int, rng):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    placements = [(top, left)
                  for top in range(h - sh + 1)
                  for left in range(w - sw + 1)]
    rng.shuffle(placements)
    dr, dc = delta

    for top, left in placements:
        source = {(top + r, left + c) for r, c in shape}
        translated = {(r + dr, c + dc) for r, c in source}
        visible = {(r, c) for r, c in translated if 0 <= r < h and 0 <= c < w}
        if not visible or visible & source:
            continue
        if visibility == "full" and len(visible) != len(source):
            continue
        if visibility == "clipped" and len(visible) >= len(source):
            continue

        occupied = source | visible
        marker_pairs = []
        for r8 in range(h):
            for c8 in range(w):
                r9, c9 = r8 + dr, c8 + dc
                if not (0 <= r9 < h and 0 <= c9 < w):
                    continue
                p8, p9 = (r8, c8), (r9, c9)
                if p8 in occupied or p9 in occupied:
                    continue
                marker_pairs.append((p8, p9))
        rng.shuffle(marker_pairs)

        for p8, p9 in marker_pairs:
            free = [(r, c) for r in range(h) for c in range(w)
                    if (r, c) not in occupied and (r, c) not in (p8, p9)]
            if decoration_size == 1:
                decorations = [(rng.choice(free),)] if free else []
            else:
                pairs = _adjacent_pairs(free)
                rng.shuffle(pairs)
                decorations = pairs
            if not decorations:
                continue
            decoration = decorations[0]
            return source, visible, p8, p9, decoration
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)

    scheduled_h, scheduled_w = _DIMENSION_CYCLE[sample_index % len(_DIMENSION_CYCLE)]
    h = _scheduled_int(ctx, "grid_h", scheduled_h, 9, 12, overrides)
    w = _scheduled_int(ctx, "grid_w", scheduled_w, 10, 12, overrides)
    shape_size = _scheduled_int(
        ctx, "shape_size", 3 + sample_index % 7, 3, 9, overrides)
    decoration_size = _scheduled_int(
        ctx, "decoration_size", 1 + sample_index % 2, 1, 2, overrides)
    scheduled_visibility = "full" if (sample_index // 2) % 2 == 0 else "clipped"
    visibility = _scheduled_choice(
        ctx, "copy_visibility", scheduled_visibility, ("full", "clipped"), overrides)

    mode = schedule_profile(seed, sample_index, difficulty)
    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'unbanded'}")
    deltas = _candidate_deltas(h, w, mode, layout_rng)
    shapes = [_compact_polyomino(layout_rng, shape_size) for _ in range(12)]
    shapes.append(_fallback_shape(shape_size))

    for shape in shapes:
        for delta in deltas:
            layout = _place_layout(
                h, w, shape, delta, visibility, decoration_size, layout_rng)
            if layout is None:
                continue
            source, _visible, p8, p9, decoration = layout
            grid = full_grid(h, w, 0)
            for r, c in source:
                grid[r][c] = 2
            grid[p8[0]][p8[1]] = 8
            grid[p9[0]][p9[1]] = 9
            decoration_color = layout_rng.choice(_DECORATION_COLORS)
            for r, c in decoration:
                grid[r][c] = decoration_color
            errors = self_check(grid)
            if not errors:
                return grid

    raise RuntimeError(
        f"unable to construct {mode}/{visibility} layout for {h}x{w}, "
        f"shape_size={shape_size}, decoration_size={decoration_size}")


def _positions(grid, color: int):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == color]


def _connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for dr, dc in _CARD:
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                todo.append(point)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate exactly the ordinary generated/canonical input grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["expected a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["expected nonempty list rows"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(len(row) != w for row in grid):
        return ["expected a rectangular grid"]
    if not 9 <= h <= 12 or not 10 <= w <= 12:
        errors.append(f"expected dimensions 9..12 by 10..12; found {h}x{w}")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return errors + ["colors must be integers 0..9, excluding bool"]

    palette = {value for row in grid for value in row}
    if len(palette) != 5:
        errors.append(f"expected exactly five colors; found {len(palette)}")
    source = _positions(grid, 2)
    p8s = _positions(grid, 8)
    p9s = _positions(grid, 9)
    if not 3 <= len(source) <= 9:
        errors.append(f"expected 3..9 color-2 cells; found {len(source)}")
    elif not _connected(source):
        errors.append("color-2 cells must form one 4-connected object")
    if len(p8s) != 1:
        errors.append(f"expected exactly one color-8 marker; found {len(p8s)}")
    if len(p9s) != 1:
        errors.append(f"expected exactly one color-9 marker; found {len(p9s)}")

    extras = palette - {0, 2, 8, 9}
    if len(extras) != 1:
        errors.append(f"expected exactly one decoration color; found {sorted(extras)}")
        decoration = []
    else:
        decoration = _positions(grid, next(iter(extras)))
        if not 1 <= len(decoration) <= 2:
            errors.append(f"expected 1..2 decoration cells; found {len(decoration)}")
        elif not _connected(decoration):
            errors.append("decoration cells must be 4-connected")

    if errors or len(p8s) != 1 or len(p9s) != 1 or not source:
        return errors
    p8, p9 = p8s[0], p9s[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    if (dr, dc) == (0, 0):
        errors.append("marker delta must be nonzero")
        return errors
    visible = {(r + dr, c + dc) for r, c in source
               if 0 <= r + dr < h and 0 <= c + dc < w}
    if not visible:
        errors.append("translated object must retain at least one in-bounds cell")
    if visible & set(source):
        errors.append("translated object must not overlap the source object")
    if visible & {p8, p9}:
        errors.append("translated object must not overwrite a marker")
    if visible & set(decoration):
        errors.append("translated object must not overwrite the decoration")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    source = _positions(grid, 2)
    p8, p9 = _positions(grid, 8)[0], _positions(grid, 9)[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    visible_count = sum(0 <= r + dr < h and 0 <= c + dc < w for r, c in source)
    decoration_color = next(iter({v for row in grid for v in row} - {0, 2, 8, 9}))
    return {
        "grid_h": h,
        "grid_w": w,
        "shape_size": len(source),
        "decoration_size": len(_positions(grid, decoration_color)),
        "copy_visibility": "full" if visible_count == len(source) else "clipped",
    }


def rule_mirror(grid):
    """Independent Python mirror used only for tests and semantic probes."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    source = _positions(grid, 2)
    p8, p9 = _positions(grid, 8)[0], _positions(grid, 9)[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    for r, c in source:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 3
    return out


def _diagonal_only(grid):
    """Plausible wrong rule: ignore purely horizontal or vertical vectors."""
    p8, p9 = _positions(grid, 8)[0], _positions(grid, 9)[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    return rule_mirror(grid) if dr != 0 and dc != 0 else deepcopy(grid)


def _axial_vector(grid) -> bool:
    if self_check(grid):
        return False
    p8, p9 = _positions(grid, 8)[0], _positions(grid, 9)[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    return bool((dr == 0) ^ (dc == 0) and _diagonal_only(grid) != rule_mirror(grid))


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "diagonal_only": _diagonal_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"axial_vector": _axial_vector}
WITNESS_RIVALS = {"axial_vector": ["diagonal_only"]}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to distinguish every declared competitor."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    if self_check(query["input"]):
        reasons.append("query input is outside the shifted-copy grammar")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output does not match the shifted-copy rule")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errs = self_check(demo["input"])
        if errs:
            reasons.append(f"demo {index} input is outside the shifted-copy grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match the shifted-copy rule")
            continue
        valid_demos.append(demo)

    if len(valid_demos) == len(demos) and not reasons:
        for name, competitor in LESSON_COMPETITORS.items():
            fits_demos = all(competitor(pair["input"]) == pair["output"]
                             for pair in valid_demos)
            changes_query = competitor(query["input"]) != query["output"]
            if fits_demos and changes_query:
                reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
