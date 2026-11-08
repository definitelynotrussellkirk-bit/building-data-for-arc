"""Hodel-style "objects" — sets of (color, (r, c)) tuples that preserve
per-cell coloring, so you can shift / recolor / paint colored shapes
without separately tracking which color went where.

We use plain `set[(value, (r, c))]`. Where Hodel/re-arc passes patches
as either an `Indices` set or an `Object` set interchangeably, our
`to_indices` accepts both.
"""
from __future__ import annotations

from typing import Iterable

from .indices import (
    Cell, Indices, adjacent_patches, center_of_mass, neighbors_4,
    neighbors_8, shift_cells, vmatching,
)


ColoredCell = tuple[int, Cell]
Object = set[ColoredCell]


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def as_object(g) -> Object:
    """Whole grid → object (every cell with its color)."""
    return {(v, (r, c)) for r, row in enumerate(g)
            for c, v in enumerate(row)}


def to_object(indices: Iterable[Cell], g) -> Object:
    """Indices + grid → object (read colors from g, drop OOB)."""
    h, w = len(g), len(g[0]) if g else 0
    return {(g[r][c], (r, c)) for r, c in indices
            if 0 <= r < h and 0 <= c < w}


def to_indices(patch: Iterable) -> Indices:
    """Extract (r, c) positions from either an object or an index set."""
    out: Indices = set()
    for x in patch:
        # Object cell: (value, (r, c)). Index cell: (r, c).
        if isinstance(x, tuple) and len(x) == 2 and isinstance(x[1], tuple):
            out.add(x[1])
        else:
            out.add(x)
    return out


def recolor(color: int, patch: Iterable) -> Object:
    """Build a mono-colored object from a patch (any iterable of cells)."""
    return {(color, idx) for idx in to_indices(patch)}


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def shift_obj(obj: Iterable[ColoredCell], offset: Cell) -> Object:
    dr, dc = offset
    return {(v, (r + dr, c + dc)) for v, (r, c) in obj}


def normalize_obj(obj: Iterable[ColoredCell]) -> Object:
    """Translate so min row and min col over object's cells are 0."""
    cells = list(obj)
    if not cells:
        return set()
    rs = [r for _, (r, _) in cells]
    cs = [c for _, (_, c) in cells]
    rmin, cmin = min(rs), min(cs)
    return {(v, (r - rmin, c - cmin)) for v, (r, c) in cells}


# ---------------------------------------------------------------------------
# Painting
# ---------------------------------------------------------------------------

def paint(g, obj: Iterable[ColoredCell]) -> None:
    """In-place: paint object's colored cells onto g. OOB skipped."""
    h, w = len(g), len(g[0]) if g else 0
    for v, (r, c) in obj:
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = v


def underpaint(g, obj: Iterable[ColoredCell], *, bg: int = 0) -> None:
    """In-place: paint object's cells only where current value == bg."""
    h, w = len(g), len(g[0]) if g else 0
    for v, (r, c) in obj:
        if 0 <= r < h and 0 <= c < w and g[r][c] == bg:
            g[r][c] = v


def cover(g, patch: Iterable, *, bg: int | None = None) -> None:
    """In-place: clear patch cells (set to bg, default = mostcolor)."""
    from .grid import mode_color
    if bg is None:
        bg = mode_color(g)
    h, w = len(g), len(g[0]) if g else 0
    for r, c in to_indices(patch):
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = bg


def move_obj(g, obj: Iterable[ColoredCell], offset: Cell, *, bg: int | None = None) -> None:
    """In-place: erase obj's current cells, paint shifted version."""
    cover(g, obj, bg=bg)
    paint(g, shift_obj(obj, offset))


# ---------------------------------------------------------------------------
# Object-level introspection
# ---------------------------------------------------------------------------

def obj_color(obj: Iterable[ColoredCell]) -> int:
    """Any color of obj's cells (assumes mono-colored)."""
    for v, _ in obj:
        return v
    raise ValueError("obj_color: empty object")


