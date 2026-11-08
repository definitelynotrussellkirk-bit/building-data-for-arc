"""Generator for ``db1284892611`` — recolor size-ranked objects and pack.

The first row is an ordered palette.  Below a blank separator row, every
nonzero 4-connected component is an object.  Sort the objects by area, crop
each object, recolor it with the corresponding nonzero palette entry, and pack
the pieces left-to-right with one zero column between pieces.  A short unused
palette tail is legal and is ignored after the last object.

The four-phase curriculum deliberately breaks shortcuts that fit all canonical
examples: canonical objects happen to be spatially ordered by size, body color
order happens to agree with size order, every body color is unique, and the
palette is a contiguous left prefix.  Generated lessons include descending
spatial size order, repeated colors across disconnected objects, color ranks
that disagree with size ranks, noncontiguous/right-aligned palettes, and unused
palette entries.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db1284892611"
TASK_ID = "db1284892611"
VERSION = "4.0.0"  # exact axes, canonical anchors, repeated-color shortcut guards
RULE_HASH = "f599f53cd1ea"

SUMMARY = (
    "Read the nonzero cells of row 0 from left to right as an ordered palette. "
    "Find the nonzero 4-connected body objects below the blank separator row, "
    "sort them by area, crop and recolor each object with the corresponding "
    "palette color, then pack the pieces left-to-right with one zero-column "
    "gap. Ignore any unused palette tail after the last object."
)

INVARIANTS = [
    "background is 0 and row 1 is a blank separator",
    "row 0 contains 2-7 distinct nonzero palette entries",
    "the body contains 2-5 isolated monochrome 4-connected objects",
    "body-object areas are pairwise distinct",
    "the palette has at least one entry per body object and at most two extras",
    "body-object identity is connectivity-based, not color-based",
]

_BANDS = ("easy", "medium", "hard")
_PALETTE_LAYOUTS = ("left", "spaced", "right")
_SIZE_ORDERS = ("ascending", "descending")
_BODY_COLOR_PATTERNS = ("all_same", "mixed")
_PALETTE_OVERLAPS = ("none", "one")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-phase band schedule with canonical anchors",
        "valid": "10..13",
    },
    "grid_w": {
        "type": "int",
        "default": "four-phase band schedule with canonical anchors",
        "valid": "10..16",
    },
    "n": {
        "type": "int",
        "default": "scheduled 3..5 body objects",
        "valid": "2..5",
    },
    "palette_extra": {
        "type": "int",
        "default": "scheduled 0..2 unused tail entries",
        "valid": "0..2",
    },
    "palette_layout": {
        "type": "enum",
        "default": "scheduled left/spaced/right",
        "valid": "left|spaced|right",
    },
    "size_order": {
        "type": "enum",
        "default": "scheduled ascending/descending spatial order",
        "valid": "ascending|descending",
    },
    "body_color_pattern": {
        "type": "enum",
        "default": "scheduled all-same or two-color repeated pattern",
        "valid": "all_same|mixed",
    },
    "palette_overlap": {
        "type": "enum",
        "default": "scheduled zero or one shared body/palette color",
        "valid": "none|one",
    },
}

# Every declared cross-product is realizable in the minimum 10x10 grid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "connectivity_and_rank_guard",
    "palette_tail_and_prefix_guard",
    "combined_shortcut_guard",
)


# ---------------------------------------------------------------------------
# Deterministic schedule and exact keyed draws
# ---------------------------------------------------------------------------


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BANDS:
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the exact four-phase lesson schedule to the semantic gate."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(sample_index: int, band: str) -> dict[str, Any]:
    phase = sample_index % len(SCHEDULE_PROFILES)
    if phase == 0:
        # Exact canonical mechanical profiles, one in every band.
        h, w, extra = {
            "easy": (10, 10, 0),
            "medium": (11, 11, 1),
            "hard": (11, 12, 1),
        }[band]
        return {
            "grid_h": h,
            "grid_w": w,
            "n": 3,
            "palette_extra": extra,
            "palette_layout": "left",
            "size_order": "ascending",
            "body_color_pattern": "mixed",
            "palette_overlap": "none",
        }
    if phase == 1:
        h, w, n = {
            "easy": (10, 11, 3),
            "medium": (11, 13, 4),
            "hard": (12, 15, 5),
        }[band]
        return {
            "grid_h": h,
            "grid_w": w,
            "n": n,
            "palette_extra": 1,
            "palette_layout": "spaced",
            "size_order": "descending",
            "body_color_pattern": "all_same",
            "palette_overlap": "none",
        }
    if phase == 2:
        h, w, n = {
            "easy": (10, 12, 3),
            "medium": (12, 14, 4),
            "hard": (13, 16, 5),
        }[band]
        return {
            "grid_h": h,
            "grid_w": w,
            "n": n,
            "palette_extra": 2,
            "palette_layout": "right",
            "size_order": "ascending",
            "body_color_pattern": "mixed",
            "palette_overlap": "one",
        }
    h, w, n = {
        "easy": (11, 12, 3),
        "medium": (12, 15, 4),
        "hard": (13, 16, 5),
    }[band]
    return {
        "grid_h": h,
        "grid_w": w,
        "n": n,
        "palette_extra": 1,
        "palette_layout": "spaced",
        "size_order": "descending",
        "body_color_pattern": "mixed",
        "palette_overlap": "one",
    }


def _draw_scheduled_int(ctx: Any, label: str, scheduled: int, lo: int, hi: int) -> int:
    bounds = (lo, hi) if ctx.overrides.get(label) is not None else (scheduled, scheduled)
    return ctx.draw_int(label, *bounds)


def _draw_scheduled_choice(
    ctx: Any,
    label: str,
    scheduled: str,
    options: tuple[str, ...],
) -> str:
    choices = options if ctx.overrides.get(label) is not None else (scheduled,)
    return str(ctx.draw_choice(label, choices))


# ---------------------------------------------------------------------------
# Structural analysis and the Python test mirror
# ---------------------------------------------------------------------------


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _body_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(sorted(cells))
    return out


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    materialized = list(cells)
    rows = [r for r, _ in materialized]
    cols = [c for _, c in materialized]
    return min(rows), min(cols), max(rows), max(cols)


def _component_piece(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    color: int | None = None,
) -> list[list[int]]:
    r1, c1, r2, c2 = _bbox(cells)
    piece = full_grid(r2 - r1 + 1, c2 - c1 + 1, 0)
    for r, c in cells:
        piece[r - r1][c - c1] = grid[r][c] if color is None else color
    return piece


def _paste_nonzero(
    target: list[list[int]],
    piece: list[list[int]],
    top: int,
    left: int,
) -> None:
    for r, row in enumerate(piece):
        for c, value in enumerate(row):
            if value != 0:
                target[top + r][left + c] = value


def _pack_pieces(pieces: list[list[list[int]]]) -> list[list[int]]:
    if not pieces:
        return [[0]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        _paste_nonzero(out, piece, 0, left)
        left += len(piece[0]) + 1
    return out


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts.update({"grid": grid, "grid_h": h, "grid_w": w})
    if h < 4 or w < 4:
        errors.append("grid is too small to contain palette, separator, and objects")

    palette_cols = [c for c, value in enumerate(grid[0]) if value != 0]
    palette = [grid[0][c] for c in palette_cols]
    facts.update({"palette_cols": palette_cols, "palette": palette})
    if not (2 <= len(palette) <= 7):
        errors.append(f"expected 2-7 nonzero palette entries, got {len(palette)}")
    if len(set(palette)) != len(palette):
        errors.append("palette entries must use distinct colors")
    if h > 1 and any(grid[1][c] != 0 for c in range(w)):
        errors.append("row 1 must be a blank separator")

    raw_components = _body_components(grid)
    components: list[dict[str, Any]] = []
    for cells in raw_components:
        colors = {grid[r][c] for r, c in cells}
        r1, c1, r2, c2 = _bbox(cells)
        components.append(
            {
                "cells": cells,
                "size": len(cells),
                "colors": colors,
                "color": next(iter(colors)) if len(colors) == 1 else None,
                "bbox": (r1, c1, r2, c2),
                "top_left": (r1, c1),
            }
        )
    components.sort(key=lambda comp: comp["top_left"])
    facts["components"] = components

    if not (2 <= len(components) <= 5):
        errors.append(f"expected 2-5 body components, got {len(components)}")
    if len(palette) < len(components):
        errors.append(
            f"palette is too short: palette={len(palette)} components={len(components)}"
        )
    if len(palette) - len(components) > 2:
        errors.append("palette may contain at most two unused tail entries")

    sizes = [comp["size"] for comp in components]
    facts["sizes_spatial"] = sizes
    if len(set(sizes)) != len(sizes):
        errors.append(f"body component sizes must be distinct; got {sizes}")
    for index, comp in enumerate(components):
        if len(comp["colors"]) != 1:
            errors.append(
                f"body component {index} must be monochrome; got {sorted(comp['colors'])}"
            )

    # Require a visible zero moat between separate objects, including diagonals.
    owner: dict[tuple[int, int], int] = {}
    for index, comp in enumerate(components):
        for cell in comp["cells"]:
            owner[cell] = index
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    errors.append("separate body objects must have a one-cell zero moat")
                    break
            else:
                continue
            break
        if errors and errors[-1].startswith("separate body objects"):
            break

    facts["palette_extra"] = len(palette) - len(components)
    facts["body_colors"] = [comp["color"] for comp in components]
    facts["body_color_set"] = {
        color for color in facts["body_colors"] if color is not None
    }
    facts["palette_overlap_count"] = len(
        set(palette).intersection(facts["body_color_set"])
    )
    return facts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the task's palette/body grammar without mutating ``grid``."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked semantic predicate; every accepted scene teaches the rule."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = _analyze(grid)
    try:
        truth = rule_mirror(grid)
    except ValueError as exc:
        return [str(exc)]
    if truth == grid:
        reasons.append("the authoritative transformation is an identity")
    if len({tuple(map(tuple, truth))}) != 1:  # defensive, always one value
        reasons.append("output construction was unstable")
    if facts["palette_extra"] < 0:
        reasons.append("palette does not cover every size rank")
    return reasons


def _official_pieces(grid: Any, palette: list[int] | None = None) -> list[list[list[int]]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    colors = list(facts["palette"] if palette is None else palette)
    ranked = sorted(facts["components"], key=lambda comp: comp["size"])
    return [
        _component_piece(facts["grid"], comp["cells"], color)
        for comp, color in zip(ranked, colors)
    ]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror; the selected Racket program remains authoritative."""
    return _pack_pieces(_official_pieces(grid))


