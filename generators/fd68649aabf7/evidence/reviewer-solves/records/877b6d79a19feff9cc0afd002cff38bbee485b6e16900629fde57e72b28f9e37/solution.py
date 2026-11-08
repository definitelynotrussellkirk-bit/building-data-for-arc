"""Post-repair visible-example solution; prior rule exposure is disclosed."""


def solve(grid):
    result = [list(row) for row in grid]
    markers = [(col, color) for col, color in enumerate(grid[0]) if color]
    marker_colors = {color for _, color in markers}
    visited = set()
    height, width = len(grid), len(grid[0])
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or color in marker_colors or (row, col) in visited:
                continue
            blob = [(row, col)]
            visited.add((row, col))
            for r, c in blob:
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (1 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in visited and grid[rr][cc] == color):
                        visited.add((rr, cc))
                        blob.append((rr, cc))
            doubled_center = min(c for _, c in blob) + max(c for _, c in blob)
            _, replacement = min(markers, key=lambda m: (abs(2 * m[0] - doubled_center), m[0]))
            for r, c in blob:
                result[r][c] = replacement
    return result
