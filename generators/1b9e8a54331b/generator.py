"""Generator for 5b:m29 — directional rays by seed color.

Color 2 emits a horizontal color-7 ray; color 1 emits a vertical color-8
ray.  Color-5 cells block rays and stay unchanged.  Horizontal/vertical
ray intersections become color 6 and every other cell becomes 0.

Ordinary samples are constructive teaching examples: each one contains a
crossing and a visible wall-stop consequence.  This removes the two audited
lesson shortcuts ("ignore crossings" and "ignore walls") from every
three-example window rather than hoping random placement happens to refute
them.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b9e8a54331b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "db20de981b4f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a 0-background grid, isolated color-2 seeds emit horizontal color-7 "
    "rays and isolated color-1 seeds emit vertical color-8 rays. Color-5 line "
    "segments stop rays and remain gray; cells reached by both ray families "
    "become color 6. Ordinary draws constructively include both a crossing "
    "and a wall-stop witness."
)

INVARIANTS = [
    "background is 0 and inputs use only colors 0, 1, 2, and 5",
    "1-2 isolated color-2 seeds emit horizontal rays",
    "1-2 isolated color-1 seeds emit vertical rays",
    "a color-5 line segment of length 4-7 blocks at least one ray",
    "ordinary draws contain at least one color-6 crossing in the output",
    "seeds and walls are mutually non-adjacent under 8-connectivity",
]

_BLOCK_AXES = ("horizontal", "vertical")
DEGENERATE_TEXTURES = ("no_seeds", "no_walls", "no_crossings")
HELPFUL_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
SCHEDULE_PROFILES = (0, 1, 2, 3, 4, 5)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled by difficulty",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled by difficulty",
        "valid": "8..14",
    },
    "horizontal_seed_count": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "vertical_seed_count": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "block_axis": {
        "type": "str",
        "default": "alternates horizontal/vertical",
        "valid": "horizontal|vertical",
    },
}

_BAND_SIZES = {
    "easy": ((7, 8), (8, 9), (9, 10), (8, 11)),
    "medium": ((9, 10), (10, 12), (11, 13), (10, 14)),
    "hard": ((12, 12), (13, 14), (14, 13), (14, 14)),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del difficulty
    return (seed + sample_index) % len(SCHEDULE_PROFILES)


def _scheduled_size(seed: int, sample_index: int, band: str) -> tuple[int, int]:
    options = _BAND_SIZES[band]
    return options[(seed * 3 + sample_index) % len(options)]


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    lo: int,
    hi: int,
    default: int,
) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _draw_choice_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    options: tuple[Any, ...],
    default: Any,
):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _pick_isolated_positions(
    low: int,
    high: int,
    count: int,
    variant: int,
) -> tuple[int, ...]:
    """Pick a deterministic, varied set of mutually non-adjacent positions."""
    if low > high:
        raise ValueError(f"empty coordinate interval {low}..{high}")
    candidates = [
        choice
        for choice in combinations(range(low, high + 1), count)
        if all(b - a >= 2 for a, b in zip(choice, choice[1:]))
    ]
    if not candidates:
        raise ValueError(f"cannot place {count} isolated points in {low}..{high}")
    return candidates[variant % len(candidates)]


def _reflect_grid(
    grid: list[list[int]],
    *,
    horizontal: bool,
    vertical: bool,
) -> list[list[int]]:
    reflected = [list(reversed(row)) for row in grid] if horizontal else [list(row) for row in grid]
    if vertical:
        reflected.reverse()
    return reflected


def _ordinary_layout(
    h: int,
    w: int,
    horizontal_seed_count: int,
    vertical_seed_count: int,
    block_axis: str,
    variant: int,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)

    if block_axis == "horizontal":
        # A vertical wall blocks every horizontal emitter, with one column
        # beyond the wall so the ignore-walls rival has an observable error.
        wall_c = w - 2
        max_wall_len = min(7, h - 3)
        wall_len = 4 + variant % (max_wall_len - 3)
        horizontal_rows = _pick_isolated_positions(
            0, wall_len - 1, horizontal_seed_count, variant // 2
        )
        vertical_cols = _pick_isolated_positions(
            2, wall_c - 2, vertical_seed_count, variant // 3
        )
        horizontal_seed_col = variant % 2
        vertical_seed_row = h - 1 - ((variant // 2) % 2)
        for r in range(wall_len):
            grid[r][wall_c] = 5
        for r in horizontal_rows:
            grid[r][horizontal_seed_col] = 2
        for c in vertical_cols:
            grid[vertical_seed_row][c] = 1
    elif block_axis == "vertical":
        # A horizontal wall blocks every vertical emitter, with one row beyond
        # it.  Horizontal emitters sit above the wall and cross all vertical
        # rays before those rays are stopped.
        wall_r = h - 2
        max_wall_len = min(7, w - 3)
        wall_len = 4 + variant % (max_wall_len - 3)
        vertical_cols = _pick_isolated_positions(
            0, wall_len - 1, vertical_seed_count, variant // 2
        )
        horizontal_rows = _pick_isolated_positions(
            1, wall_r - 1, horizontal_seed_count, variant // 3
        )
        vertical_seed_row = variant % 2
        horizontal_seed_col = w - 1 - ((variant // 2) % 2)
        for c in range(wall_len):
            grid[wall_r][c] = 5
        for c in vertical_cols:
            grid[vertical_seed_row][c] = 1
        for r in horizontal_rows:
            grid[r][horizontal_seed_col] = 2
    else:
        raise ValueError(f"unknown block_axis: {block_axis!r}")

    # Reflections preserve the semantic axis while multiplying layout variety.
    return _reflect_grid(
        grid,
        horizontal=bool((variant // 5) % 2),
        vertical=bool((variant // 7) % 2),
    )


def _draw_from_degenerate(name: str, h: int, w: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    if name == "no_seeds":
        for c in range(1, min(w - 1, 7)):
            grid[2][c] = 5
        return grid
    if name == "no_walls":
        grid[2][1] = 2
        grid[h - 2][w - 3] = 1
        return grid
    if name == "no_crossings":
        # The vertical wall lies strictly before the potential intersection
        # (2, w-3), so the horizontal ray stops and color 6 never appears.
        wall_c = w - 4
        for r in range(4):
            grid[r][wall_c] = 5
        grid[2][1] = 2
        grid[h - 2][w - 3] = 1
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    allowed = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(
            f"texture override {texture!r} is not one of {DEGENERATE_TEXTURES}"
        )
    if texture is not None:
        incompatible = sorted(
            key
            for key in overrides
            if key in {"horizontal_seed_count", "vertical_seed_count", "block_axis"}
            and overrides[key] is not None
        )
        if incompatible:
            raise ValueError(
                "degenerate texture is incompatible with ordinary semantic axes: "
                + ", ".join(incompatible)
            )

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    default_h, default_w = _scheduled_size(seed, sample_index, band)
    h = _draw_int_axis(ctx, overrides, "grid_h", 7, 14, default_h)
    w = _draw_int_axis(ctx, overrides, "grid_w", 8, 14, default_w)

    if texture is not None:
        grid = _draw_from_degenerate(texture, h, w)
        errors = self_check(grid, difficulty=band, meta={"texture": texture})
        if errors:
            raise AssertionError(f"internal degenerate invariant failed: {errors}")
        return grid

    default_horizontal_count = 1 + ((seed + sample_index + sample_index // 2) % 2)
    default_vertical_count = 1 + ((seed * 3 + sample_index // 2) % 2)
    default_block_axis = _BLOCK_AXES[(seed + sample_index) % 2]
    horizontal_seed_count = _draw_int_axis(
        ctx,
        overrides,
        "horizontal_seed_count",
        1,
        2,
        default_horizontal_count,
    )
    vertical_seed_count = _draw_int_axis(
        ctx,
        overrides,
        "vertical_seed_count",
        1,
        2,
        default_vertical_count,
    )
    block_axis = _draw_choice_axis(
        ctx,
        overrides,
        "block_axis",
        _BLOCK_AXES,
        default_block_axis,
    )

    grid = _ordinary_layout(
        h,
        w,
        horizontal_seed_count,
        vertical_seed_count,
        block_axis,
        variant=seed * 101 + sample_index,
    )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "horizontal_seed_count": horizontal_seed_count,
        "vertical_seed_count": vertical_seed_count,
        "block_axis": block_axis,
    }
    if observed != expected:
        raise AssertionError(f"observer mismatch: expected {expected}, got {observed}")
    if not _has_crossing(grid):
        raise AssertionError("ordinary sample failed to exhibit a crossing")
    return grid


def _inspect(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if not (7 <= h <= 14 and 8 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 7..14 by 8..14")

    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("grid contains a non-ARC color")
                return info, errors
    palette = {value for row in grid for value in row}
    illegal = sorted(palette - {0, 1, 2, 5})
    if illegal:
        errors.append(f"input uses unsupported colors: {illegal}")
    if 0 not in palette:
        errors.append("background color 0 is absent")

    horizontal_seeds = tuple(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 2
    )
    vertical_seeds = tuple(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 1
    )
    wall_cells = tuple(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 5
    )
    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "palette": tuple(sorted(palette)),
            "horizontal_seeds": horizontal_seeds,
            "vertical_seeds": vertical_seeds,
            "horizontal_seed_count": len(horizontal_seeds),
            "vertical_seed_count": len(vertical_seeds),
            "wall_cells": wall_cells,
        }
    )
    if not errors:
        info["blocked_axes"] = tuple(sorted(_blocked_axes(grid)))
        info["has_crossing"] = _has_crossing(grid)
    return info, errors


def _ordinary_errors(grid: Any, info: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    h = info["grid_h"]
    w = info["grid_w"]
    h_count = info["horizontal_seed_count"]
    v_count = info["vertical_seed_count"]
    wall_cells = info["wall_cells"]
    if not (1 <= h_count <= 2):
        errors.append(f"expected 1..2 color-2 seeds, got {h_count}")
    if not (1 <= v_count <= 2):
        errors.append(f"expected 1..2 color-1 seeds, got {v_count}")
    if len(wall_cells) < 4:
        errors.append(f"expected at least four color-5 wall cells, got {len(wall_cells)}")

    seeds = set(info["horizontal_seeds"]) | set(info["vertical_seeds"])
    for r, c in seeds:
        neighbors = [
            (rr, cc)
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
            if (rr, cc) != (r, c) and grid[rr][cc] != 0
        ]
        if neighbors:
            errors.append(f"seed at {(r, c)} is not 8-neighbor isolated")
            break

    for r, c in wall_cells:
        if not any(
            0 <= r + dr < h
            and 0 <= c + dc < w
            and grid[r + dr][c + dc] == 5
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        ):
            errors.append(f"isolated wall cell at {(r, c)}")
            break
    return errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _inspect(grid)
    if not errors:
        errors.extend(_ordinary_errors(grid, info))
    blocked_axes = info.get("blocked_axes", ())
    if not errors and len(blocked_axes) != 1:
        errors.append(
            "ordinary axis observer needs exactly one blocked ray family, got "
            + repr(blocked_axes)
        )
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "horizontal_seed_count": info["horizontal_seed_count"],
        "vertical_seed_count": info["vertical_seed_count"],
        "block_axis": blocked_axes[0],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info, errors = _inspect(grid)
    if errors:
        return errors
    texture = (meta or {}).get("texture")
    if texture is None:
        errors.extend(_ordinary_errors(grid, info))
        return errors
    if texture not in DEGENERATE_TEXTURES:
        return [f"unknown texture metadata: {texture!r}"]
    if texture == "no_seeds" and (
        info["horizontal_seed_count"] or info["vertical_seed_count"]
    ):
        errors.append("no_seeds texture contains a seed")
    elif texture == "no_walls" and info["wall_cells"]:
        errors.append("no_walls texture contains a wall")
    elif texture == "no_crossings" and info["has_crossing"]:
        errors.append("no_crossings texture produces a crossing")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def _ray_sets(
    grid: Any,
    *,
    honor_walls: bool = True,
    swap_seed_directions: bool = False,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    horizontal: set[tuple[int, int]] = set()
    vertical: set[tuple[int, int]] = set()
    horizontal_color = 1 if swap_seed_directions else 2
    vertical_color = 2 if swap_seed_directions else 1

    for r in range(h):
        for c in range(w):
            if grid[r][c] == horizontal_color:
                horizontal.add((r, c))
                for dc in (-1, 1):
                    cc = c + dc
                    while 0 <= cc < w:
                        if honor_walls and grid[r][cc] == 5:
                            break
                        horizontal.add((r, cc))
                        cc += dc
            if grid[r][c] == vertical_color:
                vertical.add((r, c))
                for dr in (-1, 1):
                    rr = r + dr
                    while 0 <= rr < h:
                        if honor_walls and grid[rr][c] == 5:
                            break
                        vertical.add((rr, c))
                        rr += dr
    return horizontal, vertical


def _render_rays(
    grid: Any,
    *,
    honor_walls: bool = True,
    crossing_color: int = 6,
    swap_seed_directions: bool = False,
) -> list[list[int]]:
    info, errors = _inspect(grid)
    if errors:
        raise ValueError("; ".join(errors))
    horizontal, vertical = _ray_sets(
        grid,
        honor_walls=honor_walls,
        swap_seed_directions=swap_seed_directions,
    )
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    for r in range(info["grid_h"]):
        for c in range(info["grid_w"]):
            point = (r, c)
            if grid[r][c] == 5:
                out[r][c] = 5
            elif point in horizontal and point in vertical:
                out[r][c] = crossing_color
            elif point in horizontal:
                out[r][c] = 7
            elif point in vertical:
                out[r][c] = 8
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    return _render_rays(grid)


def _has_crossing(grid: Any) -> bool:
    horizontal, vertical = _ray_sets(grid)
    return bool(horizontal & vertical)


def _blocked_axes(grid: Any) -> set[str]:
    """Return ray families for which a wall hides at least one output cell."""
    h, w = len(grid), len(grid[0])
    blocked: set[str] = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 2:
                for dc in (-1, 1):
                    cc = c + dc
                    while 0 <= cc < w and grid[r][cc] != 5:
                        cc += dc
                    if 0 <= cc < w and grid[r][cc] == 5:
                        cc += dc
                        while 0 <= cc < w:
                            if grid[r][cc] != 5:
                                blocked.add("horizontal")
                                break
                            cc += dc
            elif grid[r][c] == 1:
                for dr in (-1, 1):
                    rr = r + dr
                    while 0 <= rr < h and grid[rr][c] != 5:
                        rr += dr
                    if 0 <= rr < h and grid[rr][c] == 5:
                        rr += dr
                        while 0 <= rr < h:
                            if grid[rr][c] != 5:
                                blocked.add("vertical")
                                break
                            rr += dr
    return blocked


def _rival_ignore_walls(grid: Any) -> list[list[int]]:
    return _render_rays(grid, honor_walls=False)


def _rival_horizontal_precedence_no_color6(grid: Any) -> list[list[int]]:
    return _render_rays(grid, crossing_color=7)


def _rival_swap_seed_directions(grid: Any) -> list[list[int]]:
    return _render_rays(grid, swap_seed_directions=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_walls": _rival_ignore_walls,
    "horizontal_precedence_no_color6": _rival_horizontal_precedence_no_color6,
    "swap_seed_directions": _rival_swap_seed_directions,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    valid_pairs: list[dict[str, Any]] = []
    saw_crossing = False
    saw_wall_stop = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the pinned rule")
            continue
        valid_pairs.append(pair)
        saw_crossing |= any(6 in row for row in expected)
        saw_wall_stop |= _rival_ignore_walls(pair["input"]) != expected

    if not saw_crossing:
        reasons.append("demonstrations do not exhibit crossing color 6")
    if not saw_wall_stop:
        reasons.append("demonstrations do not exhibit a ray stopped by a wall")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_pairs and all(rival(pair["input"]) == pair["output"] for pair in valid_pairs):
            reasons.append(f"demonstrations do not refute competitor {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input invalid: {'; '.join(query_errors)}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the pinned rule")

    return reasons