def _palette_layout(palette_cols: list[int], width: int) -> str:
    count = len(palette_cols)
    if palette_cols == list(range(count)):
        return "left"
    if palette_cols == list(range(width - count, width)):
        return "right"
    return "spaced"


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared axis exactly from a returned generated grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))

    sizes = facts["sizes_spatial"]
    if sizes == sorted(sizes):
        size_order = "ascending"
    elif sizes == sorted(sizes, reverse=True):
        size_order = "descending"
    else:
        raise ValueError(f"spatial size order is outside the declared domain: {sizes}")

    distinct_body_colors = len(facts["body_color_set"])
    if distinct_body_colors == 1:
        body_pattern = "all_same"
    elif distinct_body_colors == 2:
        body_pattern = "mixed"
    else:
        raise ValueError(
            "body color pattern is outside the declared generated domain: "
            f"{distinct_body_colors} distinct colors"
        )

    overlap_count = facts["palette_overlap_count"]
    if overlap_count == 0:
        overlap = "none"
    elif overlap_count == 1:
        overlap = "one"
    else:
        raise ValueError(f"palette/body overlap count {overlap_count} is not declared")

    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n": len(facts["components"]),
        "palette_extra": facts["palette_extra"],
        "palette_layout": _palette_layout(facts["palette_cols"], facts["grid_w"]),
        "size_order": size_order,
        "body_color_pattern": body_pattern,
        "palette_overlap": overlap,
    }


