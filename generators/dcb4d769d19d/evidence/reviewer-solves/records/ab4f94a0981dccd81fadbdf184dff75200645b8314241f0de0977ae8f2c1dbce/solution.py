from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand every orthogonally isolated red (2) cell into a green (4) plus."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [row[:] for row in grid]

    isolated: list[tuple[int, int]] = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 2:
                continue
            has_red_neighbor = any(
                0 <= rr < rows and 0 <= cc < cols and grid[rr][cc] == 2
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            )
            if not has_red_neighbor:
                isolated.append((r, c))

    for r, c in isolated:
        for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= rr < rows and 0 <= cc < cols:
                out[rr][cc] = 4
    return out
