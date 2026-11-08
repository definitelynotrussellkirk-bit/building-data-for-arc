"""Tile-by-tile transform inferred from this episode's visible pairs."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    horizontal = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    vertical = [c for c in range(width) if all(row[c] == 9 for row in grid)]
    r_bounds = [-1, *horizontal, height]
    c_bounds = [-1, *vertical, width]
    answer = [[9 if value == 9 else 0 for value in row] for row in grid]
    for r_previous, r_next in zip(r_bounds, r_bounds[1:]):
        for c_previous, c_next in zip(c_bounds, c_bounds[1:]):
            top, left = r_previous + 1, c_previous + 1
            tile = [row[left:c_next] for row in grid[top:r_next]]
            active = any(value == 3 for row in tile for value in row)
            motif = [[8 if value == 2 else 0 for value in row] for row in tile]
            if active:
                motif = [list(row) for row in zip(*motif[::-1])]
            for r, row in enumerate(motif):
                answer[top + r][left:left + len(row)] = row
    return answer
