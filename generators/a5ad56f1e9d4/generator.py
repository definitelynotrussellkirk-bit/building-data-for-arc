"""Curriculum generator for nearest-marker Manhattan recoloring.

A solid gray (5) rectangle and two distinct colored singleton markers are
placed on a black background.  The selected Racket rule recolors every gray
cell to the closest marker by Manhattan distance; ties use the lower marker
color and then marker row/column.  This module samples inputs only.  The
Python mirrors and rivals below are executable review contracts, not label
sources.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box

GENERATOR_ID = "a5ad56f1e9d4"
TASK_ID = GENERATOR_ID
RULE_HASH = "7cf87a6a8bce"
VERSION = "2.0.0"
SUMMARY = (
    "Place one 2..4 by 2..4 solid gray rectangle and two distinct colored "
    "markers; recolor each gray cell to its Manhattan-nearest marker, with "
    "lower color then row/column resolving ties."
)

INVARIANTS = [
    "background is color 0 and the target is one solid color-5 rectangle",
    "the rectangle has height and width in 2..4",
    "exactly two distinct non-{0,5} singleton markers lie outside the rectangle",
    "each marker is strictly nearest to at least one rectangle cell",
    "ties, contact, marker order, rectangle geometry, and marker sides all vary",
]

AXES = {
    "rect_h": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "rect_w": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "contact_mode": {
        "type": "str",
        "default": "scheduled touching|gapped",
        "valid": "touching|gapped",
    },
    "tie_mode": {
        "type": "str",
        "default": "include outside canonical-profile anchors",
        "valid": "avoid|include",
    },
    "marker_order": {
        "type": "str",
        "default": "lower_second outside canonical-profile anchors",
        "valid": "lower_first|lower_second",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

_INT_DOMAINS = {"rect_h": range(2, 5), "rect_w": range(2, 5)}
_CHOICE_DOMAINS = {
    "contact_mode": ("touching", "gapped"),
    "tie_mode": ("avoid", "include"),
    "marker_order": ("lower_first", "lower_second"),
}
_MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_SIDES = ("top", "right", "bottom", "left")
_CANONICAL_PROFILES = {
    (5, 6, 4, 3, 3),
    (5, 7, 4, 2, 3),
    (5, 7, 4, 3, 4),
}
_ANCHOR_SPECS = (
    (5, 6, 3, 3),
    (5, 7, 2, 3),
    (5, 7, 3, 4),
)
_DEFAULT_SHAPES = (
    (2, 2),
    (2, 3),
    (2, 4),
    (3, 2),
    (3, 3),
    (3, 4),
    (4, 2),
    (4, 3),
    (4, 4),
)

Grid = list[list[int]]
Position = tuple[int, int]
Layout = tuple[int, int, Position, Position]


def _clone(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_DOMAINS:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            if value not in _INT_DOMAINS[name]:
                domain = _INT_DOMAINS[name]
                raise ValueError(
                    f"override {name}={value!r} outside "
                    f"{domain.start}..{domain.stop - 1}"
                )
        elif type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")
        elif value not in _CHOICE_DOMAINS[name]:
            raise ValueError(
                f"override {name}={value!r} not in {_CHOICE_DOMAINS[name]}"
            )


def _axis_int(ctx, name: str, default: int) -> int:
    domain = _INT_DOMAINS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, domain.start, domain.stop - 1)
    # A singleton default draw records provenance while preserving the explicit
    # curriculum schedule.  Exact caller overrides always use the full domain.
    return ctx.draw_choice(name, (default,))


def _axis_choice(ctx, name: str, default: str) -> str:
    domain = _CHOICE_DOMAINS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, domain)
    return ctx.draw_choice(name, (default,))


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be nonempty and rectangular"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"]}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within 1..30")
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if type(value) is not int or not (0 <= value <= 9)
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"grid contains invalid ARC values: {bad_values[:4]}")

    five_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    ]
    if not five_cells:
        errors.append("no color-5 rectangle cells found")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "markers": [],
        }

    top = min(row for row, _ in five_cells)
    bottom = max(row for row, _ in five_cells)
    left = min(col for _, col in five_cells)
    right = max(col for _, col in five_cells)
    rect_h = bottom - top + 1
    rect_w = right - left + 1
    rectangle = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    if set(five_cells) != rectangle:
        errors.append("color-5 cells are not one solid filled rectangle")
    if not (2 <= rect_h <= 4 and 2 <= rect_w <= 4):
        errors.append(
            f"color-5 rectangle dimensions must be 2..4 by 2..4, got {rect_h}x{rect_w}"
        )

    markers = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    if len(markers) != 2:
        errors.append(f"expected exactly two marker cells, found {len(markers)}")
    elif len({color for _, _, color in markers}) != 2:
        errors.append("marker colors must be distinct")

    contact_mode = None
    tie_mode = None
    marker_order = None
    if len(markers) == 2 and len({color for _, _, color in markers}) == 2:
        marker_positions = [(row, col) for row, col, _ in markers]
        distances_to_rect = [
            min(abs(row - rr) + abs(col - cc) for rr, cc in rectangle)
            for row, col in marker_positions
        ]
        contact_mode = "touching" if min(distances_to_rect) == 1 else "gapped"

        first, second = sorted(markers)
        lower = min(markers, key=lambda item: item[2])
        marker_order = "lower_first" if lower[:2] == first[:2] else "lower_second"

        first_pos = markers[0][:2]
        second_pos = markers[1][:2]
        comparisons = [
            (
                abs(row - first_pos[0]) + abs(col - first_pos[1]),
                abs(row - second_pos[0]) + abs(col - second_pos[1]),
            )
            for row, col in rectangle
        ]
        tie_mode = "include" if any(a == b for a, b in comparisons) else "avoid"
        if not any(a < b for a, b in comparisons):
            errors.append("first marker is never strictly nearest to a rectangle cell")
        if not any(b < a for a, b in comparisons):
            errors.append("second marker is never strictly nearest to a rectangle cell")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "rect_h": rect_h,
        "rect_w": rect_w,
        "rectangle": rectangle,
        "markers": sorted(markers),
        "contact_mode": contact_mode,
        "tie_mode": tie_mode,
        "marker_order": marker_order,
    }


def observe_overrides(grid: Grid) -> dict[str, int | str]:
    """Recover every declared exact control from returned pixels."""
    info = _analyze(grid)
    if info["errors"]:
        return {}
    return {
        "rect_h": info["rect_h"],
        "rect_w": info["rect_w"],
        "contact_mode": info["contact_mode"],
        "tie_mode": info["tie_mode"],
        "marker_order": info["marker_order"],
    }


def self_check(grid: Grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete legal input grammar and any requested overrides."""
    info = _analyze(grid)
    errors = list(info["errors"])
    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid: Grid) -> list[str]:
    """Recognize the three canonical input profiles inside the lawful grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    info = _analyze(grid)
    palette_size = len({value for row in grid for value in row})
    profile = (
        info["height"],
        info["width"],
        palette_size,
        info["rect_h"],
        info["rect_w"],
    )
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile!r} is outside the three canonical profiles"]
    if info["contact_mode"] != "touching":
        return ["canonical profiles require at least one marker touching the rectangle"]
    return []


def _recolor_with_key(grid: Grid, key: Callable[[int, int, tuple[int, int, int]], tuple]) -> Grid:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("invalid nearest-marker input: " + "; ".join(info["errors"]))
    output = _clone(grid)
    markers = info["markers"]
    for row, col in info["rectangle"]:
        output[row][col] = min(markers, key=lambda marker: key(row, col, marker))[2]
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent mirror of the pinned Manhattan/color/position authority."""
    return _recolor_with_key(
        grid,
        lambda row, col, marker: (
            abs(row - marker[0]) + abs(col - marker[1]),
            marker[2],
            marker[0],
            marker[1],
        ),
    )