# ---------------------------------------------------------------------------
# Scene construction
# ---------------------------------------------------------------------------


_SHAPE_OPTIONS: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    ),
}


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _shelf_rows(
    shapes: list[tuple[tuple[int, int], ...]],
    width: int,
) -> list[list[tuple[tuple[int, int], ...]]]:
    rows: list[list[tuple[tuple[int, int], ...]]] = []
    current: list[tuple[tuple[int, int], ...]] = []
    used = 0
    for shape in shapes:
        _, shape_w = _shape_dims(shape)
        needed = shape_w if not current else shape_w + 1
        if current and used + needed > width:
            rows.append(current)
            current = [shape]
            used = shape_w
        else:
            current.append(shape)
            used += needed
    if current:
        rows.append(current)
    return rows


def _layout_shapes(
    shapes: list[tuple[tuple[int, int], ...]],
    body_h: int,
    width: int,
    rng: Any,
) -> list[tuple[tuple[int, int], ...]]:
    rows = _shelf_rows(shapes, width)
    row_heights = [max(_shape_dims(shape)[0] for shape in row) for row in rows]
    required_h = sum(row_heights) + max(0, len(rows) - 1)
    if required_h > body_h:
        raise ValueError(
            f"shape shelves need {required_h} body rows but only {body_h} are available"
        )

    top_slack = body_h - required_h
    top = rng.randint(0, top_slack)
    placed: list[tuple[tuple[int, int], ...]] = []
    for row, row_h in zip(rows, row_heights):
        widths = [_shape_dims(shape)[1] for shape in row]
        required_w = sum(widths) + max(0, len(row) - 1)
        left = rng.randint(0, width - required_w)
        for shape, shape_w in zip(row, widths):
            placed.append(tuple((top + r, left + c) for r, c in shape))
            left += shape_w + 1
        top += row_h + 1
    return placed


