"""Generator for ARC task f0069f2752a4 (Keep Border Touchers).

The input is a zero-background grid containing several separated, monochrome,
4-connected components.  Components touching any outer edge survive unchanged;
strictly interior components are erased.  Color, shape, size, and numeric color
order are deliberately non-predictive of keep/erase status.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f0069f2752a4"
TASK_ID = "f0069f2752a4"
VERSION = "4.0.0"
RULE_HASH = "9502d1357bdc"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a 0-background grid, preserve every monochrome 4-connected component "
    "that touches the outer border and erase every strictly interior component. "
    "Every ordinary draw contains both roles. Counts, dimensions, edge sides, "
    "shapes, sizes, and palettes vary; consecutive lessons include same-color "
    "and same-shape components in opposite roles to rebut color/shape shortcuts."
)

INVARIANTS = [
    "background is 0",
    "at least one border-touching component is present and survives",
    "at least one strictly interior component is present and is erased",
    "components are monochrome, 4-connected, and not orthogonally adjacent",
    "component role depends only on border contact, never color, shape, or size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..18 with a 1/3 canonical-profile anchor",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 8..18 with a 1/3 canonical-profile anchor",
        "valid": "8..18",
    },
    "n_border": {
        "type": "int",
        "default": "difficulty-aware 1..4; anchored lessons use 2 or 3",
        "valid": "1..4",
    },
    "n_interior": {
        "type": "int",
        "default": "difficulty-aware 1..4; anchored lessons use 1 or 2",
        "valid": "1..4",
    },
    "palette_kind": {
        "type": "enum",
        "default": "keyed choice",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Each palette has one exclusive signature color (1, 2, 3, or 5), always used
# by the first component.  This makes palette_kind exactly observable from the
# returned grid without adding a marker or changing the task grammar.
_PALETTES = {
    "default": (1, 4, 6, 8),
    "warm": (2, 4, 7, 9),
    "cool": (3, 6, 7, 8),
    "varied": (5, 4, 8, 9),
}
_SIGNATURE_TO_PALETTE = {1: "default", 2: "warm", 3: "cool", 5: "varied"}

# Normalized, 4-connected shapes.  Singletons are retained for guaranteed
# boundary overrides on the smallest legal 8x8 canvas; normal draws strongly
# prefer larger shapes.
_SHAPES = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
)
_CANONICAL_PROFILES = ((8, 8, 5), (9, 9, 5), (8, 9, 5))
_CANONICAL_ROLE_COUNTS = ((2, 2), (3, 1))

_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_SIDES = ("top", "right", "bottom", "left")


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _translated(shape, r0: int, c0: int) -> tuple[tuple[int, int], ...]:
    return tuple((r0 + dr, c0 + dc) for dr, dc in shape)


def _can_place(
    cells: Iterable[tuple[int, int]], used: set[tuple[int, int]], h: int, w: int
) -> bool:
    cells = tuple(cells)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        return False
    cell_set = set(cells)
    if len(cell_set) != len(cells) or cell_set & used:
        return False
    # Separate components under the exact 4-connectivity used by the oracle.
    return not any((r + dr, c + dc) in used for r, c in cells for dr, dc in _DIR4)


def _border_origins(shape, side: str, h: int, w: int) -> list[tuple[int, int]]:
    sh, sw = _shape_dims(shape)
    if sh > h or sw > w:
        return []
    if side == "top":
        return [(0, c) for c in range(w - sw + 1)]
    if side == "bottom":
        return [(h - sh, c) for c in range(w - sw + 1)]
    if side == "left":
        return [(r, 0) for r in range(h - sh + 1)]
    if side == "right":
        return [(r, w - sw) for r in range(h - sh + 1)]
    raise ValueError(f"unknown border side: {side}")


def _interior_origins(shape, h: int, w: int) -> list[tuple[int, int]]:
    sh, sw = _shape_dims(shape)
    if h - sh - 1 < 1 or w - sw - 1 < 1:
        return []
    return [
        (r, c)
        for r in range(1, h - sh)
        for c in range(1, w - sw)
    ]


def _place_one(
    *,
    role: str,
    preferred_side: str | None,
    preferred_shape,
    shape_pool,
    used: set[tuple[int, int]],
    h: int,
    w: int,
    rng,
) -> tuple[tuple[int, int], ...] | None:
    shapes = [preferred_shape, *shape_pool]
    # Stable de-duplication while preserving preference.
    shapes = list(dict.fromkeys(tuple(s) for s in shapes))
    if role == "border":
        side_order = [preferred_side, *[s for s in _SIDES if s != preferred_side]]
        for shape in shapes:
            for side in side_order:
                origins = _border_origins(shape, side, h, w)
                rng.shuffle(origins)
                for r0, c0 in origins:
                    cells = _translated(shape, r0, c0)
                    if _can_place(cells, used, h, w):
                        return cells
    else:
        for shape in shapes:
            origins = _interior_origins(shape, h, w)
            rng.shuffle(origins)
            for r0, c0 in origins:
                cells = _translated(shape, r0, c0)
                if _can_place(cells, used, h, w):
                    return cells
    return None


def _fallback_singletons(
    h: int, w: int, n_border: int, n_interior: int, side_offset: int
) -> list[dict[str, Any]]:
    """Guaranteed count-preserving layout for every declared boundary case."""
    used: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []

    edge_by_side = {
        "top": [(0, c) for c in range(w)],
        "right": [(r, w - 1) for r in range(h)],
        "bottom": [(h - 1, c) for c in reversed(range(w))],
        "left": [(r, 0) for r in reversed(range(h))],
    }
    sides = [_SIDES[(side_offset + i) % 4] for i in range(n_border)]
    for side in sides:
        candidates = edge_by_side[side]
        chosen = next(
            (
                p
                for p in candidates
                if _can_place((p,), used, h, w)
            ),
            None,
        )
        if chosen is None:
            # Try every edge cell before declaring an impossible legal domain.
            all_edges = list(dict.fromkeys(sum(edge_by_side.values(), [])))
            chosen = next((p for p in all_edges if _can_place((p,), used, h, w)), None)
        if chosen is None:
            raise ValueError("could not place requested border-component count")
        used.add(chosen)
        components.append({"role": "border", "cells": (chosen,)})

    # Center-out checkerboard order gives four mutually separated interior
    # cells on the minimum 8x8 grid while remaining far from selected edges.
    interior = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if (r + c) % 2 == 0
    ]
    cr, cc = (h - 1) / 2.0, (w - 1) / 2.0
    interior.sort(key=lambda p: (abs(p[0] - cr) + abs(p[1] - cc), p))
    for _ in range(n_interior):
        chosen = next((p for p in interior if _can_place((p,), used, h, w)), None)
        if chosen is None:
            raise ValueError("could not place requested interior-component count")
        used.add(chosen)
        components.append({"role": "interior", "cells": (chosen,)})
    return components


def _build_layout(
    h: int,
    w: int,
    n_border: int,
    n_interior: int,
    sample_index: int,
    difficulty: str | None,
    rng,
    *,
    canonical_anchor: bool,
) -> list[dict[str, Any]]:
    total = n_border + n_interior
    max_size = {"easy": 4, "medium": 5, "hard": 5}.get(difficulty, 5)
    if total >= 7 or min(h, w) <= 8:
        max_size = min(max_size, 3)
    shape_pool = [s for s in _SHAPES if 1 < len(s) <= max_size]
    if not shape_pool:
        shape_pool = [s for s in _SHAPES if len(s) == 1]

    # In every non-anchor draw, first kept and erased objects use the same
    # shape. This makes shape an explicitly falsified shortcut in each lesson.
    paired_shape = shape_pool[(sample_index + len(shape_pool)) % len(shape_pool)]
    side_offset = sample_index % 4

    for _attempt in range(48):
        used: set[tuple[int, int]] = set()
        components: list[dict[str, Any]] = []
        ok = True
        for index in range(n_border):
            preferred = paired_shape if index == 0 else rng.choice(shape_pool)
            cells = _place_one(
                role="border",
                preferred_side=_SIDES[(side_offset + index) % 4],
                preferred_shape=preferred,
                shape_pool=shape_pool,
                used=used,
                h=h,
                w=w,
                rng=rng,
            )
            if cells is None:
                ok = False
                break
            used.update(cells)
            components.append({"role": "border", "cells": cells})
        if not ok:
            continue
        for index in range(n_interior):
            preferred = paired_shape if index == 0 and not canonical_anchor else rng.choice(shape_pool)
            cells = _place_one(
                role="interior",
                preferred_side=None,
                preferred_shape=preferred,
                shape_pool=shape_pool,
                used=used,
                h=h,
                w=w,
                rng=rng,
            )
            if cells is None:
                ok = False
                break
            used.update(cells)
            components.append({"role": "interior", "cells": cells})
        if ok:
            return components
    return _fallback_singletons(h, w, n_border, n_interior, side_offset)


def _component_colors(
    components: list[dict[str, Any]], palette: tuple[int, ...], sample_index: int
) -> list[int]:
    n_border = sum(c["role"] == "border" for c in components)
    total = len(components)
    if sample_index % 3 == 0 and total >= 4:
        # Canonical-profile anchor: four nonzero colors are all represented.
        return [palette[i % len(palette)] for i in range(total)]

    colors = [palette[0]] * total
    next_color = 1
    # First border and first interior deliberately share the signature color.
    for index in range(1, n_border):
        colors[index] = palette[next_color % len(palette)]
        next_color += 1
    for index in range(n_border + 1, total):
        colors[index] = palette[next_color % len(palette)]
        next_color += 1
    return colors


def _draw_int_axis(ctx, label: str, lo: int, hi: int, fixed: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if fixed is not None:
        return ctx.draw_int(label, fixed, fixed)
    return ctx.draw_int_diff(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    numeric_overridden = any(
        name in overrides and overrides[name] is not None
        for name in ("grid_h", "grid_w", "n_border", "n_interior")
    )
    canonical_anchor = (not numeric_overridden) and sample_index % 3 == 0
    anchor_slot = (sample_index // 3) % 3
    anchor_dims = ((8, 8), (9, 9), (8, 9))[anchor_slot]
    anchor_counts = ((2, 2), (2, 2), (3, 1))[anchor_slot]

    h = _draw_int_axis(ctx, "grid_h", 8, 18, anchor_dims[0] if canonical_anchor else None)
    w = _draw_int_axis(ctx, "grid_w", 8, 18, anchor_dims[1] if canonical_anchor else None)
    n_border = _draw_int_axis(
        ctx, "n_border", 1, 4, anchor_counts[0] if canonical_anchor else None
    )
    n_interior = _draw_int_axis(
        ctx, "n_interior", 1, 4, anchor_counts[1] if canonical_anchor else None
    )
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    rng = ctx.draw_rng("layout")
    components = _build_layout(
        h,
        w,
        n_border,
        n_interior,
        sample_index,
        difficulty,
        rng,
        canonical_anchor=canonical_anchor,
    )
    colors = _component_colors(components, _PALETTES[palette_kind], sample_index)
    grid = full_grid(h, w, 0)
    for component, color in zip(components, colors):
        for r, c in component["cells"]:
            grid[r][c] = color
    return grid


def _coerce_grid(grid) -> list[list[int]]:
    return [
        [int(value) if isinstance(value, str) and value.isdigit() else value for value in row]
        for row in grid
    ]


def _grid_error(grid) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple, str)) and row for row in grid):
        return ["every row must be a nonempty sequence or digit string"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return errors
    coerced = _coerce_grid(grid)
    if not (1 <= len(coerced) <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within ARC bounds 1..30")
    if any(
        not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
        for row in coerced
        for v in row
    ):
        errors.append("grid values must be integer colors 0..9")
    return errors

def _components(grid) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _DIR4:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            touches = any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "touches_border": touches,
                }
            )
    return result


def _analysis(grid) -> dict[str, Any]:
    errors = _grid_error(grid)
    if errors:
        return {"errors": errors}
    coerced = _coerce_grid(grid)
    h, w = len(coerced), len(coerced[0])
    components = _components(coerced)
    border = [c for c in components if c["touches_border"]]
    interior = [c for c in components if not c["touches_border"]]
    adjacency_errors = []
    for r in range(h):
        for c in range(w):
            if coerced[r][c] == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < h and cc < w and coerced[rr][cc] not in (0, coerced[r][c]):
                    adjacency_errors.append(((r, c), (rr, cc)))
    output = full_grid(h, w, 0)
    for component in border:
        for r, c in component["cells"]:
            output[r][c] = component["color"]
    colors = {v for row in coerced for v in row if v != 0}
    signatures = sorted(colors & set(_SIGNATURE_TO_PALETTE))
    palette_kind = _SIGNATURE_TO_PALETTE[signatures[0]] if len(signatures) == 1 else None
    return {
        "errors": errors,
        "grid": coerced,
        "components": components,
        "border": border,
        "interior": interior,
        "n_border": len(border),
        "n_interior": len(interior),
        "adjacency_errors": adjacency_errors,
        "output": output,
        "palette_kind": palette_kind,
        "nonzero_colors": colors,
    }


def rule_mirror(grid):
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("invalid grid: " + "; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def observe_overrides(grid) -> dict[str, Any]:
    info = _analysis(grid)
    if info.get("errors") or info.get("palette_kind") is None:
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_border": info["n_border"],
        "n_interior": info["n_interior"],
        "palette_kind": info["palette_kind"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    if errors:
        return errors
    if info["n_border"] < 1:
        errors.append("missing border-touching component")
    if info["n_interior"] < 1:
        errors.append("missing strictly interior component")
    if info["adjacency_errors"]:
        errors.append("different-colored components are orthogonally adjacent")
    if info["output"] == info["grid"]:
        errors.append("identity lesson: no interior component is erased")
    if not any(v != 0 for row in info["output"] for v in row):
        errors.append("empty answer: no border component survives")

    requested = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    observed = observe_overrides(grid)
    for name in AXES:
        if name in requested and requested[name] is not None:
            if name == "palette_kind" and info["palette_kind"] is None:
                errors.append("generated palette signature is absent or ambiguous")
                continue
            if observed.get(name) != requested[name]:
                errors.append(
                    f"override {name}={requested[name]!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    info = _analysis(grid)
    profile = (len(grid), len(grid[0]), len(info["nonzero_colors"]) + 1)
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"profile {profile} is outside canonical profiles")
    counts = (info["n_border"], info["n_interior"])
    if counts not in _CANONICAL_ROLE_COUNTS:
        errors.append(f"role counts {counts} are outside canonical relations")
    if len(info["components"]) != 4:
        errors.append("canonical scenes contain exactly four components")
    return errors


MIN_STRICT_FRAC = 0.20


def _normalized_shape(component: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    cells = component["cells"]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _safe_info(grid) -> dict[str, Any]:
    try:
        return _analysis(grid)
    except Exception:
        return {"errors": ["analysis failed"], "border": [], "interior": []}


def _shared_role_color(grid) -> bool:
    info = _safe_info(grid)
    return bool(
        not info.get("errors")
        and {c["color"] for c in info["border"]}
        & {c["color"] for c in info["interior"]}
    )


def _shared_role_shape(grid) -> bool:
    info = _safe_info(grid)
    return bool(
        not info.get("errors")
        and {_normalized_shape(c) for c in info["border"]}
        & {_normalized_shape(c) for c in info["interior"]}
    )


def _touches_horizontal(grid) -> bool:
    info = _safe_info(grid)
    if info.get("errors"):
        return False
    h = len(grid)
    return any(any(r in (0, h - 1) for r, _ in c["cells"]) for c in info["border"])


def _touches_vertical(grid) -> bool:
    info = _safe_info(grid)
    if info.get("errors"):
        return False
    w = len(grid[0])
    return any(any(c0 in (0, w - 1) for _, c0 in c["cells"]) for c in info["border"])


SEMANTIC_WITNESSES = {
    "canonical_profile": lambda grid: strict_canonical_like(grid) == [],
    "two_border_two_interior": lambda grid: (
        (_safe_info(grid).get("n_border"), _safe_info(grid).get("n_interior")) == (2, 2)
    ),
    "three_border_one_interior": lambda grid: (
        (_safe_info(grid).get("n_border"), _safe_info(grid).get("n_interior")) == (3, 1)
    ),
    "same_color_opposite_roles": _shared_role_color,
    "same_shape_opposite_roles": _shared_role_shape,
    "horizontal_edge_survivor": _touches_horizontal,
    "vertical_edge_survivor": _touches_vertical,
}


def _edge_sides(component: dict[str, Any], h: int, w: int) -> set[str]:
    sides: set[str] = set()
    for r, c in component["cells"]:
        if r == 0:
            sides.add("top")
        if r == h - 1:
            sides.add("bottom")
        if c == 0:
            sides.add("left")
        if c == w - 1:
            sides.add("right")
    return sides


def lesson_identifiable(demos, query) -> list[str]:
    findings: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is malformed")
            continue
        if rule_mirror(pair["input"]) != _coerce_grid(pair["output"]):
            findings.append(f"pair {index} output disagrees with border-touch rule")
    if findings:
        return findings

    kept_colors: set[int] = set()
    erased_colors: set[int] = set()
    kept_shapes: set[tuple[tuple[int, int], ...]] = set()
    erased_shapes: set[tuple[tuple[int, int], ...]] = set()
    sides: set[str] = set()
    for pair in demos:
        info = _analysis(pair["input"])
        kept_colors.update(c["color"] for c in info["border"])
        erased_colors.update(c["color"] for c in info["interior"])
        kept_shapes.update(_normalized_shape(c) for c in info["border"])
        erased_shapes.update(_normalized_shape(c) for c in info["interior"])
        for component in info["border"]:
            sides.update(_edge_sides(component, len(pair["input"]), len(pair["input"][0])))
    if not kept_colors or not erased_colors:
        findings.append("demos do not show both a kept and an erased component")
    if not (kept_colors & erased_colors):
        findings.append("demos permit a fixed color-whitelist shortcut")
    if not (kept_shapes & erased_shapes):
        findings.append("demos permit a fixed shape-whitelist shortcut")
    if len(sides) < 2:
        findings.append("demos expose fewer than two border sides")
    return findings
