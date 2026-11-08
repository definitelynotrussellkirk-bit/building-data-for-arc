def solve(grid):
    """Fill zero-valued holes enclosed by magenta with azure."""
    from collections import deque

    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    visited = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in visited:
                continue
            queue = deque([(row, col)])
            visited.add((row, col))
            component = []
            touches_edge = False
            boundary = set()
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                touches_edge |= r in (0, height - 1) or c in (0, width - 1)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < height and 0 <= cc < width):
                        continue
                    if grid[rr][cc] != 0:
                        boundary.add(grid[rr][cc])
                    elif (rr, cc) not in visited:
                        visited.add((rr, cc))
                        queue.append((rr, cc))
            if not touches_edge and boundary == {6}:
                for r, c in component:
                    output[r][c] = 8
    return output
