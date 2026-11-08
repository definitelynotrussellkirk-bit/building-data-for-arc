"""Constructive inputs for motif cropping, ranking, and horizontal packing.

Each nonzero color forms one separated four-connected motif.  Motif cell counts
are distinct, so the canonical descending-size order is unambiguous.  Racket is
still the label authority; this module produces inputs and validates the grammar.
"""
from __future__ import annotations

from collections import deque
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2314acbb67be"
TASK_ID = GENERATOR_ID
RULE_HASH = "293c753eb7cd"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "Two to four separated, differently colored four-connected motifs with "
    "distinct cell counts; crop each, rank by descending cell count, and pack "
    "the crops horizontally with one zero column between them."
)
INVARIANTS = [
    "background is 0 and every cell is an exact ARC color",
    "each nonzero color forms exactly one four-connected motif",
    "motifs are separated by at least one cell and have distinct cell counts",
    "exact controls are honored or rejected; no advertised axis is ignored",
]
PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 6, 8, 9),
    "varied": (2, 3, 4, 5, 7, 8),
}
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 8..30", "valid": "8..30"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 12..30", "valid": "12..30"},
    "n": {"type": "int", "default": "difficulty-weighted 2..4", "valid": "2..4"},
    "palette_kind": {"type": "str", "default": "rng default|warm|cool|varied",
                     "valid": "default|warm|cool|varied"},
}
_BOUNDS = {"grid_h": (8, 30), "grid_w": (12, 30), "n": (2, 4)}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    values = {name: value for name, value in overrides.items() if value is not None}
    for name in _BOUNDS:
        if name not in values:
            continue
        value = values[name]
        lo, hi = _BOUNDS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "palette_kind" in values:
        value = values["palette_kind"]
        if type(value) is not str or value not in PALETTES:
            raise ValueError(f"palette_kind must be one of {tuple(PALETTES)}")
    return values


def _weighted_int(ctx, name, lo, hi, favored):
    choices = list(range(lo, hi + 1)) + [x for x in favored if lo <= x <= hi] * 5
    return ctx.draw_choice(name, choices)


def _build_motif(rng, size):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        nxt = (r + dr, c + dc)
        if nxt not in seen:
            seen.add(nxt)
            cells.append(nxt)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return [(r - min_r, c - min_c) for r, c in cells]


def _free(grid, r0, c0, height, width):
    h, w = len(grid), len(grid[0])
    if r0 < 0 or c0 < 0 or r0 + height > h or c0 + width > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + height + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + width + 1)):
            if grid[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    values = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=values)
    if difficulty == "easy":
        favored_h, favored_w, favored_n = (8, 9, 10, 11), (12, 13, 14, 15, 16), (2, 2, 3)
    elif difficulty == "hard":
        favored_h, favored_w, favored_n = (18, 22, 26, 30), (20, 24, 28, 30), (3, 4, 4)
    else:
        favored_h, favored_w, favored_n = (9, 10, 12, 14, 16), (13, 14, 16, 18, 20), (2, 3, 3, 4)
    h = _weighted_int(ctx, "grid_h", 8, 30, favored_h)
    w = _weighted_int(ctx, "grid_w", 12, 30, favored_w)
    n = ctx.draw_choice("n", list(range(2, 5)) + list(favored_n) * 4)
    palette_kind = ctx.draw_choice("palette_kind", tuple(PALETTES))
    rng = ctx.draw_rng("layout")

    # Small canvases receive compact sizes; larger scenes include substantially
    # larger objects while preserving a bounded 30x30 grammar.
    max_size = min(14, max(7, (h * w) // (n * 9)))
    size_pool = list(range(3, max_size + 1))
    if len(size_pool) < n:
        raise ValueError("grid is too small for the requested number of distinct motifs")

    for _ in range(160):
        grid = full_grid(h, w, 0)
        sizes = sorted(rng.sample(size_pool, n), reverse=True)
        colors = rng.sample(list(PALETTES[palette_kind]), n)
        placed_all = True
        for size, color in zip(sizes, colors, strict=True):
            placed = False
            for _ in range(160):
                cells = _build_motif(rng, size)
                sh = max(r for r, _ in cells) + 1
                sw = max(c for _, c in cells) + 1
                if sh > h or sw > w:
                    continue
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                if not _free(grid, r0, c0, sh, sw):
                    continue
                for r, c in cells:
                    grid[r0 + r][c0 + c] = color
                placed = True
                break
            if not placed:
                placed_all = False
                break
        if placed_all and self_check(grid, difficulty=difficulty) == []:
            return grid
    raise ValueError("could not realize a separated distinct-size motif layout")


def _color_cells(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result.setdefault(value, []).append((r, c))
    return result


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    queue = deque([remaining.pop()])
    seen = 1
    while queue:
        r, c = queue.popleft()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in remaining:
                remaining.remove(nxt)
                queue.append(nxt)
                seen += 1
    return seen == len(cells)


def observe_overrides(grid):
    colors = _color_cells(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n": len(colors),
        "colors": sorted(colors),
        "sizes": sorted((len(cells) for cells in colors.values()), reverse=True),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty or malformed grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer colors 0..9"]
    colors = _color_cells(grid)
    errors = []
    if not 2 <= len(colors) <= 4:
        errors.append(f"expected 2..4 nonzero colors, found {len(colors)}")
    sizes = [len(cells) for cells in colors.values()]
    if len(sizes) != len(set(sizes)):
        errors.append(f"motif cell counts must be distinct: {sizes}")
    for color, cells in colors.items():
        if not _connected(cells):
            errors.append(f"color {color} is not one four-connected motif")
    occupied = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    by_pos = {(r, c): value for r, c, value in occupied}
    for r, c, value in occupied:
        for rr in range(max(0, r - 1), min(len(grid), r + 2)):
            for cc in range(max(0, c - 1), min(width, c + 2)):
                other = by_pos.get((rr, cc), value)
                if other != value:
                    errors.append(f"colors {value} and {other} touch without a background gap")
                    return errors
    return errors
