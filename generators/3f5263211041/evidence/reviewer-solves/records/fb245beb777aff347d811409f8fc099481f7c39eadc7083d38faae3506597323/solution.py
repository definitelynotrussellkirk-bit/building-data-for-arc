"""Visible-example solution: select, transform, and concatenate framed sprites."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    visited = set()
    sprites = {}
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 9 or (row, col) in visited:
                continue
            stack = [(row, col)]
            visited.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 9 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            top, bottom = min(r for r, c in cells), max(r for r, c in cells)
            left, right = min(c for r, c in cells), max(c for r, c in cells)
            labels = [grid[top-1][c] for c in range(left, right+1) if top and grid[top-1][c] not in (0, 9)]
            if len(labels) != 1:
                raise ValueError('Expected one label above each frame')
            occupied = [(r, c) for r in range(top+1, bottom) for c in range(left+1, right) if grid[r][c] != 0]
            r0, r1 = min(r for r, c in occupied), max(r for r, c in occupied)
            c0, c1 = min(c for r, c in occupied), max(c for r, c in occupied)
            sprites[labels[0]] = [list(grid[r][c0:c1+1]) for r in range(r0, r1+1)]
    command_row = max(r for r in range(height) if any(grid[r]))
    pieces = []
    for col, code in enumerate(grid[command_row]):
        if not code:
            continue
        sprite = sprites[grid[command_row-1][col]]
        if code == 5:
            transformed = [r[:] for r in sprite]
        elif code == 6:
            transformed = [list(row) for row in zip(*sprite[::-1])]
        elif code == 7:
            transformed = [r[::-1] for r in sprite]
        else:
            raise ValueError('Unknown command')
        pieces.append(transformed)
    output_height = max(len(piece) for piece in pieces)
    result = [[] for _ in range(output_height)]
    for index, piece in enumerate(pieces):
        for r in range(output_height):
            if index:
                result[r].append(0)
            result[r].extend(piece[r] if r < len(piece) else [0]*len(piece[0]))
    return result
