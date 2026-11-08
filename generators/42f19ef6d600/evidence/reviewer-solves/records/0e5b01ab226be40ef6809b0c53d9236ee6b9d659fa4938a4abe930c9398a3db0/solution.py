from collections import Counter


def solve(grid):
    """Mark exposed sides of cells that participate in an orthogonal turn."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    output = [row[:] for row in grid]

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background:
                continue

            same = set()
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == color:
                    same.add((dr, dc))

            has_turn = any(
                vertical in same and horizontal in same
                for vertical in ((-1, 0), (1, 0))
                for horizontal in ((0, -1), (0, 1))
            )
            if not has_turn:
                continue

            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == background:
                    output[nr][nc] = 2

    return output
