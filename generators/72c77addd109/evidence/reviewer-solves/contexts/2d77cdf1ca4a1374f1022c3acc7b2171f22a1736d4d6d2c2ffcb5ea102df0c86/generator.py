"""Generator for ARC task ``72c77addd109``.

Two hollow rectangular frames and two other monochrome components appear on a
zero background.  Rank frames by *interior area* and solids by *cell count*,
then pair equal ranks.  The output is a fresh background grid containing the
frames in their original locations and each paired solid's tight crop centered
on its frame.  The authoritative program centers relative to the frame
interior but does not clip: a crop larger than the interior may overwrite frame
border cells.

The curriculum deliberately breaks two shortcuts that all public examples
leave alive: the smaller solid is not always first in reading order and is not
always the lower-numbered color.  It also varies frame reading order, includes
non-rectangular solids, and includes lawful border-overwrite cases.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "72c77addd109"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a657cfe83f60"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "A 0-background grid contains exactly two hollow rectangular frames and "
    "two other connected monochrome objects, all in distinct colors. Sort "
    "frames by interior area and objects by cell count; pair equal ranks. "
    "Return a fresh 0 grid with every frame redrawn at its original location "
    "and each paired object's tight crop centered on that frame. Nonzero crop "
    "cells are pasted after the frame, so a crop larger than the interior can "
    "overwrite frame-border cells. Original object locations disappear."
)

INVARIANTS = [
    "background is 0 and exactly four distinct nonzero colors are used",
    "exactly two complete hollow rectangular frames have unequal interior areas",
    "exactly two other 4-connected monochrome objects have unequal cell counts",
    "each solid crop fits inside the outer bounding box of its rank-paired frame",
    "objects are spatially separated in generated lessons, while canonical arbitrary solids remain accepted",
]

SOLID_STYLES = ("rectangles", "irregular", "mixed")
RANK_ORDERS = ("ascending", "descending")
COLOR_ORDERS = ("ascending", "descending")
PALETTE_KINDS = ("canonical", "varied")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors 11; otherwise difficulty-aware 12..16",
        "valid": "11..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors 12 or 13; otherwise difficulty-aware 14..18",
        "valid": "12..18",
    },
    "solid_style": {
        "type": "str",
        "default": "three-slot schedule",
        "valid": "rectangles|irregular|mixed",
    },
    "solid_rank_order": {
        "type": "str",
        "default": "three-slot counter-shortcut schedule",
        "valid": "ascending|descending",
    },
    "frame_rank_order": {
        "type": "str",
        "default": "three-slot counter-shortcut schedule",
        "valid": "ascending|descending",
    },
    "solid_color_order": {
        "type": "str",
        "default": "three-slot counter-shortcut schedule",
        "valid": "ascending|descending",
    },
    "palette_kind": {
        "type": "str",
        "default": "canonical on two schedule slots, varied on one",
        "valid": "canonical|varied",
    },
}

# Every cross-product combination of the public exact axes is constructible,
# including both dimension endpoints in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Tight, normalized cell sets.  Each pair is (smaller area, larger area).
# Rotations/reflections are applied later without changing area or rectangularity.
_RECTANGLE_PAIRS: tuple[tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]], ...] = (
    (frozenset({(0, 0)}), frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})),
    (frozenset({(0, 0), (0, 1)}), frozenset({(r, c) for r in range(2) for c in range(3)})),
    (frozenset({(0, 0)}), frozenset({(r, c) for r in range(3) for c in range(2)})),
)

_L3 = frozenset({(0, 0), (0, 1), (1, 1)})
_PLUS5 = frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})
_P5 = frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)})
_Z4 = frozenset({(0, 0), (0, 1), (1, 1), (1, 2)})
_U7 = frozenset({(0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)})
_IRREGULAR_PAIRS = (
    (_L3, _PLUS5),
    (_L3, _P5),
    (_Z4, _U7),
)
_MIXED_PAIRS = (
    (frozenset({(0, 0)}), _PLUS5),
    (_L3, frozenset({(r, c) for r in range(2) for c in range(3)})),
    (frozenset({(0, 0), (0, 1)}), _P5),
)

# (small-frame dimensions, large-frame dimensions).  Interior areas are always
# distinct; all shape templates fit in the paired frame's OUTER bounding box.
_FRAME_PROFILES = (
    ((3, 3), (4, 4)),
    ((3, 3), (3, 4)),
    ((3, 3), (4, 3)),
)


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    for name in ("grid_h", "grid_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:  # reject bool and permissive int("12") coercion
            raise ValueError(f"{name} override must be an integer, got {value!r}")
        lo, hi = (11, 16) if name == "grid_h" else (12, 18)
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    domains = {
        "solid_style": SOLID_STYLES,
        "solid_rank_order": RANK_ORDERS,
        "frame_rank_order": RANK_ORDERS,
        "solid_color_order": COLOR_ORDERS,
        "palette_kind": PALETTE_KINDS,
    }
    for name, domain in domains.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str or value not in domain:
            raise ValueError(f"{name} override {value!r} not in {domain}")


def _scheduled_dimensions(seed: int, sample_index: int, difficulty) -> tuple[int, int]:
    """Two-thirds canonical anchors; remaining slots widen by difficulty."""
    slot = int(sample_index) % 6
    if slot in (0, 3):
        return 11, 12
    if slot in (1, 4):
        return 11, 13

    if difficulty == "easy":
        return 12, 14
    if difficulty == "medium":
        return 14, 16
    if difficulty == "hard":
        return 16, 18
    # Deterministic broad defaults without unkeyed randomness.
    return 12 + (int(seed) + int(sample_index)) % 5, 14 + (2 * int(seed) + int(sample_index)) % 5


def _scheduled_semantics(sample_index: int) -> dict[str, str]:
    """Any three consecutive samples include the principal counterexample slot."""
    slot = int(sample_index) % 3
    return {
        "solid_style": SOLID_STYLES[slot],
        "solid_rank_order": ("ascending", "descending", "descending")[slot],
        "frame_rank_order": ("ascending", "descending", "descending")[slot],
        "solid_color_order": ("ascending", "descending", "descending")[slot],
        "palette_kind": ("canonical", "canonical", "varied")[slot],
    }


def _draw_int_axis(ctx, overrides: dict[str, object], name: str, lo: int, hi: int, default: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_choice_axis(
    ctx,
    overrides: dict[str, object],
    name: str,
    domain: Sequence[str],
    default: str,
) -> str:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, domain)
    return ctx.draw_choice(name, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _transform(cells: frozenset[tuple[int, int]], code: int) -> frozenset[tuple[int, int]]:
    """Apply one of eight dihedral transforms and renormalize."""
    points = set(cells)
    if code & 4:
        points = {(r, -c) for r, c in points}
    for _ in range(code & 3):
        points = {(c, -r) for r, c in points}
    return _normalize(points)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _is_filled_shape(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = _normalize(cells)
    h, w = _shape_dims(normalized)
    return normalized == frozenset((r, c) for r in range(h) for c in range(w))


def _shape_pair(
    style: str, ctx, entropy_tag: str
) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    banks = {
        "rectangles": _RECTANGLE_PAIRS,
        "irregular": _IRREGULAR_PAIRS,
        "mixed": _MIXED_PAIRS,
    }
    bank = banks[style]
    variant = ctx.draw_rng(f"shape_variant:{entropy_tag}").randrange(len(bank))
    small, large = bank[variant]
    small = _transform(small, ctx.draw_rng(f"small_shape_transform:{entropy_tag}").randrange(8))
    large = _transform(large, ctx.draw_rng(f"large_shape_transform:{entropy_tag}").randrange(8))
    if not len(small) < len(large):
        raise AssertionError("shape bank lost strict area order")
    return small, large


def _palette(
    kind: str, color_order: str, ctx, entropy_tag: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return colors ordered by solid/frame area: (small, large)."""
    rng = ctx.draw_rng(f"palette_values:{entropy_tag}")
    if kind == "canonical":
        solid = (2, 5) if color_order == "ascending" else (5, 2)
        frame = (7, 8)
        if rng.randint(0, 1):
            frame = frame[::-1]
        return solid, frame

    for _ in range(32):
        picked = rng.sample(list(range(1, 10)), 4)
        solid_set = picked[:2]
        frame = (picked[2], picked[3])
        if set(solid_set) == {2, 5} and set(frame) == {7, 8}:
            continue
        solid_sorted = tuple(sorted(solid_set))
        solid = solid_sorted if color_order == "ascending" else solid_sorted[::-1]
        if rng.randint(0, 1):
            frame = frame[::-1]
        return solid, frame
    raise ValueError("could not draw a non-canonical varied palette")


