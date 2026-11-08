"""Grid construction primitives.

All functions return list[list[int]] grids; in-place mutators take a
grid by reference and modify it. ARC values are 0..9.
"""
from __future__ import annotations

from typing import Sequence


Grid = list[list[int]]


def full_grid(h: int, w: int, color: int) -> Grid:
    """A fresh h×w grid filled with `color`."""
    if h <= 0 or w <= 0:
        raise ValueError(f"full_grid: invalid dims ({h},{w})")
    if not (0 <= color <= 9):
        raise ValueError(f"full_grid: color {color} not in 0..9")
    return [[color] * w for _ in range(h)]


def clone_grid(g: Grid) -> Grid:
    """Deep copy."""
    return [row[:] for row in g]


def set_cell(g: Grid, r: int, c: int, v: int) -> None:
    """In-place: assign one cell."""
    g[r][c] = v


def draw_rect(g: Grid, r: int, c: int, rh: int, rw: int, color: int) -> None:
    """In-place: paint a solid rh×rw rectangle at (r, c). Asserts bounds."""
    h, w = len(g), len(g[0]) if g else 0
    if r < 0 or c < 0 or r + rh > h or c + rw > w:
        raise ValueError(
            f"draw_rect: rect ({rh}x{rw}) at ({r},{c}) doesn't fit in grid {h}x{w}")
    for dr in range(rh):
        for dc in range(rw):
            g[r + dr][c + dc] = color


def draw_rect_outline(
    g: Grid, r: int, c: int, rh: int, rw: int, color: int
) -> None:
    """In-place: paint just the perimeter cells of an rh×rw rectangle."""
    h, w = len(g), len(g[0]) if g else 0
    if r < 0 or c < 0 or r + rh > h or c + rw > w:
        raise ValueError(
            f"draw_rect_outline: rect ({rh}x{rw}) at ({r},{c}) doesn't fit")
    for dc in range(rw):
        g[r][c + dc] = color
        g[r + rh - 1][c + dc] = color
    for dr in range(rh):
        g[r + dr][c] = color
        g[r + dr][c + rw - 1] = color


# --- Corner-pair (r1, c1, r2, c2) variants — mirror Racket vocabulary.
# Racket primitives (`draw-rect-filled`, `draw-rect-outline`) take the bbox
# corners; ~60 corpus generators have re-implemented the same shape inline as
# `_draw_frame(g, r1, c1, r2, c2, color)`. These wrappers expose the same
# vocabulary in Python so generator code matches the Racket rule it pairs with.

def fill_box(g: Grid, r1: int, c1: int, r2: int, c2: int, color: int) -> None:
    """In-place: paint the solid rectangle whose inclusive bbox is (r1,c1)-(r2,c2).
    Mirrors Racket `(draw-rect-filled g r1 c1 r2 c2 color)`."""
    if r1 > r2 or c1 > c2:
        raise ValueError(
            f"fill_box: empty rect ({r1},{c1})-({r2},{c2})")
    h = len(g)
    w = len(g[0]) if g else 0
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        raise ValueError(
            f"fill_box: rect ({r1},{c1})-({r2},{c2}) out of bounds {h}x{w}")
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g[r][c] = color


def draw_frame(g: Grid, r1: int, c1: int, r2: int, c2: int, color: int) -> None:
    """In-place: paint just the perimeter of the rect (r1,c1)-(r2,c2) (inclusive).
    Mirrors Racket `(draw-rect-outline g r1 c1 r2 c2 color)`."""
    if r1 > r2 or c1 > c2:
        raise ValueError(
            f"draw_frame: empty rect ({r1},{c1})-({r2},{c2})")
    h = len(g)
    w = len(g[0]) if g else 0
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        raise ValueError(
            f"draw_frame: rect ({r1},{c1})-({r2},{c2}) out of bounds {h}x{w}")
    for c in range(c1, c2 + 1):
        g[r1][c] = color
        g[r2][c] = color
    for r in range(r1 + 1, r2):
        g[r][c1] = color
        g[r][c2] = color


