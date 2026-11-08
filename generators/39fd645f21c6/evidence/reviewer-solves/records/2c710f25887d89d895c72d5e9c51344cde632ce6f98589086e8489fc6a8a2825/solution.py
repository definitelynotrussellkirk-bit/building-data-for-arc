from __future__ import annotations

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    out = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in _CARDINAL:
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            out.append((color, tuple(cells)))
    return out


def _normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return {(row - row0, col - col0) for row, col in cells}


def _signature(cells):
    shape = _normalize(cells)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1

    # Count background regions enclosed strictly inside the shape's bounding box.
    seen = set()
    holes = 0
    for row0 in range(height):
        for col0 in range(width):
            if (row0, col0) in shape or (row0, col0) in seen:
                continue
            region = []
            stack = [(row0, col0)]
            seen.add((row0, col0))
            while stack:
                row, col = stack.pop()
                region.append((row, col))
                for dr, dc in _CARDINAL:
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in shape
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            if all(
                0 < row < height - 1 and 0 < col < width - 1
                for row, col in region
            ):
                holes += 1

    horizontal = all((height - 1 - row, col) in shape for row, col in shape)
    vertical = all((row, width - 1 - col) in shape for row, col in shape)
    symmetry_class = 3 if horizontal and vertical else 1 if horizontal else 2 if vertical else 0
    return (len(shape), holes, symmetry_class)


def solve(grid):
    components = _components(grid)
    blue = next(cells for color, cells in components if color == 1)
    wanted = _signature(blue)
    answer = [row[:] for row in grid]
    for color, cells in components:
        if color != 1 and _signature(cells) == wanted:
            for row, col in cells:
                answer[row][col] = 8
    return answer
