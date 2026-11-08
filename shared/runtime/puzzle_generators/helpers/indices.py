"""Operations on sets of (r, c) cell indices.

Native Python alternatives to Hodel/re-arc DSL operations on patches:
asindices, ofcolor, connect, shift, normalize, bbox, box, inbox,
outbox, backdrop, delta, neighbors, manhattan, hmatching, etc.

Index sets are plain `set[tuple[int, int]]`. We use builtin set
operators (`|`, `&`, `-`, `<=`) directly — no Hodel-style frozenset
wrapping needed.
"""
from __future__ import annotations

from typing import Iterable

Cell = tuple[int, int]
Indices = set[Cell]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def all_indices(h: int, w: int) -> Indices:
    """Every (r, c) of an h x w grid."""
    return {(r, c) for r in range(h) for c in range(w)}


def of_color(g, color: int) -> Indices:
    """All (r, c) where g[r][c] == color."""
    return {(r, c) for r, row in enumerate(g)
            for c, v in enumerate(row) if v == color}


def connect(a: Cell, b: Cell) -> Indices:
    """Cells along the orthogonal/45-deg-diagonal line from a to b
    (inclusive). Empty when a and b are not aligned."""
    ar, ac = a
    br, bc = b
    if ar == br:
        s, e = min(ac, bc), max(ac, bc)
        return {(ar, c) for c in range(s, e + 1)}
    if ac == bc:
        s, e = min(ar, br), max(ar, br)
        return {(r, ac) for r in range(s, e + 1)}
    if br - ar == bc - ac:  # main-diagonal
        rs, re_ = min(ar, br), max(ar, br)
        cs = ac if ar < br else bc
        return {(rs + k, cs + k) for k in range(re_ - rs + 1)}
    if br - ar == ac - bc:  # anti-diagonal
        rs, re_ = min(ar, br), max(ar, br)
        cs = ac if ar < br else bc
        return {(rs + k, cs - k) for k in range(re_ - rs + 1)}
    return set()


def shoot(start: Cell, direction: Cell, *, distance: int = 42) -> Indices:
    """Line of `distance + 1` cells starting at start, stepping by
    direction. Inclusive of start. Off-grid cells are NOT filtered;
    use `in_bounds` to clip."""
    dr, dc = direction
    return {(start[0] + k * dr, start[1] + k * dc)
            for k in range(distance + 1)}


# ---------------------------------------------------------------------------
# Translation / normalization
# ---------------------------------------------------------------------------

def shift_cells(cells: Iterable[Cell], offset: Cell) -> Indices:
    dr, dc = offset
    return {(r + dr, c + dc) for r, c in cells}


def normalize_to_origin(cells: Iterable[Cell]) -> Indices:
    """Shift so min row and min col are 0."""
    cs = list(cells)
    if not cs:
        return set()
    rmin = min(r for r, _ in cs)
    cmin = min(c for _, c in cs)
    return {(r - rmin, c - cmin) for r, c in cs}


# ---------------------------------------------------------------------------
# Bounding box / corners
# ---------------------------------------------------------------------------

def bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    """(r1, c1, r2, c2) inclusive bbox. Empty input → (0, 0, -1, -1)."""
    cs = list(cells)
    if not cs:
        return (0, 0, -1, -1)
    rs = [r for r, _ in cs]
    cols = [c for _, c in cs]
    return (min(rs), min(cols), max(rs), max(cols))


def uppermost(cells: Iterable[Cell]) -> int:
    return min(r for r, _ in cells)


def lowermost(cells: Iterable[Cell]) -> int:
    return max(r for r, _ in cells)


def leftmost(cells: Iterable[Cell]) -> int:
    return min(c for _, c in cells)


def rightmost(cells: Iterable[Cell]) -> int:
    return max(c for _, c in cells)


def ulcorner(cells: Iterable[Cell]) -> Cell:
    cs = list(cells)
    return (uppermost(cs), leftmost(cs))


def urcorner(cells: Iterable[Cell]) -> Cell:
    cs = list(cells)
    return (uppermost(cs), rightmost(cs))


