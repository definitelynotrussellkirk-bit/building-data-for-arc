"""Generator for arc_additional_puzzles_21_set14_bundle:M96.

Rule: normalize the color-2 cells and the color-3 cells independently
(each shifted so its bbox starts at (0,0)), then overlay them in the
union bbox. A cell that is in BOTH normalized shapes -> 8, only in the
2-shape -> 2, only in the 3-shape -> 3, else 0. The output depends only
on the two shapes, not on where they sit in the input.

Version 2.1.0 repairs the ordinary-source contract: only exact observable
size controls are advertised, unknown controls are rejected, keyed draws
honour requested sizes, and ``self_check`` validates the full semantic domain.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b6b40a92e4f"
VERSION = "2.1.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A 0-background grid contains exactly one connected color-2 shape and "
    "one connected color-3 shape, separated in the input. Normalize each "
    "shape to its own bounding box and overlay them: shared cells become 8, "
    "color-2-only cells stay 2, and color-3-only cells stay 3."
)

INVARIANTS = [
    "background is 0 and foreground colors are exactly 2 and 3",
    "exactly one four-connected color-2 component and one color-3 component",
    "the two input components are separated by at least one king-move gap",
    "normalized footprints overlap and each has at least one exclusive cell",
]

# Keep only controls recoverable exactly from returned pixels.  The previous
# palette/anchor/asymmetry declarations were dead controls and are intentionally
# removed rather than silently accepted.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 9..16", "valid": "9..16"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 10..18", "valid": "10..18"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    bounds = {"grid_h": (9, 16), "grid_w": (10, 18)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an exact integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_axis(ctx, label: str, lo: int, hi: int, preferred: tuple[int, int]) -> int:
    options = list(range(lo, hi + 1))
    options.extend(range(preferred[0], preferred[1] + 1))
    options.extend(range(preferred[0], preferred[1] + 1))
    return ctx.draw_choice(label, tuple(options))


def _norm(cells):
    cells = set(cells)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _place_cluster(occupied, cells, h, w):
    """Place cells only if in bounds and king-move separated from prior cells."""
    cset = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or occupied[r][c]:
            return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occupied[rr][cc]:
                    return False
    for r, c in cells:
        occupied[r][c] = True
    return True


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
        preferred_h, preferred_w, size_range = (9, 11), (10, 13), (3, 4)
    elif difficulty == "hard":
        preferred_h, preferred_w, size_range = (12, 16), (14, 18), (5, 7)
    else:
        preferred_h, preferred_w, size_range = (10, 14), (12, 16), (4, 6)

    h = _weighted_axis(ctx, "grid_h", 9, 16, preferred_h)
    w = _weighted_axis(ctx, "grid_w", 10, 18, preferred_w)
    rng = ctx.draw_rng("layout")

    for _attempt in range(240):
        a = _poly(rng, rng.randint(*size_range))
        b = _poly(rng, rng.randint(*size_range))
        if not (a & b) or not (a - b) or not (b - a):
            continue
        ah, aw = max(r for r, _ in a) + 1, max(c for _, c in a) + 1
        bh, bw = max(r for r, _ in b) + 1, max(c for _, c in b) + 1
        if ah > h or aw > w or bh > h or bw > w:
            continue

        grid = full_grid(h, w, 0)
        occupied = [[False] * w for _ in range(h)]
        placed = []
        for cells, color, sh, sw in ((a, 2, ah, aw), (b, 3, bh, bw)):
            success = False
            for _ in range(120):
                top = rng.randint(0, h - sh)
                left = rng.randint(0, w - sw)
                absolute = [(top + r, left + c) for r, c in cells]
                if _place_cluster(occupied, absolute, h, w):
                    for r, c in absolute:
                        grid[r][c] = color
                    placed.append(absolute)
                    success = True
                    break
            if not success:
                break
        if len(placed) != 2:
            continue
        errors = self_check(grid, difficulty=difficulty)
        if not errors:
            return grid
    raise ValueError("could not realize a valid separated two-shape layout")


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact control from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete ordinary semantic manifold."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]

    errors: list[str] = []
    height = len(grid)
    if not 9 <= height <= 16:
        errors.append(f"grid_h={height} outside 9..16")
    if not 10 <= width <= 18:
        errors.append(f"grid_w={width} outside 10..18")
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        errors.append(f"cells must be exact ARC colors 0..9: {bad[:3]}")
        return errors
    extra = sorted({value for row in grid for value in row} - {0, 2, 3})
    if extra:
        errors.append(f"unexpected foreground color(s): {extra}")

    by_color = {
        color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        for color in (2, 3)
    }
    for color, cells in by_color.items():
        if not cells:
            errors.append(f"no color-{color} blob cells")
        elif len(_components(cells)) != 1:
            errors.append(f"color-{color} cells must form exactly one connected component")
    if any(not cells for cells in by_color.values()):
        return errors

    # The two objects must be spatially separate in the input; otherwise a model
    # could infer an input overlay instead of independent normalization.
    if any(
        abs(r2 - r3) <= 1 and abs(c2 - c3) <= 1
        for r2, c2 in by_color[2]
        for r3, c3 in by_color[3]
    ):
        errors.append("color-2 and color-3 components must be separated by a king-move gap")

    normalized2 = _norm(by_color[2])
    normalized3 = _norm(by_color[3])
    if not (normalized2 & normalized3):
        errors.append("normalized color-2 and color-3 footprints must overlap")
    if not (normalized2 - normalized3):
        errors.append("normalized color-2 footprint needs a color-2-only cell")
    if not (normalized3 - normalized2):
        errors.append("normalized color-3 footprint needs a color-3-only cell")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)