def _ordered_pair_by_rank(
    small: Any, large: Any, order: str
) -> tuple[Any, Any]:
    if order == "ascending":
        return small, large
    if order == "descending":
        return large, small
    raise ValueError(f"unknown rank order {order!r}")


def _horizontal_positions(width: int, item_widths: Sequence[int], rng) -> tuple[int, ...]:
    if len(item_widths) != 2:
        raise ValueError("this generator places exactly two horizontal items")
    slack = width - sum(item_widths)
    if slack < 1:
        raise ValueError(f"items {item_widths} do not fit width {width} with a gap")
    gap = rng.randint(1, min(3, slack))
    remaining = width - sum(item_widths) - gap
    start = rng.randint(0, remaining)
    return start, start + item_widths[0] + gap


def _paint_shape(
    grid: list[list[int]], top: int, left: int,
    cells: Iterable[tuple[int, int]], color: int,
) -> None:
    for r, c in cells:
        if grid[top + r][left + c] != 0:
            raise ValueError("shape placement collision")
        grid[top + r][left + c] = color


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

    default_h, default_w = _scheduled_dimensions(seed, sample_index, difficulty)
    defaults = _scheduled_semantics(sample_index)
    height = _draw_int_axis(ctx, overrides, "grid_h", 11, 16, default_h)
    width = _draw_int_axis(ctx, overrides, "grid_w", 12, 18, default_w)
    style = _draw_choice_axis(ctx, overrides, "solid_style", SOLID_STYLES, defaults["solid_style"])
    solid_order = _draw_choice_axis(
        ctx, overrides, "solid_rank_order", RANK_ORDERS, defaults["solid_rank_order"]
    )
    frame_order = _draw_choice_axis(
        ctx, overrides, "frame_rank_order", RANK_ORDERS, defaults["frame_rank_order"]
    )
    color_order = _draw_choice_axis(
        ctx, overrides, "solid_color_order", COLOR_ORDERS, defaults["solid_color_order"]
    )
    palette_kind = _draw_choice_axis(
        ctx, overrides, "palette_kind", PALETTE_KINDS, defaults["palette_kind"]
    )

    entropy_tag = "none" if difficulty is None else str(difficulty)
    small_shape, large_shape = _shape_pair(style, ctx, entropy_tag)
    frame_profile = _FRAME_PROFILES[
        ctx.draw_rng(f"frame_profile:{entropy_tag}").randrange(len(_FRAME_PROFILES))
    ]
    small_frame, large_frame = frame_profile
    solid_colors, frame_colors = _palette(palette_kind, color_order, ctx, entropy_tag)

    # Reading-order axes are encoded geometrically by left-to-right order. Both
    # members in a pair share the same top row, so the observer is exact.
    left_shape, right_shape = _ordered_pair_by_rank(small_shape, large_shape, solid_order)
    shape_color_by_object = {
        small_shape: solid_colors[0],
        large_shape: solid_colors[1],
    }
    left_frame, right_frame = _ordered_pair_by_rank(small_frame, large_frame, frame_order)
    frame_color_by_dim = {
        small_frame: frame_colors[0],
        large_frame: frame_colors[1],
    }

    solid_heights = [_shape_dims(left_shape)[0], _shape_dims(right_shape)[0]]
    solid_widths = [_shape_dims(left_shape)[1], _shape_dims(right_shape)[1]]
    frame_heights = [left_frame[0], right_frame[0]]
    frame_widths = [left_frame[1], right_frame[1]]

    max_solid_h = max(solid_heights)
    max_frame_h = max(frame_heights)
    solid_top_limit = min(2, height - max_solid_h - max_frame_h - 2)
    if solid_top_limit < 0:
        raise ValueError("requested canvas is too short for separated solids and frames")
    solid_pos_rng = ctx.draw_rng(f"solid_position:{entropy_tag}")
    solid_top = solid_pos_rng.randint(0, solid_top_limit)
    solid_lefts = _horizontal_positions(width, solid_widths, solid_pos_rng)

    min_frame_top = solid_top + max_solid_h + 2
    max_frame_top = height - max_frame_h
    if min_frame_top > max_frame_top:
        raise ValueError("requested canvas cannot separate frames from solids")
    frame_pos_rng = ctx.draw_rng(f"frame_position:{entropy_tag}")
    frame_top = frame_pos_rng.randint(max(min_frame_top, max_frame_top - 2), max_frame_top)
    frame_lefts = _horizontal_positions(width, frame_widths, frame_pos_rng)

    grid = full_grid(height, width, 0)
    for shape, top, left in zip((left_shape, right_shape), (solid_top, solid_top), solid_lefts):
        _paint_shape(grid, top, left, shape, shape_color_by_object[shape])
    for dim, left in zip((left_frame, right_frame), frame_lefts):
        fh, fw = dim
        draw_frame(
            grid,
            frame_top,
            left,
            frame_top + fh - 1,
            left + fw - 1,
            frame_color_by_dim[dim],
        )

    findings = self_check(grid)
    if findings:
        raise ValueError("internal generation defect: " + "; ".join(findings))
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and exact observation
# ---------------------------------------------------------------------------


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r1, c1, r2, c2 = _bbox(cells)
    return r2 - r1 + 1, c2 - c1 + 1


