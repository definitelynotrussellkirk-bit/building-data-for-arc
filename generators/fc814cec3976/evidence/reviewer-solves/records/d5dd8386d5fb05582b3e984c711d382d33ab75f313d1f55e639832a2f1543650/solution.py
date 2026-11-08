"""A self-contained solver written during the final visible-example attempt."""
def solve(grid):
    h, w = len(grid), len(grid[0])
    ranked = []
    for r in range(h - 2):
        for c in range(w - 2):
            positions = [(x, y) for x in range(r, r + 3)
                         for y in range(c, c + 3)]
            if grid[r + 1][c + 1] != 5:
                continue
            if any(grid[x][y] not in (2, 5) for x, y in positions):
                continue
            reds = {(x, y) for x, y in positions if grid[x][y] == 2}
            if reds:
                ranked.append((-len(reds), r, c, reds))
    ranked.sort(key=lambda item: item[:3])
    occupied_reds = set()
    marked_gray = set()
    output = [list(row) for row in grid]
    for _, r, c, reds in ranked:
        if reds & occupied_reds:
            continue
        occupied_reds |= reds
        for x in range(r, r + 3):
            for y in range(c, c + 3):
                if grid[x][y] == 5 and (x, y) not in marked_gray:
                    output[x][y] = 4 if (x == r + 1 and y == c + 1) else 7
                    marked_gray.add((x, y))
    return output
