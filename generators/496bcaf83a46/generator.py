"""Generator for arc_additional_puzzles_21_set6:H40.

The input contains two to four rectangular frames in colors other than 0 and
8.  Color 8 marks seed cells inside those frames.  The Racket rule keeps every
eligible border and fills the interior of every frame tied for the maximum seed
count.  Medium and hard lessons sometimes add a separate color-8 rectangle;
because 8 is the seed color rather than an eligible frame color, that distractor
disappears.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "496bcaf83a46"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "703485a20938"

SUMMARY = (
    "Count color-8 seeds inside each non-8 rectangular frame, preserve all "
    "eligible borders, and fill every frame tied for the maximum count."
)

INVARIANTS = [
    "background is 0",
    "two to four eligible objects are complete rectangular borders in distinct colors other than 0 and 8",
    "every eligible frame contains at least one color-8 seed strictly inside it",
    "at least one eligible frame has fewer seeds than the maximum, while one or two frames attain the maximum",
    "medium and hard lessons may contain one separate color-8 rectangular distractor that the oracle removes",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 11..20", "valid": "11..20"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 13..24", "valid": "13..24"},
    "n_frames": {"type": "int", "default": "difficulty-aware rng 2..4", "valid": "2..4"},
}

_FRAME_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_axis_int(ctx, name: str, full: tuple[int, int], ordinary: tuple[int, int]) -> int:
    """Honor every declared boundary even when it lies outside a band's usual range."""
    lo, hi = full if name in ctx.overrides else ordinary
    return ctx.draw_int(name, lo, hi)


def _regions(h: int, w: int, count: int, rng) -> list[tuple[int, int, int, int]]:
    """Return count disjoint regions with a one-cell moat between them."""
    if count not in (2, 3, 4):
        raise ValueError(f"unsupported object count: {count}")

    row_gap = h // 2
    col_gap = w // 2
    top = (1, 1, row_gap - 1, w - 2)
    bottom = (row_gap + 1, 1, h - 2, w - 2)
    left = (1, 1, h - 2, col_gap - 1)
    right = (1, col_gap + 1, h - 2, w - 2)
    tl = (1, 1, row_gap - 1, col_gap - 1)
    tr = (1, col_gap + 1, row_gap - 1, w - 2)
    bl = (row_gap + 1, 1, h - 2, col_gap - 1)
    br = (row_gap + 1, col_gap + 1, h - 2, w - 2)

    if count == 2:
        choices = [[left, right], [top, bottom]]
    elif count == 3:
        choices = [[tl, tr, bottom], [top, bl, br], [left, tr, br], [tl, bl, right]]
    else:
        choices = [[tl, tr, bl, br]]

    legal = [
        regions
        for regions in choices
        if all(r2 - r1 + 1 >= 4 and c2 - c1 + 1 >= 4 for r1, c1, r2, c2 in regions)
    ]
    if not legal:
        raise ValueError(f"grid {h}x{w} cannot host {count} separated frames")
    out = list(rng.choice(legal))
    rng.shuffle(out)
    return out


def _frame_box(region: tuple[int, int, int, int], rng) -> tuple[int, int, int, int]:
    r1, c1, r2, c2 = region
    region_h, region_w = r2 - r1 + 1, c2 - c1 + 1
    frame_h = rng.randint(4, region_h)
    frame_w = rng.randint(4, region_w)
    top = rng.randint(r1, r2 - frame_h + 1)
    left = rng.randint(c1, c2 - frame_w + 1)
    return top, left, top + frame_h - 1, left + frame_w - 1


