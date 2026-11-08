"""Generator for 902d22dfd388 — crop framed interior and center on canvas.

Find the unique color-7 rectangular outline.  Ignore every cell outside that
frame.  Within the frame, crop the non-zero interior content to its bounding
box.  Remove the frame and paste the crop, preserving its colors and holes,
centered on an otherwise-zero canvas with the original dimensions.

The ordinary lesson schedule deliberately includes two controls that the two
canonical demonstrations do not jointly expose: an off-centre frame (which
refutes frame-relative centering) and non-zero cells outside the frame (which
refute cropping all non-7 cells globally).  A canonical-like anchor also shows
that the crop may already be at its canvas-centred destination; visible motion
is not a precondition of the rule.
"""
from __future__ import annotations

from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "902d22dfd388"
TASK_ID = "902d22dfd388"
VERSION = "3.0.0"
RULE_HASH = "3a6fc1c246e2"

SUMMARY = (
    "Find the unique color-7 rectangular outline. Ignore cells outside it, "
    "crop the non-zero cells in its interior to their bounding box, remove "
    "the frame, and paste that crop centered on a zero canvas of the original "
    "height and width. Centering is relative to the whole canvas, not the "
    "frame interior; internal zero holes and all content colors are preserved."
)

INVARIANTS = [
    "background is 0 and exactly one complete color-7 rectangular outline is present",
    "the frame is at least 5x5 and encloses 3..8 non-zero, non-7 content cells",
    "interior content uses exactly two or three colors and has a proper crop with a zero hole",
    "zero to two non-7 distractor cells may lie outside the frame and are ignored",
    "the authoritative output removes the frame and centers the interior crop on the full canvas",
]

