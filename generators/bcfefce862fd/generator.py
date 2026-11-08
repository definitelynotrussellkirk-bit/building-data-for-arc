"""Generator for ``Fill the Rectangle from Opposite Corners``.

Two equal nonzero markers occupy opposite diagonal corners of an axis-aligned
rectangle.  The authoritative Racket rule fills the marker bounding box with
the marker color.  Normal generated scenes keep both rectangle dimensions at
least three so the solid-fill lesson visibly differs from marker-only and
outline-only shortcuts; ``self_check`` remains broader and accepts every lawful
2-D rectangle with distinct marker rows and columns.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bcfefce862fd"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8bb000d0cbe5"

SUMMARY = (
    "A 0-background grid contains exactly two equal-color markers at opposite "
    "diagonal corners of a rectangle. Return a same-size grid whose inclusive "
    "marker bounding box is filled solidly with that color and whose remaining "
    "cells are 0. Ordinary lessons vary both diagonal orientations, rectangle "
    "shape, color, grid size, and edge/interior placement."
)

INVARIANTS = [
    "background is 0 and marker colors are ARC colors 1..9",
    "exactly two same-color markers occupy distinct rows and distinct columns",
    "ordinary generated rectangles are 3..5 cells high and 3..5 cells wide",
    "the output is the inclusive marker bounding box filled with marker color",
    "every four consecutive ordinary samples cover both diagonals and square, tall, and wide rectangles",
]

DIAGONALS = ("main", "anti")
PLACEMENTS = ("interior", "top", "bottom", "left", "right")
RECTANGLE_SCHEDULE = ((3, 3), (5, 3), (3, 5), (4, 4))
GRID_HEIGHTS = {
    "easy": (7, 8),
    "medium": (8, 9),
    "hard": (9, 10),
}
GRID_WIDTHS = {
    "easy": (7, 8, 9),
    "medium": (9, 10, 11),
    "hard": (10, 11, 12),
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = tuple(range(20))  # lcm(rectangle cycle 4, placement cycle 5)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded 7..10 schedule",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded 7..12 schedule",
        "valid": "7..12",
    },
    "rect_height": {
        "type": "int",
        "default": "four-sample 3|5|3|4 schedule",
        "valid": "3..5",
    },
    "rect_width": {
        "type": "int",
        "default": "four-sample 3|3|5|4 schedule",
        "valid": "3..5",
    },
    "marker_color": {
        "type": "int",
        "default": "alternating low/high schedule covering 1..9",
        "valid": "1..9",
    },
    "diagonal": {
        "type": "str",
        "default": "alternating main/anti by sample_index",
        "valid": "main|anti",
    },
    "placement": {
        "type": "str",
        "default": "cyclic interior/top/bottom/left/right",
        "valid": "interior|top|bottom|left|right",
    },
}

# Every declared axis combination is constructible: the minimum grid dimension
# is 7, the maximum rectangle dimension is 5, and every placement keeps at
# least one cell of margin on non-selected edges.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _has_override(overrides: dict[str, Any], name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _draw_scheduled_int(
    ctx,
    overrides: dict[str, Any],
    name: str,
    lo: int,
    hi: int,
    scheduled: int,
) -> int:
    if _has_override(overrides, name):
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (scheduled,))


def _draw_scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    name: str,
    options: tuple[str, ...],
    scheduled: str,
) -> str:
    if _has_override(overrides, name):
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (scheduled,)))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the complete 20-slot morphology schedule to semantic audits."""
    del seed, difficulty
    return int(sample_index) % 20


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    h_options = GRID_HEIGHTS[band]
    w_options = GRID_WIDTHS[band]
    scheduled_h = h_options[int(sample_index) % len(h_options)]
    scheduled_w = w_options[int(sample_index) % len(w_options)]
    scheduled_rect_h, scheduled_rect_w = RECTANGLE_SCHEDULE[
        int(sample_index) % len(RECTANGLE_SCHEDULE)
    ]

    h = _draw_scheduled_int(ctx, overrides, "grid_h", 7, 10, scheduled_h)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", 7, 12, scheduled_w)
    rect_h = _draw_scheduled_int(
        ctx, overrides, "rect_height", 3, 5, scheduled_rect_h
    )
    rect_w = _draw_scheduled_int(
        ctx, overrides, "rect_width", 3, 5, scheduled_rect_w
    )
    sample_slot = int(sample_index)
    scheduled_color = (
        1 + (sample_slot // 2) % 2
        if sample_slot % 2 == 0
        else 3 + (sample_slot // 2) % 7
    )
    color = _draw_scheduled_int(
        ctx, overrides, "marker_color", 1, 9, scheduled_color
    )
    diagonal = _draw_scheduled_choice(
        ctx,
        overrides,
        "diagonal",
        DIAGONALS,
        DIAGONALS[int(sample_index) % len(DIAGONALS)],
    )
    placement = _draw_scheduled_choice(
        ctx,
        overrides,
        "placement",
        PLACEMENTS,
        PLACEMENTS[int(sample_index) % len(PLACEMENTS)],
    )

    max_top = h - rect_h
    max_left = w - rect_w
    # h,w >= 7 and rect_h,rect_w <= 5 guarantee both are at least two,
    # which makes all five mutually observable placement profiles feasible.
    rng = ctx.draw_rng("position")
    if placement == "interior":
        top = rng.randint(1, max_top - 1)
        left = rng.randint(1, max_left - 1)
    elif placement == "top":
        top = 0
        left = rng.randint(1, max_left - 1)
    elif placement == "bottom":
        top = max_top
        left = rng.randint(1, max_left - 1)
    elif placement == "left":
        top = rng.randint(1, max_top - 1)
        left = 0
    elif placement == "right":
        top = rng.randint(1, max_top - 1)
        left = max_left
    else:  # draw_choice already validates, retained as a defensive assertion.
        raise AssertionError(f"unreachable placement: {placement!r}")

    bottom = top + rect_h - 1
    right = left + rect_w - 1
    grid = full_grid(h, w, 0)
    if diagonal == "main":
        grid[top][left] = color
        grid[bottom][right] = color
    else:
        grid[top][right] = color
        grid[bottom][left] = color
    return grid


def _normalize_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    normalized: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                normalized.append([int(value) for value in row])
            except ValueError:
                return []
        elif isinstance(row, (list, tuple)):
            normalized.append(list(row))
        else:
            return []
    return normalized


def _analyse(grid: Any, *, strict: bool = False) -> tuple[dict[str, Any], list[str]]:
    g = _normalize_grid(grid)
    if not g:
        return {}, ["grid must be a non-empty list of rows"]
    if not g[0]:
        return {}, ["grid rows must be non-empty"]

    h, w = len(g), len(g[0])
    errors: list[str] = []
    if any(len(row) != w for row in g):
        return {"grid_h": h, "grid_w": w}, ["grid must be rectangular"]
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC bounds: {h}x{w}")

    bad_values = [
        value
        for row in g
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("grid values must be integer ARC colors 0..9")

    markers = [
        (r, c, value)
        for r, row in enumerate(g)
        for c, value in enumerate(row)
        if isinstance(value, int) and not isinstance(value, bool) and value != 0
    ]
    info: dict[str, Any] = {
        "grid": g,
        "grid_h": h,
        "grid_w": w,
        "markers": tuple(markers),
    }
    if len(markers) != 2:
        errors.append(f"expected exactly 2 nonzero markers, got {len(markers)}")
        return info, errors

    first, second = sorted(markers, key=lambda item: (item[0], item[1]))
    if first[2] != second[2]:
        errors.append(f"markers must share one color, got {first[2]} and {second[2]}")
    if first[0] == second[0]:
        errors.append("markers must occupy distinct rows")
    if first[1] == second[1]:
        errors.append("markers must occupy distinct columns")
    if errors:
        return info, errors

    top = min(first[0], second[0])
    bottom = max(first[0], second[0])
    left = min(first[1], second[1])
    right = max(first[1], second[1])
    rect_h = bottom - top + 1
    rect_w = right - left + 1
    diagonal = "main" if first[1] < second[1] else "anti"

    contacts: list[str] = []
    if top == 0:
        contacts.append("top")
    if bottom == h - 1:
        contacts.append("bottom")
    if left == 0:
        contacts.append("left")
    if right == w - 1:
        contacts.append("right")
    placement = "interior" if not contacts else contacts[0] if len(contacts) == 1 else "multi_edge"

    info.update(
        {
            "marker_color": first[2],
            "bbox": (top, left, bottom, right),
            "rect_height": rect_h,
            "rect_width": rect_w,
            "diagonal": diagonal,
            "edge_contacts": tuple(contacts),
            "placement": placement,
        }
    )

    if strict:
        if not 7 <= h <= 10:
            errors.append(f"canonical-like grid height must be 7..10, got {h}")
        if not 7 <= w <= 12:
            errors.append(f"canonical-like grid width must be 7..12, got {w}")
        if rect_h < 3 or rect_w < 3:
            errors.append(
                "canonical-like markers must expose a visible interior-capable span (both dimensions >= 3)"
            )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level input grammar, including lawful 2x2 boxes."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    """Validate the narrower canonical/generation manifold used for lessons."""
    return _analyse(grid, strict=True)[1]


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every exact generated axis from the returned input grid."""
    info, errors = _analyse(grid, strict=True)
    if errors:
        raise ValueError("; ".join(errors))
    if not 3 <= info["rect_height"] <= 5 or not 3 <= info["rect_width"] <= 5:
        raise ValueError("generated rectangle dimensions must both be 3..5")
    if info["placement"] not in PLACEMENTS:
        raise ValueError(
            "generated placement must touch zero or exactly one edge, got "
            f"{info['edge_contacts']!r}"
        )
    return {name: info[name] for name in AXES}


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python evidence mirror; the canonical Racket program remains authority."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    top, left, bottom, right = info["bbox"]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            out[row][col] = info["marker_color"]
    return out


def _copy_grid(grid: Any) -> list[list[int]]:
    normalized = _normalize_grid(grid)
    return [list(row) for row in normalized]


def _outline_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    top, left, bottom, right = info["bbox"]
    for col in range(left, right + 1):
        out[top][col] = info["marker_color"]
        out[bottom][col] = info["marker_color"]
    for row in range(top, bottom + 1):
        out[row][left] = info["marker_color"]
        out[row][right] = info["marker_color"]
    return out


def _conditional_rule(
    predicate: Callable[[dict[str, Any]], bool]
) -> Callable[[Any], list[list[int]]]:
    def rival(grid: Any) -> list[list[int]]:
        info, errors = _analyse(grid)
        if errors:
            raise ValueError("; ".join(errors))
        return rule_mirror(grid) if predicate(info) else _copy_grid(grid)

    return rival


# Named wrong rules.  Conditional rivals are intentionally plausible: each can
# fit a small biased demonstration set while disagreeing on a nearby query.
SEMANTIC_RIVALS = {
    "markers_only": _copy_grid,
    "bbox_outline": _outline_only,
    "square_only": _conditional_rule(lambda info: info["rect_height"] == info["rect_width"]),
    "non_square_only": _conditional_rule(lambda info: info["rect_height"] != info["rect_width"]),
    "low_color_only": _conditional_rule(lambda info: info["marker_color"] <= 2),
    "high_color_only": _conditional_rule(lambda info: info["marker_color"] > 2),
    "horizontal_edge_only": _conditional_rule(lambda info: info["placement"] in ("top", "bottom")),
    "non_horizontal_placement_only": _conditional_rule(
        lambda info: info["placement"] not in ("top", "bottom")
    ),
    "main_diagonal_only": _conditional_rule(lambda info: info["diagonal"] == "main"),
    "anti_diagonal_only": _conditional_rule(lambda info: info["diagonal"] == "anti"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "bbox_outline": _outline_only,
    "square_only": SEMANTIC_RIVALS["square_only"],
    "low_color_only": SEMANTIC_RIVALS["low_color_only"],
    "horizontal_edge_only": SEMANTIC_RIVALS["horizontal_edge_only"],
}


def _valid_info(grid: Any) -> dict[str, Any] | None:
    info, errors = _analyse(grid, strict=True)
    return None if errors else info


def _witness_main(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["diagonal"] == "main")


def _witness_anti(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["diagonal"] == "anti")


def _witness_square(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["rect_height"] == info["rect_width"])


def _witness_non_square(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["rect_height"] != info["rect_width"])


def _witness_low_color(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["marker_color"] <= 2)


def _witness_high_color(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["marker_color"] > 2)


def _witness_horizontal_edge(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["placement"] in ("top", "bottom"))


def _witness_non_horizontal_placement(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["placement"] not in ("top", "bottom"))


def _witness_solid_interior(grid: Any) -> bool:
    info = _valid_info(grid)
    return bool(info and info["rect_height"] >= 3 and info["rect_width"] >= 3)


SEMANTIC_WITNESSES = {
    "main_diagonal_markers": _witness_main,
    "anti_diagonal_markers": _witness_anti,
    "square_rectangle": _witness_square,
    "non_square_rectangle": _witness_non_square,
    "low_marker_color": _witness_low_color,
    "high_marker_color": _witness_high_color,
    "horizontal_edge_placement": _witness_horizontal_edge,
    "non_horizontal_placement": _witness_non_horizontal_placement,
    "solid_fill_has_interior": _witness_solid_interior,
}

WITNESS_RIVALS = {
    "main_diagonal_markers": ["anti_diagonal_only"],
    "anti_diagonal_markers": ["main_diagonal_only"],
    "square_rectangle": ["non_square_only"],
    "non_square_rectangle": ["square_only"],
    "low_marker_color": ["high_color_only"],
    "high_marker_color": ["low_color_only"],
    "horizontal_edge_placement": ["non_horizontal_placement_only"],
    "non_horizontal_placement": ["horizontal_edge_only"],
    "solid_fill_has_interior": ["markers_only", "bbox_outline"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each four-demo window to refute every named shortcut rival."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    infos: list[dict[str, Any]] = []
    normalized_demos: list[tuple[list[list[int]], list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"], strict=True)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        output = _normalize_grid(pair["output"])
        if output != expected:
            reasons.append(f"demo {index} output is not the solid inclusive bbox fill")
            continue
        infos.append(info)
        normalized_demos.append((_normalize_grid(pair["input"]), output))

    if len(infos) == len(demos):
        diagonals = {info["diagonal"] for info in infos}
        shape_classes = {
            "square"
            if info["rect_height"] == info["rect_width"]
            else "tall"
            if info["rect_height"] > info["rect_width"]
            else "wide"
            for info in infos
        }
        colors = {info["marker_color"] for info in infos}
        placements = {info["placement"] for info in infos}
        if diagonals != set(DIAGONALS):
            reasons.append(f"demos must cover both marker diagonals, got {sorted(diagonals)}")
        if shape_classes != {"square", "tall", "wide"}:
            reasons.append(
                "demos must cover square, tall, and wide rectangles, got "
                f"{sorted(shape_classes)}"
            )
        if len(colors) < 4:
            reasons.append(f"demos must use four marker colors, got {sorted(colors)}")
        if len(placements) < 4:
            reasons.append(
                f"demos must cover at least four placement profiles, got {sorted(placements)}"
            )

        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(inp) == output for inp, output in normalized_demos):
                reasons.append(f"named rival {name!r} fits every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, query_errors = _analyse(query["input"], strict=True)
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and _normalize_grid(query["output"]) != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative solid-fill transform")
    return reasons
