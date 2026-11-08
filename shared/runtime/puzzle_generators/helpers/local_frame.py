"""Helpers for marker-defined local coordinate frames."""
from __future__ import annotations

Grid = list[list[int]]
Vec = tuple[int, int]
Point = tuple[int, int]

DIR4: tuple[Vec, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


def gpos(origin: Point, vx: Vec, vy: Vec, u: int, v: int) -> Point:
    """Convert local frame coordinates to a grid position."""
    r, c = origin
    return r + u * vx[0] + v * vy[0], c + u * vx[1] + v * vy[1]


def frame_cells(origin: Point, vx: Vec, vy: Vec) -> list[Point]:
    """Return marker cells for local (0,0), (1,0), and (0,1)."""
    return [origin, gpos(origin, vx, vy, 1, 0), gpos(origin, vx, vy, 0, 1)]


def draw_marker_frame(grid: Grid, origin: Point, vx: Vec, vy: Vec, colors: tuple[int, int, int]) -> None:
    """Draw a three-color marker frame."""
    for (r, c), color in zip(frame_cells(origin, vx, vy), colors):
        grid[r][c] = color


def choose_frame(
    rng,
    h: int,
    w: int,
    local_points: list[tuple[int, int]] | tuple[tuple[int, int], ...],
    *,
    forbidden: set[Point] | None = None,
) -> tuple[Point, Vec, Vec]:
    """Choose a frame where all listed local points fit and avoid forbidden cells."""
    blocked = forbidden or set()
    required = set(local_points) | {(0, 0), (1, 0), (0, 1)}
    options: list[tuple[Point, Vec, Vec]] = []
    for r in range(h):
        for c in range(w):
            origin = (r, c)
            for vx in DIR4:
                for vy in DIR4:
                    if vx[0] * vy[0] + vx[1] * vy[1] != 0:
                        continue
                    cells = [gpos(origin, vx, vy, u, v) for u, v in required]
                    if any(rr < 0 or cc < 0 or rr >= h or cc >= w for rr, cc in cells):
                        continue
                    if any(cell in blocked for cell in cells):
                        continue
                    options.append((origin, vx, vy))
    if not options:
        raise ValueError("choose_frame: no fitting frame")
    return rng.choice(options)
