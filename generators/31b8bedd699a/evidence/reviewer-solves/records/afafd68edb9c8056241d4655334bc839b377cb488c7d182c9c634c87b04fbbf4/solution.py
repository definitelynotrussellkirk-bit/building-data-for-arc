def solve(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    frames = []
    while unseen:
        first = min(unseen)
        color = grid[first[0]][first[1]]
        cells = {first}
        unseen.remove(first)
        frontier = [first]
        while frontier:
            r, c = frontier.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    cells.add(p)
                    frontier.append(p)
        top = min(r for r, c in cells)
        bottom = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        if len(cells) < (bottom - top + 1) * (right - left + 1):
            frames.append((top, left, color))
    row_span = max(r for r, c, color in frames) - min(r for r, c, color in frames)
    col_span = max(c for r, c, color in frames) - min(c for r, c, color in frames)
    vertical = row_span > col_span
    frames.sort(key=lambda frame: frame[0 if vertical else 1])
    output = [[0] * (4 if vertical else 4 * len(frames))
              for _ in range(4 * len(frames) if vertical else 4)]
    for i, (_, _, color) in enumerate(frames):
        for r in range(4):
            for c in range(4):
                if r in (0, 3) or c in (0, 3):
                    output[(4 * i if vertical else 0) + r][(0 if vertical else 4 * i) + c] = color
    return output