def _is_frame_component(cells: Iterable[tuple[int, int]]) -> bool:
    cells = tuple(cells)
    if not cells:
        return False
    r1, c1, r2, c2 = _bbox(cells)
    h, w = r2 - r1 + 1, c2 - c1 + 1
    if h < 3 or w < 3:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return set(cells) == border


def _is_filled_component(cells: Iterable[tuple[int, int]]) -> bool:
    cells = tuple(cells)
    if not cells:
        return False
    r1, c1, r2, c2 = _bbox(cells)
    return set(cells) == {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
    }


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components_found: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components_found.append({"color": color, "cells": tuple(sorted(cells))})
    return components_found


def _analyze(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "frames": [],
        "solids": [],
    }
    errors: list[str] = result["errors"]
    if not isinstance(grid, list) or not grid:
        errors.append("expected a non-empty list of rows")
        return result
    if not isinstance(grid[0], list) or not grid[0]:
        errors.append("expected non-empty list rows")
        return result
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid rows have inconsistent widths")
        return result
    bad = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        errors.append("grid contains a non-integer or color outside 0..9")
        return result

    result["height"], result["width"] = len(grid), width
    components_found = _components(grid)
    frames = [obj for obj in components_found if _is_frame_component(obj["cells"])]
    solids = [obj for obj in components_found if not _is_frame_component(obj["cells"])]
    result["frames"], result["solids"] = frames, solids

    if len(frames) != 2:
        errors.append(f"expected exactly 2 hollow frames, found {len(frames)}")
    if len(solids) != 2:
        errors.append(f"expected exactly 2 non-frame solids, found {len(solids)}")
    if len(components_found) == 4 and len({obj["color"] for obj in components_found}) != 4:
        errors.append("the four objects must use distinct nonzero colors")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background 0 must remain present")

    if len(frames) == 2:
        frame_areas = [(_dims(obj["cells"])[0] - 2) * (_dims(obj["cells"])[1] - 2) for obj in frames]
        if len(set(frame_areas)) != 2:
            errors.append("frame interior areas are tied")
    if len(solids) == 2:
        solid_areas = [len(obj["cells"]) for obj in solids]
        if len(set(solid_areas)) != 2:
            errors.append("solid cell counts are tied")
    if len(frames) == 2 and len(solids) == 2:
        ranked_frames = sorted(frames, key=_frame_interior_area)
        ranked_solids = sorted(solids, key=lambda obj: len(obj["cells"]))
        for index, (frame, solid) in enumerate(zip(ranked_frames, ranked_solids)):
            fh, fw = _dims(frame["cells"])
            sh, sw = _dims(solid["cells"])
            if sh > fh or sw > fw:
                errors.append(
                    f"rank {index} solid crop {sh}x{sw} exceeds paired frame bbox {fh}x{fw}"
                )
    return result


