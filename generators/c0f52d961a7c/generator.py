"""Generator for ARC task ``c0f52d961a7c``.

A single marker color selects a cardinal translation for the connected
color-6 payload: 1=left, 2=up, 3=right, 4=down.  The output is a blank grid
containing only the payload shifted one cell; the marker is discarded.

The four-slot teaching schedule deliberately places the marker on a spatial
side that does *not* encode the requested direction.  Four consecutive
examples therefore expose the complete color-to-direction key and refute the
plausible shortcut "move the object toward the marker".
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c0f52d961a7c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0f51670bbbc2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A connected magenta (6) payload and one direction marker appear on a "
    "black grid. Marker colors 1/2/3/4 mean left/up/right/down. Shift every "
    "payload cell one step in that direction and output only the shifted "
    "payload on a blank grid."
)

INVARIANTS = [
    "the grid contains exactly one marker cell, colored 1, 2, 3, or 4",
    "the color-6 payload has 3..8 cells and is one 4-connected component",
    "the marker color, not its spatial position, selects left/up/right/down",
    "the selected one-cell shift remains in bounds",
    "the output drops the marker and every unshifted input cell",
]

_DELTA = {
    1: (0, -1),
    2: (-1, 0),
    3: (0, 1),
    4: (1, 0),
}
_CARDINAL = tuple(_DELTA.values())
_CANONICAL_DIMS = {(6, 7), (7, 8), (8, 9)}
_MARKER_REGIONS = ("above", "below", "left", "right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical-dimension schedule",
        "valid": "6..20",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical-dimension schedule",
        "valid": "7..22",
    },
    "payload_size": {
        "type": "int",
        "default": "four-slot teaching schedule",
        "valid": "3..8",
    },
    "marker_color": {
        "type": "int",
        "default": "four-slot complete direction schedule",
        "valid": "1|2|3|4",
    },
}

# Every Cartesian boundary combination is constructible.  Declaring the empty
# set opts into strict rejection accounting in the override contract checker.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# Marker region is a teaching branch rather than an override axis.  In every
# slot it conflicts with the marker-color direction, which prevents spatial
# marker position from becoming a substitute rule.  Four consecutive indexes
# always expose all four marker meanings, regardless of the starting residue.
_SCHEDULE = (
    {
        "name": "left_key_marker_right",
        "grid_h": 6,
        "grid_w": 7,
        "payload_size": 5,
        "marker_color": 1,
        "marker_region": "right",
    },
    {
        "name": "up_key_marker_below",
        "grid_h": 7,
        "grid_w": 8,
        "payload_size": 4,
        "marker_color": 2,
        "marker_region": "below",
    },
    {
        "name": "right_key_marker_above",
        "grid_h": 8,
        "grid_w": 9,
        "payload_size": 4,
        "marker_color": 3,
        "marker_region": "above",
    },
    {
        "name": "down_key_marker_left",
        "grid_h": 6,
        "grid_w": 7,
        "payload_size": 5,
        "marker_color": 4,
        "marker_region": "left",
    },
)
SCHEDULE_PROFILES = tuple(slot["name"] for slot in _SCHEDULE)

# Small explicit polyomino seeds keep every payload connected and make the full
# override cross-product constructible even on the minimum 6x7 canvas.  All D4
# orientations are derived once at import time.
_BASE_SHAPES: dict[int, tuple[tuple[str, ...], ...]] = {
    3: (
        ("11", "10"),
        ("111",),
    ),
    4: (
        ("111", "100"),
        ("010", "111"),
        ("11", "11"),
        ("110", "011"),
    ),
    5: (
        ("010", "111", "010"),
        ("111", "110"),
        ("1111", "1000"),
    ),
    6: (
        ("111", "111"),
        ("110", "111", "001"),
        ("1111", "1100"),
    ),
    7: (
        ("1111", "1110"),
        ("111", "101", "110"),
        ("111", "111", "100"),
    ),
    8: (
        ("1111", "1111"),
        ("111", "111", "110"),
        ("1111", "1100", "1100"),
    ),
}


def _normalize(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _cells_from_rows(rows: tuple[str, ...]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == "1"
    }


def _rotate_cells(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(c, -r) for r, c in cells}


def _reflect_cells(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(r, -c) for r, c in cells}


def _d4_variants(rows: tuple[str, ...]) -> set[tuple[tuple[int, int], ...]]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    state = _cells_from_rows(rows)
    for _ in range(4):
        variants.add(_normalize(state))
        variants.add(_normalize(_reflect_cells(state)))
        state = _rotate_cells(state)
    return variants


def _build_shape_catalog() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    catalog: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size, bases in _BASE_SHAPES.items():
        variants: set[tuple[tuple[int, int], ...]] = set()
        for rows in bases:
            variants.update(_d4_variants(rows))
        if any(len(shape) != size for shape in variants):
            raise AssertionError(f"shape catalog for {size} contains wrong cell count")
        catalog[size] = tuple(sorted(variants))
    return catalog


_SHAPES = _build_shape_catalog()


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _scheduled_int(
    ctx,
    label: str,
    scheduled: int,
    lo: int,
    hi: int,
    overrides: dict[str, Any],
    *,
    explore_full_range: bool = False,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if explore_full_range:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]["name"]


def _shape_extent(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


def _marker_position(
    *,
    region: str,
    top: int,
    left: int,
    shape_h: int,
    shape_w: int,
    grid_h: int,
    grid_w: int,
    rng,
) -> tuple[int, int]:
    if region == "above":
        return rng.randint(0, top - 1), rng.randint(left, left + shape_w - 1)
    if region == "below":
        return rng.randint(top + shape_h, grid_h - 1), rng.randint(
            left, left + shape_w - 1
        )
    if region == "left":
        return rng.randint(top, top + shape_h - 1), rng.randint(0, left - 1)
    if region == "right":
        return rng.randint(top, top + shape_h - 1), rng.randint(
            left + shape_w, grid_w - 1
        )
    raise ValueError(f"unknown marker region {region!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one lawful input grid; every declared override is exact or loud."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = _SCHEDULE[sample_index % len(_SCHEDULE)]
    # Half the index blocks are exact canonical-size anchors; the alternating
    # blocks exercise the full declared canvas range.  Direction teaching
    # remains on sample_index % 4, so every four-demo window still covers the
    # complete key even when its canvases are exploratory.
    canonical_anchor = sample_index % 8 < 4
    h = _scheduled_int(
        ctx, "grid_h", slot["grid_h"], 6, 20, overrides,
        explore_full_range=not canonical_anchor,
    )
    w = _scheduled_int(
        ctx, "grid_w", slot["grid_w"], 7, 22, overrides,
        explore_full_range=not canonical_anchor,
    )
    payload_size = _scheduled_int(
        ctx, "payload_size", slot["payload_size"], 3, 8, overrides
    )
    marker_color = _scheduled_int(
        ctx, "marker_color", slot["marker_color"], 1, 4, overrides
    )

    band = difficulty or "unbanded"
    shape_rng = ctx.draw_rng(f"payload_shape:{band}")
    shape = shape_rng.choice(_SHAPES[payload_size])
    shape_h, shape_w = _shape_extent(shape)

    # A full one-cell margin on all sides means every marker-color override can
    # be honored without changing any other requested axis or dropping cells.
    position_rng = ctx.draw_rng(f"payload_position:{band}")
    top = position_rng.randint(1, h - shape_h - 1)
    left = position_rng.randint(1, w - shape_w - 1)
    payload = [(top + r, left + c) for r, c in shape]

    marker_rng = ctx.draw_rng(f"marker_position:{band}")
    mr, mc = _marker_position(
        region=slot["marker_region"],
        top=top,
        left=left,
        shape_h=shape_h,
        shape_w=shape_w,
        grid_h=h,
        grid_w=w,
        rng=marker_rng,
    )

    grid = full_grid(h, w, 0)
    for r, c in payload:
        grid[r][c] = 6
    grid[mr][mc] = marker_color
    return grid


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "h": None,
        "w": None,
        "payload": set(),
        "payload_size": 0,
        "marker": None,
        "marker_color": None,
        "bbox": None,
        "marker_region": None,
    }
    if not isinstance(grid, list) or not grid or not all(
        isinstance(row, list) for row in grid
    ):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        result["errors"].append("grid must be rectangular and nonempty")
        return result
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        result["errors"].append("grid values must be integer ARC colors 0..9")
        return result

    h, w = len(grid), width
    result["h"], result["w"] = h, w
    if not 6 <= h <= 20:
        result["errors"].append(f"grid height must be 6..20, got {h}")
    if not 7 <= w <= 22:
        result["errors"].append(f"grid width must be 7..22, got {w}")

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 1, 2, 3, 4, 6})
    if unexpected:
        result["errors"].append(f"unexpected input colors {unexpected}")

    markers = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] in _DELTA
    ]
    if len(markers) != 1:
        result["errors"].append(
            f"expected exactly one direction marker, found {len(markers)}"
        )
    else:
        mr, mc, marker_color = markers[0]
        result["marker"] = (mr, mc)
        result["marker_color"] = marker_color

    payload = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 6
    }
    result["payload"] = payload
    result["payload_size"] = len(payload)
    if not 3 <= len(payload) <= 8:
        result["errors"].append(
            f"payload must contain 3..8 color-6 cells, got {len(payload)}"
        )
    if payload and not _connected(payload):
        result["errors"].append("color-6 payload must be one 4-connected component")

    if payload:
        r1 = min(r for r, _ in payload)
        r2 = max(r for r, _ in payload)
        c1 = min(c for _, c in payload)
        c2 = max(c for _, c in payload)
        result["bbox"] = (r1, c1, r2, c2)

    if len(markers) == 1 and payload:
        mr, mc, marker_color = markers[0]
        r1, c1, r2, c2 = result["bbox"]
        if r1 <= mr <= r2 and c1 <= mc <= c2:
            result["errors"].append("marker must lie outside the payload bounding box")
        else:
            directions: list[str] = []
            if mr < r1:
                directions.append("above")
            elif mr > r2:
                directions.append("below")
            if mc < c1:
                directions.append("left")
            elif mc > c2:
                directions.append("right")
            result["marker_region"] = "_".join(directions)

        dr, dc = _DELTA[marker_color]
        if any(not (0 <= r + dr < h and 0 <= c + dc < w) for r, c in payload):
            result["errors"].append("payload would shift out of bounds")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked teaching grammar."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe axes on malformed grid: " + "; ".join(analysis["errors"])
        )
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "payload_size": analysis["payload_size"],
        "marker_color": analysis["marker_color"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Accept the task's canonical grammar; canvas scale is incidental."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    palette = {value for row in grid for value in row}
    marker_color = _analysis(grid)["marker_color"]
    expected = {0, 6, marker_color}
    if palette != expected:
        reasons.append(
            f"canonical palette must be {sorted(expected)}, got {sorted(palette)}"
        )
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket authority, for diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input: " + "; ".join(analysis["errors"]))
    h, w = analysis["h"], analysis["w"]
    dr, dc = _DELTA[analysis["marker_color"]]
    output = full_grid(h, w, 0)
    for r, c in analysis["payload"]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            output[nr][nc] = 6
    return output


def _translate_payload(grid, delta: tuple[int, int]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input: " + "; ".join(analysis["errors"]))
    h, w = analysis["h"], analysis["w"]
    dr, dc = delta
    output = full_grid(h, w, 0)
    for r, c in analysis["payload"]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            output[nr][nc] = 6
    return output


def _direction_toward_marker(grid) -> tuple[int, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input: " + "; ".join(analysis["errors"]))
    mr, mc = analysis["marker"]
    r1, c1, r2, c2 = analysis["bbox"]
    candidates: list[tuple[int, int, tuple[int, int]]] = []
    if mr < r1:
        candidates.append((r1 - mr, 0, (-1, 0)))
    if mr > r2:
        candidates.append((mr - r2, 0, (1, 0)))
    if mc < c1:
        candidates.append((c1 - mc, 1, (0, -1)))
    if mc > c2:
        candidates.append((mc - c2, 1, (0, 1)))
    if not candidates:
        raise ValueError("marker is not spatially outside the payload")
    # Choose the larger separation; on diagonal ties prefer horizontal.  That
    # makes this shortcut fit both canonical training pairs while the canonical
    # test pair (color 3 with marker above) falsifies it.
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _rival_follow_marker_position(grid) -> list[list[int]]:
    return _translate_payload(grid, _direction_toward_marker(grid))


def _rival_move_away_from_marker(grid) -> list[list[int]]:
    dr, dc = _direction_toward_marker(grid)
    return _translate_payload(grid, (-dr, -dc))


def _rival_no_shift(grid) -> list[list[int]]:
    return _translate_payload(grid, (0, 0))


def _rival_always_left(grid) -> list[list[int]]:
    return _translate_payload(grid, (0, -1))


def _rival_wrong_color_cycle(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input: " + "; ".join(analysis["errors"]))
    wrong = {
        1: (-1, 0),
        2: (0, 1),
        3: (1, 0),
        4: (0, -1),
    }
    return _translate_payload(grid, wrong[analysis["marker_color"]])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "follow_marker_position": _rival_follow_marker_position,
    "move_away_from_marker": _rival_move_away_from_marker,
    "do_not_shift_payload": _rival_no_shift,
    "always_move_left": _rival_always_left,
    "rotate_color_key": _rival_wrong_color_cycle,
}


def _rival_visible(
    grid,
    rival: Callable[[list[list[int]]], list[list[int]]],
    *,
    marker_color: int | None = None,
) -> bool:
    try:
        analysis = _analysis(grid)
        return (
            not analysis["errors"]
            and (marker_color is None or analysis["marker_color"] == marker_color)
            and rival(grid) != rule_mirror(grid)
        )
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "color_1_key_visible": lambda grid: _rival_visible(
        grid, _rival_wrong_color_cycle, marker_color=1
    ),
    "color_2_key_visible": lambda grid: _rival_visible(
        grid, _rival_wrong_color_cycle, marker_color=2
    ),
    "color_3_key_visible": lambda grid: _rival_visible(
        grid, _rival_wrong_color_cycle, marker_color=3
    ),
    "color_4_key_visible": lambda grid: _rival_visible(
        grid, _rival_wrong_color_cycle, marker_color=4
    ),
    "marker_position_shortcut_refuted": lambda grid: _rival_visible(
        grid, _rival_follow_marker_position
    ),
    "away_from_marker_shortcut_refuted": lambda grid: _rival_visible(
        grid, _rival_move_away_from_marker
    ),
    "translation_is_visible": lambda grid: _rival_visible(grid, _rival_no_shift),
    "non_left_direction_visible": lambda grid: _rival_visible(
        grid, _rival_always_left
    ),
}

WITNESS_RIVALS = {
    "color_1_key_visible": ["rotate_color_key"],
    "color_2_key_visible": ["rotate_color_key"],
    "color_3_key_visible": ["rotate_color_key"],
    "color_4_key_visible": ["rotate_color_key"],
    "marker_position_shortcut_refuted": ["follow_marker_position"],
    "away_from_marker_shortcut_refuted": ["move_away_from_marker"],
    "translation_is_visible": ["do_not_shift_payload"],
    "non_left_direction_visible": ["always_move_left"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# This is the strongest wrong rule supported by the two public training pairs:
# both move toward the marker, but the public test pair must move right despite
# its marker being above the payload.
CANONICAL_SHORTCUTS = {
    "follow_marker_position": _rival_follow_marker_position,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-demo lesson to determine the keyed translation rule."""
    reasons: list[str] = []
    if len(demos) != EXAMPLES_NEEDED:
        reasons.append(
            f"expected {EXAMPLES_NEEDED} demos, received {len(demos)}"
        )

    marker_colors: set[int] = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {'; '.join(errors)}")
            continue
        marker_colors.add(_analysis(grid)["marker_color"])
        if output != rule_mirror(grid):
            reasons.append(f"demo {index} output does not match the pinned rule")

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {'; '.join(query_errors)}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query output does not match the pinned rule")

    if marker_colors != {1, 2, 3, 4}:
        reasons.append(
            f"demos expose marker colors {sorted(marker_colors)}, not all 1..4"
        )
    if demos and not any(
        _rival_follow_marker_position(pair["input"]) != pair["output"]
        for pair in demos
        if isinstance(pair, dict) and not self_check(pair.get("input"))
    ):
        reasons.append("demos do not refute the move-toward-marker shortcut")

    if not query_errors:
        for name, competitor in LESSON_COMPETITORS.items():
            try:
                fits_demos = all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                )
                changes_query = competitor(query_grid) != query_output
            except Exception as exc:
                reasons.append(
                    f"competitor {name} raised {type(exc).__name__}: {exc}"
                )
                continue
            if fits_demos and changes_query:
                reasons.append(
                    f"competitor {name} fits every demo but changes the query"
                )
    return reasons