def _palette_columns(width: int, count: int, layout: str) -> list[int]:
    if layout == "left":
        return list(range(count))
    if layout == "right":
        return list(range(width - count, width))
    # Spread from edge to edge. With width >= 10 and count <= 7 this is never
    # the same as either contiguous boundary layout.
    return [round(index * (width - 1) / (count - 1)) for index in range(count)]


def _body_palette(
    palette: list[int],
    n: int,
    body_pattern: str,
    overlap: str,
    palette_extra: int,
    rng: Any,
) -> list[int]:
    needed = 1 if body_pattern == "all_same" else 2
    remaining = [color for color in range(1, 10) if color not in palette]
    rng.shuffle(remaining)
    if overlap == "none":
        choices = remaining[:needed]
    else:
        shared = palette[-1] if palette_extra else palette[0]
        choices = [shared]
        if needed == 2:
            choices.append(remaining[0])
    if len(choices) != needed:
        raise AssertionError("not enough ARC colors for the requested color relation")

    if body_pattern == "all_same":
        return [choices[0]] * n
    # Alternate high/low relative to the two chosen values.  Size-order ranks
    # therefore do not coincide with numeric body-color order.
    low, high = sorted(choices)
    return [high if index % 2 == 0 else low for index in range(n)]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    band = _band(difficulty)
    scheduled = _scheduled_defaults(sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, "grid_h", scheduled["grid_h"], 10, 13)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled["grid_w"], 10, 16)
    n = _draw_scheduled_int(ctx, "n", scheduled["n"], 2, 5)
    palette_extra = _draw_scheduled_int(
        ctx, "palette_extra", scheduled["palette_extra"], 0, 2
    )
    palette_layout = _draw_scheduled_choice(
        ctx, "palette_layout", scheduled["palette_layout"], _PALETTE_LAYOUTS
    )
    size_order = _draw_scheduled_choice(
        ctx, "size_order", scheduled["size_order"], _SIZE_ORDERS
    )
    body_color_pattern = _draw_scheduled_choice(
        ctx,
        "body_color_pattern",
        scheduled["body_color_pattern"],
        _BODY_COLOR_PATTERNS,
    )
    palette_overlap = _draw_scheduled_choice(
        ctx,
        "palette_overlap",
        scheduled["palette_overlap"],
        _PALETTE_OVERLAPS,
    )

    palette_count = n + palette_extra
    palette_rng = ctx.draw_rng("palette_colors")
    palette = palette_rng.sample(range(1, 10), palette_count)
    body_colors_by_rank = _body_palette(
        palette,
        n,
        body_color_pattern,
        palette_overlap,
        palette_extra,
        ctx.draw_rng("body_colors"),
    )

    ranked_sizes = list(range(2, n + 2))
    spatial_sizes = ranked_sizes if size_order == "ascending" else list(reversed(ranked_sizes))
    shape_rng = ctx.draw_rng("shape_variants")
    spatial_shapes = [shape_rng.choice(_SHAPE_OPTIONS[size]) for size in spatial_sizes]
    try:
        placements = _layout_shapes(
            spatial_shapes,
            body_h=h - 2,
            width=w,
            rng=ctx.draw_rng("layout"),
        )
    except ValueError:
        # Deterministic compact fallback, still preserving the requested axes.
        compact = [
            _SHAPE_OPTIONS[size][0]
            for size in spatial_sizes
        ]
        placements = _layout_shapes(
            compact,
            body_h=h - 2,
            width=w,
            rng=ctx.draw_rng("layout_compact"),
        )

    rank_color = {
        size: body_colors_by_rank[rank]
        for rank, size in enumerate(ranked_sizes)
    }
    grid = full_grid(h, w, 0)
    for column, color in zip(
        _palette_columns(w, palette_count, palette_layout), palette
    ):
        grid[0][column] = color
    for size, cells in zip(spatial_sizes, placements):
        color = rank_color[size]
        for r, c in cells:
            grid[r + 2][c] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generator emitted invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected: dict[str, int | str] = {
        "grid_h": h,
        "grid_w": w,
        "n": n,
        "palette_extra": palette_extra,
        "palette_layout": palette_layout,
        "size_order": size_order,
        "body_color_pattern": body_color_pattern,
        "palette_overlap": palette_overlap,
    }
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected={expected} observed={observed}")
    return grid


