"""Generator for nested rectangular-frame depth recoloring.

The canonical rule detects every non-background connected component that is
exactly the border of its bounding box, then recolors each nonzero cell to one
plus the number of detected frames whose bounding boxes contain that cell.

This repaired source deliberately covers the canonical branches that the old
2.1.0 source omitted: inset outer frames, two through four nested frames, and
isolated singleton components inside or outside the stack.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = TASK_ID = "938fbbaf1437"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background grid contains two to four separated nested rectangular "
    "color-1 frames, optionally inset from the canvas, plus zero to two isolated "
    "color-1 singleton components. Recolor every nonzero cell to 1 plus the "
    "number of rectangular-frame components whose bounding boxes contain it."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "2..4 nested rectangular frame components",
    "successive frames have at least one blank cell between borders",
    "singleton components never cardinal-touch another nonzero cell",
]
AXES = {
    "grid_h": {"type": "int", "default": "rng 9..30", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "rng 9..30", "valid": "9..30"},
    "n_frames": {"type": "int", "default": "rng 2..4 subject to size", "valid": "2..4"},
    "outer_inset": {"type": "int", "default": "rng 0..2 subject to size", "valid": "0..2"},
    "singleton_count": {"type": "int", "default": "rng 0..2 subject to space", "valid": "0..2"},
}


def _strict_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an exact integer")


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            todo = deque([(sr, sc)])
            seen.add((sr, sc))
            cells: set[tuple[int, int]] = set()
            while todo:
                r, c = todo.popleft()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return result


def _rect_bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    border = (
        {(r0, c) for c in range(c0, c1 + 1)}
        | {(r1, c) for c in range(c0, c1 + 1)}
        | {(r, c0) for r in range(r0, r1 + 1)}
        | {(r, c1) for r in range(r0, r1 + 1)}
    )
    return (r0, r1, c0, c1) if cells == border else None


def _candidate_singletons(grid: list[list[int]]) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    candidates = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if any(
                0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                continue
            candidates.append((r, c))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_strict("grid_h", 9, 30)
    w = ctx.draw_int_strict("grid_w", 9, 30)
    min_side = min(h, w)

    max_inset = min(2, max(0, (min_side - 9) // 2))
    if "outer_inset" in overrides and overrides["outer_inset"] is not None:
        inset = ctx.draw_int_strict("outer_inset", 0, 2)
        if inset > max_inset:
            raise ValueError("outer_inset leaves no room for two nested frames")
    else:
        inset = ctx.draw_int("outer_inset", 0, max_inset)

    usable = min_side - 2 * inset
    max_frames = min(4, (usable - 1) // 4)
    if max_frames < 2:
        raise ValueError("grid dimensions and inset leave no room for two frames")
    if "n_frames" in overrides and overrides["n_frames"] is not None:
        n_frames = ctx.draw_int_strict("n_frames", 2, 4)
        if n_frames > max_frames:
            raise ValueError("n_frames does not fit requested dimensions/inset")
    else:
        n_frames = ctx.draw_int("n_frames", 2, max_frames)

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    r0 = c0 = inset
    fh, fw = h - 2 * inset, w - 2 * inset
    for level in range(n_frames):
        if level:
            remaining = n_frames - level - 1
            minimum = 4 * remaining + 5
            max_h, max_w = fh - 4, fw - 4
            next_h = rng.randint(minimum, max_h)
            next_w = rng.randint(minimum, max_w)
            extra_h = max_h - next_h
            extra_w = max_w - next_w
            r0 += 2 + rng.randint(0, extra_h)
            c0 += 2 + rng.randint(0, extra_w)
            fh, fw = next_h, next_w
        draw_rect_outline(grid, r0, c0, fh, fw, 1)
        boxes.append((r0, c0, fh, fw))

    candidates = _candidate_singletons(grid)
    # Prefer the deepest interior, then widely separated deterministic locations.
    ir, ic, ih, iw = boxes[-1]
    preferred = [(ir + ih // 2, ic + iw // 2)]
    candidates.sort(key=lambda p: (p not in preferred, p[0], p[1]))
    placements: list[tuple[int, int]] = []
    for r, c in candidates:
        if any(abs(r - rr) + abs(c - cc) <= 1 for rr, cc in placements):
            continue
        placements.append((r, c))
        if len(placements) == 2:
            break
    if "singleton_count" in overrides and overrides["singleton_count"] is not None:
        count = ctx.draw_int_strict("singleton_count", 0, 2)
        if count > len(placements):
            raise ValueError("singleton_count does not fit without touching a frame")
    else:
        count = ctx.draw_int("singleton_count", 0, len(placements))
    for r, c in placements[:count]:
        grid[r][c] = 1
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid exceeds 30x30"]
    if any(type(v) is not int or v not in (0, 1) for row in grid for v in row):
        return ["input must use only 0 background and 1 foreground"]
    rects = [bbox for cells in _components(grid) if (bbox := _rect_bbox(cells)) is not None]
    proper = [bbox for bbox in rects if bbox[0] != bbox[1] or bbox[2] != bbox[3]]
    if not 2 <= len(proper) <= 4:
        return ["normal instance must contain two through four proper rectangular frames"]
    # Every later proper frame must be strictly enclosed with a blank moat.
    proper.sort(key=lambda b: (b[1] - b[0] + 1) * (b[3] - b[2] + 1), reverse=True)
    for outer, inner in zip(proper, proper[1:]):
        if not (
            outer[0] + 2 <= inner[0]
            and inner[1] <= outer[1] - 2
            and outer[2] + 2 <= inner[2]
            and inner[3] <= outer[3] - 2
        ):
            return ["proper frames must be nested with a blank moat"]
    changed = any(
        1 + sum(r0 <= r <= r1 and c0 <= c <= c1 for r0, r1, c0, c1 in rects) != 1
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    )
    return [] if changed else ["canonical recoloring would be an identity"]
