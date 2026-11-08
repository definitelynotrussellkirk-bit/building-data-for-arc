"""Generator for S7_M2 — rigid downward gravity around an immobile 8-wall.

Every nonzero connected component except color 8 is a rigid body.  Repeatedly
move bodies straight down, bottom-most first, until each is stopped by the
floor, the cyan wall, or another body.  Colors and shapes are preserved.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2d40680cd25"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "09ddc1726a80"

SUMMARY = (
    "Two to four rigid colored pieces fall straight down around one fixed "
    "vertical color-8 wall; canonical-scale anchors occur in every difficulty "
    "band, and ordinary draws include wall support plus floor or piece-on-piece "
    "support."
)

INVARIANTS = [
    "background is modal color 0",
    "one contiguous vertical color-8 wall of 2..6 cells remains fixed",
    "2..4 uniquely colored, 4-connected rigid pieces of at least two cells",
    "every movable piece descends by a positive whole-object translation",
    "ordinary generated scenes contain a wall-supported piece and a second stop type",
]

PALETTE_KINDS = ("low", "high", "mixed")
WALL_POSITIONS = ("left", "center", "right")
INTERACTION_MODES = ("wall_only", "wall_and_stack")

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchor or difficulty-skewed 9..14", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "canonical anchor or difficulty-skewed 10..14", "valid": "10..14"},
    "wall_size": {"type": "int", "default": "difficulty-skewed 2..6", "valid": "2..6"},
    "n_blobs": {"type": "int", "default": "canonical anchor or difficulty-skewed 2..4", "valid": "2..4"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "|".join(PALETTE_KINDS)},
    "wall_position": {"type": "str", "default": "rng", "valid": "|".join(WALL_POSITIONS)},
    "interaction_mode": {"type": "str", "default": "rng", "valid": "|".join(INTERACTION_MODES)},
}

# Exact canonical inputs are admitted because the official examples deliberately
# show the all-to-floor branch, where the wall separates lanes but supports no
# piece.  Non-canonical generated lessons are held to the stronger wall-support
# teaching invariant below.
_CANONICAL_INPUTS = frozenset(
    {
        tuple(tuple(int(value) for value in row) for row in rows)
        for rows in (
            (
                "0000000000",
                "0020003000",
                "0220003300",
                "0000800000",
                "0000800000",
                "0000800000",
                "0000800000",
                "0000000000",
                "0000000000",
            ),
            (
                "00040000000",
                "00044000000",
                "00000080000",
                "02000080030",
                "22000080033",
                "00000080000",
                "00000080000",
                "00000000000",
                "00000000000",
            ),
            (
                "003000000000",
                "033000000000",
                "000000080000",
                "000200080000",
                "000220080400",
                "000000080440",
                "000000080000",
                "000000000000",
                "000000000000",
                "000000000000",
            ),
        )
    }
)

# (height, width, movable-piece count).  With background 0 and the fixed wall
# color 8, these reproduce the three official (height, width, palette-size)
# profiles: (9, 10, 4), (9, 11, 5), and (10, 12, 5).  The anchor is a prior,
# not a restriction: unanchored draws retain the full advertised ranges.
_CANONICAL_PROFILES = (
    (9, 10, 2),
    (9, 11, 3),
    (10, 12, 3),
)
_CANONICAL_PROFILE_RATE = 0.40

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_L_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)


def _normal_grid(grid) -> list[list[int]]:
    if not grid:
        return []
    if isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    """Return same-color 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in _NEIGHBORS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def _positions_by_color(grid: list[list[int]]) -> dict[int, set[tuple[int, int]]]:
    positions: dict[int, set[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                positions.setdefault(color, set()).add((r, c))
    return positions


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror of the canonical Racket rule.

    The Racket program remains the output authority; this mirror exists only
    for structural self-checks and focused regression tests.
    """
    out = _normal_grid(grid)
    if not out or not out[0]:
        return out
    h, w = len(out), len(out[0])
    fuel = 3 * h * w
    while fuel > 0:
        movable = [item for item in _components(out) if item[0] != 8]
        movable.sort(key=lambda item: max(r for r, _ in item[1]), reverse=True)
        changed = False
        for color, original_cells in movable:
            cells = set(original_cells)
            blockers = {
                (r, c)
                for r, row in enumerate(out)
                for c, value in enumerate(row)
                if value != 0 and (r, c) not in cells
            }
            shifted = set(cells)
            while True:
                candidate = {(r + 1, c) for r, c in shifted}
                if any(r >= h or c < 0 or c >= w for r, c in candidate):
                    break
                if candidate & blockers:
                    break
                shifted = candidate
            if shifted == cells:
                continue
            for r, c in cells:
                out[r][c] = 0
            for r, c in shifted:
                out[r][c] = color
            changed = True
        if not changed:
            return out
        fuel -= 1
    return out


def _decorative_wall_rival(grid) -> list[list[int]]:
    """Plausible wrong rule: color 8 is an overlay, not a collision body.

    The public demonstrations never require a falling body to stop on the
    cyan wall, so this rule agrees with all of them.  Generated lessons make
    the distinction observable by guaranteeing a wall-supported body.
    """
    g = _normal_grid(grid)
    if not g or not g[0]:
        return g
    wall_cells = {
        (r, c)
        for r, row in enumerate(g)
        for c, value in enumerate(row)
        if value == 8
    }
    without_wall = [row[:] for row in g]
    for r, c in wall_cells:
        without_wall[r][c] = 0
    out = rule_mirror(without_wall)
    for r, c in wall_cells:
        out[r][c] = 8
    return out


def _wall_position_column(width: int, position: str) -> int:
    return {
        "left": 2,
        "center": width // 2,
        "right": width - 3,
    }[position]


def _scene_analysis(grid) -> dict:
    g = _normal_grid(grid)
    result = {
        "grid": g,
        "errors": [],
        "wall_cells": set(),
        "blob_components": [],
        "output": None,
        "wall_supported": set(),
        "stacked": set(),
        "floor_supported": set(),
        "moves": {},
    }
    if not g or not g[0]:
        result["errors"].append("empty grid")
        return result
    width = len(g[0])
    if any(len(row) != width for row in g):
        result["errors"].append("ragged grid")
        return result
    h, w = len(g), width
    if not (9 <= h <= 14 and 10 <= w <= 14):
        result["errors"].append(f"dims {h}x{w} outside 9..14 x 10..14")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in g
        for value in row
    ):
        result["errors"].append("colors must be integer ARC colors 0..9")
        return result

    components = _components(g)
    wall_components = [set(cells) for color, cells in components if color == 8]
    if len(wall_components) != 1:
        result["errors"].append(f"expected one color-8 wall component, found {len(wall_components)}")
    else:
        wall = wall_components[0]
        result["wall_cells"] = wall
        columns = {c for _, c in wall}
        rows = sorted(r for r, _ in wall)
        if len(columns) != 1 or rows != list(range(rows[0], rows[-1] + 1)):
            result["errors"].append("color-8 wall must be one contiguous vertical segment")
        if not 2 <= len(wall) <= 6:
            result["errors"].append(f"wall size {len(wall)} outside 2..6")

    blobs = [(color, set(cells)) for color, cells in components if color != 8]
    result["blob_components"] = blobs
    if not 2 <= len(blobs) <= 4:
        result["errors"].append(f"expected 2..4 movable components, found {len(blobs)}")
    colors = [color for color, _ in blobs]
    if len(colors) != len(set(colors)):
        result["errors"].append("each movable component must have a distinct color")
    for color, cells in blobs:
        if not 2 <= len(cells) <= 5:
            result["errors"].append(f"color {color} size {len(cells)} outside 2..5")
        if any(r == h - 1 for r, _ in cells):
            result["errors"].append(f"color {color} already touches the floor")

    nonzero = sum(value != 0 for row in g for value in row)
    if nonzero >= h * w - nonzero:
        result["errors"].append("background 0 is not strictly modal")

    if result["errors"]:
        return result

    output = rule_mirror(g)
    result["output"] = output
    if output == g:
        result["errors"].append("oracle is identity")
        return result
    before = _positions_by_color(g)
    after = _positions_by_color(output)
    if before.get(8) != after.get(8):
        result["errors"].append("wall changed under the gravity rule")
    for color, cells in blobs:
        final_cells = after.get(color, set())
        if len(final_cells) != len(cells):
            result["errors"].append(f"color {color} cell count changed")
            continue
        if _normalize_cells(cells) != _normalize_cells(final_cells):
            result["errors"].append(f"color {color} shape changed")
            continue
        before_top = min(r for r, _ in cells)
        after_top = min(r for r, _ in final_cells)
        delta = after_top - before_top
        translated = {(r + delta, c) for r, c in cells}
        if delta <= 0 or translated != final_cells:
            result["errors"].append(f"color {color} did not make one positive vertical translation")
            continue
        result["moves"][color] = delta
        for r, c in final_cells:
            if r == h - 1:
                result["floor_supported"].add(color)
                continue
            below = output[r + 1][c]
            if below == 8:
                result["wall_supported"].add(color)
            elif below not in (0, color):
                result["stacked"].add(color)

    canonical = tuple(tuple(row) for row in g) in _CANONICAL_INPUTS
    if not canonical:
        if not result["wall_supported"]:
            result["errors"].append("generated lesson has no wall-supported piece")
        if not (result["floor_supported"] or result["stacked"]):
            result["errors"].append("generated lesson has no second stop type")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, identity, non-rigid, or rule-hiding scenes."""
    del difficulty, meta
    return list(_scene_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Semantic-gate hook: generated lessons obey the task grammar."""
    return self_check(grid)


def _has_wall_support_witness(grid) -> bool:
    analysis = _scene_analysis(grid)
    return (
        not analysis["errors"]
        and bool(analysis["wall_supported"])
        and _decorative_wall_rival(grid) != analysis["output"]
    )


SEMANTIC_WITNESSES = {"wall_support": _has_wall_support_witness}
SEMANTIC_RIVALS = {"decorative_wall": _decorative_wall_rival}
WITNESS_RIVALS = {"wall_support": ["decorative_wall"]}
CANONICAL_SHORTCUTS = {"decorative_wall": _decorative_wall_rival}
LESSON_COMPETITORS = {"decorative_wall": _decorative_wall_rival}


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic axis from a valid generated grid."""
    analysis = _scene_analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    g = analysis["grid"]
    h, w = len(g), len(g[0])
    wall_columns = {c for _, c in analysis["wall_cells"]}
    wall_column = next(iter(wall_columns))
    positions = {
        name: _wall_position_column(w, name)
        for name in WALL_POSITIONS
    }
    matches = [name for name, column in positions.items() if column == wall_column]
    if len(matches) != 1:
        raise ValueError(f"wall column {wall_column} does not encode one wall_position")

    colors = {color for color, _ in analysis["blob_components"]}
    if colors <= {1, 2, 3, 4}:
        palette_kind = "low"
    elif colors <= {5, 6, 7, 9}:
        palette_kind = "high"
    elif 1 in colors and 9 in colors:
        palette_kind = "mixed"
    else:
        raise ValueError(f"blob colors do not encode one palette_kind: {sorted(colors)}")

    interaction_mode = "wall_and_stack" if analysis["stacked"] else "wall_only"
    return {
        "wall_size": len(analysis["wall_cells"]),
        "n_blobs": len(analysis["blob_components"]),
        "palette_kind": palette_kind,
        "wall_position": matches[0],
        "interaction_mode": interaction_mode,
    }


def _palette(rng, kind: str, count: int) -> list[int]:
    if kind == "low":
        return rng.sample([1, 2, 3, 4], count)
    if kind == "high":
        return rng.sample([5, 6, 7, 9], count)
    return [1, 9] + rng.sample([2, 3, 4, 5, 6, 7], count - 2)


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            raise RuntimeError(f"internal placement out of bounds: {(r, c)}")
        if grid[r][c] != 0:
            raise RuntimeError(f"internal placement overlap at {(r, c)}")
    for r, c in cells:
        grid[r][c] = color


def _translated(shape, top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + r, left + c) for r, c in shape)


def _draw_scene_profile(ctx, overrides) -> tuple[int, int, int]:
    """Draw dimensions/count, occasionally from a linked canonical profile.

    Any explicit override among these linked axes disables the prior so the
    caller's requested axis cannot silently constrain either of the others.
    Each value still passes through a typed GenCtx draw and is recorded.
    """
    linked_axes = ("grid_h", "grid_w", "n_blobs")
    has_linked_override = any(overrides.get(axis) is not None for axis in linked_axes)
    anchor_rng = ctx.draw_rng("canonical_profile")
    if not has_linked_override and anchor_rng.random() < _CANONICAL_PROFILE_RATE:
        h, w, n_blobs = anchor_rng.choice(_CANONICAL_PROFILES)
        return (
            int(ctx.draw_choice("grid_h", (h,))),
            int(ctx.draw_choice("grid_w", (w,))),
            int(ctx.draw_choice("n_blobs", (n_blobs,))),
        )
    return (
        ctx.draw_int_diff("grid_h", 9, 14),
        ctx.draw_int_diff("grid_w", 10, 14),
        ctx.draw_int_diff("n_blobs", 2, 4),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None/easy/medium/hard")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_blobs = _draw_scene_profile(ctx, overrides)
    wall_size = ctx.draw_int_diff("wall_size", 2, 6)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    wall_position = ctx.draw_choice("wall_position", WALL_POSITIONS)
    interaction_mode = ctx.draw_choice("interaction_mode", INTERACTION_MODES)

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    colors = _palette(palette_rng, palette_kind, n_blobs)
    grid = full_grid(h, w, 0)

    wall_column = _wall_position_column(w, wall_position)
    max_wall_top = h - wall_size
    wall_top = layout_rng.randint(3, max_wall_top)
    wall_cells = tuple((r, wall_column) for r in range(wall_top, wall_top + wall_size))
    _paint(grid, wall_cells, 8)

    support_left = min((wall_column // 2) * 2, w - 2)
    support_columns = {support_left, support_left + 1}
    lanes = [
        left
        for left in range(0, w - 1, 2)
        if not ({left, left + 1} & support_columns)
    ]
    layout_rng.shuffle(lanes)

    color_index = 0
    if interaction_mode == "wall_and_stack":
        # Two adjacent horizontal dominoes descend in lockstep: the lower one
        # lands on the wall and the upper one then lands on the lower body.
        max_lift = wall_top - 2
        lift = layout_rng.randint(1, max_lift)
        lower_row = wall_top - 1 - lift
        upper_row = wall_top - 2 - lift
        bar = ((0, 0), (0, 1))
        _paint(grid, _translated(bar, lower_row, support_left), colors[color_index])
        color_index += 1
        _paint(grid, _translated(bar, upper_row, support_left), colors[color_index])
        color_index += 1
        floor_count = n_blobs - 2
    else:
        shape = layout_rng.choice(_L_SHAPES)
        final_top = wall_top - 2
        lift = layout_rng.randint(1, final_top)
        _paint(
            grid,
            _translated(shape, final_top - lift, support_left),
            colors[color_index],
        )
        color_index += 1
        floor_count = n_blobs - 1

    if len(lanes) < floor_count:
        raise ValueError(
            f"incompatible dimensions/layout: {w=} leaves {len(lanes)} floor lanes for {floor_count} pieces"
        )
    for left in lanes[:floor_count]:
        shape = layout_rng.choice(_L_SHAPES)
        final_top = h - 2
        initial_top = layout_rng.randint(0, final_top - 1)
        _paint(
            grid,
            _translated(shape, initial_top, left),
            colors[color_index],
        )
        color_index += 1

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid
