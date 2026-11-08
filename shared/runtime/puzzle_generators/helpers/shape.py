"""Shape primitives — cell-set construction and normalization."""
from __future__ import annotations

from typing import Sequence

Cell = tuple[int, int]
Cells = list[Cell]


def rect_cells(rh: int, rw: int) -> Cells:
    """All cells of a solid rh×rw rectangle, origin (0, 0). Row-major."""
    return [(r, c) for r in range(rh) for c in range(rw)]


def rect_outline_cells(rh: int, rw: int) -> Cells:
    """Perimeter cells of an rh×rw rectangle. Row-major, no duplicates."""
    out: Cells = []
    for c in range(rw):
        out.append((0, c))
        if rh > 1:
            out.append((rh - 1, c))
    for r in range(1, rh - 1):
        out.append((r, 0))
        if rw > 1:
            out.append((r, rw - 1))
    return out


def cross_cells(arm: int) -> Cells:
    """A plus-sign shape with arms of length `arm`. Origin at center."""
    out: Cells = [(0, 0)]
    for k in range(1, arm + 1):
        out.extend([(-k, 0), (k, 0), (0, -k), (0, k)])
    return out


def normalize(cells: Sequence[Cell]) -> Cells:
    """Translate so min row and min column are 0. Stable order."""
    if not cells:
        return []
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    rmin, cmin = min(rs), min(cs)
    return [(r - rmin, c - cmin) for r, c in cells]


def shape_dims(cells: Sequence[Cell]) -> tuple[int, int]:
    """Bounding-box (h, w) of a cell set. (0, 0) for empty.

    Delegates to `puzzle_generators.helpers.indices.bbox` to keep one
    canonical bbox implementation."""
    if not cells:
        return (0, 0)
    from .indices import bbox  # local import: shape ↔ indices avoid cycle
    r1, c1, r2, c2 = bbox(cells)
    return (r2 - r1 + 1, c2 - c1 + 1)


# --- Common shape literals (named so multiple generators can share) ---

# 3-cell L-trominoes — 4 orientations of an L in a 2×2 bbox.
# Named by which corner is *missing* (NE = top-right missing, etc.).
L_TROMINO_NE: Cells = [(0, 0), (1, 0), (1, 1)]   # missing top-right
L_TROMINO_NW: Cells = [(0, 1), (1, 0), (1, 1)]   # missing top-left
L_TROMINO_SE: Cells = [(0, 0), (0, 1), (1, 0)]   # missing bottom-right
L_TROMINO_SW: Cells = [(0, 0), (0, 1), (1, 1)]   # missing bottom-left
L_TROMINOES: tuple[Cells, ...] = (
    L_TROMINO_NE, L_TROMINO_NW, L_TROMINO_SE, L_TROMINO_SW)

# 2×2 solid square (4 cells).
SQUARE_2X2: Cells = [(0, 0), (0, 1), (1, 0), (1, 1)]

# 5-cell plus sign (cross with arm length 1), origin at top-left of 3×3 bbox.
PLUS_5: Cells = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]

# 3-cell straight lines in 1×3 / 3×1 bboxes.
H_LINE_3: Cells = [(0, 0), (0, 1), (0, 2)]
V_LINE_3: Cells = [(0, 0), (1, 0), (2, 0)]

# T-tetromino (4 cells, 2×3 bbox, top row + middle of row below).
T_TETROMINO: Cells = [(0, 0), (0, 1), (0, 2), (1, 1)]

# 3×3 hollow ring (8 cells, the 3×3 bbox minus its center).
RING_3X3: Cells = [(0, 0), (0, 1), (0, 2),
                   (1, 0),         (1, 2),
                   (2, 0), (2, 1), (2, 2)]

# 4 cardinal direction-deltas (used by neighbour-walks).
CARDINAL_DELTAS: Cells = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIAGONAL_DELTAS: Cells = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ALL_8_DELTAS: Cells = CARDINAL_DELTAS + DIAGONAL_DELTAS
