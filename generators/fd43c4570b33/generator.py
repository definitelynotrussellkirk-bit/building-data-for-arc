"""Generator for ``fd43c4570b33`` — Dual Inward Slide.

Two colored objects move horizontally toward one another in lock-step.  The
left object moves one column right per step and the right object moves one
column left per step.  Motion stops *for both objects* immediately before the
next simultaneous step would collide, touch a full-height color-8 wall, or
leave the grid.  The output keeps the wall, clears the original object cells,
and paints both final objects color 7.

The ordinary schedule deliberately alternates collision-limited lessons,
left-object wall stops, right-object wall stops, overlapping row bands, and
disjoint row bands.  Three scheduled profiles anchor the exact canonical
(height, width, palette-size) profiles and use the canonical object colors.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd43c4570b33"
TASK_ID = "fd43c4570b33"
VERSION = "4.0.0"
RULE_HASH = "050fdd26887a"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 0-background grid contains exactly two differently colored connected "
    "objects, with the left object's bounding box strictly left of the right "
    "object. They advance inward simultaneously (left object rightward, right "
    "object leftward). Both stop at the last common step before either object "
    "would collide with the other or a full-height color-8 wall. The output "
    "preserves the wall and recolors both final objects to 7."
)

INVARIANTS = [
    "background is 0 and input color 7 is absent",
    "exactly two distinct-color, 4-connected non-wall objects are present",
    "the two object bounding boxes are horizontally ordered with a visible gap",
    "a wall, when present, is exactly one full-height color-8 column in the gap",
    "every accepted scene permits at least one simultaneous movement step",
    "without a wall, occupied rows overlap and collision is the stopping event",
    "with a wall, exactly one side reaches it first, making lock-step stopping observable",
]

STOP_MODES = ("collision", "left_wall", "right_wall")
ROW_RELATIONS = ("overlap", "disjoint")

AXES = {
    "grid_h": {"type": "int", "default": "canonical profile or difficulty-shaped", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "canonical profile or fit-to-scene", "valid": "12..24"},
    "left_size": {"type": "int", "default": "3..5 cells", "valid": "2..6"},
    "right_size": {"type": "int", "default": "3..5 cells", "valid": "2..6"},
    "gap": {"type": "int", "default": "3..8 blank columns between bboxes", "valid": "3..12"},
    "row_relation": {"type": "str", "default": "scheduled overlap/disjoint", "valid": "|".join(ROW_RELATIONS)},
    "stop_mode": {"type": "str", "default": "scheduled collision/left_wall/right_wall", "valid": "|".join(STOP_MODES)},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"stop_mode": "collision", "row_relation": "disjoint"},
    {"stop_mode": "left_wall", "gap": 3},
    {"stop_mode": "right_wall", "gap": 3},
    {"row_relation": "disjoint", "gap": 3},
    {"gap": 12, "grid_w": 12},
]

MIN_STRICT_FRAC = 0.40
SCHEDULE_PROFILES = tuple(range(6))

_CANONICAL_PROFILES = {
    0: {
        "grid_h": 7,
        "grid_w": 12,
        "left_size": 3,
        "right_size": 4,
        "gap": 5,
        "row_relation": "overlap",
        "stop_mode": "collision",
    },
    1: {
        "grid_h": 8,
        "grid_w": 13,
        "left_size": 3,
        "right_size": 4,
        "gap": 7,
        "row_relation": "disjoint",
        "stop_mode": "right_wall",
    },
    2: {
        "grid_h": 9,
        "grid_w": 14,
        "left_size": 4,
        "right_size": 4,
        "gap": 7,
        "row_relation": "overlap",
        "stop_mode": "right_wall",
    },
}

_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    ),
}

_OBJECT_COLORS = (1, 2, 3, 4, 5, 6, 9)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Expose the six-way deterministic curriculum schedule to the semantic gate."""
    del seed, difficulty
    return sample_index % 6