# ---------------------------------------------------------------------------
# Plausible wrong rules and task-linked witnesses
# ---------------------------------------------------------------------------


def _rival_spatial_order(grid: Any) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    pieces = [
        _component_piece(facts["grid"], comp["cells"], color)
        for comp, color in zip(facts["components"], facts["palette"])
    ]
    return _pack_pieces(pieces)


def _rival_body_color_order(grid: Any) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    ranked = sorted(
        facts["components"],
        key=lambda comp: (comp["color"], comp["top_left"]),
    )
    pieces = [
        _component_piece(facts["grid"], comp["cells"], color)
        for comp, color in zip(ranked, facts["palette"])
    ]
    return _pack_pieces(pieces)


def _rival_group_by_color(grid: Any) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    by_color: dict[int, list[tuple[int, int]]] = {}
    for comp in facts["components"]:
        by_color.setdefault(int(comp["color"]), []).extend(comp["cells"])
    grouped = sorted(by_color.values(), key=len)
    pieces = [
        _component_piece(facts["grid"], cells, color)
        for cells, color in zip(grouped, facts["palette"])
    ]
    return _pack_pieces(pieces)


def _rival_raw_prefix_palette(grid: Any) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    raw_prefix = list(facts["grid"][0][: len(facts["components"])])
    ranked = sorted(facts["components"], key=lambda comp: comp["size"])
    pieces = [
        _component_piece(facts["grid"], comp["cells"], color)
        for comp, color in zip(ranked, raw_prefix)
    ]
    return _pack_pieces(pieces)


def _rival_consume_all_palette(grid: Any) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    ranked = sorted(facts["components"], key=lambda comp: comp["size"])
    expanded = list(ranked)
    while len(expanded) < len(facts["palette"]):
        expanded.append(ranked[-1])
    pieces = [
        _component_piece(facts["grid"], comp["cells"], color)
        for comp, color in zip(expanded, facts["palette"])
    ]
    return _pack_pieces(pieces)


def _rival_preserve_body_colors(grid: Any) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    ranked = sorted(facts["components"], key=lambda comp: comp["size"])
    return _pack_pieces(
        [_component_piece(facts["grid"], comp["cells"]) for comp in ranked]
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "spatial_order": _rival_spatial_order,
    "body_color_order": _rival_body_color_order,
    "group_by_color": _rival_group_by_color,
    "raw_prefix_palette": _rival_raw_prefix_palette,
    "consume_all_palette": _rival_consume_all_palette,
    "preserve_body_colors": _rival_preserve_body_colors,
}

