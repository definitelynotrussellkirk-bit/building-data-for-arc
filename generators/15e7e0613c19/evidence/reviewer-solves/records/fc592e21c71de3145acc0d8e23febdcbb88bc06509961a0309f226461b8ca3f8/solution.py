def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    pieces = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            top = min(r for r, c in cells)
            left = min(c for r, c in cells)
            ph = max(r for r, c in cells) - top + 1
            pw = max(c for r, c in cells) - left + 1
            crop = [[0] * pw for _ in range(ph)]
            for r, c in cells:
                crop[r - top][c - left] = color
            pieces.append(((len(cells), ph, pw, color), crop))
    if not pieces:
        return [[0]]
    pieces.sort(key=lambda item: item[0])
    output_height = max(len(crop) for key, crop in pieces)
    output_width = sum(len(crop[0]) for key, crop in pieces) + len(pieces) - 1
    output = [[0] * output_width for _ in range(output_height)]
    offset = 0
    for key, crop in pieces:
        for r, row in enumerate(crop):
            output[r][offset:offset + len(row)] = row
        offset += len(crop[0]) + 1
    return output
