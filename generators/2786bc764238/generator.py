"""Generator for ``Largest Crop`` (task 2786bc764238).

A zero-background grid contains two to five separated nonzero 4-connected
components.  Exactly one component is largest by cell count.  The canonical
Racket rule selects that component and returns the exact input subgrid spanning
its bounding box.

Version 3.0.0 replaces the former axis-dead random-walk generator.  The old
source ignored five declared overrides, allowed placement fall-through, rejected
canonical tied distractor sizes in its prose, and had no semantic contract.
This version anchors every canonical profile, exposes only observable axes,
constructs named shortcut counterexamples, and structurally validates the
lesson before returning it.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2786bc764238"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "92d8b810afaf"

SUMMARY = (
    "A zero-background 9-12 by 12-15 grid contains exactly two to five "
    "spatially separated nonzero 4-connected components. One component is "
    "uniquely largest by cell count; smaller components may tie with each "
    "other, as they do in the canonical examples. Select the largest "
    "component and return the exact input subgrid spanning its bounding box, "
    "preserving internal zeros and every target color. Distractor bounding "
    "boxes stay outside the selected box, so the crop contains the selected "
    "component rather than unrelated context."
)

INVARIANTS = [
    "zero background and integer ARC colors 0..9",
    "exactly 2..5 nonzero 4-connected components separated by an 8-neighbor moat",
    "one component is uniquely largest by cell count; distractors may tie",
    "every distractor bbox is disjoint from the largest-component bbox",
    "the largest bbox is a strict subrectangle of the input",
    "ordinary schedules include canonical profiles and shortcut-rebutting scenes",
]

# (height, width, palette size including background), in canonical pair order.
CANONICAL_PROFILES = (
    (10, 12, 4),
    (11, 13, 4),
    (9, 14, 4),
    (12, 15, 4),
)
CANONICAL_LARGEST_SIZES = (7, 6, 8, 11)
CANONICAL_COMPONENT_SIZES = (
    (7, 5, 5),
    (6, 5, 1, 1, 1),
    (8, 5, 5),
    (11, 6, 4),
)

EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 0.12
SCHEDULE_PROFILES = tuple(range(EXAMPLES_NEEDED + 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-scaled schedule",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-scaled schedule",
        "valid": "12..15",
    },
    "component_count": {
        "type": "int",
        "default": "scheduled 2..5; canonical anchors use 3 or 5",
        "valid": "2..5",
    },
    "largest_size": {
        "type": "int",
        "default": "scheduled canonical/teaching size",
        "valid": "6|7|8|11",
    },
}

_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Canonical target morphologies, normalized to their own bbox.
_CANONICAL_TARGETS = {
    6: {(r, c) for r in range(3) for c in range(2)},
    7: {
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2),
                (2, 1),
    },
    8: {
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    },
    11: {
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2),
        (2, 0),         (2, 2),
        (3, 0), (3, 1), (3, 2),
    },
}

_FILLED_TARGETS = {
    6: {(r, c) for r in range(2) for c in range(3)},
    8: {(r, c) for r in range(2) for c in range(4)},
}

# Slot-1 witnesses: one smaller object has greater bbox area/height, and the
# other has greater width, than a compact target.  These refute cell-count vs.
# bbox-size/width/height shortcuts on the same generated lesson.
_BBOX_DECOYS = {
    6: (
        {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)},       # size 5, 4x2
        {(0, 0), (0, 1), (0, 2), (0, 3)},               # size 4, 1x4
    ),
    7: (
        {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)},
        {(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)},
    ),
    8: (
        {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (2, 2)},
        {(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0)},
    ),
    11: (
        {
            (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
            (4, 1), (4, 2), (3, 2), (2, 2), (1, 2),
        },
        {
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 0), (2, 0), (2, 1), (2, 2),
        },
    ),
}


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    """Reject coercible public scalars before they reach ``gen_ctx``."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(name for name in overrides if name not in AXES)
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))
    integer_bounds = {
        "grid_h": (9, 12),
        "grid_w": (12, 15),
        "component_count": (2, 5),
    }
    for name, (low, high) in integer_bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"{name} must be in {low}..{high}")
    value = overrides.get("largest_size")
    if value is not None:
        if type(value) is not int:
            raise TypeError("largest_size must be an integer (not bool)")
        if value not in (6, 7, 8, 11):
            raise ValueError("largest_size must be one of 6, 7, 8, 11")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the seven-slot lesson schedule to the semantic gate."""
    _validate_call(seed, sample_index, difficulty, {})
    return sample_index % (EXAMPLES_NEEDED + 1)


def _normalize_grid(grid: Any) -> list[list[int]]:
    """Return a list-of-lists view, accepting canonical digit strings."""
    if not isinstance(grid, (list, tuple)):
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


def _components(grid: Any) -> list[dict[str, Any]]:
    """Extract nonzero 4-connected components, ignoring color boundaries."""
    g = _normalize_grid(grid)
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        return []
    h, w = len(g), len(g[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and g[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            colors = [g[rr][cc] for rr, cc in cells]
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "colors": tuple(colors),
                    "palette": frozenset(colors),
                }
            )
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(component: dict[str, Any]) -> int:
    r1, c1, r2, c2 = component["bbox"]
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _rectangles_intersect(left, right) -> bool:
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    return not (lr2 < rr1 or rr2 < lr1 or lc2 < rc1 or rc2 < lc1)


def _crop(grid: Any, component: dict[str, Any]) -> list[list[int]]:
    g = _normalize_grid(grid)
    r1, c1, r2, c2 = component["bbox"]
    return [row[c1 : c2 + 1] for row in g[r1 : r2 + 1]]


def _largest_component(grid: Any) -> dict[str, Any] | None:
    components = _components(grid)
    if not components:
        return None
    ordered = sorted(
        components,
        key=lambda component: (
            -component["size"],
            component["bbox"][0],
            component["bbox"][1],
        ),
    )
    return ordered[0]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror for focused evidence; Racket remains output authority."""
    largest = _largest_component(grid)
    if largest is None:
        raise ValueError("no nonzero component")
    return _crop(grid, largest)


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _transform_shape(
    cells: Iterable[tuple[int, int]], transform_code: int
) -> frozenset[tuple[int, int]]:
    transformed = set(cells)
    if transform_code >= 4:
        transformed = {(r, -c) for r, c in transformed}
    for _ in range(transform_code % 4):
        transformed = {(c, -r) for r, c in transformed}
    return _normalize_shape(transformed)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _random_shape(size: int, rng, *, max_h: int = 5, max_w: int = 5):
    """Grow a deterministic compact 4-connected polyomino."""
    for _attempt in range(120):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _NEIGHBORS4
                if (r + dr, c + dc) not in cells
            }
            candidates = []
            for cell in frontier:
                candidate = _normalize_shape(cells | {cell})
                bh, bw = _shape_dims(candidate)
                if bh <= max_h and bw <= max_w:
                    candidates.append(cell)
            if not candidates:
                break
            cells.add(rng.choice(sorted(candidates)))
        if len(cells) == size:
            return _normalize_shape(cells)
    raise RuntimeError(f"could not grow a compact {size}-cell shape")


