from collections import deque


def solve(grid):
    """Fill the interior of each complete blue component measuring 4 by 4."""
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    seen = set()
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 1 or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] == 1 and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            top = min(r for r, c in cells)
            bottom = max(r for r, c in cells)
            left = min(c for r, c in cells)
            right = max(c for r, c in cells)
            if bottom - top != 3 or right - left != 3:
                continue
            border = {(r, c) for r in range(top, bottom+1)
                      for c in range(left, right+1)
                      if r in (top, bottom) or c in (left, right)}
            if set(cells) == border:
                for r in range(top+1, bottom):
                    for c in range(left+1, right):
                        output[r][c] = 2
    return output