# Every public axis is exactly recoverable from the returned input.  Placement,
# palette identity, and profile role are intentionally private random choices.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "8..14",
    },
    "content_cells": {
        "type": "int",
        "default": "scheduled 4..7",
        "valid": "3..8",
    },
    "content_colors": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "outside_count": {
        "type": "int",
        "default": "scheduled 0..2",
        "valid": "0..2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Three consecutive examples are sufficient and necessary for the scheduled
# four-profile curriculum.  Every cyclic length-three window contains at least
# one profile carrying BOTH decisive controls.
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_PROFILES: tuple[dict[str, object], ...] = (
    {
        "name": "anchor_shifted",
        "content_cells": 4,
        "content_colors": 2,
        "outside_count": 0,
    },
    {
        "name": "both_controls_nw",
        "content_cells": 5,
        "content_colors": 2,
        "outside_count": 1,
    },
    {
        "name": "both_controls_se",
        "content_cells": 6,
        "content_colors": 3,
        "outside_count": 2,
    },
    {
        "name": "anchor_stationary",
        "content_cells": 7,
        "content_colors": 3,
        "outside_count": 0,
    },
)
SCHEDULE_PROFILES = tuple(str(profile["name"]) for profile in _PROFILES)

# Difficulty controls scale only.  It never changes the task semantics.
_DEFAULT_DIMS = {
    None: ((9, 9), (10, 11), (11, 10), (10, 10)),
    "easy": ((9, 9), (8, 10), (10, 8), (9, 10)),
    "medium": ((10, 10), (10, 11), (11, 10), (11, 11)),
    "hard": ((11, 11), (13, 12), (12, 13), (14, 14)),
}

# Proper, 4-connected occupancy templates.  Every template has at least one
# zero inside its bounding box, so cropping (rather than object-list packing)
# remains observable.  All fit a 3x3 box, including the minimum 8x8 scene.
_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    3: ((0, 0), (0, 1), (1, 0)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
    7: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile used by semantic audits."""
    del seed
    if difficulty not in _DEFAULT_DIMS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    return SCHEDULE_PROFILES[(int(sample_index) + offsets[difficulty]) % len(_PROFILES)]


def _profile_for(sample_index: int, difficulty: str | None) -> tuple[int, dict[str, object]]:
    name = schedule_profile(0, sample_index, difficulty)
    for index, profile in enumerate(_PROFILES):
        if profile["name"] == name:
            return index, profile
    raise AssertionError(f"unreachable profile: {name!r}")


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Honor every declared boundary while keeping ordinary profiles scheduled."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transpose(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, r) for r, c in cells)


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    width = 1 + max(c for _, c in cells)
    return _normalize((r, width - 1 - c) for r, c in cells)


def _shape_for(content_cells: int, rng) -> tuple[tuple[int, int], ...]:
    shape = _SHAPES[content_cells]
    if rng.randrange(2):
        shape = _transpose(shape)
    if rng.randrange(2):
        shape = _flip_lr(shape)
    return _normalize(shape)


def _bbox_size(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _frame_position(h: int, w: int, profile_name: str) -> tuple[int, int, int, int]:
    """Return a large frame with a one-cell canonical anchor or a decisive offset."""
    frame_h = h - 2
    frame_w = w - 2
    if profile_name == "both_controls_nw":
        r1, c1 = 0, 0
    elif profile_name == "both_controls_se":
        r1, c1 = h - frame_h, w - frame_w
    else:
        r1, c1 = (h - frame_h) // 2, (w - frame_w) // 2
    return r1, c1, r1 + frame_h - 1, c1 + frame_w - 1


def _paint_frame(grid, frame: tuple[int, int, int, int]) -> None:
    r1, c1, r2, c2 = frame
    for c in range(c1, c2 + 1):
        grid[r1][c] = 7
        grid[r2][c] = 7
    for r in range(r1, r2 + 1):
        grid[r][c1] = 7
        grid[r][c2] = 7


def _shape_origin(
    h: int,
    w: int,
    frame: tuple[int, int, int, int],
    shape_h: int,
    shape_w: int,
    profile_name: str,
) -> tuple[int, int]:
    r1, c1, r2, c2 = frame
    interior_h = r2 - r1 - 1
    interior_w = c2 - c1 - 1
    global_r = (h - shape_h) // 2
    global_c = (w - shape_w) // 2
    frame_r = r1 + 1 + (interior_h - shape_h) // 2
    frame_c = c1 + 1 + (interior_w - shape_w) // 2

    if profile_name in ("both_controls_nw", "both_controls_se"):
        # The content is centered relative to the frame.  Because the frame is
        # offset, this is a direct counterexample to frame-relative centering.
        return frame_r, frame_c
    if profile_name == "anchor_stationary":
        # A lawful no-translation case: the frame disappears, but the crop is
        # already at the canvas-centred destination.
        return global_r, global_c

    # Canonical-style shifted anchor.  Pick an extreme legal placement that is
    # not the global destination, without making visible motion a checker rule.
    min_r, max_r = r1 + 1, r2 - shape_h
    min_c, max_c = c1 + 1, c2 - shape_w
    candidates = ((min_r, min_c), (max_r, max_c), (min_r, max_c), (max_r, min_c))
    for candidate in candidates:
        if candidate != (global_r, global_c):
            return candidate
    return min_r, min_c


def _outside_positions(
    h: int,
    w: int,
    frame: tuple[int, int, int, int],
    profile_name: str,
) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = frame
    outside = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if not (r1 <= r <= r2 and c1 <= c <= c2)
    ]
    if profile_name == "both_controls_nw":
        outside.sort(key=lambda p: (-(p[0] + p[1]), -p[0], -p[1]))
    elif profile_name == "both_controls_se":
        outside.sort(key=lambda p: (p[0] + p[1], p[0], p[1]))
    else:
        outside.sort(key=lambda p: (p[0], p[1]))
    return outside


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; canonical Racket owns the output."""
    if difficulty not in _DEFAULT_DIMS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    profile_index, profile = _profile_for(int(sample_index), difficulty)
    default_h, default_w = _DEFAULT_DIMS[difficulty][profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", default_h, 8, 14)
    w = _draw_profile_int(ctx, overrides, "grid_w", default_w, 8, 14)
    content_cells = _draw_profile_int(
        ctx, overrides, "content_cells", int(profile["content_cells"]), 3, 8
    )
    content_colors = _draw_profile_int(
        ctx, overrides, "content_colors", int(profile["content_colors"]), 2, 3
    )
    outside_count = _draw_profile_int(
        ctx, overrides, "outside_count", int(profile["outside_count"]), 0, 2
    )

    rng = ctx.draw_rng("scene")
    shape = _shape_for(content_cells, rng)
    shape_h, shape_w = _bbox_size(shape)
    profile_name = str(profile["name"])
    frame = _frame_position(h, w, profile_name)
    r1, c1, r2, c2 = frame
    if shape_h > r2 - r1 - 1 or shape_w > c2 - c1 - 1:
        raise ValueError("content shape does not fit frame interior")

    grid = full_grid(h, w, 0)
    _paint_frame(grid, frame)
    top, left = _shape_origin(h, w, frame, shape_h, shape_w, profile_name)

    palette = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], content_colors)
    order = list(shape)
    rng.shuffle(order)
    for index, (dr, dc) in enumerate(order):
        grid[top + dr][left + dc] = palette[index % content_colors]

    outside_palette = [color for color in [1, 2, 3, 4, 5, 6, 8, 9] if color not in palette]
    if not outside_palette:
        outside_palette = palette[:]
    for index, (r, c) in enumerate(_outside_positions(h, w, frame, profile_name)[:outside_count]):
        grid[r][c] = outside_palette[index % len(outside_palette)]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "content_cells": content_cells,
        "content_colors": content_colors,
        "outside_count": outside_count,
    }
    if observed != expected:
        raise AssertionError(f"generated axes not observable: {observed!r} != {expected!r}")
    return [row[:] for row in grid]


