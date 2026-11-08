"""Visible-example solution authored for the exposed post-repair episode."""

def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if any(len(row) != width for row in grid):
        raise ValueError("A rectangular grid is required")
    answer = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in visited:
                continue
            frontier = [(row, column)]
            visited.add((row, column))
            cells = []
            while frontier:
                r, c = frontier.pop()
                cells.append((r, c))
                for rr, cc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in visited
                            and grid[rr][cc] == color):
                        visited.add((rr, cc))
                        frontier.append((rr, cc))
            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            answer[(top + bottom) // 2][(left + right) // 2] = color
    return answer