def _seed_counts(capacities: list[int], tie_max: bool, rng) -> list[int]:
    n = len(capacities)
    max_count = rng.randint(2, min(4, min(capacities)))
    if tie_max and n >= 3:
        winners = set(rng.sample(range(n), 2))
    else:
        winners = {rng.randrange(n)}
    counts = [max_count if i in winners else rng.randint(1, max_count - 1) for i in range(n)]
    rng.shuffle(counts)
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    ordinary_ranges = {
        "easy": ((11, 13), (13, 16)),
        "medium": ((12, 16), (14, 20)),
        "hard": ((14, 20), (18, 24)),
    }
    h_range, w_range = ordinary_ranges[band]
    h = _draw_axis_int(ctx, "grid_h", (11, 20), h_range)
    w = _draw_axis_int(ctx, "grid_w", (13, 24), w_range)

    # Materialization draws sample indices 0..3 for each three-demo lesson.
    # Reserve one ordinary demonstration for tied maxima and one for the
    # canonical seed-color distractor, while retaining exact n_frames overrides.
    if band == "easy":
        n_range = (2, 3)
    elif band == "hard" and sample_index % 4 == 1:
        n_range = (3, 3)
    elif band == "hard":
        n_range = (3, 4)
    elif sample_index % 4 == 0:
        n_range = (3, 4)
    elif sample_index % 4 == 2:
        n_range = (2, 3)
    else:
        n_range = (2, 4)
    n_frames = _draw_axis_int(ctx, "n_frames", (2, 4), n_range)

    tie_max = n_frames >= 3 and band != "easy" and sample_index % 4 == 0
    has_distractor = n_frames <= 3 and (
        (band == "hard" and sample_index % 4 == 1)
        or (band == "medium" and sample_index % 4 == 2)
    )

    rng = ctx.draw_rng("layout")
    total_objects = n_frames + int(has_distractor)
    regions = _regions(h, w, total_objects, rng)
    candidate_regions = regions[:n_frames]
    distractor_region = regions[-1] if has_distractor else None

    grid = full_grid(h, w, 0)
    colors = rng.sample(list(_FRAME_COLORS), n_frames)
    boxes = [_frame_box(region, rng) for region in candidate_regions]
    capacities = [(r2 - r1 - 1) * (c2 - c1 - 1) for r1, c1, r2, c2 in boxes]
    counts = _seed_counts(capacities, tie_max, rng)

    for color, box, count in zip(colors, boxes, counts):
        r1, c1, r2, c2 = box
        draw_frame(grid, r1, c1, r2, c2, color)
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
        rng.shuffle(interior)
        for r, c in interior[:count]:
            grid[r][c] = 8

    if distractor_region is not None:
        r1, c1, r2, c2 = _frame_box(distractor_region, rng)
        draw_frame(grid, r1, c1, r2, c2, 8)
        # Canonical train 3 contains an 8-colored frame with an attached/interior
        # 8 cell.  Include that exact cue class on half the distractor lessons.
        if sample_index % 8 == 1:
            grid[r1 + 1][c1 + 1] = 8

    return grid


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            comp: set[tuple[int, int]] = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                comp.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(comp)
    return out


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _analyze(grid) -> dict:
    errors: list[str] = []
    result = {"errors": errors, "frames": [], "distractors": []}
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be nonempty")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("rows must be nonempty")
        return result
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        errors.append("cells must be ARC colors 0..9")
        return result

    h = len(grid)
    frames = []
    covered_nonseed: set[tuple[int, int]] = set()
    for color in sorted({v for row in grid for v in row if v not in (0, 8)}):
        for comp in _components(grid, color):
            box = _bbox(comp)
            r1, c1, r2, c2 = box
            border = _border_cells(box)
            if r2 - r1 < 2 or c2 - c1 < 2 or comp != border:
                errors.append(f"color {color} component is not a complete rectangular border")
                continue
            inside = {(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)}
            count8 = sum(grid[r][c] == 8 for r, c in inside)
            frames.append({"color": color, "bbox": box, "border": border, "inside": inside, "seed_count": count8})
            covered_nonseed |= border

    all_nonseed = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)}
    if all_nonseed != covered_nonseed:
        errors.append("every non-0/non-8 cell must belong to an eligible frame border")
    if not 2 <= len(frames) <= 4:
        errors.append(f"expected 2..4 eligible frames, found {len(frames)}")

    inside_owner: dict[tuple[int, int], int] = {}
    for i, frame in enumerate(frames):
        for cell in frame["inside"]:
            if cell in inside_owner:
                errors.append("eligible frame interiors overlap")
            inside_owner[cell] = i

    external8 = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8 and (r, c) not in inside_owner}
    distractors = []
    assigned_external: set[tuple[int, int]] = set()
    for comp in _components(grid, 8):
        external_part = comp & external8
        if not external_part:
            continue
        box = _bbox(comp)
        r1, c1, r2, c2 = box
        border = _border_cells(box)
        if r2 - r1 < 3 or c2 - c1 < 3 or not border <= comp or not comp <= {
            (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
        }:
            errors.append("color-8 cells outside eligible frames must form a complete rectangular distractor")
            continue
        distractors.append({"bbox": box, "cells": comp})
        assigned_external |= external_part
    if assigned_external != external8:
        errors.append("unassigned color-8 cells exist outside eligible frame interiors")
    if len(distractors) > 1:
        errors.append("at most one color-8 distractor rectangle is allowed")

    counts = [frame["seed_count"] for frame in frames]
    if any(count < 1 for count in counts):
        errors.append("every eligible frame must contain at least one seed")
    if counts:
        max_count = max(counts)
        winners = [i for i, count in enumerate(counts) if count == max_count]
        if len(winners) == len(counts) and not distractors:
            errors.append("all eligible frames tie without a seed-color distractor, so the lesson has no selection contrast")
        if len(winners) > 2:
            errors.append("at most two max-count frames are allowed in the teaching distribution")
        result.update({"max_count": max_count, "winner_count": len(winners)})

    result.update({"height": h, "width": w, "frames": frames, "distractors": distractors})
    return result


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_frames": len(analysis["frames"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = (meta or {}).get("overrides") or {}
    observed = None
    if not errors and requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and observed.get(name) != requested[name]:
                errors.append(f"override {name}={requested[name]!r} realized as {observed.get(name)!r}")
    return errors