def _grid_errors(grid) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a non-empty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return errors
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        },
        key=repr,
    )
    if bad:
        errors.append(f"invalid ARC colors: {bad[:4]}")
    if not 8 <= len(grid) <= 14:
        errors.append(f"height must be 8..14, found {len(grid)}")
    if not 8 <= width <= 14:
        errors.append(f"width must be 8..14, found {width}")
    return errors


def _frame_bboxes(grid) -> list[tuple[int, int, int, int]]:
    """Return connected color-7 components that are exact rectangle outlines."""
    h, w = len(grid), len(grid[0])
    cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    seen: set[tuple[int, int]] = set()
    frames: list[tuple[int, int, int, int]] = []
    for start in sorted(cells):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbour = (r + dr, c + dc)
                if neighbour in cells and neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        r1 = min(r for r, _ in component)
        c1 = min(c for _, c in component)
        r2 = max(r for r, _ in component)
        c2 = max(c for _, c in component)
        outline = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if set(component) == outline:
            frames.append((r1, c1, r2, c2))
    return frames


def _analyze(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    frames = _frame_bboxes(grid)
    if len(frames) != 1:
        return {
            "errors": [f"expected exactly one complete color-7 rectangular outline, found {len(frames)}"]
        }
    frame = frames[0]
    r1, c1, r2, c2 = frame
    errors = []
    frame_h, frame_w = r2 - r1 + 1, c2 - c1 + 1
    if frame_h < 5 or frame_w < 5:
        errors.append(f"frame must be at least 5x5, found {frame_h}x{frame_w}")

    interior_content = [
        (r, c, grid[r][c])
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if grid[r][c] != 0
    ]
    if any(value == 7 for _, _, value in interior_content):
        errors.append("frame interior may not contain color 7")
    content = [(r, c, value) for r, c, value in interior_content if value != 7]
    if not 3 <= len(content) <= 8:
        errors.append(f"interior content must contain 3..8 cells, found {len(content)}")
    color_count = len({value for _, _, value in content})
    if not 2 <= color_count <= 3:
        errors.append(f"interior content must use 2..3 colors, found {color_count}")

    outside = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if not (r1 <= r <= r2 and c1 <= c <= c2) and grid[r][c] != 0
    ]
    if any(value == 7 for _, _, value in outside):
        errors.append("color 7 may appear only on the unique frame outline")
    outside_non7 = [(r, c, value) for r, c, value in outside if value != 7]
    if not 0 <= len(outside_non7) <= 2:
        errors.append(f"outside distractor count must be 0..2, found {len(outside_non7)}")

    crop_bbox = None
    crop = None
    truth = None
    if content:
        br1 = min(r for r, _, _ in content)
        bc1 = min(c for _, c, _ in content)
        br2 = max(r for r, _, _ in content)
        bc2 = max(c for _, c, _ in content)
        crop_bbox = (br1, bc1, br2, bc2)
        crop_h, crop_w = br2 - br1 + 1, bc2 - bc1 + 1
        if crop_h > 4 or crop_w > 4:
            errors.append(f"content crop must fit 4x4, found {crop_h}x{crop_w}")
        occupied = {(r, c) for r, c, _ in content}
        if all((r, c) in occupied for r in range(br1, br2 + 1) for c in range(bc1, bc2 + 1)):
            errors.append("content crop must contain at least one zero hole")
        crop = [row[bc1 : bc2 + 1] for row in grid[br1 : br2 + 1]]
        truth = full_grid(h, w, 0)
        top = (h - crop_h) // 2
        left = (w - crop_w) // 2
        for rr, row in enumerate(crop):
            for cc, value in enumerate(row):
                if value != 0:
                    truth[top + rr][left + cc] = value

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "frame": frame,
        "content": tuple(content),
        "content_colors": frozenset(value for _, _, value in content),
        "outside": tuple(outside_non7),
        "crop_bbox": crop_bbox,
        "crop": crop,
        "truth": truth,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in _DEFAULT_DIMS:
        return [f"unknown difficulty: {difficulty!r}"]
    return list(_analyze(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror for tests/reports; canonical Racket remains authority."""
    analysis = _analyze(grid)
    errors = analysis.get("errors", [])
    if errors:
        raise ValueError("; ".join(errors))
    truth = analysis.get("truth")
    if truth is None:
        raise ValueError("non-empty framed interior is required")
    return [row[:] for row in truth]


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": int(analysis["height"]),
        "grid_w": int(analysis["width"]),
        "content_cells": len(analysis["content"]),
        "content_colors": len(analysis["content_colors"]),
        "outside_count": len(analysis["outside"]),
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    r1, c1, r2, c2 = analysis["frame"]
    br1, bc1, br2, bc2 = analysis["crop_bbox"]
    h, w = int(analysis["height"]), int(analysis["width"])
    crop_h, crop_w = br2 - br1 + 1, bc2 - bc1 + 1
    global_top = (h - crop_h) // 2
    global_left = (w - crop_w) // 2
    interior_h, interior_w = r2 - r1 - 1, c2 - c1 - 1
    frame_top = r1 + 1 + (interior_h - crop_h) // 2
    frame_left = c1 + 1 + (interior_w - crop_w) // 2
    return {
        **observe_overrides(grid),
        "frame_offset_changes_destination": (frame_top, frame_left) != (global_top, global_left),
        "outside_control_present": len(analysis["outside"]) > 0,
        "crop_already_canvas_centered": (br1, bc1) == (global_top, global_left),
        "visible_translation": (br1, bc1) != (global_top, global_left),
        "frame_removed": all(value != 7 for row in analysis["truth"] for value in row),
    }


def _paste_nonzero(
    canvas: list[list[int]], crop: list[list[int]], top: int, left: int
) -> list[list[int]]:
    out = [row[:] for row in canvas]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value != 0 and 0 <= top + r < len(out) and 0 <= left + c < len(out[0]):
                out[top + r][left + c] = value
    return out


def _solve_frame_relative(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    r1, c1, r2, c2 = analysis["frame"]
    crop = analysis["crop"]
    top = r1 + 1 + ((r2 - r1 - 1) - len(crop)) // 2
    left = c1 + 1 + ((c2 - c1 - 1) - len(crop[0])) // 2
    return _paste_nonzero(full_grid(len(grid), len(grid[0]), 0), crop, top, left)


def _solve_global_non7(grid) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    cells = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 7)
    ]
    if not cells:
        return full_grid(h, w, 0)
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    crop = [
        [0 if grid[r][c] == 7 else grid[r][c] for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    return _paste_nonzero(
        full_grid(h, w, 0), crop, (h - len(crop)) // 2, (w - len(crop[0])) // 2
    )


def _solve_retain_frame(grid) -> list[list[int]]:
    truth = rule_mirror(grid)
    analysis = _analyze(grid)
    r1, c1, r2, c2 = analysis["frame"]
    out = [row[:] for row in truth]
    for c in range(c1, c2 + 1):
        out[r1][c] = 7
        out[r2][c] = 7
    for r in range(r1, r2 + 1):
        out[r][c1] = 7
        out[r][c2] = 7
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "frame_relative_center": _solve_frame_relative,
    "global_non7_center": _solve_global_non7,
    "retain_frame": _solve_retain_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "frame_relative_center": _solve_frame_relative,
    "global_non7_center": _solve_global_non7,
}


def _rival_differs(grid, name: str) -> bool:
    try:
        return rule_mirror(grid) != SEMANTIC_RIVALS[name](grid)
    except Exception:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "canvas_reference_refutes_frame_relative": lambda grid: _rival_differs(
        grid, "frame_relative_center"
    ),
    "outside_cells_refute_global_crop": lambda grid: _rival_differs(
        grid, "global_non7_center"
    ),
    "frame_is_removed": lambda grid: _rival_differs(grid, "retain_frame"),
}

WITNESS_RIVALS = {
    "canvas_reference_refutes_frame_relative": ["frame_relative_center"],
    "outside_cells_refute_global_crop": ["global_non7_center"],
    "frame_is_removed": ["retain_frame"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every named non-equivalent shortcut."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} is not lawful: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the framed-interior rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is not lawful: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the framed-interior rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
            if survives and rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo and changes the query answer"
                )
        except Exception as exc:
            reasons.append(f"competitor {name!r} errored: {type(exc).__name__}: {exc}")
    return reasons