# These four wrong rules fit every canonical train/test pair. Generated lessons
# must therefore provide the counterexamples the canonical set cannot.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "spatial_order",
        "body_color_order",
        "group_by_color",
        "raw_prefix_palette",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _differs(grid: Any, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _witness_descending_rank(grid: Any) -> bool:
    try:
        return observe_overrides(grid)["size_order"] == "descending" and _differs(
            grid, "spatial_order"
        )
    except ValueError:
        return False


def _witness_repeated_body_color(grid: Any) -> bool:
    facts = _analyze(grid)
    return (
        not facts["errors"]
        and len(facts["body_color_set"]) < len(facts["components"])
        and _differs(grid, "group_by_color")
    )


def _witness_color_rank_conflict(grid: Any) -> bool:
    return _differs(grid, "body_color_order")


def _witness_nonprefix_palette(grid: Any) -> bool:
    try:
        return observe_overrides(grid)["palette_layout"] != "left" and _differs(
            grid, "raw_prefix_palette"
        )
    except ValueError:
        return False


def _witness_unused_palette_tail(grid: Any) -> bool:
    facts = _analyze(grid)
    return (
        not facts["errors"]
        and facts["palette_extra"] > 0
        and _differs(grid, "consume_all_palette")
    )


def _witness_recolor_required(grid: Any) -> bool:
    return _differs(grid, "preserve_body_colors")


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "descending_spatial_rank": _witness_descending_rank,
    "repeated_body_color": _witness_repeated_body_color,
    "body_color_rank_conflict": _witness_color_rank_conflict,
    "nonprefix_palette": _witness_nonprefix_palette,
    "unused_palette_tail": _witness_unused_palette_tail,
    "recolor_required": _witness_recolor_required,
}
WITNESS_RIVALS = {
    "descending_spatial_rank": ["spatial_order"],
    "repeated_body_color": ["group_by_color"],
    "body_color_rank_conflict": ["body_color_order"],
    "nonprefix_palette": ["raw_prefix_palette"],
    "unused_palette_tail": ["consume_all_palette"],
    "recolor_required": ["preserve_body_colors"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Reject a lesson when a named plausible wrong rule survives its demos."""
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must be a materialized pair"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is malformed")
            continue
        try:
            truth = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the selected rule")
    if reasons:
        return reasons

    try:
        query_truth = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        return [f"query is outside the task grammar: {exc}"]
    if query.get("output") is not None and query["output"] != query_truth:
        return ["query output disagrees with the selected rule"]

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            competitor_query = competitor(query["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"competing rule {name!r} raised: {exc}")
            continue
        if survives and competitor_query != query_truth:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


# ---------------------------------------------------------------------------
# Mutation and negative-recombination fixtures
# ---------------------------------------------------------------------------


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named structural impostors proving ``self_check`` has rejection power."""
    valid = generate(
        73_901,
        3,
        difficulty="hard",
        grid_h=12,
        grid_w=14,
        n=4,
        palette_extra=1,
        palette_layout="spaced",
        size_order="descending",
        body_color_pattern="mixed",
        palette_overlap="one",
    )
    facts = _analyze(valid)
    fixtures: list[tuple[str, list[list[int]]]] = []

    short_palette = deepcopy(valid)
    short_palette[0][facts["palette_cols"][-1]] = 0
    short_palette[0][facts["palette_cols"][-2]] = 0
    fixtures.append(("palette_shorter_than_object_count", short_palette))

    duplicate_palette = deepcopy(valid)
    duplicate_palette[0][facts["palette_cols"][1]] = duplicate_palette[0][
        facts["palette_cols"][0]
    ]
    fixtures.append(("duplicate_palette_color", duplicate_palette))

    occupied_separator = deepcopy(valid)
    occupied_separator[1][0] = next(
        color for color in range(1, 10) if color not in set(facts["palette"])
    )
    fixtures.append(("occupied_separator_row", occupied_separator))

    mixed_component = deepcopy(valid)
    first_component = facts["components"][0]
    r, c = first_component["cells"][0]
    mixed_component[r][c] = (int(first_component["color"]) % 9) + 1
    fixtures.append(("multicolor_body_component", mixed_component))

    equal_size = deepcopy(valid)
    smallest = min(facts["components"], key=lambda comp: comp["size"])
    occupied = {cell for comp in facts["components"] for cell in comp["cells"]}
    added = False
    for r, c in smallest["cells"]:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (2 <= nr < len(valid) and 0 <= nc < len(valid[0])):
                continue
            if (nr, nc) in occupied:
                continue
            if any(
                (nr + rr, nc + cc) in occupied
                and (nr + rr, nc + cc) not in smallest["cells"]
                for rr in (-1, 0, 1)
                for cc in (-1, 0, 1)
            ):
                continue
            equal_size[nr][nc] = int(smallest["color"])
            added = True
            break
        if added:
            break
    if not added:
        raise AssertionError("could not construct equal-size mutation fixture")
    fixtures.append(("equal_size_rank_tie", equal_size))
    return fixtures


def negative_recombination_fixture() -> tuple[list[list[int]], int]:
    """Insert a wholly unseen color into one connected object.

    The teaching grammar rejects the multicolor object, while the Racket oracle
    remains defined because connectivity and nonzeroness are unchanged.
    """
    valid = generate(91_337, 1, difficulty="medium")
    facts = _analyze(valid)
    present = {value for row in valid for value in row}
    replacement = next(color for color in range(1, 10) if color not in present)
    out = deepcopy(valid)
    r, c = facts["components"][0]["cells"][0]
    out[r][c] = replacement
    return out, replacement