def obj_palette(obj: Iterable[ColoredCell]) -> set[int]:
    return {v for v, _ in obj}


def obj_size(obj: Iterable[ColoredCell]) -> int:
    return len(set(obj))


def gravitate(source: Iterable, destination: Iterable) -> Cell:
    """Manhattan offset (dr, dc) to move `source` toward `destination`
    until they're 4-adjacent (or 42 steps, whichever comes first).
    Returns (0, 0) if already adjacent."""
    src = to_indices(source)
    dst = to_indices(destination)
    if not src or not dst:
        return (0, 0)
    si, sj = center_of_mass(src)
    di, dj = center_of_mass(dst)
    i, j = 0, 0
    if vmatching(src, dst):
        i = 1 if si < di else -1
    else:
        j = 1 if sj < dj else -1
    direction = (i, j)
    grav_i, grav_j = i, j
    cells = src
    for _ in range(42):
        if adjacent_patches(cells, dst):
            break
        cells = shift_cells(cells, direction)
        grav_i += i
        grav_j += j
    return (grav_i - i, grav_j - j)


# ---------------------------------------------------------------------------
# Connected components
# ---------------------------------------------------------------------------

def find_objects(
    g, *,
    univalued: bool = False,
    diagonal: bool = False,
    without_bg: bool = True,
    bg: int | None = None,
) -> list[Object]:
    """Find connected components on g (generator-side semantics).

    Contract — see docs/OWNERSHIP.md row "Connected components — Python
    (generator side)":
      - Multicolor by default (univalued=False): different non-bg
        colors merge if adjacent, just like `objects-multicolor` in
        the Racket prelude.
      - bg=None → inferred as `mode_color(g)`. Pass `bg=0` explicitly
        for the constant-bg semantics arc_repl.grid_ops uses.
      - Connectivity: 4 (default) or 8 (diagonal=True).
      - Return: list of `Object`, each a set of `(color, (r, c))`
        tuples (see `Object` typedef in this module).

    NOT the same as `arc_repl.grid_ops.find_objects`, which is always
    univalued, defaults bg=0 (no inference), and returns a list of
    dicts. The two return shapes are not interchangeable — convert
    explicitly with `as_object` / `to_object` if you need to cross.
    """
    from .grid import mode_color
    h, w = len(g), len(g[0]) if g else 0
    if without_bg and bg is None:
        bg = mode_color(g)
    nbr = neighbors_8 if diagonal else neighbors_4
    visited: set[Cell] = set()
    out: list[Object] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in visited:
                continue
            v = g[r][c]
            if without_bg and v == bg:
                continue
            obj: Object = set()
            anchor = v
            stack = [(r, c)]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                cr, cc = cur
                if not (0 <= cr < h and 0 <= cc < w):
                    continue
                cv = g[cr][cc]
                if without_bg and cv == bg:
                    continue
                if univalued and cv != anchor:
                    continue
                visited.add(cur)
                obj.add((cv, cur))
                stack.extend(nbr(cur))
            if obj:
                out.append(obj)
    return out


# Explicit alias for `find_objects` so generator authors can be unambiguous
# at the import site and avoid confusion with `arc_repl.grid_ops.find_objects`
# (which has different defaults — see docs/OWNERSHIP.md). This is a name
# alias, not a behavior change.
find_generator_objects = find_objects


def partition_by_color(g) -> dict[int, Object]:
    """Color → object containing every cell of that color (one bucket per color)."""
    out: dict[int, Object] = {}
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            out.setdefault(v, set()).add((v, (r, c)))
    return out


def fg_partition(g, *, bg: int | None = None) -> dict[int, Object]:
    """Like partition_by_color but excludes the bg color."""
    from .grid import mode_color
    if bg is None:
        bg = mode_color(g)
    parts = partition_by_color(g)
    parts.pop(bg, None)
    return parts
