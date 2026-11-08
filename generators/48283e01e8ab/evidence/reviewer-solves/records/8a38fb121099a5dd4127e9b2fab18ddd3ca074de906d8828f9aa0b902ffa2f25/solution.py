"""Solution inferred from visible examples, with earlier authoring exposure disclosed."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    visited = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 6 or (row, col) in visited:
                continue
            pending, cells = [(row, col)], []
            visited.add((row, col))
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 6 and (rr, cc) not in visited:
                        visited.add((rr, cc))
                        pending.append((rr, cc))
            size = len(cells)
            if size == 3:
                straight = len({r for r, _ in cells}) == 1 or len({c for _, c in cells}) == 1
                color = 2 if straight else 4
            else:
                color = {2: 9, 4: 8, 5: 3, 6: 5}.get(size, 6)
            for r, c in cells:
                output[r][c] = color
    return output
