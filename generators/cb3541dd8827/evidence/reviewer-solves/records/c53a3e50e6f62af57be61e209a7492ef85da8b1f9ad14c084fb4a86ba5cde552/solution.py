from collections import deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                rr, cc = queue.popleft()
                component.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield component


def _rectangular_frames(grid):
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        for component in _components(grid, color):
            rows = [row for row, _ in component]
            cols = [col for _, col in component]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            if bottom - top < 2 or right - left < 2:
                continue
            perimeter = {
                (row, col)
                for row in range(top, bottom + 1)
                for col in range(left, right + 1)
                if row in (top, bottom) or col in (left, right)
            }
            if component == perimeter:
                yield top, bottom, left, right, color


def solve(grid):
    """Fill each monochrome rectangular frame with its unique interior seed."""
    output = [list(row) for row in grid]
    for top, bottom, left, right, frame_color in _rectangular_frames(grid):
        seed_colors = {
            grid[row][col]
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] not in (0, frame_color)
        }
        if len(seed_colors) != 1:
            continue
        seed_color = next(iter(seed_colors))
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = seed_color
    return output