def llcorner(cells: Iterable[Cell]) -> Cell:
    cs = list(cells)
    return (lowermost(cs), leftmost(cs))


def lrcorner(cells: Iterable[Cell]) -> Cell:
    cs = list(cells)
    return (lowermost(cs), rightmost(cs))


def corners(cells: Iterable[Cell]) -> Indices:
    cs = list(cells)
    return {ulcorner(cs), urcorner(cs), llcorner(cs), lrcorner(cs)}


def patch_dims(cells: Iterable[Cell]) -> tuple[int, int]:
    """(h, w) of bbox. (0, 0) for empty."""
    cs = list(cells)
    if not cs:
        return (0, 0)
    r1, c1, r2, c2 = bbox(cs)
    return (r2 - r1 + 1, c2 - c1 + 1)


def patch_height(cells: Iterable[Cell]) -> int:
    return patch_dims(cells)[0]


def patch_width(cells: Iterable[Cell]) -> int:
    return patch_dims(cells)[1]


def center_of_mass(cells: Iterable[Cell]) -> Cell:
    cs = list(cells)
    n = len(cs)
    if n == 0:
        return (0, 0)
    return (sum(r for r, _ in cs) // n,
            sum(c for _, c in cs) // n)


# ---------------------------------------------------------------------------
# Outline / fill of a bbox
# ---------------------------------------------------------------------------

def backdrop(cells: Iterable[Cell]) -> Indices:
    """All cells in the bbox of `cells`, inclusive."""
    cs = list(cells)
    if not cs:
        return set()
    r1, c1, r2, c2 = bbox(cs)
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def delta(cells: Iterable[Cell]) -> Indices:
    """Cells in bbox but NOT in the patch."""
    cs = set(cells)
    return backdrop(cs) - cs


def box_outline(cells: Iterable[Cell]) -> Indices:
    """The bbox perimeter (corners + edges)."""
    cs = list(cells)
    if not cs:
        return set()
    r1, c1, r2, c2 = bbox(cs)
    out = set()
    for c in range(c1, c2 + 1):
        out.add((r1, c))
        out.add((r2, c))
    for r in range(r1, r2 + 1):
        out.add((r, c1))
        out.add((r, c2))
    return out


def inbox(cells: Iterable[Cell]) -> Indices:
    """One step inside the bbox perimeter."""
    cs = list(cells)
    if not cs:
        return set()
    r1, c1, r2, c2 = bbox(cs)
    r1, r2 = r1 + 1, r2 - 1
    c1, c2 = c1 + 1, c2 - 1
    if r2 < r1 or c2 < c1:
        return set()
    out = set()
    for c in range(c1, c2 + 1):
        out.add((r1, c))
        out.add((r2, c))
    for r in range(r1, r2 + 1):
        out.add((r, c1))
        out.add((r, c2))
    return out


def outbox(cells: Iterable[Cell]) -> Indices:
    """One step outside the bbox perimeter."""
    cs = list(cells)
    if not cs:
        return set()
    r1, c1, r2, c2 = bbox(cs)
    r1 -= 1
    r2 += 1
    c1 -= 1
    c2 += 1
    out = set()
    for c in range(c1, c2 + 1):
        out.add((r1, c))
        out.add((r2, c))
    for r in range(r1, r2 + 1):
        out.add((r, c1))
        out.add((r, c2))
    return out


# ---------------------------------------------------------------------------
# Neighbors
# ---------------------------------------------------------------------------

def neighbors_4(loc: Cell) -> Indices:
    r, c = loc
    return {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}


def neighbors_diag(loc: Cell) -> Indices:
    r, c = loc
    return {(r - 1, c - 1), (r - 1, c + 1),
            (r + 1, c - 1), (r + 1, c + 1)}


def neighbors_8(loc: Cell) -> Indices:
    return neighbors_4(loc) | neighbors_diag(loc)


def neighborhood_4(cells: Iterable[Cell]) -> Indices:
    """All 4-conn neighbors of any cell in `cells`, EXCLUDING the cells
    themselves. Useful for building "halo" bands around a patch."""
    cs = set(cells)
    out: set[Cell] = set()
    for cell in cs:
        out |= neighbors_4(cell)
    return out - cs


def neighborhood_8(cells: Iterable[Cell]) -> Indices:
    cs = set(cells)
    out: set[Cell] = set()
    for cell in cs:
        out |= neighbors_8(cell)
    return out - cs


# ---------------------------------------------------------------------------
# Distance / relations
# ---------------------------------------------------------------------------

def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def manhattan_patches(a: Iterable[Cell], b: Iterable[Cell]) -> int:
    """Closest manhattan distance between any cell of a and any of b."""
    a = list(a)
    b = list(b)
    return min(manhattan(p, q) for p in a for q in b)


def adjacent_patches(a: Iterable[Cell], b: Iterable[Cell]) -> bool:
    return manhattan_patches(a, b) == 1


def hmatching(a: Iterable[Cell], b: Iterable[Cell]) -> bool:
    """True if a and b share at least one row."""
    return len({r for r, _ in a} & {r for r, _ in b}) > 0


def vmatching(a: Iterable[Cell], b: Iterable[Cell]) -> bool:
    """True if a and b share at least one column."""
    return len({c for _, c in a} & {c for _, c in b}) > 0


def bordering(cells: Iterable[Cell], h: int, w: int) -> bool:
    """True if the patch touches any of the 4 grid borders."""
    cs = list(cells)
    if not cs:
        return False
    r1, c1, r2, c2 = bbox(cs)
    return r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1


# ---------------------------------------------------------------------------
# Bounds clipping
# ---------------------------------------------------------------------------

def in_bounds(cells: Iterable[Cell], h: int, w: int) -> Indices:
    return {(r, c) for r, c in cells if 0 <= r < h and 0 <= c < w}


def all_in_bounds(cells: Iterable[Cell], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


# ---------------------------------------------------------------------------
# Shape predicates
# ---------------------------------------------------------------------------

def is_square(cells: Iterable[Cell]) -> bool:
    cs = list(cells)
    if not cs:
        return False
    h, w = patch_dims(cs)
    return h == w and len(set(cs)) == h * w


def is_vline(cells: Iterable[Cell]) -> bool:
    cs = list(cells)
    if not cs:
        return False
    h, w = patch_dims(cs)
    return w == 1 and len(set(cs)) == h


def is_hline(cells: Iterable[Cell]) -> bool:
    cs = list(cells)
    if not cs:
        return False
    h, w = patch_dims(cs)
    return h == 1 and len(set(cs)) == w


# ---------------------------------------------------------------------------
# Center / relative position
# ---------------------------------------------------------------------------

def center(cells: Iterable[Cell]) -> Cell:
    """Cell at the geometric center of the bbox: (r1 + h//2, c1 + w//2)."""
    cs = list(cells)
    if not cs:
        return (0, 0)
    r1, c1, r2, c2 = bbox(cs)
    return (r1 + (r2 - r1 + 1) // 2, c1 + (c2 - c1 + 1) // 2)


def position(a: Iterable[Cell], b: Iterable[Cell]) -> Cell:
    """Relative direction (dr, dc) ∈ {-1, 0, 1}² from a to b."""
    ai, aj = center(a)
    bi, bj = center(b)
    if ai == bi:
        return (0, 1 if aj < bj else -1)
    if aj == bj:
        return (1 if ai < bi else -1, 0)
    if ai < bi:
        return (1, 1 if aj < bj else -1)
    return (-1, 1 if aj < bj else -1)


# ---------------------------------------------------------------------------
# Full-row / full-col index lines
# ---------------------------------------------------------------------------

def hfrontier_indices(row: int, w: int) -> Indices:
    """All cells in row `row`, width w."""
    return {(row, c) for c in range(w)}


def vfrontier_indices(col: int, h: int) -> Indices:
    """All cells in col `col`, height h."""
    return {(r, col) for r in range(h)}