def paint_at(g: Grid, r0: int, c0: int, cells, color: int | None = None) -> None:
    """In-place: paint each `cells` offset (relative to (r0, c0)).

    If `color` is given, all cells are painted that color; cells must be
    `(dr, dc)` 2-tuples (same idiom as `paint_cells(g, cells, color)`).

    If `color` is None, cells must be `(dr, dc, v)` 3-tuples and the
    per-cell value is used (same idiom as `paint_cells(g, cells)`).

    Out-of-bounds offsets are silently skipped. Reads like the Racket
    paint-shape-at-anchor idiom."""
    h = len(g)
    w = len(g[0]) if g else 0
    for cell in cells:
        if color is not None:
            dr, dc = cell[0], cell[1]
            v = color
        else:
            dr, dc, v = cell
        r = r0 + dr
        c = c0 + dc
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = v


def paste(g: Grid, sub: Grid, r: int, c: int, *, transparent: int | None = None) -> None:
    """In-place: paste `sub` into `g` at (r, c).

    If `transparent` is set, cells in `sub` equal to that value are skipped.
    """
    h, w = len(g), len(g[0]) if g else 0
    sh, sw = len(sub), len(sub[0]) if sub else 0
    if r + sh > h or c + sw > w or r < 0 or c < 0:
        raise ValueError(
            f"paste: sub {sh}x{sw} at ({r},{c}) doesn't fit in {h}x{w}")
    for dr in range(sh):
        for dc in range(sw):
            v = sub[dr][dc]
            if transparent is not None and v == transparent:
                continue
            g[r + dr][c + dc] = v


def paint_cells(g: Grid, cells, color: int | None = None) -> None:
    """In-place: paint a list of (r, c) or (r, c, v) cells.

    If `color` is given, every cell is painted that color (the per-cell
    value, if any, is ignored). If `color` is None, each cell must be a
    3-tuple (r, c, v) and `v` is used. Out-of-bounds cells are silently
    skipped. Mirrors Racket `(paint-cells g cells [color #f])`."""
    h = len(g)
    w = len(g[0]) if g else 0
    for cell in cells:
        if color is not None:
            r, c = cell[0], cell[1]
            v = color
        else:
            r, c, v = cell
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = v


def grid_dims(g: Grid) -> tuple[int, int]:
    """(h, w). Defined for empty grids as (0, 0)."""
    return (len(g), len(g[0]) if g else 0)


def is_well_formed(g) -> bool:
    """True iff g is a list[list[int]], rectangular, dims in [1, 30],
    values in 0..9. Used by the runner's input validation."""
    if not isinstance(g, list) or not g:
        return False
    if not all(isinstance(row, list) for row in g):
        return False
    h = len(g)
    if h < 1 or h > 30:
        return False
    w = len(g[0])
    if w < 1 or w > 30:
        return False
    for row in g:
        if len(row) != w:
            return False
        for v in row:
            if not isinstance(v, int) or not (0 <= v <= 9):
                return False
    return True


# ---------------------------------------------------------------------------
# Cropping & subgrids
# ---------------------------------------------------------------------------

def crop(g: Grid, r0: int, c0: int, h: int, w: int) -> Grid:
    """Subgrid of size h × w starting at (r0, c0). Bounds are caller's
    responsibility — slicing will silently truncate if out of range."""
    return [list(row[c0:c0 + w]) for row in g[r0:r0 + h]]


