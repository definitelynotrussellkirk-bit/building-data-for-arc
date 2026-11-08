"""Generator for ARC task 4729a9750abc — select, transform, and pack.

Each maroon rectangular frame carries two keys.  The key immediately above the
frame chooses the smallest (2) or largest (3) interior component.  The key
immediately left chooses identity (3), clockwise rotation (4), left-right flip
(5), or 180-degree rotation (6).  Selected components are cropped, transformed,
and packed from left to right with one blank column between them and vertical
centering.

The generator intentionally makes every ordinary scene expose both rank keys
and at least one shape-changing transform.  A deterministic three-of-four
frame-count schedule makes every four-pair lesson and every query rotation
distinguish the complete frame-order rule from a tempting two-frame shortcut.
Only four exact, observable structural axes are public.
"""
from __future__ import annotations

from collections import deque
import hashlib
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4729a9750abc"
TASK_ID = GENERATOR_ID
RULE_HASH = "12e5396a1c4e"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "3.0.2"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Two or three side-by-side hollow color-9 frames each contain one to three "
    "same-color 4-connected components with distinct sizes.  A 2/3 key above "
    "each frame selects its smallest/largest component; a 3/4/5/6 key on the "
    "left applies identity/clockwise/left-right/180-degree transformation.  "
    "Crop each selected component and horizontally pack the transformed pieces "
    "in frame order with one blank column and vertical centering."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly two or three equal-sized hollow color-9 rectangular frames",
    "each frame has exactly one selection key above it and one transform key left of it",
    "interior components are same-color 4-connected objects with strictly distinct sizes",
    "ordinary generated frames share the declared component count",
]

AXES = {
    "n_frames": {
        "type": "int",
        "default": "period-4 schedule with three 3-frame scenes and one 2-frame scene",
        "valid": "2..3",
    },
    "frame_h": {
        "type": "int",
        "default": "weighted choice favoring canonical 8",
        "valid": "8..9",
    },
    "frame_w": {
        "type": "int",
        "default": "weighted choice favoring canonical 7",
        "valid": "7..8",
    },
    "n_components": {
        "type": "int",
        "default": "weighted choice favoring 2",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Connected, asymmetric shapes.  Their sizes encode an unambiguous rank.
_SHAPES = {
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 1), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    ),
}
_COMPONENT_COLORS = (1, 7, 8)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} is ragged")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors
    return errors