def _incompatible(message: str, *axes: str) -> ValueError:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)  # override-contract v7 structured rejection
    return exc


def _normalize(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variants(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    for base in _BASE_SHAPES[size]:
        for mirror in (False, True):
            for turns in range(4):
                transformed: list[tuple[int, int]] = []
                for row, col in base:
                    if mirror:
                        col = -col
                    for _ in range(turns):
                        row, col = col, -row
                    transformed.append((row, col))
                variants.add(_normalize(transformed))
    return tuple(sorted(variants))


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 8) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _movement(
    left: set[tuple[int, int]],
    right: set[tuple[int, int]],
    wall: set[tuple[int, int]],
    height: int,
    width: int,
) -> dict[str, Any]:
    """Pure Python audit mirror of the Racket loop's stopping conditions."""
    current_left = set(left)
    current_right = set(right)
    steps = 0
    for _ in range(width + 3):
        next_left = {(r, c + 1) for r, c in current_left}
        next_right = {(r, c - 1) for r, c in current_right}
        reasons: set[str] = set()
        if any(not (0 <= r < height and 0 <= c < width) for r, c in next_left):
            reasons.add("left_boundary")
        if any(not (0 <= r < height and 0 <= c < width) for r, c in next_right):
            reasons.add("right_boundary")
        if next_left & wall:
            reasons.add("left_wall")
        if next_right & wall:
            reasons.add("right_wall")
        if next_left & next_right or next_left & current_right or next_right & current_left:
            reasons.add("collision")
        if reasons:
            stop_mode = "collision"
            if reasons == {"left_wall"}:
                stop_mode = "left_wall"
            elif reasons == {"right_wall"}:
                stop_mode = "right_wall"
            elif reasons != {"collision"}:
                stop_mode = "mixed"
            return {
                "left": current_left,
                "right": current_right,
                "steps": steps,
                "reasons": reasons,
                "stop_mode": stop_mode,
            }
        current_left = next_left
        current_right = next_right
        steps += 1
    raise RuntimeError("movement did not terminate within a grid-width bound")


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["rows must be nonempty lists"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        errors.append("grid values must be integer ARC colors 0..9")
    if 7 in flat:
        errors.append("input must not contain output color 7")

    wall_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    wall_col: int | None = None
    if wall_cells:
        wall_cols = {c for _, c in wall_cells}
        if len(wall_cols) != 1:
            errors.append("color-8 wall cells must occupy one column")
        else:
            wall_col = next(iter(wall_cols))
            expected = {(r, wall_col) for r in range(height)}
            if wall_cells != expected:
                errors.append("the color-8 wall must span the full grid height")

    components = _components(grid)
    if len(components) != 2:
        errors.append(f"expected exactly two non-wall objects, found {len(components)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "wall": wall_cells,
            "wall_col": wall_col,
            "components": components,
        }

    colors = [color for color, _ in components]
    if len(set(colors)) != 2:
        errors.append("the two objects must have distinct colors")
    if any(color in (0, 7, 8) for color in colors):
        errors.append("object colors must exclude 0, 7, and 8")

    ordered = sorted(components, key=lambda item: _bbox(item[1])[1])
    left_color, left_cells = ordered[0]
    right_color, right_cells = ordered[1]
    left_box = _bbox(left_cells)
    right_box = _bbox(right_cells)
    gap = right_box[1] - left_box[3] - 1
    if gap < 2:
        errors.append("object bounding boxes need at least two blank columns between them")
    if left_box[3] >= right_box[1]:
        errors.append("object bounding boxes must be strictly left/right ordered")

    left_rows = {r for r, _ in left_cells}
    right_rows = {r for r, _ in right_cells}
    row_relation = "overlap" if left_rows & right_rows else "disjoint"

    if wall_col is not None and not (left_box[3] < wall_col < right_box[1]):
        errors.append("the wall must lie strictly between the object bounding boxes")

    movement: dict[str, Any] | None = None
    if not errors:
        try:
            movement = _movement(left_cells, right_cells, wall_cells, height, width)
        except Exception as exc:  # structural failure is reported, never hidden
            errors.append(f"movement simulation failed: {exc}")
        if movement is not None:
            if movement["steps"] < 1:
                errors.append("accepted lessons must require at least one movement step")
            if wall_col is None:
                if row_relation != "overlap":
                    errors.append("wall-free lessons require occupied-row overlap")
                if movement["stop_mode"] != "collision":
                    errors.append("wall-free lessons must stop by object collision")
            else:
                if movement["stop_mode"] not in ("left_wall", "right_wall"):
                    errors.append("wall lessons require one uniquely limiting object")

    palette = set(flat)
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": ordered,
        "left_color": left_color,
        "right_color": right_color,
        "left": left_cells,
        "right": right_cells,
        "left_box": left_box,
        "right_box": right_box,
        "left_size": len(left_cells),
        "right_size": len(right_cells),
        "gap": gap,
        "row_relation": row_relation,
        "wall": wall_cells,
        "wall_col": wall_col,
        "movement": movement,
        "stop_mode": movement["stop_mode"] if movement is not None else None,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar, including stopping semantics."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def _draw_exact_int(ctx, label: str, lo: int, hi: int, default_values: list[int]) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, default_values)


def _draw_scene_parameters(
    ctx, canonical: dict[str, Any] | None, profile_index: int
) -> dict[str, Any]:
    if canonical is not None:
        return {
            label: ctx.draw_choice(label, [value])
            for label, value in canonical.items()
        }

    stop_override = ctx.overrides.get("stop_mode")
    row_override = ctx.overrides.get("row_relation")
    gap_override = ctx.overrides.get("gap")
    h_override = ctx.overrides.get("grid_h")
    w_override = ctx.overrides.get("grid_w")

    if ctx.difficulty == "easy":
        size_values = [2, 3, 4]
        h_values = list(range(7, 11))
        w_values = list(range(12, 17))
    elif ctx.difficulty == "hard":
        size_values = [4, 5, 6]
        h_values = list(range(11, 17))
        w_values = list(range(18, 25))
    else:
        size_values = [3, 4, 5]
        h_values = list(range(9, 14))
        w_values = list(range(14, 21))

    left_size = _draw_exact_int(ctx, "left_size", 2, 6, size_values)
    right_size = _draw_exact_int(ctx, "right_size", 2, 6, size_values)
    grid_h = ctx.draw_int("grid_h", 7, 16) if h_override is not None else None
    grid_w = ctx.draw_int("grid_w", 12, 24) if w_override is not None else None

    if stop_override is not None:
        stop_mode = ctx.draw_choice("stop_mode", STOP_MODES)
    elif row_override == "disjoint":
        stop_mode = ctx.draw_choice("stop_mode", ("left_wall", "right_wall"))
    elif gap_override is not None and int(gap_override) == 3:
        stop_mode = ctx.draw_choice("stop_mode", ("collision",))
    else:
        scheduled_stop = {
            0: "collision",
            1: "right_wall",
            2: "right_wall",
            3: "collision",
            4: "left_wall",
            5: "right_wall",
        }[profile_index]
        stop_mode = ctx.draw_choice("stop_mode", (scheduled_stop,))

    if row_override is not None:
        row_relation = ctx.draw_choice("row_relation", ROW_RELATIONS)
    elif stop_mode == "collision":
        row_relation = ctx.draw_choice("row_relation", ("overlap",))
    else:
        row_relation = ctx.draw_choice("row_relation", ROW_RELATIONS)

    if stop_mode == "collision" and row_relation == "disjoint":
        raise _incompatible(
            "collision stopping requires occupied-row overlap",
            "stop_mode",
            "row_relation",
        )

    if gap_override is not None:
        gap = ctx.draw_int("gap", 3, 12)
    else:
        gap_lo = 3 if stop_mode == "collision" else 4
        gap_hi = 8 if stop_mode == "collision" else 9
        if grid_w is not None:
            left_min_w = min(_shape_dims(shape)[1] for shape in _shape_variants(left_size))
            right_min_w = min(_shape_dims(shape)[1] for shape in _shape_variants(right_size))
            gap_hi = min(gap_hi, grid_w - left_min_w - right_min_w)
        if gap_hi < gap_lo:
            raise _incompatible(
                "grid_w cannot fit the selected object sizes and stop mode",
                "grid_w",
                "left_size",
                "right_size",
                "stop_mode",
            )
        gap = ctx.draw_int("gap", gap_lo, gap_hi)

    if stop_mode != "collision" and gap < 4:
        if row_relation == "disjoint":
            raise _incompatible(
                "disjoint occupied rows require a wall and at least four gap columns",
                "row_relation",
                "gap",
            )
        raise _incompatible(
            "an asymmetric wall stop needs at least four gap columns",
            "stop_mode",
            "gap",
        )

    return {
        "stop_mode": stop_mode,
        "row_relation": row_relation,
        "gap": gap,
        "left_size": left_size,
        "right_size": right_size,
        "grid_h": grid_h,
        "grid_w": grid_w,
        "h_values": h_values,
        "w_values": w_values,
    }


def _choose_shapes(ctx, params: dict[str, Any]) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    left_variants = _shape_variants(params["left_size"])
    right_variants = _shape_variants(params["right_size"])
    candidates: list[tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]] = []
    for left in left_variants:
        lh, lw = _shape_dims(left)
        for right in right_variants:
            rh, rw = _shape_dims(right)
            min_h = lh + rh if params["row_relation"] == "disjoint" else max(lh, rh)
            min_w = lw + params["gap"] + rw
            if params["grid_h"] is not None and min_h > params["grid_h"]:
                continue
            if params["grid_w"] is not None and min_w > params["grid_w"]:
                continue
            if params["row_relation"] == "overlap":
                left_rows = {r for r, _ in left}
                right_rows = {r for r, _ in right}
                if not left_rows & right_rows:
                    continue
            candidates.append((left, right))
    if not candidates:
        axes = ["left_size", "right_size", "gap"]
        if params["grid_h"] is not None:
            axes.append("grid_h")
        if params["grid_w"] is not None:
            axes.append("grid_w")
        if params["row_relation"] == "disjoint":
            axes.append("row_relation")
        raise _incompatible("requested exact axes cannot fit a connected shape pair", *axes)
    rng = ctx.draw_rng("shape_pair")
    return rng.choice(candidates)


def _finalize_dimensions(ctx, params: dict[str, Any], left, right) -> tuple[int, int]:
    lh, lw = _shape_dims(left)
    rh, rw = _shape_dims(right)
    min_h = lh + rh if params["row_relation"] == "disjoint" else max(lh, rh)
    min_w = lw + params["gap"] + rw

    if params["grid_h"] is None:
        values = [value for value in params["h_values"] if value >= min_h]
        if not values:
            values = [value for value in range(7, 17) if value >= min_h]
        if not values:
            raise _incompatible("no declared grid_h can fit the shape pair", "grid_h", "left_size", "right_size")
        params["grid_h"] = ctx.draw_choice("grid_h", values)
    if params["grid_w"] is None:
        values = [value for value in params["w_values"] if value >= min_w]
        if not values:
            values = [value for value in range(12, 25) if value >= min_w]
        if not values:
            raise _incompatible("no declared grid_w can fit the requested gap and shapes", "grid_w", "gap", "left_size", "right_size")
        params["grid_w"] = ctx.draw_choice("grid_w", values)
    return params["grid_h"], params["grid_w"]


def _place_rows(ctx, height: int, left, right, row_relation: str) -> tuple[int, int]:
    lh, _ = _shape_dims(left)
    rh, _ = _shape_dims(right)
    rng = ctx.draw_rng("vertical_placement")
    if row_relation == "disjoint":
        slack = height - lh - rh
        if slack < 0:
            raise _incompatible("grid_h cannot fit disjoint object row bands", "grid_h", "row_relation", "left_size", "right_size")
        top = rng.randint(0, slack)
        if rng.randrange(2):
            return top, top + lh
        return top + rh, top

    candidates: list[tuple[int, int]] = []
    for left_top in range(height - lh + 1):
        left_rows = {left_top + r for r, _ in left}
        for right_top in range(height - rh + 1):
            right_rows = {right_top + r for r, _ in right}
            if left_rows & right_rows:
                candidates.append((left_top, right_top))
    if not candidates:
        raise _incompatible("grid_h cannot realize occupied-row overlap", "grid_h", "row_relation")
    return rng.choice(candidates)


def _wall_column(stop_mode: str, left_end: int, gap: int, rng) -> int | None:
    if stop_mode == "collision":
        return None
    # d_left + wall + d_right = gap, and both clear-side distances are >= 1.
    if gap < 4:
        raise _incompatible("wall stop requires gap>=4", "gap", "stop_mode")
    if stop_mode == "left_wall":
        max_near = (gap - 2) // 2
        d_left = rng.randint(1, max_near)
        d_right = gap - 1 - d_left
        if not d_left < d_right:
            raise AssertionError("left-wall construction lost its strict inequality")
    else:
        max_near = (gap - 2) // 2
        d_right = rng.randint(1, max_near)
        d_left = gap - 1 - d_right
        if not d_right < d_left:
            raise AssertionError("right-wall construction lost its strict inequality")
    return left_end + 1 + d_left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_index = schedule_profile(seed, sample_index, difficulty)
    canonical = _CANONICAL_PROFILES.get(profile_index) if not overrides else None
    params = _draw_scene_parameters(ctx, canonical, profile_index)
    left_shape, right_shape = _choose_shapes(ctx, params)
    height, width = _finalize_dimensions(ctx, params, left_shape, right_shape)

    lh, lw = _shape_dims(left_shape)
    rh, rw = _shape_dims(right_shape)
    horizontal_slack = width - (lw + params["gap"] + rw)
    if horizontal_slack < 0:
        raise _incompatible("grid_w is too small for the requested gap and shapes", "grid_w", "gap", "left_size", "right_size")
    placement_rng = ctx.draw_rng("horizontal_placement")
    left_col = placement_rng.randint(0, horizontal_slack)
    right_col = left_col + lw + params["gap"]
    left_top, right_top = _place_rows(ctx, height, left_shape, right_shape, params["row_relation"])

    grid = full_grid(height, width, 0)
    if canonical is not None:
        left_color, right_color = 3, 4
    else:
        left_color, right_color = ctx.draw_distinct_colors(
            "object_colors", n=2, exclude={0, 7, 8}
        )

    for dr, dc in left_shape:
        grid[left_top + dr][left_col + dc] = left_color
    for dr, dc in right_shape:
        grid[right_top + dr][right_col + dc] = right_color

    wall_col = _wall_column(
        params["stop_mode"],
        left_col + lw - 1,
        params["gap"],
        ctx.draw_rng("wall_position"),
    )
    if wall_col is not None:
        for row in range(height):
            grid[row][wall_col] = 8

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator constructed an invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis in AXES:
        requested = ctx.axis_value(axis)
        if requested is not None and observed[axis] != requested:
            raise AssertionError(
                f"constructed {axis}={observed[axis]!r}, requested {requested!r}"
            )
    return grid


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid itself."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "left_size": info["left_size"],
        "right_size": info["right_size"],
        "gap": info["gap"],
        "row_relation": info["row_relation"],
        "stop_mode": info["stop_mode"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python audit mirror only; the canonical Racket program remains authority."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = full_grid(info["height"], info["width"], 0)
    for row, col in info["wall"]:
        out[row][col] = 8
    for row, col in info["movement"]["left"] | info["movement"]["right"]:
        out[row][col] = 7
    return out


def strict_canonical_like(grid) -> list[str]:
    """Recognize the three canonical semantic profiles, not only coarse size."""
    info = _analysis(grid)
    reasons = list(info["errors"])
    if reasons:
        return reasons
    if {info["left_color"], info["right_color"]} != {3, 4}:
        reasons.append("canonical objects use colors 3 and 4")

    profile = (info["height"], info["width"])
    expected: dict[str, Any] | None = None
    for candidate in _CANONICAL_PROFILES.values():
        if (candidate["grid_h"], candidate["grid_w"]) == profile:
            expected = candidate
            break
    if expected is None:
        reasons.append(f"dimensions {profile} are not a canonical profile")
        return reasons

    for key in ("left_size", "right_size", "gap", "row_relation", "stop_mode"):
        if info[key] != expected[key]:
            reasons.append(f"canonical profile expects {key}={expected[key]!r}, got {info[key]!r}")
    return reasons


def _lawful_info(grid) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


def _canonical_anchor(grid) -> bool:
    return not strict_canonical_like(grid)


def _recolor_in_place(grid: list[list[int]]) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = full_grid(info["height"], info["width"], 0)
    for row, col in info["wall"]:
        out[row][col] = 8
    for row, col in info["left"] | info["right"]:
        out[row][col] = 7
    return out


def _slide_one_to_wall(cells: set[tuple[int, int]], dc: int, wall: set[tuple[int, int]], height: int, width: int) -> set[tuple[int, int]]:
    current = set(cells)
    for _ in range(width + 2):
        nxt = {(r, c + dc) for r, c in current}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in nxt) or nxt & wall:
            return current
        current = nxt
    raise RuntimeError("independent rival did not terminate")


def _independent_to_blocker(grid: list[list[int]]) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if not info["wall"]:
        return rule_mirror(grid)
    left = _slide_one_to_wall(info["left"], 1, info["wall"], info["height"], info["width"])
    right = _slide_one_to_wall(info["right"], -1, info["wall"], info["height"], info["width"])
    out = full_grid(info["height"], info["width"], 0)
    for row, col in info["wall"]:
        out[row][col] = 8
    for row, col in left | right:
        out[row][col] = 7
    return out


SEMANTIC_RIVALS = {
    "recolor_in_place": _recolor_in_place,
    "independent_to_blocker": _independent_to_blocker,
}

SEMANTIC_WITNESSES = {
    "canonical_profile_anchor": _canonical_anchor,
    "collision_stop": lambda grid: _witness(grid, lambda info: info["stop_mode"] == "collision"),
    "left_wall_limits_both": lambda grid: _witness(grid, lambda info: info["stop_mode"] == "left_wall"),
    "right_wall_limits_both": lambda grid: _witness(grid, lambda info: info["stop_mode"] == "right_wall"),
    "overlapping_occupied_rows": lambda grid: _witness(grid, lambda info: info["row_relation"] == "overlap"),
    "disjoint_rows_still_lockstep": lambda grid: _witness(grid, lambda info: info["row_relation"] == "disjoint"),
    "nonzero_motion": lambda grid: _witness(grid, lambda info: info["movement"]["steps"] >= 1),
    "multi_step_motion": lambda grid: _witness(grid, lambda info: info["movement"]["steps"] >= 2),
}

WITNESS_RIVALS = {
    "left_wall_limits_both": ["independent_to_blocker"],
    "right_wall_limits_both": ["independent_to_blocker"],
    "nonzero_motion": ["recolor_in_place"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    reasons: list[str] = []
    episodes = [*demos, query]
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(f"{role} input is malformed: {findings[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the simultaneous-motion rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demos do not falsify shortcut '{name}'")
    return reasons