def subgrid_around(g: Grid, cells) -> Grid:
    """Crop g to the bounding box of `cells` (any iterable of (r, c))."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    if not rs:
        raise ValueError("subgrid_around: empty cells")
    r1, r2 = min(rs), max(rs)
    c1, c2 = min(cs), max(cs)
    return crop(g, r1, c1, r2 - r1 + 1, c2 - c1 + 1)


# ---------------------------------------------------------------------------
# Concatenation / transformation
# ---------------------------------------------------------------------------

def concat_h(a: Grid, b: Grid) -> Grid:
    """Side-by-side; heights must match."""
    if len(a) != len(b):
        raise ValueError(f"concat_h: heights differ {len(a)} vs {len(b)}")
    return [list(ar) + list(br) for ar, br in zip(a, b)]


def concat_v(a: Grid, b: Grid) -> Grid:
    """Stack a on top of b; widths must match."""
    wa = len(a[0]) if a else 0
    wb = len(b[0]) if b else 0
    if wa != wb:
        raise ValueError(f"concat_v: widths differ {wa} vs {wb}")
    return [list(row) for row in a] + [list(row) for row in b]


def transpose(g: Grid) -> Grid:
    """Swap rows and columns."""
    if not g:
        return []
    return [list(row) for row in zip(*g)]


def rot90_cw(g: Grid) -> Grid:
    """Quarter-turn clockwise."""
    return [list(row) for row in zip(*g[::-1])]


def rot180(g: Grid) -> Grid:
    return [list(reversed(row)) for row in reversed(g)]


def rot90_ccw(g: Grid) -> Grid:
    return [list(reversed(row)) for row in zip(*g)]


def flip_lr(g: Grid) -> Grid:
    return [list(reversed(row)) for row in g]


def flip_ud(g: Grid) -> Grid:
    return [list(row) for row in reversed(g)]


def upscale_h(g: Grid, factor: int) -> Grid:
    """Each cell becomes `factor` cells horizontally."""
    return [[v for v in row for _ in range(factor)] for row in g]


def upscale_v(g: Grid, factor: int) -> Grid:
    """Each row becomes `factor` rows."""
    return [list(row) for row in g for _ in range(factor)]


def upscale(g: Grid, factor: int) -> Grid:
    return upscale_v(upscale_h(g, factor), factor)


def downscale(g: Grid, factor: int) -> Grid:
    """Sample every `factor`-th row and column."""
    return [[g[r][c] for c in range(0, len(g[0]), factor)]
            for r in range(0, len(g), factor)]


# ---------------------------------------------------------------------------
# Color operations
# ---------------------------------------------------------------------------

def replace_color(g: Grid, src: int, dst: int) -> None:
    """In-place: every src cell becomes dst."""
    h, w = len(g), len(g[0]) if g else 0
    for r in range(h):
        for c in range(w):
            if g[r][c] == src:
                g[r][c] = dst


def swap_colors(g: Grid, a: int, b: int) -> None:
    """In-place: swap colors a and b everywhere."""
    h, w = len(g), len(g[0]) if g else 0
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == a:
                g[r][c] = b
            elif v == b:
                g[r][c] = a


def iter_cells(g: Grid):
    """Yield (r, c, value) tuples row-major. The 'base' grid iterator
    that other helpers compose over."""
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            yield r, c, v


def mode_of(values, *, exclude=None):
    """Most common value in an iterable; ties broken by `min` over the
    tied values. Empty input → ValueError. The 'base' mode helper —
    `mode_color` etc. compose on top of this."""
    counts: dict = {}
    for v in values:
        if exclude is not None and v == exclude:
            continue
        counts[v] = counts.get(v, 0) + 1
    if not counts:
        raise ValueError("mode_of: empty input (after exclude)")
    best = max(counts.values())
    return min(k for k, n in counts.items() if n == best)


def palette_of(g: Grid) -> set[int]:
    """Set of colors that appear in g."""
    return {v for _, _, v in iter_cells(g)}


def mode_color(g: Grid, *, exclude: int | None = None) -> int:
    """Most common color in g; ties broken by lowest color value."""
    return mode_of((v for _, _, v in iter_cells(g)), exclude=exclude)


def color_count(g: Grid, color: int) -> int:
    return sum(1 for _, _, v in iter_cells(g) if v == color)


def dmirror(g: Grid) -> Grid:
    """Diagonal mirror (transpose, alias for `transpose`)."""
    return transpose(g)


def cmirror(g: Grid) -> Grid:
    """Anti-diagonal mirror: transpose + flip both axes."""
    return rot180(transpose(g))


# ---------------------------------------------------------------------------
# Index-set ops on grids
# ---------------------------------------------------------------------------

def paint_indices(g: Grid, indices, color: int) -> None:
    """Alias for paint_cells; kept for symmetry with helpers/indices.py
    naming. Paints (r, c) cells in `indices` to `color`. OOB skipped."""
    paint_cells(g, indices, color)


def underfill(g: Grid, color: int, indices, *, bg: int = 0) -> None:
    """In-place: paint cells from `indices` only where current value is bg."""
    h, w = len(g), len(g[0]) if g else 0
    for r, c in indices:
        if 0 <= r < h and 0 <= c < w and g[r][c] == bg:
            g[r][c] = color


# ---------------------------------------------------------------------------
# Halves / trims
# ---------------------------------------------------------------------------

def tophalf(g: Grid) -> Grid:
    """Upper half (rounded down)."""
    return [list(row) for row in g[:len(g) // 2]]


def bottomhalf(g: Grid) -> Grid:
    """Lower half (skips middle row when height is odd)."""
    return [list(row) for row in g[len(g) // 2 + len(g) % 2:]]


def lefthalf(g: Grid) -> Grid:
    if not g:
        return []
    half = len(g[0]) // 2
    return [list(row[:half]) for row in g]


def righthalf(g: Grid) -> Grid:
    if not g:
        return []
    w = len(g[0])
    start = w // 2 + w % 2
    return [list(row[start:]) for row in g]


def trim(g: Grid) -> Grid:
    """Strip 1-cell border off all four sides."""
    return [list(row[1:-1]) for row in g[1:-1]]


# ---------------------------------------------------------------------------
# Frontiers / compression
# ---------------------------------------------------------------------------

def frontier_rows(g: Grid) -> list[int]:
    """Indices of rows that are entirely a single color."""
    return [i for i, row in enumerate(g) if len(set(row)) == 1]


def frontier_cols(g: Grid) -> list[int]:
    """Indices of cols that are entirely a single color."""
    h = len(g)
    w = len(g[0]) if g else 0
    return [j for j in range(w) if len({g[i][j] for i in range(h)}) == 1]


def compress_grid(g: Grid) -> Grid:
    """Drop every entirely-uniform row and column."""
    h = len(g)
    w = len(g[0]) if g else 0
    keep_r = [i for i in range(h) if len(set(g[i])) > 1]
    keep_c = [j for j in range(w) if len({g[i][j] for i in range(h)}) > 1]
    return [[g[i][j] for j in keep_c] for i in keep_r]


# ---------------------------------------------------------------------------
# Cellwise / split / occurrences
# ---------------------------------------------------------------------------

def cellwise(a: Grid, b: Grid, fallback: int) -> Grid:
    """Cellwise: keep value where a == b, else `fallback`."""
    if len(a) != len(b) or (a and len(a[0]) != len(b[0])):
        raise ValueError("cellwise: shape mismatch")
    h = len(a)
    w = len(a[0]) if a else 0
    return [[a[r][c] if a[r][c] == b[r][c] else fallback
             for c in range(w)] for r in range(h)]


def hsplit(g: Grid, n: int) -> list[Grid]:
    """Split into n equal-width chunks (skips a 1-col separator if width
    isn't divisible by n)."""
    h = len(g)
    full_w = len(g[0]) if g else 0
    chunk_w = full_w // n
    offset = (full_w % n) != 0
    return [crop(g, 0, chunk_w * i + i * offset, h, chunk_w)
            for i in range(n)]


def vsplit(g: Grid, n: int) -> list[Grid]:
    """Split into n equal-height chunks (skips a 1-row separator if height
    isn't divisible by n)."""
    full_h = len(g)
    chunk_h = full_h // n
    w = len(g[0]) if g else 0
    offset = (full_h % n) != 0
    return [crop(g, chunk_h * i + i * offset, 0, chunk_h, w)
            for i in range(n)]


def occurrences(g: Grid, sub: Grid) -> set[tuple[int, int]]:
    """All (r, c) where `sub` appears as a sub-grid of g (top-left corner)."""
    h, w = len(g), len(g[0]) if g else 0
    sh, sw = len(sub), len(sub[0]) if sub else 0
    out: set[tuple[int, int]] = set()
    for r in range(h - sh + 1):
        for c in range(w - sw + 1):
            ok = True
            for dr in range(sh):
                for dc in range(sw):
                    if g[r + dr][c + dc] != sub[dr][dc]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                out.add((r, c))
    return out