def _components(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
    *,
    background: int = 0,
    only_color: int | None = None,
) -> list[dict[str, Any]]:
    """Row-major same-color four-connected components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if (
                (r, c) in seen
                or color == background
                or (only_color is not None and color != only_color)
            ):
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _frame_bbox(component: dict[str, Any]) -> tuple[int, int, int, int] | None:
    r1, c1, r2, c2 = _bbox(component["cells"])
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return (r1, c1, r2, c2) if set(component["cells"]) == border else None


def _analyse(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "frames": []}

    h, w = len(grid), len(grid[0])
    nine_components = _components(grid, only_color=9)
    boxes: list[tuple[int, int, int, int]] = []
    for component in nine_components:
        box = _frame_bbox(component)
        if box is None:
            errors.append("color-9 cells outside exact hollow rectangular frames")
        else:
            boxes.append(box)
    boxes.sort(key=lambda box: (box[0], box[1]))
    if len(boxes) not in (2, 3):
        errors.append(f"expected exactly 2 or 3 color-9 frames, found {len(boxes)}")

    frame_infos: list[dict[str, Any]] = []
    allowed_nonzero: set[tuple[int, int]] = set()
    if boxes:
        heights = {r2 - r1 + 1 for r1, _, r2, _ in boxes}
        widths = {c2 - c1 + 1 for _, c1, _, c2 in boxes}
        tops = {r1 for r1, _, _, _ in boxes}
        bottoms = {r2 for _, _, r2, _ in boxes}
        if len(heights) != 1 or not heights <= {8, 9}:
            errors.append("frames must share a height in 8..9")
        if len(widths) != 1 or not widths <= {7, 8}:
            errors.append("frames must share a width in 7..8")
        if len(tops) != 1 or len(bottoms) != 1:
            errors.append("frames must be top-aligned and bottom-aligned")
        for left, right in zip(boxes, boxes[1:]):
            if left[3] >= right[1] - 1:
                errors.append("frames must be side-by-side with a blank/key gap")

    for frame_index, (r1, c1, r2, c2) in enumerate(boxes):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                allowed_nonzero.add((r, c))

        selection_positions: list[tuple[int, int, int]] = []
        if r1 <= 0:
            errors.append(f"frame {frame_index} has no row for a selection key")
        else:
            for c in range(c1, c2 + 1):
                if grid[r1 - 1][c] != 0:
                    selection_positions.append((r1 - 1, c, grid[r1 - 1][c]))
        if len(selection_positions) != 1 or selection_positions[0][2] not in (2, 3):
            errors.append(
                f"frame {frame_index} needs exactly one selection key (2 or 3) above it"
            )
            selection = None
        else:
            sr, sc, selection = selection_positions[0]
            allowed_nonzero.add((sr, sc))

        transform_positions: list[tuple[int, int, int]] = []
        if c1 <= 0:
            errors.append(f"frame {frame_index} has no column for a transform key")
        else:
            for r in range(r1, r2 + 1):
                if grid[r][c1 - 1] != 0:
                    transform_positions.append((r, c1 - 1, grid[r][c1 - 1]))
        if len(transform_positions) != 1 or transform_positions[0][2] not in (3, 4, 5, 6):
            errors.append(
                f"frame {frame_index} needs exactly one transform key (3, 4, 5, or 6) left of it"
            )
            transform = None
        else:
            tr, tc, transform = transform_positions[0]
            allowed_nonzero.add((tr, tc))

        interior = [list(row[c1 + 1 : c2]) for row in grid[r1 + 1 : r2]]
        interior_components = _components(interior)
        if not (1 <= len(interior_components) <= 3):
            errors.append(
                f"frame {frame_index} interior must contain 1..3 components, found {len(interior_components)}"
            )
        sizes = [len(component["cells"]) for component in interior_components]
        if len(sizes) != len(set(sizes)):
            errors.append(f"frame {frame_index} component sizes must be strictly distinct sizes")
        for component in interior_components:
            if component["color"] in (0, 9):
                errors.append(f"frame {frame_index} has an illegal interior color")
        frame_infos.append(
            {
                "bbox": (r1, c1, r2, c2),
                "selection": selection,
                "transform": transform,
                "components": interior_components,
            }
        )

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0 and (r, c) not in allowed_nonzero:
                errors.append(f"nonzero cell outside frames and their key slots at ({r}, {c})")
                # One coordinate is enough to diagnose arbitrary noise.
                break
        if errors and errors[-1].startswith("nonzero cell outside"):
            break

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "frames": frame_infos,
    }


def _crop_component(component: dict[str, Any]) -> list[list[int]]:
    color = int(component["color"])
    r1, c1, r2, c2 = _bbox(component["cells"])
    out = full_grid(r2 - r1 + 1, c2 - c1 + 1, 0)
    for r, c in component["cells"]:
        out[r - r1][c - c1] = color
    return out


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform(piece: list[list[int]], key: int) -> list[list[int]]:
    if key == 4:
        return _rotate_cw(piece)
    if key == 5:
        return [row[::-1] for row in piece]
    if key == 6:
        return [row[::-1] for row in piece[::-1]]
    return [row[:] for row in piece]


def _solve(
    grid: list[list[int]],
    *,
    frame_limit: int | None = None,
    forced_selection: int | None = None,
    apply_transform: bool = True,
) -> list[list[int]]:
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError(f"invalid frame puzzle: {analysis['errors'][0]}")
    infos = analysis["frames"]
    if frame_limit is not None:
        infos = infos[:frame_limit]
    pieces: list[list[list[int]]] = []
    for info in infos:
        ordered = sorted(info["components"], key=lambda obj: len(obj["cells"]))
        selection = info["selection"] if forced_selection is None else forced_selection
        chosen = ordered[0] if selection == 2 else ordered[-1]
        piece = _crop_component(chosen)
        if apply_transform:
            piece = _transform(piece, int(info["transform"]))
        pieces.append(piece)

    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            out[top + r][left : left + len(row)] = row
        left += len(piece[0]) + 1
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror; the packet's canonical Racket rule is authoritative."""
    return _solve(grid)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis(es): {unknown}")
    bounds = {
        "n_frames": (2, 3),
        "frame_h": (8, 9),
        "frame_w": (7, 8),
        "n_components": (2, 3),
    }
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool/coercible)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _scheduled_n_frames(seed: int, sample_index: int) -> int:
    """Use three frames in three of every four consecutive sample indices.

    Any four-pair lesson therefore contains three full-rule witnesses.  Removing
    any one pair as the query still leaves at least two three-frame demos, so the
    first-two-frames shortcut cannot survive a query rotation.  The seed shifts
    the phase without weakening that sliding-window guarantee.
    """
    seed_bytes = f"{TASK_ID}:frame-schedule:{int(seed)}".encode("ascii")
    phase = hashlib.sha256(seed_bytes).digest()[0] % 4
    return 2 if (int(sample_index) + phase) % 4 == 2 else 3


