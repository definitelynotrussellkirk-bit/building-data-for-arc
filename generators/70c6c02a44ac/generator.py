"""Generator for ``arc_additional_puzzles_21_set6:E41``.

The input contains one red (2) source glyph and two or three green (3)
anchor cells.  The canonical Racket rule normalizes the source to its bounding
box origin, stamps that shape at every anchor, recolors every stamped cell
 green, and clears the source.

Every declared axis is exact and recoverable from the returned input grid.
Ordinary draws deliberately use non-rectangular multi-cell glyphs, more than
one anchor, a source away from the grid origin, and projected copies disjoint
from the source.  Those constraints make marker-only, bbox-fill, first-anchor,
keep-source, absolute-coordinate, and wrong-color shortcuts observable.
"""
from __future__ import annotations

from collections.abc import Callable
from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "70c6c02a44ac"
TASK_ID = "70c6c02a44ac"
VERSION = "4.0.0"
RULE_HASH = "53ceb2a607c4"

SUMMARY = (
    "Place one connected non-rectangular red (2) source glyph and two or three "
    "green (3) anchor cells on an 8-10 by 10-12 zero-background grid. The "
    "source is away from the grid origin. Most anchors hold the full glyph; "
    "a scheduled edge branch clips one copy exactly as an official training "
    "pair does. The output clears the input, stamps the normalized "
    "source shape at every anchor, and recolors all stamped cells green (3)."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid size is 8..10 rows by 10..12 columns with colors only 0, 2, and 3",
    "color 2 forms exactly one connected non-rectangular catalog glyph",
    "the source bbox origin is not grid coordinate (0, 0)",
    "there are exactly 2 or 3 green anchor cells",
    "each anchor shows at least its origin cell; scheduled edge copies may clip",
    "visible projected copy cells are disjoint from the red source cells",
]

SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "hook6": ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    "elbow4": ((0, 0), (1, 0), (1, 1), (1, 2)),
    "corner4": ((0, 0), (0, 1), (0, 2), (1, 0)),
    "zigzag5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "fork5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "stair6": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    "arch5": ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
    "tee5": ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1)),
    "tail6": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3)),
    "stair5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
}
SHAPE_FAMILIES = tuple(SHAPES)
SOURCE_BANDS = ("top", "bottom")
ANCHOR_MODES = ("separate", "overlap")
EDGE_SCHEDULE = ("clipped", "inside", "inside")
SCHEDULE_PROFILES = ("inside", "clipped")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8..9 easy / 8..10 medium / 9..10 hard",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "10..11 easy / 10..12 medium / 11..12 hard",
        "valid": "10..12",
    },
    "shape_family": {
        "type": "str",
        "default": "keyed catalog choice",
        "valid": "hook6|elbow4|corner4|zigzag5|fork5|stair6|arch5|tee5|tail6|stair5",
    },
    "n_anchors": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "2..3",
    },
    "source_band": {
        "type": "str",
        "default": "keyed top/bottom choice",
        "valid": "top|bottom",
    },
    "anchor_mode": {
        "type": "str",
        "default": "keyed separate/overlap choice",
        "valid": "separate|overlap",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic canonical-rule input grid."""
    _reject_unknown_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h_lo, h_hi, w_lo, w_hi = _difficulty_bounds(difficulty)
    h = _draw_full_range_on_override(ctx, "grid_h", h_lo, h_hi, 8, 10)
    w = _draw_full_range_on_override(ctx, "grid_w", w_lo, w_hi, 10, 12)
    shape_family = ctx.draw_choice("shape_family", SHAPE_FAMILIES)
    n_anchors = ctx.draw_int("n_anchors", 2, 3)
    source_band = ctx.draw_choice("source_band", SOURCE_BANDS)
    anchor_mode = ctx.draw_choice("anchor_mode", ANCHOR_MODES)
    edge_profile = schedule_profile(seed, sample_index, difficulty)

    shape = SHAPES[shape_family]
    shape_h, shape_w = _shape_size(shape)
    rng = ctx.draw_rng("layout")

    source_rows = _source_row_candidates(h, shape_h, source_band)
    source_cols = list(range(1, w - shape_w + 1))
    if not source_rows or not source_cols:
        raise ValueError(
            f"{h}x{w} cannot place {shape_family} in source_band={source_band!r}"
        )
    source_r = rng.choice(source_rows)
    source_c = rng.choice(source_cols)
    source_cells = {
        (source_r + dr, source_c + dc)
        for dr, dc in shape
    }

    candidates = _anchor_candidates(
        h,
        w,
        shape,
        source_cells=source_cells,
        source_band=source_band,
    )
    anchors = _choose_anchors(
        candidates,
        n_anchors=n_anchors,
        mode=anchor_mode,
        edge_profile=edge_profile,
        rng=rng,
    )

    grid = full_grid(h, w, 0)
    paint_at(grid, source_r, source_c, shape, 2)
    for r, c in anchors:
        grid[r][c] = 3
    return grid


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a returned grid."""
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe malformed glyph-broadcast grid: " + "; ".join(errors))
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "shape_family": info["shape_family"],
        "n_anchors": len(info["anchors"]),
        "source_band": info["source_band"],
        "anchor_mode": info["anchor_mode"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and scenes that hide the intended operation."""
    del difficulty, meta
    _, errors = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This generator is intentionally pinned to one strict task grammar."""
    return self_check(grid)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared edge-coverage schedule profile."""
    del seed, difficulty
    return EDGE_SCHEDULE[int(sample_index) % len(EDGE_SCHEDULE)]


def _difficulty_bounds(difficulty) -> tuple[int, int, int, int]:
    if difficulty == "easy":
        return 8, 9, 10, 11
    if difficulty == "hard":
        return 9, 10, 11, 12
    return 8, 10, 10, 12


def _draw_full_range_on_override(ctx, label, lo, hi, full_lo, full_hi):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, full_lo, full_hi)
    return ctx.draw_int(label, lo, hi)


def _reject_unknown_overrides(overrides) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _source_row_candidates(h: int, shape_h: int, band: str) -> list[int]:
    legal = list(range(0, h - shape_h + 1))
    if band == "top":
        return [r for r in legal if r + shape_h <= (h + 1) // 2]
    if band == "bottom":
        return [r for r in legal if r >= h // 2]
    raise ValueError(f"unknown source band: {band!r}")


def _stamp(anchor, shape) -> set[tuple[int, int]]:
    ar, ac = anchor
    return {(ar + dr, ac + dc) for dr, dc in shape}


def _anchor_candidates(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    *,
    source_cells: set[tuple[int, int]],
    source_band: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            anchor = (r, c)
            full = _stamp(anchor, shape)
            visible = {
                (rr, cc) for rr, cc in full
                if 0 <= rr < h and 0 <= cc < w
            }
            if not visible or visible & source_cells:
                continue
            if any(
                abs(r - sr) + abs(c - sc) <= 1
                for sr, sc in source_cells
            ):
                continue
            # Keep anchors on the opposite side of the source.  Clipped anchors
            # may sit on the final row/column, as in canonical training pair 4.
            if source_band == "top" and r < h // 3:
                continue
            if source_band == "bottom" and r > (2 * h) // 3:
                continue
            candidates.append({
                "anchor": anchor,
                "visible": visible,
                "clipped": len(visible) != len(full),
            })
    return candidates


def _choose_anchors(candidates, *, n_anchors, mode, edge_profile, rng):
    inside = [item for item in candidates if not item["clipped"]]
    clipped = [item for item in candidates if item["clipped"]]
    rng.shuffle(inside)
    rng.shuffle(clipped)

    if edge_profile not in {"inside", "clipped"}:
        raise ValueError(f"unknown edge profile: {edge_profile!r}")

    def valid(group) -> bool:
        anchors = [item["anchor"] for item in group]
        if not all(
            abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1
            for a, b in combinations(anchors, 2)
        ):
            return False
        clip_count = sum(bool(item["clipped"]) for item in group)
        if edge_profile == "inside" and clip_count != 0:
            return False
        if edge_profile == "clipped" and clip_count != 1:
            return False
        has_overlap = any(
            a["visible"] & b["visible"]
            for a, b in combinations(group, 2)
        )
        for item in group:
            others = set().union(*(other["visible"] for other in group if other is not item))
            if not (item["visible"] - others):
                return False
        return has_overlap if mode == "overlap" else not has_overlap

    groups = []
    if edge_profile == "inside":
        groups = combinations(inside, n_anchors)
    else:
        groups = (
            (edge, *rest)
            for edge in clipped
            for rest in combinations(inside, n_anchors - 1)
        )
    for group in groups:
        if valid(group):
            return tuple(sorted(item["anchor"] for item in group))
    raise ValueError(
        f"no legal {mode}/{edge_profile} placement for "
        f"n_anchors={n_anchors}"
    )


def _component(cells: set[tuple[int, int]], start: tuple[int, int]) -> set[tuple[int, int]]:
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def _analyze_grid(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {}, ["grid rows must be rectangular"]
    if not (8 <= h <= 10 and 10 <= w <= 12):
        errors.append(f"grid size {h}x{w} outside 8..10 by 10..12")

    twos: set[tuple[int, int]] = set()
    anchors: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            if value not in {0, 2, 3}:
                errors.append(f"unsupported color {value} at ({r},{c})")
            elif value == 2:
                twos.add((r, c))
            elif value == 3:
                anchors.append((r, c))
    if errors:
        return {}, errors
    if not twos:
        return {}, ["missing red (2) source glyph"]
    connected = _component(twos, next(iter(twos)))
    if connected != twos:
        errors.append("red source must be exactly one 4-connected component")

    min_r = min(r for r, _ in twos)
    max_r = max(r for r, _ in twos)
    min_c = min(c for _, c in twos)
    max_c = max(c for _, c in twos)
    normalized = tuple(sorted((r - min_r, c - min_c) for r, c in twos))
    reverse_shapes = {tuple(sorted(shape)): name for name, shape in SHAPES.items()}
    shape_family = reverse_shapes.get(normalized)
    if shape_family is None:
        errors.append(f"red source is not a declared catalog glyph: {normalized!r}")
    shape_h = max_r - min_r + 1
    shape_w = max_c - min_c + 1
    if len(twos) == shape_h * shape_w:
        errors.append("solid rectangular source hides shape-copying behind bbox fill")
    if (min_r, min_c) == (0, 0):
        errors.append("source bbox origin must not equal grid origin")
    if not 2 <= len(anchors) <= 3:
        errors.append(f"expected 2 or 3 green anchors, got {len(anchors)}")

    source_band = "top" if (min_r + max_r) < h - 1 else "bottom"
    projected: list[set[tuple[int, int]]] = []
    if shape_family is not None:
        shape = SHAPES[shape_family]
        for anchor in anchors:
            cells = _stamp(anchor, shape)
            visible = {(r, c) for r, c in cells if 0 <= r < h and 0 <= c < w}
            if not visible:
                errors.append(f"glyph stamped at anchor {anchor} has no visible cells")
            if visible & twos:
                errors.append(f"glyph stamped at anchor {anchor} overlaps red source")
            projected.append(visible)
    has_overlap = any(a & b for a, b in combinations(projected, 2))
    for index, cells in enumerate(projected):
        others = set().union(*(other for j, other in enumerate(projected) if j != index))
        if not (cells - others):
            errors.append(f"anchor {anchors[index]} contributes no unique visible output cell")
    has_clipped = False
    if shape_family is not None:
        shape = SHAPES[shape_family]
        has_clipped = any(len(_stamp(anchor, shape)) != len(projected[i])
                          for i, anchor in enumerate(anchors))
    anchor_mode = "overlap" if has_overlap else "separate"

    info = {
        "h": h,
        "w": w,
        "source_cells": twos,
        "source_origin": (min_r, min_c),
        "normalized": normalized,
        "shape_family": shape_family,
        "anchors": tuple(sorted(anchors)),
        "source_band": source_band,
        "anchor_mode": anchor_mode,
        "edge_profile": "clipped" if has_clipped else "inside",
        "projected": projected,
    }
    return info, errors


def _solve_grid(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot solve malformed grid: " + "; ".join(errors))
    out = full_grid(info["h"], info["w"], 0)
    shape = SHAPES[info["shape_family"]]
    for anchor in info["anchors"]:
        for r, c in _stamp(anchor, shape):
            if 0 <= r < info["h"] and 0 <= c < info["w"]:
                out[r][c] = 3
    return out


def _marker_only_rival(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed grid")
    out = full_grid(info["h"], info["w"], 0)
    for r, c in info["anchors"]:
        out[r][c] = 3
    return out


def _bbox_fill_rival(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed grid")
    shape = SHAPES[info["shape_family"]]
    shape_h, shape_w = _shape_size(shape)
    out = full_grid(info["h"], info["w"], 0)
    for ar, ac in info["anchors"]:
        for dr in range(shape_h):
            for dc in range(shape_w):
                r, c = ar + dr, ac + dc
                if 0 <= r < info["h"] and 0 <= c < info["w"]:
                    out[r][c] = 3
    return out


def _first_anchor_only_rival(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed grid")
    out = full_grid(info["h"], info["w"], 0)
    shape = SHAPES[info["shape_family"]]
    for r, c in _stamp(info["anchors"][0], shape):
        if 0 <= r < info["h"] and 0 <= c < info["w"]:
            out[r][c] = 3
    return out


def _keep_source_rival(grid):
    out = _solve_grid(grid)
    info, _ = _analyze_grid(grid)
    for r, c in info["source_cells"]:
        out[r][c] = 2
    return out


def _absolute_coordinates_rival(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed grid")
    out = full_grid(info["h"], info["w"], 0)
    for ar, ac in info["anchors"]:
        for sr, sc in info["source_cells"]:
            r, c = ar + sr, ac + sc
            if 0 <= r < info["h"] and 0 <= c < info["w"]:
                out[r][c] = 3
    return out


def _wrong_color_rival(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed grid")
    out = full_grid(info["h"], info["w"], 0)
    shape = SHAPES[info["shape_family"]]
    for anchor in info["anchors"]:
        for r, c in _stamp(anchor, shape):
            if 0 <= r < info["h"] and 0 <= c < info["w"]:
                out[r][c] = 2
    return out


def _discard_clipped_anchor_rival(grid):
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("malformed grid")
    out = full_grid(info["h"], info["w"], 0)
    shape = SHAPES[info["shape_family"]]
    for anchor in info["anchors"]:
        full = _stamp(anchor, shape)
        if all(0 <= r < info["h"] and 0 <= c < info["w"] for r, c in full):
            for r, c in full:
                out[r][c] = 3
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "leave only the green markers": _marker_only_rival,
    "fill the source bounding box at every anchor": _bbox_fill_rival,
    "stamp only the first anchor": _first_anchor_only_rival,
    "keep the red source in the output": _keep_source_rival,
    "use absolute source coordinates instead of bbox normalization": _absolute_coordinates_rival,
    "copy the source color instead of recoloring green": _wrong_color_rival,
    "discard anchors whose copies cross the boundary": _discard_clipped_anchor_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _info(grid):
    info, errors = _analyze_grid(grid)
    return info if not errors else {}


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "two_anchors": lambda grid: len(_info(grid).get("anchors", ())) == 2,
    "three_anchors": lambda grid: len(_info(grid).get("anchors", ())) == 3,
    "source_top": lambda grid: _info(grid).get("source_band") == "top",
    "source_bottom": lambda grid: _info(grid).get("source_band") == "bottom",
    "separate_projected_stamps": lambda grid: _info(grid).get("anchor_mode") == "separate",
    "overlapping_projected_stamps": lambda grid: _info(grid).get("anchor_mode") == "overlap",
    "fully_inside_stamps": lambda grid: _info(grid).get("edge_profile") == "inside",
    "clipped_edge_stamp": lambda grid: _info(grid).get("edge_profile") == "clipped",
    "nonrectangular_template": lambda grid: bool(_info(grid).get("shape_family")),
    "source_not_at_origin": lambda grid: _info(grid).get("source_origin") != (0, 0),
    "multiple_template_cells": lambda grid: len(_info(grid).get("source_cells", ())) > 1,
    "copies_recolored_green": lambda grid: bool(_info(grid).get("anchors")),
}

WITNESS_RIVALS = {
    "nonrectangular_template": ["fill the source bounding box at every anchor"],
    "three_anchors": ["stamp only the first anchor"],
    "two_anchors": ["stamp only the first anchor"],
    "separate_projected_stamps": ["stamp only the first anchor"],
    "overlapping_projected_stamps": ["stamp only the first anchor"],
    "fully_inside_stamps": ["keep the red source in the output"],
    "clipped_edge_stamp": ["discard anchors whose copies cross the boundary"],
    "source_not_at_origin": [
        "use absolute source coordinates instead of bbox normalization"
    ],
    "multiple_template_cells": ["leave only the green markers"],
    "copies_recolored_green": ["copy the source color instead of recoloring green"],
    "source_top": ["keep the red source in the output"],
    "source_bottom": ["keep the red source in the output"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that still admit a named shortcut on the query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is malformed: {'; '.join(errors)}")
            continue
        if pair["output"] != _solve_grid(pair["input"]):
            reasons.append(f"pair {index} output disagrees with glyph-broadcast rule")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(
                    f"demonstrations leave rival answer-equivalent on query: {name}"
                )
    return reasons
