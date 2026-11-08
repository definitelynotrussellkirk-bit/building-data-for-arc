from __future__ import annotations

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                here = stack.pop()
                cells.append(here)
                for dr, dc in _DIR4:
                    nxt = (here[0] + dr, here[1] + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            objects.append((len(cells), min(r for r, _ in cells), min(c for _, c in cells), cells))
    objects.sort(key=lambda obj: (-obj[0], obj[1], obj[2]))
    output = [row[:] for row in grid]
    if objects:
        target = objects[1] if len(objects) >= 2 else objects[0]
        for row, col in target[3]:
            output[row][col] = 8
    return output