def _frame_interior_area(obj: dict[str, Any]) -> int:
    h, w = _dims(obj["cells"])
    return (h - 2) * (w - 2)


def _reading_key(obj: dict[str, Any]) -> tuple[int, int]:
    r1, c1, _, _ = _bbox(obj["cells"])
    return r1, c1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Mutation-sensitive predicate for canonical inputs and generated lessons."""
    del difficulty, meta
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return sorted(set(errors))
    height, width = int(info["height"]), int(info["width"])
    if not 11 <= height <= 16:
        errors.append(f"height {height} outside canonical/generated envelope 11..16")
    if not 12 <= width <= 18:
        errors.append(f"width {width} outside canonical/generated envelope 12..18")
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Canonical dimensions/palette plus the actual broad object grammar."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    if (len(grid), len(grid[0])) not in {(11, 12), (11, 13)}:
        reasons.append("dimensions are not canonical 11x12 or 11x13")
    info = _analyze(grid)
    frame_colors = {obj["color"] for obj in info["frames"]}
    solid_colors = {obj["color"] for obj in info["solids"]}
    if frame_colors != {7, 8} or solid_colors != {2, 5}:
        reasons.append("canonical roles require frame colors {7,8} and solid colors {2,5}")
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from returned-grid geometry."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    frames: list[dict[str, Any]] = info["frames"]
    solids: list[dict[str, Any]] = info["solids"]
    frames_by_area = sorted(frames, key=_frame_interior_area)
    solids_by_area = sorted(solids, key=lambda obj: len(obj["cells"]))
    frames_by_reading = sorted(frames, key=_reading_key)
    solids_by_reading = sorted(solids, key=_reading_key)

    rectangular = [_is_filled_component(obj["cells"]) for obj in solids]
    if all(rectangular):
        style = "rectangles"
    elif not any(rectangular):
        style = "irregular"
    else:
        style = "mixed"

    solid_colors_by_area = [obj["color"] for obj in solids_by_area]
    solid_color_order = (
        "ascending"
        if solid_colors_by_area == sorted(solid_colors_by_area)
        else "descending"
    )
    frame_colors = {obj["color"] for obj in frames}
    solid_colors = {obj["color"] for obj in solids}
    return {
        "grid_h": int(info["height"]),
        "grid_w": int(info["width"]),
        "solid_style": style,
        "solid_rank_order": "ascending" if solids_by_reading == solids_by_area else "descending",
        "frame_rank_order": "ascending" if frames_by_reading == frames_by_area else "descending",
        "solid_color_order": solid_color_order,
        "palette_kind": (
            "canonical"
            if solid_colors == {2, 5} and frame_colors == {7, 8}
            else "varied"
        ),
    }


# ---------------------------------------------------------------------------
# Independent-in-module Python mirror and semantic counter-hypotheses
# ---------------------------------------------------------------------------


def _render(
    grid: list[list[int]],
    *,
    frame_key: Callable[[dict[str, Any]], object],
    solid_key: Callable[[dict[str, Any]], object],
    paste_mode: str = "shape",
) -> list[list[int]]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("malformed frame-ranking input: " + "; ".join(info["errors"]))
    frames = sorted(info["frames"], key=frame_key)
    solids = sorted(info["solids"], key=solid_key)
    out = full_grid(len(grid), len(grid[0]), 0)
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]

    for solid, frame in zip(solids, frames):
        sr1, sc1, sr2, sc2 = _bbox(solid["cells"])
        fr1, fc1, fr2, fc2 = _bbox(frame["cells"])
        crop_h, crop_w = sr2 - sr1 + 1, sc2 - sc1 + 1
        interior_h, interior_w = fr2 - fr1 - 1, fc2 - fc1 - 1
        top = fr1 + 1 + (interior_h - crop_h) // 2
        left = fc1 + 1 + (interior_w - crop_w) // 2

        if paste_mode == "bbox_fill":
            source_cells = [
                (r, c)
                for r in range(sr1, sr2 + 1)
                for c in range(sc1, sc2 + 1)
            ]
        else:
            source_cells = solid["cells"]
        for r, c in source_cells:
            rr, cc = top + r - sr1, left + c - sc1
            if paste_mode == "clip_interior" and not (fr1 < rr < fr2 and fc1 < cc < fc2):
                continue
            out[rr][cc] = solid["color"]
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python audit mirror; the selected Racket program remains authority."""
    return _render(
        grid,
        frame_key=_frame_interior_area,
        solid_key=lambda obj: len(obj["cells"]),
    )


