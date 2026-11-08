"""Generator for 85e65da9fb15 — file loose shapes into best-fitting frames.

The selected rule processes non-frame components in top-left order.  Each shape
claims the unused hollow rectangular frame with the least unused interior area,
rotating clockwise only when its original bbox orientation does not fit.  The
shape is centered in that frame; unmatched shapes disappear, and only frames
plus assigned contents remain.

The sampler deliberately rotates three semantic profiles over consecutive
sample indices: centering with slack, order-sensitive competition, and required
rotation with distractors.  This makes every three-demo lesson exercise the
branches that the four public canonical pairs leave ambiguous.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "85e65da9fb15"
TASK_ID = GENERATOR_ID
RULE_HASH = "d63ea92287a9"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 0-background grid contains two hollow rectangular frames and two to "
    "four loose 4-connected shapes. Process loose shapes in top-left order. "
    "For each shape, choose the unused frame it fits most tightly by bbox area, "
    "breaking ties by frame top-left position; keep the original orientation "
    "when it fits, otherwise rotate 90 degrees clockwise if that fits. Center "
    "the shape in the chosen frame. Output only the frames and successfully "
    "filed shapes; unmatched shapes disappear."
)

INVARIANTS = [
    "background is color 0 and every foreground component is 4-connected by color",
    "exactly two foreground components are hollow rectangular borders",
    "at least two non-frame components are present; arbitrary polyominoes are lawful",
    "shape assignment is sequential in top-left order and every frame is used at most once",
    "original orientation is preferred; clockwise rotation occurs only when required to fit",
    "assigned shapes are centered with floor/top-left bias on odd slack",
]

# Only exact, externally useful controls are advertised.  Profile, palette,
# colors, shape variants, and scene offset remain deterministic keyed draws.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 12..18; canonical square sizes favored",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "grid_h unless explicitly overridden",
        "valid": "12..18",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

SCHEDULE_PROFILES = (
    "centered_slack",
    "order_competition",
    "rotation_distractor",
)

# Normalized connected shape variants.  Every listed variant occupies the full
# documented bbox even though it need not fill that bbox.
_Z_2X3 = (
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
)
_L_2X2 = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_IRREGULAR_3X3 = (
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
)
_ROTATE_2X4 = (
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2)),
)
_WIDE_1X5 = (((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),)
_WIDE_2X5 = (
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
     (1, 0), (1, 4)),
    ((0, 0), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4)),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the semantic profile used by ``generate``.

    Seed and difficulty intentionally do not alter the covering schedule: any
    three consecutive examples contain all three required branches.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _dimension_choices(difficulty) -> tuple[int, ...]:
    # Every band keeps exact support for all four canonical size/palette
    # profiles.  Larger canvases add translation/background variation.
    if difficulty == "easy":
        return (12, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 17, 18)
    if difficulty == "hard":
        return (12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18)
    return (12, 12, 13, 13, 14, 14, 15, 15, 16, 17, 18)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not 12 <= value <= 18:
            raise ValueError(f"{name}={value} outside [12, 18]")


def _draw_dimensions(ctx, difficulty, overrides: dict) -> tuple[int, int]:
    h = ctx.draw_choice("grid_h", _dimension_choices(difficulty))
    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", 12, 18)
    else:
        # Record grid_w through GenCtx even though the default is coupled to h.
        w = ctx.draw_choice("grid_w", (h,))
    return h, w


def _palette_size(h: int, w: int, ctx) -> int:
    # Match every canonical exact profile whenever a canonical square is drawn.
    if h == w and h in (12, 14):
        return 5
    if h == w and h in (13, 15):
        return 7
    return ctx.draw_choice("palette_size_internal", (5, 7))


def _shape_variant(ctx, label: str, variants):
    return ctx.draw_rng(label).choice(variants)


def _put_shape(grid, r0: int, c0: int, cells, color: int) -> None:
    for dr, dc in cells:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            raise RuntimeError("constructive shape placement escaped the canvas")
        if grid[r][c] != 0:
            raise RuntimeError("constructive shape placement collided")
        grid[r][c] = color


def _scene(profile: str, ctx):
    """Return (frames, shapes) in a 12x12 local scene.

    A frame is (row, col, interior_h, interior_w). A shape is
    (row, col, normalized_cells). Object top-left coordinates are intentional:
    they are part of the selected rule's semantics.
    """
    wide1 = _shape_variant(ctx, f"{profile}:wide1", _WIDE_1X5)
    wide2 = _shape_variant(ctx, f"{profile}:wide2", _WIDE_2X5)
    if profile == "centered_slack":
        frames = ((7, 0, 3, 3), (6, 6, 4, 4))
        shapes = (
            (0, 0, _shape_variant(ctx, "centered:exact", _IRREGULAR_3X3)),
            (0, 7, wide1),
            (4, 0, _shape_variant(ctx, "centered:slack", _L_2X2)),
            (3, 7, wide2),
        )
    elif profile == "order_competition":
        # The larger frame is top-left. The first shape has a larger cell count
        # than the later 2x2-bbox shape, yet it must claim the tighter 2x3 frame.
        frames = ((6, 0, 4, 4), (8, 7, 2, 3))
        shapes = (
            (0, 0, _shape_variant(ctx, "order:first", _Z_2X3)),
            (0, 7, wide1),
            (4, 0, _shape_variant(ctx, "order:second", _L_2X2)),
            (3, 7, wide2),
        )
    elif profile == "rotation_distractor":
        frames = ((6, 0, 4, 2), (7, 7, 3, 3))
        shapes = (
            (0, 0, _shape_variant(ctx, "rotation:required", _ROTATE_2X4)),
            (0, 7, wide1),
            (3, 0, _shape_variant(ctx, "rotation:square", _IRREGULAR_3X3)),
            (3, 7, wide2),
        )
    else:
        raise ValueError(f"unknown schedule profile {profile!r}")
    return frames, shapes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    frames, shapes = _scene(profile, ctx)

    row_offset = ctx.draw_int("scene_row", 0, h - 12)
    col_offset = ctx.draw_int("scene_col", 0, w - 12)
    palette_size = _palette_size(h, w, ctx)
    colors = ctx.draw_rng("palette").sample(tuple(range(1, 10)), palette_size - 1)
    frame_colors = colors[:2]
    solid_colors = colors[2:]
    if len(solid_colors) == 2:
        # Slots 0 and 2 are the two assigned shapes in every profile. Give
        # them distinct colors while keeping repeated-color distractors apart.
        shape_colors = (solid_colors[0], solid_colors[1], solid_colors[1], solid_colors[0])
        active_shape_indexes = (0, 1, 2) if profile == "rotation_distractor" else (0, 2)
    else:
        shape_colors = tuple(solid_colors[:4])
        active_shape_indexes = tuple(range(4))

    grid = full_grid(h, w, 0)
    for color, (r0, c0, ih, iw) in zip(frame_colors, frames):
        r0 += row_offset
        c0 += col_offset
        draw_frame(grid, r0, c0, r0 + ih + 1, c0 + iw + 1, color)
    for index in active_shape_indexes:
        r0, c0, cells = shapes[index]
        _put_shape(
            grid, r0 + row_offset, c0 + col_offset, cells, shape_colors[index]
        )
    return grid


# ---------------------------------------------------------------------------
# Structural parser, executable invariant, and task-local diagnostic solvers
# ---------------------------------------------------------------------------


def _components(grid) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(x for x, _ in cells)
            c1 = min(y for _, y in cells)
            r2 = max(x for x, _ in cells)
            c2 = max(y for _, y in cells)
            components.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
                "size": len(cells),
            })
    return components


def _is_frame(obj: dict) -> bool:
    if obj["h"] < 3 or obj["w"] < 3:
        return False
    border = {
        (r, c)
        for r in range(obj["r1"], obj["r2"] + 1)
        for c in range(obj["c1"], obj["c2"] + 1)
        if r in (obj["r1"], obj["r2"]) or c in (obj["c1"], obj["c2"])
    }
    return set(obj["cells"]) == border


def _object_grid(obj: dict) -> list[list[int]]:
    out = [[0] * obj["w"] for _ in range(obj["h"])]
    for r, c in obj["cells"]:
        out[r - obj["r1"]][c - obj["c1"]] = obj["color"]
    return out


def _rotate_cw(grid) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _stamp(out, sub, r0: int, c0: int) -> None:
    for r, row in enumerate(sub):
        for c, value in enumerate(row):
            if value and 0 <= r0 + r < len(out) and 0 <= c0 + c < len(out[0]):
                out[r0 + r][c0 + c] = value


def _solve(
    grid,
    *,
    placement: str = "center",
    solid_order: str = "top_left",
    allow_rotation: bool = True,
    exact_only: bool = False,
):
    components = _components(grid)
    frames = sorted(
        [obj for obj in components if _is_frame(obj)],
        key=lambda obj: (obj["r1"], obj["c1"]),
    )
    solids = [obj for obj in components if not _is_frame(obj)]
    if solid_order == "top_left":
        solids.sort(key=lambda obj: (obj["r1"], obj["c1"]))
    elif solid_order == "area":
        solids.sort(key=lambda obj: (obj["size"], obj["r1"], obj["c1"]))
    else:
        raise ValueError(f"unknown solid order {solid_order!r}")

    out = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]

    used: set[int] = set()
    for solid in solids:
        original = _object_grid(solid)
        rotated = _rotate_cw(original)
        candidates = []
        for index, frame in enumerate(frames):
            if index in used:
                continue
            ih, iw = frame["h"] - 2, frame["w"] - 2
            oriented = None
            if len(original) <= ih and len(original[0]) <= iw:
                oriented = original
            elif allow_rotation and len(rotated) <= ih and len(rotated[0]) <= iw:
                oriented = rotated
            if oriented is None:
                continue
            if exact_only and (len(oriented), len(oriented[0])) != (ih, iw):
                continue
            candidates.append((
                ih * iw - len(oriented) * len(oriented[0]),
                frame["r1"], frame["c1"], index, frame, oriented,
            ))
        if not candidates:
            continue
        _, _, _, index, frame, oriented = min(candidates, key=lambda item: item[:3])
        used.add(index)
        if placement == "center":
            r0 = frame["r1"] + 1 + (frame["h"] - 2 - len(oriented)) // 2
            c0 = frame["c1"] + 1 + (frame["w"] - 2 - len(oriented[0])) // 2
        elif placement == "top_left":
            r0, c0 = frame["r1"] + 1, frame["c1"] + 1
        else:
            raise ValueError(f"unknown placement {placement!r}")
        _stamp(out, oriented, r0, c0)
    return out


def _frame_first(grid):
    components = _components(grid)
    frames = sorted([obj for obj in components if _is_frame(obj)], key=lambda x: (x["r1"], x["c1"]))
    solids = sorted([obj for obj in components if not _is_frame(obj)], key=lambda x: (x["r1"], x["c1"]))
    out = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]
    used: set[int] = set()
    for frame in frames:
        ih, iw = frame["h"] - 2, frame["w"] - 2
        for index, solid in enumerate(solids):
            if index in used:
                continue
            original = _object_grid(solid)
            rotated = _rotate_cw(original)
            if len(original) <= ih and len(original[0]) <= iw:
                oriented = original
            elif len(rotated) <= ih and len(rotated[0]) <= iw:
                oriented = rotated
            else:
                continue
            used.add(index)
            r0 = frame["r1"] + 1 + (ih - len(oriented)) // 2
            c0 = frame["c1"] + 1 + (iw - len(oriented[0])) // 2
            _stamp(out, oriented, r0, c0)
            break
    return out


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must lie in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    components = _components(grid)
    frames = [obj for obj in components if _is_frame(obj)]
    solids = [obj for obj in components if not _is_frame(obj)]
    problems: list[str] = []
    if len(frames) != 2:
        problems.append(f"expected exactly 2 hollow rectangular frames, found {len(frames)}")
    if not 2 <= len(solids) <= 6:
        problems.append(f"expected 2..6 loose non-frame components, found {len(solids)}")
    frame_colors = {obj["color"] for obj in frames}
    if len(frame_colors) != len(frames):
        problems.append("frame colors must be distinct")
    if frame_colors & {obj["color"] for obj in solids}:
        problems.append("frame colors must not be reused by loose shapes")
    if len(frames) == 2 and solids:
        frame_only = [[0] * width for _ in grid]
        for frame in frames:
            for r, c in frame["cells"]:
                frame_only[r][c] = frame["color"]
        if _solve(grid) == frame_only:
            problems.append("no loose shape can be filed into either frame")
    return sorted(set(problems))


def strict_canonical_like(grid):
    return self_check(grid)


# Named rivals are diagnostics, never label authority.
def _rival_top_left(grid):
    return _solve(grid, placement="top_left")


def _rival_exact_only(grid):
    return _solve(grid, exact_only=True)


def _rival_area_order(grid):
    return _solve(grid, solid_order="area")


def _rival_never_rotate(grid):
    return _solve(grid, allow_rotation=False)


def _differs_from(rival: Callable, grid) -> bool:
    return rival(deepcopy(grid)) != _solve(grid)


SEMANTIC_RIVALS = {
    "top_left_in_frame": _rival_top_left,
    "exact_bbox_only": _rival_exact_only,
    "solid_area_order": _rival_area_order,
    "frame_first": _frame_first,
    "never_rotate": _rival_never_rotate,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("top_left_in_frame", "exact_bbox_only", "solid_area_order")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "centered_slack": lambda grid: (
        _differs_from(_rival_top_left, grid)
        and _differs_from(_rival_exact_only, grid)
    ),
    "order_competition": lambda grid: (
        _differs_from(_rival_area_order, grid)
        and _differs_from(_frame_first, grid)
    ),
    "rotation_required": lambda grid: _differs_from(_rival_never_rotate, grid),
}
WITNESS_RIVALS = {
    "centered_slack": ["top_left_in_frame", "exact_bbox_only"],
    "order_competition": ["solid_area_order", "frame_first"],
    "rotation_required": ["never_rotate"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any named competitor that demos fail to eliminate for query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            changes_query = (
                competitor(deepcopy(query["input"])) != query["output"]
            )
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
