"""Generator for hard_83: sort objects by holes, then area, and pack.

Each input contains isolated monochrome connected objects.  The canonical rule
computes every object's enclosed-hole count and occupied area, sorts by
``(holes descending, area descending, input bbox)``, then horizontally packs the
cropped objects with one blank column and vertical centering.

Version 2.2.0 repairs the ordinary generator contract: advertised controls are
exact and observable, unknown controls are rejected, summary/axes match the
actual 0/1/2-hole grammar, and ``self_check`` validates the semantic manifold.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6f34233d788"
VERSION = "2.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A 0-background grid contains 2-6 isolated monochrome objects spanning "
    "solid blobs (0 holes), hollow rings (1 hole), and sometimes double rings "
    "(2 holes). Sort objects by hole count descending, then occupied area "
    "descending, and pack their crops left-to-right with one-column gaps."
)

INVARIANTS = [
    "background is 0 and every object is a monochrome four-connected component",
    "object colors are distinct and components are separated by a king-move gap",
    "each scene contains at least one 0-hole object and one object with a hole",
]

# Only exact controls recoverable from returned pixels are advertised.  Prior
# palette/texture/density aliases were not consumed and have been removed.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 9..18", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 11..22", "valid": "11..22"},
    "n": {"type": "int", "default": "difficulty-weighted 2..6", "valid": "2..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BOUNDS = {"grid_h": (9, 18), "grid_w": (11, 22), "n": (2, 6)}


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an exact integer, not {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_axis(ctx, label: str, preferred: tuple[int, int]) -> int:
    lo, hi = _BOUNDS[label]
    options = list(range(lo, hi + 1))
    options.extend(range(preferred[0], preferred[1] + 1))
    options.extend(range(preferred[0], preferred[1] + 1))
    return ctx.draw_choice(label, tuple(options))


def _free(grid, r1, c1, r2, c2):
    h, w = len(grid), len(grid[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if grid[r][c] != 0:
                return False
    return True


def _build_motif(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    top = min(r for r, _ in cells); left = min(c for _, c in cells)
    return sorted((r - top, c - left) for r, c in cells)


def _build_frame(rng, h, w):
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    ]


def _build_ring(rng, compact=False):
    choices = [(3, 3), (3, 4), (4, 3)] if compact else [(4, 4), (4, 5), (5, 4), (5, 5)]
    h, w = rng.choice(choices)
    return _build_frame(rng, h, w)


def _build_double_ring(rng):
    """Two vertically stacked rings sharing one wall: exactly two holes."""
    width = rng.choice((3, 4))
    return sorted(
        (r, c)
        for r in range(5)
        for c in range(width)
        if r in (0, 2, 4) or c in (0, width - 1)
    )


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
    if difficulty == "easy":
        preferred_h, preferred_w, preferred_n = (9, 11), (11, 14), (2, 3)
    elif difficulty == "hard":
        preferred_h, preferred_w, preferred_n = (14, 18), (16, 22), (4, 6)
    else:
        preferred_h, preferred_w, preferred_n = (11, 14), (13, 17), (3, 4)
    h = _weighted_axis(ctx, "grid_h", preferred_h)
    w = _weighted_axis(ctx, "grid_w", preferred_w)
    n = _weighted_axis(ctx, "n", preferred_n)
    rng = ctx.draw_rng("layout")

    for _outer in range(160):
        grid = full_grid(h, w, 0)
        colors = rng.sample(list(range(1, 10)), n)
        compact = h <= 11 or w <= 14 or n >= 5
        builders: list[tuple[str, int | None]] = [("blob", rng.randint(3, 6)), ("ring", None)]
        for _ in range(2, n):
            choices = ["blob", "ring"] + ([] if compact else ["double"])
            kind = rng.choice(choices)
            builders.append((kind, rng.randint(3, 6) if kind == "blob" else None))
        rng.shuffle(builders)

        ok = True
        for color, (kind, size) in zip(colors, builders):
            if kind == "ring":
                cells = _build_ring(rng, compact=compact)
            elif kind == "double":
                cells = _build_double_ring(rng)
            else:
                cells = _build_motif(rng, int(size))
            rows = [r for r, _ in cells]; cols = [c for _, c in cells]
            sh, sw = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
            placed = False
            for _ in range(240):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                if not _free(grid, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for r, c in cells:
                    grid[r0 + r - min(rows)][c0 + c - min(cols)] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok and not self_check(grid, difficulty=difficulty):
            return grid
    raise ValueError("could not realize an isolated mixed-topology layout")


def _components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while remaining:
        start = min(remaining); remaining.remove(start)
        queue = deque([start]); cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt); cells.add(nxt); queue.append(nxt)
        result.append(cells)
    return result


def _crop_mask(cells):
    top = min(r for r, _ in cells); bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells); right = max(c for _, c in cells)
    mask = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for r, c in cells:
        mask[r - top][c - left] = 1
    return mask


def _hole_count(cells):
    mask = _crop_mask(cells)
    h, w = len(mask), len(mask[0])
    zeros = {(r, c) for r in range(h) for c in range(w) if mask[r][c] == 0}
    holes = 0
    while zeros:
        start = min(zeros); zeros.remove(start)
        queue = deque([start]); touches = start[0] in (0, h - 1) or start[1] in (0, w - 1)
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in zeros:
                    zeros.remove(nxt); queue.append(nxt)
                    if nxt[0] in (0, h - 1) or nxt[1] in (0, w - 1):
                        touches = True
        if not touches:
            holes += 1
    return holes


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from the returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n": len(_components(grid))}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    errors: list[str] = []
    height = len(grid)
    if not 9 <= height <= 18:
        errors.append(f"grid_h={height} outside 9..18")
    if not 11 <= width <= 22:
        errors.append(f"grid_w={width} outside 11..22")
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        errors.append(f"cells must be exact ARC colors 0..9: {bad[:3]}")
        return errors

    objects = _components(grid)
    if not 2 <= len(objects) <= 6:
        errors.append(f"expected 2..6 connected components, found {len(objects)}")
    colors = []
    for index, cells in enumerate(objects):
        object_colors = {grid[r][c] for r, c in cells}
        if len(object_colors) != 1:
            errors.append(f"component {index} is not monochrome")
        else:
            colors.append(next(iter(object_colors)))
    if len(colors) != len(set(colors)):
        errors.append("objects must use distinct nonzero colors")

    # Components are expected to have a blank king-move moat.
    owner = {cell: index for index, cells in enumerate(objects) for cell in cells}
    touching = False
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr or dc) and (r + dr, c + dc) in owner and owner[(r + dr, c + dc)] != index:
                    touching = True
    if touching:
        errors.append("components must be separated by a king-move gap")

    holes = [_hole_count(cells) for cells in objects]
    if objects and 0 not in holes:
        errors.append("expected at least one 0-hole solid object")
    if objects and not any(value >= 1 for value in holes):
        errors.append("expected at least one object with an enclosed hole")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)