def _absolute(shape, top: int, left: int) -> frozenset[tuple[int, int]]:
    return frozenset((top + r, left + c) for r, c in shape)


def _halo(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    result = set(cells)
    for r, c in cells:
        for dr, dc in _NEIGHBORS8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                result.add((nr, nc))
    return result


def _placement_candidates(shape, h: int, w: int):
    sh, sw = _shape_dims(shape)
    return [
        _absolute(shape, top, left)
        for top in range(h - sh + 1)
        for left in range(w - sw + 1)
    ]


def _placement_relation(placements, relation: str) -> bool:
    if relation == "any":
        return True
    target = _bbox(placements[0])
    distractors = [_bbox(cells) for cells in placements[1:]]
    if relation == "top_left":
        return all(target[0] < bb[0] and target[1] < bb[1] for bb in distractors)
    if relation == "bottom_right":
        return all(target[0] > bb[0] and target[1] > bb[1] for bb in distractors)
    raise ValueError(f"unknown placement relation {relation!r}")


def _place_shapes(h: int, w: int, shapes, rng, *, relation: str):
    """Backtrack placements with an 8-neighbor moat and clean target bbox."""
    candidate_lists = [_placement_candidates(shape, h, w) for shape in shapes]
    for candidates in candidate_lists:
        rng.shuffle(candidates)

    if relation == "top_left":
        candidate_lists[0].sort(key=lambda cells: (_bbox(cells)[0], _bbox(cells)[1]))
    elif relation == "bottom_right":
        candidate_lists[0].sort(
            key=lambda cells: (-_bbox(cells)[0], -_bbox(cells)[1])
        )

    for target_cells in candidate_lists[0]:
        target_bbox = _bbox(target_cells)
        placements = [target_cells]
        forbidden = _halo(target_cells, h, w)

        def rec(index: int, current_forbidden: set[tuple[int, int]]):
            if index == len(shapes):
                return list(placements) if _placement_relation(placements, relation) else None
            for cells in candidate_lists[index]:
                if cells & current_forbidden:
                    continue
                if _rectangles_intersect(_bbox(cells), target_bbox):
                    continue
                placements.append(cells)
                result = rec(index + 1, current_forbidden | _halo(cells, h, w))
                if result is not None:
                    return result
                placements.pop()
            return None

        result = rec(1, forbidden)
        if result is not None:
            return result
    raise RuntimeError(
        f"could not place {len(shapes)} components in {h}x{w} with relation={relation}"
    )


def _draw_scheduled_int(ctx, overrides, label: str, scheduled: int, lo: int, hi: int):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, overrides, label: str, scheduled: int, options):
    if overrides.get(label) is not None:
        return int(ctx.draw_choice(label, tuple(options)))
    return int(ctx.draw_choice(label, (scheduled,)))


