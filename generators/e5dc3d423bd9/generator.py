"""Input sampler for e5dc3d423bd9 — fill centers of odd hollow frames.

The selected Racket rule leaves every exact hollow rectangular frame unchanged
except when both bbox dimensions are odd; those frames receive one same-color
cell at their unique integer center.

Canonical examples contain only odd-by-odd frames, so the wrong rule "mark the
floor center of every frame" reproduces every canonical answer.  Every ordinary
generated input therefore mixes 1-3 odd target frames with exactly one hollow
frame having an even dimension.  The even frame is a visible negative example:
the selected rule leaves its interior empty while the canonical-fitting shortcut
adds a spurious center cell.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "e5dc3d423bd9"
VERSION = "4.0.0"
TASK_ID = "e5dc3d423bd9"
RULE_HASH = "c76c9e5b1858"

SUMMARY = (
    "0-background grid with 1-3 distinct-color odd-by-odd hollow rectangular "
    "frames and one distinct-color hollow even-dimension decoy, all separated "
    "by at least one background cell. Rule: add one same-color cell at the exact "
    "bbox center of each frame whose height and width are both odd; leave the "
    "even-dimension decoy unchanged."
)

INVARIANTS = [
    "background is 0 and all frame colors are distinct integers in 1..9",
    "1-3 exact odd-by-odd hollow frames are rule targets",
    "ordinary generated inputs also contain exactly one even-dimension hollow frame",
    "frame bounding boxes are separated by at least one background row or column",
]

# Every advertised value is exact, observable from pixels, and constructive in
# every difficulty band. Difficulty changes weights only, never validity.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "full 7..14; easy/core favor canonical-scale values",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "full 10..18; easy/core favor canonical-scale values",
        "valid": "10..18",
    },
    "n_odd": {
        "type": "int",
        "default": "full 1..3; easy/core favor 1",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_BANDS = (None, "easy", "medium", "hard")
_GAP = 1
_ODD_SIDES = (3, 5, 7)

# (height, width, number of odd frames). One even decoy gives two object colors
# plus background, matching the canonical palette size of three.
_CANONICAL_PROFILES = ((7, 11, 1), (8, 10, 1), (9, 11, 1))
_CORE_SHARE = {
    "easy": ("core",) * 4 + ("broad",),
    "medium": ("core", "broad"),
    "hard": ("core", "broad", "broad"),
}
_FAVORED = {
    "grid_h": {
        "easy": (7, 8, 9),
        "medium": (8, 9, 10, 11, 12),
        "hard": (10, 11, 12, 13, 14),
    },
    "grid_w": {
        "easy": (10, 11, 12),
        "medium": (11, 12, 13, 14, 15),
        "hard": (14, 15, 16, 17, 18),
    },
    "n_odd": {
        "easy": (1, 1, 2),
        "medium": (1, 2, 2, 3),
        "hard": (2, 3, 3),
    },
}
_BOUNDS = {"grid_h": (7, 14), "grid_w": (10, 18), "n_odd": (1, 3)}


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _BANDS:
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name: str, difficulty: str | None, anchor: int | None = None) -> int:
    """Draw from the complete documented domain, with band/profile reweighting."""
    lo, hi = _BOUNDS[name]
    full_domain = list(range(lo, hi + 1))
    if anchor is not None:
        favored = (anchor,) * 12
    else:
        band = difficulty or "medium"
        favored = _FAVORED[name][band]
    # Every domain value remains present in every band, so exact overrides are
    # accepted everywhere; repeated favored values only alter probability.
    return ctx.draw_choice(name, full_domain + [v for v in favored for _ in range(10)])


def _split_extent(total: int, first_min: int, second_min: int, rng) -> tuple[tuple[int, int], tuple[int, int]]:
    """Split an extent into two slots separated by one reserved gap cell."""
    usable = total - _GAP
    lo = first_min
    hi = usable - second_min
    if hi < lo:
        raise RuntimeError(
            f"cannot split extent {total} into {first_min}+gap+{second_min}"
        )
    first = rng.randint(lo, hi)
    second = usable - first
    return (0, first), (first + _GAP, second)


def _slots(rng, h: int, w: int, count: int) -> list[tuple[int, int, int, int]]:
    """Construct count non-touching slots; every slot can host an even decoy."""
    if count == 2 and rng.random() < 0.5:
        # Horizontal: each width is >=4, so an even frame can be 3x4.
        (c1, w1), (c2, w2) = _split_extent(w, 4, 4, rng)
        slots = [(0, c1, h, w1), (0, c2, h, w2)]
    elif count == 2:
        # Vertical: full width is >=10, so evenness can always be in width.
        (r1, h1), (r2, h2) = _split_extent(h, 3, 3, rng)
        slots = [(r1, 0, h1, w), (r2, 0, h2, w)]
    else:
        # Three/four objects use a 2x2 shelf. Column slots are >=4 so even
        # decoys fit even when a row slot has the minimum height 3.
        (r1, h1), (r2, h2) = _split_extent(h, 3, 3, rng)
        (c1, w1), (c2, w2) = _split_extent(w, 4, 4, rng)
        slots = [
            (r1, c1, h1, w1),
            (r1, c2, h1, w2),
            (r2, c1, h2, w1),
            (r2, c2, h2, w2),
        ]
        rng.shuffle(slots)
        slots = slots[:count]
    rng.shuffle(slots)
    return slots


def _odd_dims(rng, slot_h: int, slot_w: int, max_side: int) -> tuple[int, int]:
    heights = [side for side in _ODD_SIDES if side <= slot_h and side <= max_side]
    widths = [side for side in _ODD_SIDES if side <= slot_w and side <= max_side]
    if not heights or not widths:
        raise RuntimeError(f"odd frame does not fit in slot {slot_h}x{slot_w}")
    return rng.choice(heights), rng.choice(widths)


def _even_dims(rng, slot_h: int, slot_w: int, max_side: int) -> tuple[int, int]:
    choices = [
        (fh, fw)
        for fh in range(3, min(slot_h, max_side) + 1)
        for fw in range(3, min(slot_w, max_side) + 1)
        if fh % 2 == 0 or fw % 2 == 0
    ]
    if not choices:
        # All constructed slots have width >=4, so this is an internal error,
        # not a stochastic rejection path.
        raise RuntimeError(f"even frame does not fit in slot {slot_h}x{slot_w}")
    return rng.choice(choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    band = difficulty or "medium"
    mode = ctx.draw_choice("curriculum_profile", _CORE_SHARE[band])
    anchor = (
        ctx.draw_choice("canonical_anchor", _CANONICAL_PROFILES)
        if mode == "core"
        else (None, None, None)
    )
    h = _draw_axis(ctx, "grid_h", difficulty, anchor[0])
    w = _draw_axis(ctx, "grid_w", difficulty, anchor[1])
    n_odd = _draw_axis(ctx, "n_odd", difficulty, anchor[2])

    layout_rng = ctx.draw_rng("layout")
    kinds = ["odd"] * n_odd + ["even"]
    layout_rng.shuffle(kinds)
    slots = _slots(layout_rng, h, w, len(kinds))
    colors = ctx.draw_rng("colors").sample(range(1, 10), len(kinds))
    max_side = 5 if mode == "core" or difficulty == "easy" else 7

    grid = full_grid(h, w, 0)
    for kind, color, (slot_r, slot_c, slot_h, slot_w) in zip(kinds, colors, slots):
        if kind == "odd":
            fh, fw = _odd_dims(layout_rng, slot_h, slot_w, max_side)
        else:
            fh, fw = _even_dims(layout_rng, slot_h, slot_w, max_side)
        r0 = layout_rng.randint(slot_r, slot_r + slot_h - fh)
        c0 = layout_rng.randint(slot_c, slot_c + slot_w - fw)
        draw_rect_outline(grid, r0, c0, fh, fw, color)
    return grid


def _same_color_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _frame_info(component: dict[str, Any]) -> dict[str, Any] | None:
    r1, c1, r2, c2 = component["bbox"]
    fh, fw = r2 - r1 + 1, c2 - c1 + 1
    if fh < 3 or fw < 3:
        return None
    expected = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if set(component["cells"]) != expected:
        return None
    return {
        **component,
        "height": fh,
        "width": fw,
        "odd": fh % 2 == 1 and fw % 2 == 1,
    }


def _frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    return [frame for component in _same_color_components(grid) if (frame := _frame_info(component))]


def _bboxes_too_close(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Reject overlap or edge adjacency, while allowing canonical diagonal adjacency."""
    ar1, ac1, ar2, ac2 = a["bbox"]
    br1, bc1, br2, bc2 = b["bbox"]
    rows_overlap = max(ar1, br1) <= min(ar2, br2)
    cols_overlap = max(ac1, bc1) <= min(ac2, bc2)
    if rows_overlap:
        if ac2 < bc1:
            return bc1 - ac2 <= _GAP
        if bc2 < ac1:
            return ac1 - bc2 <= _GAP
        return True
    if cols_overlap:
        if ar2 < br1:
            return br1 - ar2 <= _GAP
        if br2 < ar1:
            return ar1 - br2 <= _GAP
        return True
    return False


