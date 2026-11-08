"""Visible-example solution: rank connected pieces, recolor, crop, and pack."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    palette = [color for color in grid[0] if color != 0]
    seen = set()
    pieces = []
    for row in range(1, height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (r + dr, c + dc)
                    nr, nc = neighbor
                    if (1 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 1 and neighbor not in seen):
                        seen.add(neighbor)
                        stack.append(neighbor)
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            pieces.append((len(cells), top, left, bottom, right, cells))
    pieces.sort(key=lambda piece: piece[:3])
    if len(pieces) != len(palette):
        raise ValueError("Expected one palette color per body piece")
    out_height = max(bottom - top + 1 for _, top, _, bottom, _, _ in pieces)
    out_width = sum(right - left + 1 for _, _, left, _, right, _ in pieces) + len(pieces) - 1
    output = [[0] * out_width for _ in range(out_height)]
    offset = 0
    for color, (_, top, left, _, right, cells) in zip(palette, pieces):
        for row, col in cells:
            output[row - top][offset + col - left] = color
        offset += right - left + 2
    return output
