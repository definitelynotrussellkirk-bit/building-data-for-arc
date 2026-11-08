"""Expand an instruction grid using the two visible colored shape templates."""

from collections import deque


def solve(grid):
    height, width = len(grid), len(grid[0])
    templates = {}
    template_cells = set()

    for color in (6, 7):
        seen = set()
        components = []
        for row in range(height):
            for col in range(width):
                if grid[row][col] != color or (row, col) in seen:
                    continue
                component = set()
                queue = deque([(row, col)])
                seen.add((row, col))
                while queue:
                    r, c = queue.popleft()
                    component.add((r, c))
                    for nr, nc in ((r - 1, c), (r + 1, c),
                                   (r, c - 1), (r, c + 1)):
                        if (0 <= nr < height and 0 <= nc < width
                                and grid[nr][nc] == color
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
                components.append(component)

        cells = max(components, key=len)
        template_cells.update(cells)
        top = min(r for r, c in cells)
        bottom = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        templates[color] = [
            [color if (r, c) in cells else 0
             for c in range(left, right + 1)]
            for r in range(top, bottom + 1)
        ]

    instructions = {
        (r, c): grid[r][c]
        for r in range(height)
        for c in range(width)
        if 1 <= grid[r][c] <= 8 and (r, c) not in template_cells
    }
    top = min(r for r, c in instructions)
    bottom = max(r for r, c in instructions)
    left = min(c for r, c in instructions)
    right = max(c for r, c in instructions)
    tile_size = len(templates[6])
    result = [[0] * ((right - left + 1) * tile_size)
              for _ in range((bottom - top + 1) * tile_size)]

    for (r, c), code in instructions.items():
        color = 6 if code <= 4 else 7
        turns = (code - 1) % 4
        tile = templates[color]
        for _ in range(turns):
            tile = [list(row) for row in zip(*tile[::-1])]
        row_offset = (r - top) * tile_size
        col_offset = (c - left) * tile_size
        for tr, values in enumerate(tile):
            for tc, value in enumerate(values):
                result[row_offset + tr][col_offset + tc] = value

    return result