def _weighted_axis(ctx, name: str, canonical: int, alternate: int) -> int:
    # Duplicates intentionally weight canonical geometry while retaining exact
    # override support and ordinary support for both declared values.
    return int(ctx.draw_choice(name, (canonical, canonical, canonical, alternate)))


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _mirror_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    width = max(c for _, c in cells) + 1
    return _normalize_shape((r, width - 1 - c) for r, c in cells)


def _place_shape(
    grid: list[list[int]],
    *,
    frame_r: int,
    frame_c: int,
    slot: int,
    shape: tuple[tuple[int, int], ...],
    color: int,
    interior_h: int,
    interior_w: int,
) -> None:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if slot == 0:  # smallest: upper-left
        base_r, base_c = 0, 0
    elif slot == 1:  # middle: upper-right
        base_r, base_c = 0, interior_w - sw
    else:  # largest: lower area, offset right when possible
        base_r = interior_h - sh
        base_c = max(0, interior_w - sw)
    for dr, dc in shape:
        grid[frame_r + 1 + base_r + dr][frame_c + 1 + base_c + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic teaching input with exact observable overrides."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_n_frames = _scheduled_n_frames(seed, sample_index)
    frame_options = (2, 3) if "n_frames" in overrides else (scheduled_n_frames,)
    n_frames = int(ctx.draw_choice("n_frames", frame_options))
    frame_h = _weighted_axis(ctx, "frame_h", 8, 9)
    frame_w = _weighted_axis(ctx, "frame_w", 7, 8)
    n_components = _weighted_axis(ctx, "n_components", 2, 3)

    height = frame_h + 4
    # Three width-8 frames need a one-column inter-frame key gap to remain
    # within ARC's 30-column ceiling.  Canonical width-7 scenes retain their
    # two-column gaps and exact 12x29 profile.
    frame_gap = 1 if n_frames == 3 and frame_w == 8 else 2
    width = 2 + n_frames * frame_w + (n_frames - 1) * frame_gap + 2
    grid = full_grid(height, width, 0)
    top = 2
    starts = [2 + index * (frame_w + frame_gap) for index in range(n_frames)]
    band_salt = str(difficulty or "default")
    key_rng = ctx.draw_rng(f"keys:{band_salt}")
    shape_rng = ctx.draw_rng(f"shapes:{band_salt}")
    color_rng = ctx.draw_rng(f"colors:{band_salt}")

    selectors = [2 if index % 2 == 0 else 3 for index in range(n_frames)]
    if key_rng.choice((False, True)):
        selectors.reverse()
    transform_patterns = (
        (4, 5, 6),
        (3, 4, 5),
        (6, 3, 4),
        (5, 6, 3),
    )
    pattern = transform_patterns[key_rng.randrange(len(transform_patterns))]
    transforms = list(pattern[:n_frames])

    sizes = (3, 5) if n_components == 2 else (3, 4, 5)
    slots = (0, 2) if n_components == 2 else (0, 1, 2)
    interior_h, interior_w = frame_h - 2, frame_w - 2

    for frame_index, left in enumerate(starts):
        bottom = top + frame_h - 1
        right = left + frame_w - 1
        for c in range(left, right + 1):
            grid[top][c] = 9
            grid[bottom][c] = 9
        for r in range(top, bottom + 1):
            grid[r][left] = 9
            grid[r][right] = 9

        select_col = key_rng.randint(left, right)
        transform_row = key_rng.randint(top, bottom)
        grid[top - 1][select_col] = selectors[frame_index]
        grid[transform_row][left - 1] = transforms[frame_index]

        colors = list(_COMPONENT_COLORS[:n_components])
        color_rng.shuffle(colors)
        for component_index, (size, slot, color) in enumerate(zip(sizes, slots, colors)):
            variants = _SHAPES[size]
            shape = variants[shape_rng.randrange(len(variants))]
            if shape_rng.choice((False, True)):
                shape = _mirror_shape(shape)
            _place_shape(
                grid,
                frame_r=top,
                frame_c=left,
                slot=slot,
                shape=shape,
                color=color,
                interior_h=interior_h,
                interior_w=interior_w,
            )

    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int]:
    """Recover all declared axes from a lawful generated input."""
    analysis = _analyse(grid)
    if analysis["errors"] or not analysis["frames"]:
        return {}
    boxes = [info["bbox"] for info in analysis["frames"]]
    heights = {r2 - r1 + 1 for r1, _, r2, _ in boxes}
    widths = {c2 - c1 + 1 for _, c1, _, c2 in boxes}
    component_counts = {len(info["components"]) for info in analysis["frames"]}
    if len(heights) != 1 or len(widths) != 1 or len(component_counts) != 1:
        return {}
    return {
        "n_frames": len(boxes),
        "frame_h": next(iter(heights)),
        "frame_w": next(iter(widths)),
        "n_components": next(iter(component_counts)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed geometry, missing keys, ties, and hidden outside noise."""
    del difficulty
    analysis = _analyse(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    requested = _meta_overrides(meta)
    observed = observe_overrides(grid)
    for name, value in requested.items():
        if name in AXES and observed.get(name) != value:
            errors.append(f"override {name}={value!r} realized as {observed.get(name)!r}")
    try:
        if rule_mirror(grid) == grid:
            errors.append("scene hides the rule because output equals input")
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the exact canonical canvas/frame profile, without copying labels."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyse(grid)
    if (analysis["height"], analysis["width"]) != (12, 29):
        errors.append("canonical profile canvas is exactly 12x29")
    boxes = [info["bbox"] for info in analysis["frames"]]
    if len(boxes) != 3:
        errors.append("canonical profile contains exactly three frames")
    if any((r2 - r1 + 1, c2 - c1 + 1) != (8, 7) for r1, c1, r2, c2 in boxes):
        errors.append("canonical profile frames are exactly 8x7")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (7, 8, 9):
        errors.append("canonical profile uses 7, 8, or 9 distinct colors")
    return errors


def _rival_first_two_frames(grid: list[list[int]]) -> list[list[int]]:
    return _solve(grid, frame_limit=2)


def _rival_always_smallest(grid: list[list[int]]) -> list[list[int]]:
    return _solve(grid, forced_selection=2)


def _rival_always_largest(grid: list[list[int]]) -> list[list[int]]:
    return _solve(grid, forced_selection=3)


def _rival_ignore_transform(grid: list[list[int]]) -> list[list[int]]:
    return _solve(grid, apply_transform=False)


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    def predicate(grid):
        return not self_check(grid) and rule_mirror(grid) != rival(grid)

    return predicate


SEMANTIC_RIVALS = {
    "first_two_frames_only": _rival_first_two_frames,
    "always_smallest": _rival_always_smallest,
    "always_largest": _rival_always_largest,
    "ignore_transform": _rival_ignore_transform,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "third_frame_matters": _differs_from(_rival_first_two_frames),
    "smallest_key_matters": _differs_from(_rival_always_largest),
    "largest_key_matters": _differs_from(_rival_always_smallest),
    "transform_key_matters": _differs_from(_rival_ignore_transform),
}
WITNESS_RIVALS = {
    "third_frame_matters": ["first_two_frames_only"],
    "smallest_key_matters": ["always_largest"],
    "largest_key_matters": ["always_smallest"],
    "transform_key_matters": ["ignore_transform"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate labels and require demonstrations to eliminate every shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with select-transform-pack rule")
            continue
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with select-transform-pack rule")

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
                reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
