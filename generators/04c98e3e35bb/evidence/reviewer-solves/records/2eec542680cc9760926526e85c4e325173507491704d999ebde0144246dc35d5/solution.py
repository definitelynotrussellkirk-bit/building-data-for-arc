def solve(grid):
    """Recolor monochromatic components by whether they meet a grid edge."""
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    result = [list(row) for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            frontier = [(row, col)]
            seen.add((row, col))
            touches_edge = False
            while frontier:
                r, c = frontier.pop()
                component.append((r, c))
                if r == 0 or r == height - 1 or c == 0 or c == width - 1:
                    touches_edge = True
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        frontier.append((nr, nc))

            replacement = 2 if touches_edge else 8
            for r, c in component:
                result[r][c] = replacement

    return result