def _solid_reading_order_rival(grid):
    return _render(grid, frame_key=_frame_interior_area, solid_key=_reading_key)


def _solid_color_order_rival(grid):
    return _render(grid, frame_key=_frame_interior_area, solid_key=lambda obj: obj["color"])


def _frame_reading_order_rival(grid):
    return _render(grid, frame_key=_reading_key, solid_key=lambda obj: len(obj["cells"]))


def _clip_to_interior_rival(grid):
    return _render(
        grid,
        frame_key=_frame_interior_area,
        solid_key=lambda obj: len(obj["cells"]),
        paste_mode="clip_interior",
    )


def _solid_bbox_fill_rival(grid):
    return _render(
        grid,
        frame_key=_frame_interior_area,
        solid_key=lambda obj: len(obj["cells"]),
        paste_mode="bbox_fill",
    )


SEMANTIC_RIVALS = {
    "solid_reading_order": _solid_reading_order_rival,
    "solid_color_order": _solid_color_order_rival,
    "frame_reading_order": _frame_reading_order_rival,
    "clip_to_frame_interior": _clip_to_interior_rival,
    "fill_solid_bounding_box": _solid_bbox_fill_rival,
}


def _rival_differs(name: str, grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "crossed_solid_reading_order": lambda grid: _rival_differs("solid_reading_order", grid),
    "crossed_solid_color_order": lambda grid: _rival_differs("solid_color_order", grid),
    "crossed_frame_reading_order": lambda grid: _rival_differs("frame_reading_order", grid),
    "border_overwrite": lambda grid: _rival_differs("clip_to_frame_interior", grid),
    "irregular_solids": lambda grid: _rival_differs("fill_solid_bounding_box", grid),
}

WITNESS_RIVALS = {
    "crossed_solid_reading_order": ["solid_reading_order"],
    "crossed_solid_color_order": ["solid_color_order"],
    "crossed_frame_reading_order": ["frame_reading_order"],
    "border_overwrite": ["clip_to_frame_interior"],
    "irregular_solids": ["fill_solid_bounding_box"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These two wrong rules happen to reproduce every public train/test pair.
CANONICAL_SHORTCUTS = {
    "solid_reading_order": SEMANTIC_RIVALS["solid_reading_order"],
    "solid_color_order": SEMANTIC_RIVALS["solid_color_order"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require correct examples and explicit refutation of every named rival."""
    reasons: list[str] = []
    episodes = [*demos, query]
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(f"{role} input malformed: {findings[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the rank-and-center rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"demos do not falsify shortcut {name!r}")
    return reasons
