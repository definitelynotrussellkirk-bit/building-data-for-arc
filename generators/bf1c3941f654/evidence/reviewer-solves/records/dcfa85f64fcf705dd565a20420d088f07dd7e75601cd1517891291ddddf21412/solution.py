from collections import deque


def solve(grid):
    """Recolor marker 2 -> 4 exactly when it lies inside a closed 1-frame."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    seen = set()
    frames = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in component)
            bottom = max(r for r, _ in component)
            left = min(c for _, c in component)
            right = max(c for _, c in component)

            # Accept only a complete axis-aligned rectangular border.
            border = {
                (r, c)
                for r in range(top, bottom + 1)
                for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)
            }
            if border and all(grid[r][c] == 1 for r, c in border):
                frames.append((top, bottom, left, right))

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2 and any(
                top < row < bottom and left < col < right
                for top, bottom, left, right in frames
            ):
                out[row][col] = 4

    return out