def _ordinary_dimensions(slot: int, episode: int, band: str) -> tuple[int, int]:
    if slot == 0:
        profile = CANONICAL_PROFILES[episode % len(CANONICAL_PROFILES)]
        return profile[0], profile[1]
    ranges = {
        "easy": ((9, 10), (12, 13)),
        "medium": ((10, 11), (13, 14)),
        "hard": ((11, 12), (14, 15)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[band]
    return h_lo + ((episode + slot) % (h_hi - h_lo + 1)), w_lo + (
        (episode * 2 + slot) % (w_hi - w_lo + 1)
    )


def _ordinary_component_count(slot: int, episode: int) -> int:
    if slot == 0:
        return len(CANONICAL_COMPONENT_SIZES[episode % len(CANONICAL_COMPONENT_SIZES)])
    return (3, 3, 3, 3, 2, 4, 5)[slot]


def _ordinary_largest_size(slot: int, episode: int) -> int:
    if slot == 0:
        return CANONICAL_LARGEST_SIZES[episode % len(CANONICAL_LARGEST_SIZES)]
    return (6, 6, 7, 8, 11, 7, 8)[slot]


def _component_sizes(
    largest_size: int,
    component_count: int,
    *,
    slot: int,
    episode: int,
) -> list[int]:
    if slot == 0:
        profile_index = episode % len(CANONICAL_COMPONENT_SIZES)
        canonical = CANONICAL_COMPONENT_SIZES[profile_index]
        if len(canonical) == component_count and canonical[0] == largest_size:
            return list(canonical)
    if slot == 1 and component_count >= 3:
        sizes = [largest_size, largest_size - 1, largest_size - 2]
        while len(sizes) < component_count:
            sizes.append(max(2, largest_size - len(sizes) - 1))
        return sizes
    if component_count == 5:
        base = [max(2, largest_size - 2), max(2, largest_size - 3), 2, 1]
        distractors = base[:4]
    else:
        available = list(range(max(1, largest_size - 1), 0, -1))
        if component_count - 1 > len(available):
            raise ValueError(
                f"largest_size={largest_size} cannot support {component_count} components"
            )
        # Include tied distractors on alternating episodes because canonical does.
        if component_count >= 3 and episode % 2 == 0:
            distractors = [available[0], available[0]]
            distractors.extend(available[1 : component_count - 2])
        else:
            distractors = available[: component_count - 1]
    return [largest_size, *distractors[: component_count - 1]]


def _target_shape(largest_size: int, slot: int, rng):
    if slot == 1:
        if largest_size in _FILLED_TARGETS:
            return _normalize_shape(_FILLED_TARGETS[largest_size])
        return _normalize_shape(_CANONICAL_TARGETS[largest_size])
    if slot == 4 and largest_size in _FILLED_TARGETS:
        return _transform_shape(_FILLED_TARGETS[largest_size], rng.randrange(8))
    if slot == 0:
        return _transform_shape(_CANONICAL_TARGETS[largest_size], rng.randrange(8))
    if slot in (3, 5, 6):
        return _random_shape(largest_size, rng, max_h=5, max_w=5)
    bases = [_CANONICAL_TARGETS[largest_size]]
    if largest_size in _FILLED_TARGETS:
        bases.append(_FILLED_TARGETS[largest_size])
    return _transform_shape(rng.choice(bases), rng.randrange(8))


def _distractor_shapes(sizes: list[int], largest_size: int, slot: int, rng):
    if slot == 1 and len(sizes) >= 2:
        decoys = list(_BBOX_DECOYS[largest_size])
        shapes = [_normalize_shape(decoys[0]), _normalize_shape(decoys[1])]
        for size in sizes[2:]:
            shapes.append(_random_shape(size, rng))
        return shapes
    return [_random_shape(size, rng) for size in sizes]


def _component_colors(component_count: int, slot: int, rng) -> list[int]:
    colors = rng.sample(list(range(1, 10)), component_count)
    if slot == 2 and component_count >= 2:
        colors[1] = colors[0]
    if slot == 4:
        low = rng.choice((1, 2, 3))
        others = rng.sample([color for color in range(5, 10)], component_count - 1)
        colors = [low, *others]
    elif slot == 5:
        high = rng.choice((7, 8, 9))
        others = rng.sample([color for color in range(1, 6)], component_count - 1)
        colors = [high, *others]
    return colors


def _paint_components(
    h: int,
    w: int,
    placements,
    colors: list[int],
    *,
    multicolor_target: bool,
    rng,
):
    grid = full_grid(h, w, 0)
    for index, (cells, color) in enumerate(zip(placements, colors)):
        ordered = sorted(cells)
        for r, c in ordered:
            grid[r][c] = color
        if index == 0 and multicolor_target and len(ordered) >= 3:
            alternate = next(value for value in range(1, 10) if value not in colors)
            for r, c in ordered[::3]:
                grid[r][c] = alternate
            # Keep the component connected regardless of the color pattern;
            # connectivity is defined on nonzero cells, matching the Racket mask.
            if all(grid[r][c] == alternate for r, c in ordered):
                grid[ordered[-1][0]][ordered[-1][1]] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic fresh input; canonical Racket owns output."""
    _validate_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = "medium" if difficulty is None else difficulty
    slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
    episode = int(sample_index) // (EXAMPLES_NEEDED + 1)

    scheduled_h, scheduled_w = _ordinary_dimensions(slot, episode, band)
    h = _draw_scheduled_int(ctx, overrides, "grid_h", scheduled_h, 9, 12)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", scheduled_w, 12, 15)
    component_count = _draw_scheduled_int(
        ctx,
        overrides,
        "component_count",
        _ordinary_component_count(slot, episode),
        2,
        5,
    )
    largest_size = _draw_scheduled_choice(
        ctx,
        overrides,
        "largest_size",
        _ordinary_largest_size(slot, episode),
        (6, 7, 8, 11),
    )

    rng = ctx.draw_rng(f"layout_{band}")
    sizes = _component_sizes(
        largest_size,
        component_count,
        slot=slot,
        episode=episode,
    )
    explicit_override = any(
        name in overrides and overrides[name] is not None for name in AXES
    )
    relation = (
        "any"
        if explicit_override
        else "top_left" if slot == 4
        else "bottom_right" if slot == 5
        else "any"
    )

    last_error: Exception | None = None
    for _attempt in range(40):
        try:
            target = _target_shape(largest_size, slot, rng)
            distractors = _distractor_shapes(sizes[1:], largest_size, slot, rng)
            placements = _place_shapes(
                h,
                w,
                [target, *distractors],
                rng,
                relation=relation,
            )
            colors = _component_colors(component_count, slot, rng)
            if slot == 0 and component_count == 5:
                # Canonical train[1] has two normal components plus three
                # isolated cells sharing a third foreground color.
                palette = rng.sample(list(range(1, 10)), 3)
                colors = [palette[0], palette[1], palette[2], palette[2], palette[2]]
            grid = _paint_components(
                h,
                w,
                placements,
                colors,
                multicolor_target=(slot in (3, 6)),
                rng=rng,
            )
            errors = self_check(grid, difficulty=difficulty)
            if errors:
                raise RuntimeError("; ".join(errors))
            observed = observe_overrides(grid)
            for axis, requested in ctx.recorded_draws().items():
                if axis in AXES and observed.get(axis) != requested:
                    raise RuntimeError(
                        f"axis realization mismatch for {axis}: "
                        f"requested {requested}, observed {observed.get(axis)}"
                    )
            return [row[:] for row in grid]
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"failed to construct a valid scene after retries: {last_error}")


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact declared semantic axis from the returned grid."""
    g = _normalize_grid(grid)
    components = _components(g)
    return {
        "grid_h": len(g),
        "grid_w": len(g[0]) if g else 0,
        "component_count": len(components),
        "largest_size": max((component["size"] for component in components), default=0),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding largest-crop scenes."""
    del difficulty, meta
    g = _normalize_grid(grid)
    if not g or not g[0]:
        return ["grid must be a non-empty rectangle"]
    width = len(g[0])
    if any(len(row) != width for row in g):
        return ["grid must be rectangular"]
    height = len(g)
    errors: list[str] = []
    if not (9 <= height <= 12 and 12 <= width <= 15):
        errors.append(
            f"grid dimensions {height}x{width} outside supported 9..12 by 12..15"
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in g
        for value in row
    ):
        errors.append("cells must be integer ARC colors in 0..9")
        return errors
    if all(value != 0 for row in g for value in row):
        errors.append("zero background is absent")

    components = _components(g)
    if not 2 <= len(components) <= 5:
        errors.append(f"expected 2..5 nonzero components, found {len(components)}")
        return errors
    sizes = [component["size"] for component in components]
    largest_size = max(sizes)
    if sizes.count(largest_size) != 1:
        errors.append(f"largest component is not unique: sizes={sorted(sizes)}")
        return errors
    if largest_size not in (6, 7, 8, 11):
        errors.append(f"largest component size {largest_size} is outside 6|7|8|11")

    largest = max(components, key=lambda component: component["size"])
    r1, c1, r2, c2 = largest["bbox"]
    if (r1, c1, r2, c2) == (0, 0, height - 1, width - 1):
        errors.append("largest bbox equals the whole input; crop would be identity")
    for component in components:
        if component is largest:
            continue
        if _rectangles_intersect(component["bbox"], largest["bbox"]):
            errors.append("a distractor bbox intersects the largest-component bbox")
    if not _crop(g, largest) or _crop(g, largest) == g:
        errors.append("largest-component crop is empty or identical to the input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the four linked canonical size/palette profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    g = _normalize_grid(grid)
    components = _components(g)
    palette_size = len({value for row in g for value in row})
    profile = (len(g), len(g[0]), palette_size)
    if profile not in CANONICAL_PROFILES:
        return [f"profile {profile} is outside the four canonical profiles"]
    profile_index = CANONICAL_PROFILES.index(profile)
    sizes = tuple(sorted((component["size"] for component in components), reverse=True))
    if sizes != tuple(sorted(CANONICAL_COMPONENT_SIZES[profile_index], reverse=True)):
        return [
            f"component sizes {sizes} do not match canonical profile "
            f"{CANONICAL_COMPONENT_SIZES[profile_index]}"
        ]
    if any(len(component["palette"]) != 1 for component in components):
        return ["canonical components are monochromatic"]
    return []


def _reading_rank(grid: Any) -> tuple[int, int] | None:
    components = _components(grid)
    largest = _largest_component(grid)
    if largest is None:
        return None
    ordered = sorted(components, key=lambda component: (component["bbox"][0], component["bbox"][1]))
    return ordered.index(largest), len(ordered)


def _largest_first(grid: Any) -> bool:
    rank = _reading_rank(grid)
    return bool(rank and rank[0] == 0)


def _largest_last(grid: Any) -> bool:
    rank = _reading_rank(grid)
    return bool(rank and rank[0] == rank[1] - 1)


def _same_component(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left["cells"] == right["cells"]


def _largest_color(grid: Any) -> int | None:
    largest = _largest_component(grid)
    if largest is None:
        return None
    counts: dict[int, int] = {}
    for color in largest["colors"]:
        counts[color] = counts.get(color, 0) + 1
    return max(counts, key=lambda color: (counts[color], -color))


def _largest_low_color(grid: Any) -> bool:
    largest = _largest_component(grid)
    if largest is None or len(largest["palette"]) != 1:
        return False
    target = next(iter(largest["palette"]))
    others = {
        color
        for component in _components(grid)
        if not _same_component(component, largest)
        for color in component["palette"]
    }
    return bool(others and target < min(others))


def _largest_high_color(grid: Any) -> bool:
    largest = _largest_component(grid)
    if largest is None or len(largest["palette"]) != 1:
        return False
    target = next(iter(largest["palette"]))
    others = {
        color
        for component in _components(grid)
        if not _same_component(component, largest)
        for color in component["palette"]
    }
    return bool(others and target > max(others))


def _target_multicolor(grid: Any) -> bool:
    largest = _largest_component(grid)
    return bool(largest and len(largest["palette"]) >= 2)


def _target_color_repeated(grid: Any) -> bool:
    largest = _largest_component(grid)
    if largest is None:
        return False
    return any(
        not _same_component(component, largest)
        and bool(component["palette"] & largest["palette"])
        for component in _components(grid)
    )


def _bbox_decoy(grid: Any) -> bool:
    largest = _largest_component(grid)
    if largest is None:
        return False
    lr1, lc1, lr2, lc2 = largest["bbox"]
    lh, lw = lr2 - lr1 + 1, lc2 - lc1 + 1
    return any(
        component["size"] < largest["size"]
        and (
            _bbox_area(component) > _bbox_area(largest)
            or component["bbox"][2] - component["bbox"][0] + 1 > lh
            or component["bbox"][3] - component["bbox"][1] + 1 > lw
        )
        for component in _components(grid)
        if not _same_component(component, largest)
    )


def _filled_target_bbox(grid: Any) -> bool:
    largest = _largest_component(grid)
    return bool(largest and all(value != 0 for row in _crop(grid, largest) for value in row))


def _target_bbox_has_zero(grid: Any) -> bool:
    largest = _largest_component(grid)
    return bool(largest and any(value == 0 for row in _crop(grid, largest) for value in row))


def _non_square_target(grid: Any) -> bool:
    largest = _largest_component(grid)
    if largest is None:
        return False
    r1, c1, r2, c2 = largest["bbox"]
    return (r2 - r1) != (c2 - c1)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "canonical_profile": lambda grid: strict_canonical_like(grid) == [],
    "two_components": lambda grid: len(_components(grid)) == 2,
    "three_components": lambda grid: len(_components(grid)) == 3,
    "four_components": lambda grid: len(_components(grid)) == 4,
    "five_components": lambda grid: len(_components(grid)) == 5,
    "larger_bbox_smaller_cell_decoy": _bbox_decoy,
    "largest_first_in_reading_order": _largest_first,
    "largest_last_in_reading_order": _largest_last,
    "largest_has_lowest_color": _largest_low_color,
    "largest_has_highest_color": _largest_high_color,
    "target_color_repeated_in_distractor": _target_color_repeated,
    "multicolor_target_preserved": _target_multicolor,
    "filled_target_bbox": _filled_target_bbox,
    "zero_inside_target_bbox": _target_bbox_has_zero,
    "non_square_target_crop": _non_square_target,
}


def _candidate_components(grid: Any) -> dict[str, dict[str, Any]]:
    components = _components(grid)
    if not components:
        return {}

    def mono_color(component):
        return min(component["palette"]) if component["palette"] else -1

    return {
        "smallest_component": min(components, key=lambda component: component["size"]),
        "topmost_component": min(components, key=lambda component: (component["bbox"][0], component["bbox"][1])),
        "bottommost_component": max(components, key=lambda component: (component["bbox"][2], component["bbox"][3])),
        "leftmost_component": min(components, key=lambda component: (component["bbox"][1], component["bbox"][0])),
        "rightmost_component": max(components, key=lambda component: (component["bbox"][3], component["bbox"][2])),
        "lowest_color_component": min(components, key=mono_color),
        "highest_color_component": max(components, key=mono_color),
        "largest_bbox_area": max(components, key=_bbox_area),
        "widest_bbox": max(components, key=lambda component: component["bbox"][3] - component["bbox"][1]),
        "tallest_bbox": max(components, key=lambda component: component["bbox"][2] - component["bbox"][0]),
    }


def _selector_rival(name: str):
    def solve(grid):
        candidates = _candidate_components(grid)
        if name not in candidates:
            raise ValueError("outside largest-crop grammar")
        return _crop(grid, candidates[name])
    return solve


def _rival_monochrome_target(grid):
    largest = _largest_component(grid)
    if largest is None:
        raise ValueError("outside largest-crop grammar")
    crop = _crop(grid, largest)
    color = _largest_color(grid) or 1
    return [[color if value != 0 else 0 for value in row] for row in crop]


def _rival_fixed_color4(grid):
    largest = _largest_component(grid)
    if largest is None:
        raise ValueError("outside largest-crop grammar")
    return [[4 if value != 0 else 0 for value in row] for row in _crop(grid, largest)]


SEMANTIC_RIVALS = {
    name: _selector_rival(name)
    for name in (
        "smallest_component",
        "topmost_component",
        "bottommost_component",
        "leftmost_component",
        "rightmost_component",
        "lowest_color_component",
        "highest_color_component",
        "largest_bbox_area",
        "widest_bbox",
        "tallest_bbox",
    )
}
SEMANTIC_RIVALS.update(
    {
        "monochrome_largest_crop": _rival_monochrome_target,
        "fixed_color4_largest_crop": _rival_fixed_color4,
    }
)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "largest_bbox_area": SEMANTIC_RIVALS["largest_bbox_area"],
    "monochrome_largest_crop": _rival_monochrome_target,
}
WITNESS_RIVALS = {
    "larger_bbox_smaller_cell_decoy": ["largest_bbox_area", "widest_bbox", "tallest_bbox"],
    "largest_first_in_reading_order": ["bottommost_component", "rightmost_component"],
    "largest_last_in_reading_order": ["topmost_component", "leftmost_component"],
    "largest_has_lowest_color": ["highest_color_component"],
    "largest_has_highest_color": ["lowest_color_component"],
    "multicolor_target_preserved": ["monochrome_largest_crop", "fixed_color4_largest_crop"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a materialized lesson when a named wrong rule remains viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"{role} input is outside the teaching grammar: {findings[:2]}")
            continue
        if rule_mirror(pair["input"]) != _normalize_grid(pair["output"]):
            reasons.append(f"{role} output disagrees with largest-by-cell-count crop")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                _normalize_grid(rival(pair["input"])) == _normalize_grid(pair["output"])
                for pair in demos
            )
            if not survives:
                continue
            query_matches = (
                _normalize_grid(rival(query["input"])) == _normalize_grid(query["output"])
            )
            if query_matches:
                reasons.append(f"shortcut {name!r} survives every demo and the query")
            else:
                reasons.append(f"shortcut {name!r} fits every demo but changes the query")
        except Exception as exc:
            reasons.append(f"shortcut {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
