from copy import deepcopy

_NEIGHBORS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def solve(grid):
    """Expand each eight-neighbor-isolated colored cell into a diagonal X."""
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            isolated = all(
                not (0 <= r + dr < h and 0 <= c + dc < w)
                or grid[r + dr][c + dc] == 0
                for dr, dc in _NEIGHBORS
            )
            if not isolated:
                continue
            for dr, dc in _DIAGONALS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                    out[rr][cc] = color
    return out