def _rival_euclidean(grid: Grid) -> Grid:
    """Shortcut rival: use squared Euclidean rather than Manhattan distance."""
    return _recolor_with_key(
        grid,
        lambda row, col, marker: (
            (row - marker[0]) ** 2 + (col - marker[1]) ** 2,
            marker[2],
            marker[0],
            marker[1],
        ),
    )


def _rival_reading_order(grid: Grid) -> Grid:
    """Shortcut rival: resolve Manhattan ties by reading order, not color."""
    return _recolor_with_key(
        grid,
        lambda row, col, marker: (
            abs(row - marker[0]) + abs(col - marker[1]),
            marker[0],
            marker[1],
            marker[2],
        ),
    )


def _witness(rival: Callable[[Grid], Grid], grid: Grid) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _euclidean_metric_rebutted(grid: Grid) -> bool:
    return _witness(_rival_euclidean, grid)


def _reading_order_tie_rebutted(grid: Grid) -> bool:
    return _witness(_rival_reading_order, grid)


CANONICAL_SHORTCUTS = {
    "euclidean_distance": _rival_euclidean,
    "reading_order_tie": _rival_reading_order,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    "euclidean_metric_rebutted": _euclidean_metric_rebutted,
    "reading_order_tie_rebutted": _reading_order_tie_rebutted,
}
WITNESS_RIVALS = {
    "euclidean_metric_rebutted": ["euclidean_distance"],
    "reading_order_tie_rebutted": ["reading_order_tie"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to refute both canonical-fitting shortcuts."""
    del query
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]
    for name, rival in CANONICAL_SHORTCUTS.items():
        refuted = False
        for pair in demos:
            grid = pair.get("input") if isinstance(pair, dict) else None
            expected = pair.get("output") if isinstance(pair, dict) else None
            try:
                if grid is not None and expected is not None and rival(grid) != expected:
                    refuted = True
                    break
            except (TypeError, ValueError):
                continue
        if not refuted:
            reasons.append(f"demonstrations do not refute shortcut {name}")
    return reasons


def _rect_cells(top: int, left: int, rect_h: int, rect_w: int) -> tuple[Position, ...]:
    return tuple(
        (row, col)
        for row in range(top, top + rect_h)
        for col in range(left, left + rect_w)
    )


def _distance_to_rect(position: Position, rectangle: tuple[Position, ...]) -> int:
    row, col = position
    return min(abs(row - rr) + abs(col - cc) for rr, cc in rectangle)


def _marker_sides(
    position: Position, top: int, left: int, rect_h: int, rect_w: int
) -> set[str]:
    row, col = position
    sides: set[str] = set()
    if row < top:
        sides.add("top")
    if row >= top + rect_h:
        sides.add("bottom")
    if col < left:
        sides.add("left")
    if col >= left + rect_w:
        sides.add("right")
    return sides


def _euclidean_disagreement(
    rectangle: tuple[Position, ...], first: Position, second: Position
) -> bool:
    """Abstract low color is on row-major second, matching witness lessons."""
    earlier, later = sorted((first, second))
    # Index 0 is lower color and deliberately sits at row-major-later position.
    markers = ((later[0], later[1], 0), (earlier[0], earlier[1], 1))
    for row, col in rectangle:
        manhattan = min(
            markers,
            key=lambda marker: (
                abs(row - marker[0]) + abs(col - marker[1]),
                marker[2],
                marker[0],
                marker[1],
            ),
        )
        euclidean = min(
            markers,
            key=lambda marker: (
                (row - marker[0]) ** 2 + (col - marker[1]) ** 2,
                marker[2],
                marker[0],
                marker[1],
            ),
        )
        if manhattan[:2] != euclidean[:2]:
            return True
    return False


@lru_cache(maxsize=None)
def _layouts(
    height: int,
    width: int,
    rect_h: int,
    rect_w: int,
    contact_mode: str,
    tie_mode: str,
    require_dual_witness: bool,
    target_side: str,
) -> tuple[Layout, ...]:
    """Construct a broad finite layout pool; no capped random rejection is used."""
    layouts: list[Layout] = []
    per_origin_limit = 12
    for top in range(height - rect_h + 1):
        for left in range(width - rect_w + 1):
            rectangle = _rect_cells(top, left, rect_h, rect_w)
            rect_set = set(rectangle)
            outside = [
                (row, col)
                for row in range(height)
                for col in range(width)
                if (row, col) not in rect_set
            ]
            origin_count = 0
            for first, second in combinations(outside, 2):
                side_union = _marker_sides(first, top, left, rect_h, rect_w)
                side_union |= _marker_sides(second, top, left, rect_h, rect_w)
                if target_side not in side_union:
                    continue

                first_gap = _distance_to_rect(first, rectangle)
                second_gap = _distance_to_rect(second, rectangle)
                if contact_mode == "touching":
                    if min(first_gap, second_gap) != 1:
                        continue
                elif first_gap < 2 or second_gap < 2:
                    continue

                comparisons = [
                    (
                        abs(row - first[0]) + abs(col - first[1]),
                        abs(row - second[0]) + abs(col - second[1]),
                    )
                    for row, col in rectangle
                ]
                has_tie = any(a == b for a, b in comparisons)
                if has_tie != (tie_mode == "include"):
                    continue
                if not any(a < b for a, b in comparisons):
                    continue
                if not any(b < a for a, b in comparisons):
                    continue
                if require_dual_witness and not _euclidean_disagreement(
                    rectangle, first, second
                ):
                    continue

                earlier, later = sorted((first, second))
                layouts.append((top, left, earlier, later))
                origin_count += 1
                if origin_count >= per_origin_limit:
                    break
    return tuple(layouts)


def _choose_layout(
    ctx,
    *,
    height: int,
    width: int,
    rect_h: int,
    rect_w: int,
    contact_mode: str,
    tie_mode: str,
    require_dual_witness: bool,
    target_side: str,
) -> Layout:
    # The first requested canvas normally suffices.  The monotone fallback is a
    # proof-friendly guard for future domain extensions, not probabilistic retry.
    for extra in range(5):
        candidate_height = height + extra
        candidate_width = width + extra
        candidates = _layouts(
            candidate_height,
            candidate_width,
            rect_h,
            rect_w,
            contact_mode,
            tie_mode,
            require_dual_witness,
            target_side,
        )
        if candidates:
            rng = ctx.draw_rng("layout")
            return (
                candidate_height,
                candidate_width,
                *candidates[rng.randrange(len(candidates))],
            )
    raise RuntimeError(
        "no constructive layout for "
        f"rect={rect_h}x{rect_w}, contact={contact_mode}, tie={tie_mode}, "
        f"dual={require_dual_witness}, side={target_side}"
    )


def _default_spec(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    anchor = sample_index % 3 == 0
    target_side = _SIDES[sample_index % len(_SIDES)]
    if anchor:
        height, width, rect_h, rect_w = _ANCHOR_SPECS[(sample_index // 3) % 3]
        return {
            "anchor": True,
            "height": height,
            "width": width,
            "rect_h": rect_h,
            "rect_w": rect_w,
            "contact_mode": "touching",
            "tie_mode": "include",
            "marker_order": "lower_first",
            "target_side": target_side,
            "require_dual_witness": False,
        }

    rect_h, rect_w = _DEFAULT_SHAPES[sample_index % len(_DEFAULT_SHAPES)]
    band_extra = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 1)
    return {
        "anchor": False,
        "height": max(6, rect_h + 3) + band_extra,
        "width": max(7, rect_w + 3) + band_extra,
        "rect_h": rect_h,
        "rect_w": rect_w,
        "contact_mode": "touching" if sample_index % 2 else "gapped",
        "tie_mode": "include",
        "marker_order": "lower_second",
        "target_side": target_side,
        "require_dual_witness": True,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    spec = _default_spec(sample_index, difficulty)
    # Any explicit override leaves the canonical-anchor schedule so every exact
    # product remains satisfiable without hidden profile constraints.
    if overrides:
        rect_h_default, rect_w_default = _DEFAULT_SHAPES[
            sample_index % len(_DEFAULT_SHAPES)
        ]
        spec["anchor"] = False
        spec["rect_h"] = rect_h_default
        spec["rect_w"] = rect_w_default
        spec["height"] = max(6, rect_h_default + 3) + {
            "easy": 0,
            "medium": 1,
            "hard": 2,
        }.get(difficulty, 1)
        spec["width"] = max(7, rect_w_default + 3) + {
            "easy": 0,
            "medium": 1,
            "hard": 2,
        }.get(difficulty, 1)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rect_h = _axis_int(ctx, "rect_h", spec["rect_h"])
    rect_w = _axis_int(ctx, "rect_w", spec["rect_w"])
    contact_mode = _axis_choice(ctx, "contact_mode", spec["contact_mode"])
    tie_mode = _axis_choice(ctx, "tie_mode", spec["tie_mode"])
    marker_order = _axis_choice(ctx, "marker_order", spec["marker_order"])

    if spec["anchor"] and not overrides:
        height, width = spec["height"], spec["width"]
    else:
        height = max(spec["height"], rect_h + 3)
        width = max(spec["width"], rect_w + 3)
    require_dual_witness = (
        not overrides
        and not spec["anchor"]
        and tie_mode == "include"
        and marker_order == "lower_second"
    )
    chosen = _choose_layout(
        ctx,
        height=height,
        width=width,
        rect_h=rect_h,
        rect_w=rect_w,
        contact_mode=contact_mode,
        tie_mode=tie_mode,
        require_dual_witness=require_dual_witness,
        target_side=spec["target_side"],
    )
    actual_height, actual_width, top, left, earlier, later = chosen

    low_color, high_color = sorted(
        ctx.draw_rng("marker_palette").sample(list(_MARKER_COLORS), 2)
    )
    if marker_order == "lower_first":
        marker_values = ((earlier, low_color), (later, high_color))
    else:
        marker_values = ((earlier, high_color), (later, low_color))

    grid = full_grid(actual_height, actual_width, 0)
    fill_box(grid, top, left, top + rect_h - 1, left + rect_w - 1, 5)
    for (row, col), color in marker_values:
        grid[row][col] = color

    errors = self_check(grid, meta={"overrides": overrides})
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    if require_dual_witness:
        missing = [
            name
            for name, witness in SEMANTIC_WITNESSES.items()
            if not witness(grid)
        ]
        if missing:
            raise RuntimeError(f"constructed lesson witness is missing: {missing}")
    return grid