def observe_overrides(grid):
    """Recover every exposed exact control from a lawful completed input."""
    found = _frames(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_odd": sum(frame["odd"] for frame in found),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared input manifold; all canonical inputs remain lawful."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid rows must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    components = _same_color_components(grid)
    errors: list[str] = []
    if not components:
        return ["expected at least one hollow frame"]

    frames: list[dict[str, Any]] = []
    for component in components:
        frame = _frame_info(component)
        if frame is None:
            errors.append(
                f"color {component['color']} component is not an exact hollow rectangular frame"
            )
        else:
            frames.append(frame)

    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        errors.append("separate frames must use distinct colors")

    for index, first in enumerate(frames):
        for second in frames[index + 1 :]:
            if _bboxes_too_close(first, second):
                errors.append(
                    f"frames of colors {first['color']} and {second['color']} touch or lack a background gap"
                )

    n_odd = sum(frame["odd"] for frame in frames)
    n_even = len(frames) - n_odd
    if not 1 <= n_odd <= 3:
        errors.append(f"expected 1..3 odd-by-odd frames; got {n_odd}")
    # Canonical inputs have zero even frames; ordinary generated inputs have one.
    if n_even > 1:
        errors.append(f"expected at most one even-dimension frame; got {n_even}")
    return errors


def strict_canonical_like(grid):
    """Strict task-manifold validator used by the semantic gate."""
    return self_check(grid)


def _has_even_decoy(grid) -> bool:
    return any(not frame["odd"] for frame in _frames(grid))


def _mark_every_frame_floor_center(grid):
    """RIVAL, not label authority: marks odd and even frames indiscriminately."""
    out = [list(row) for row in grid]
    for frame in _frames(grid):
        r1, c1, r2, c2 = frame["bbox"]
        out[(r1 + r2) // 2][(c1 + c2) // 2] = frame["color"]
    return out


def lesson_identifiable(demos, query):
    """Reject a lesson whose demos all admit a declared rival that changes query."""
    reasons: list[str] = []
    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos) and (
            rival(query["input"]) != query["output"]
        ):
            reasons.append(
                f"rival {name} fits every demonstration but answers the query differently"
            )
    return reasons


SEMANTIC_WITNESSES = {"even_frame_left_unmarked": _has_even_decoy}
SEMANTIC_RIVALS = {"mark_every_frame_floor_center": _mark_every_frame_floor_center}
WITNESS_RIVALS = {
    "even_frame_left_unmarked": ["mark_every_frame_floor_center"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
