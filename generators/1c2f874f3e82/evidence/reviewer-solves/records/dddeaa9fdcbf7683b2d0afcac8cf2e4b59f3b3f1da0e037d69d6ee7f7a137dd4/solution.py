def solve(grid):
    h = len(grid)
    w = len(grid[0])
    anchor = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    offsets = [(r - anchor[0], c - anchor[1]) for r, c in source]

    out = [[0 for _ in range(w)] for _ in range(h)]
    for marker_color in (3, 4, 5):
        markers = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == marker_color
        ]
        for mr, mc in markers:
            for dr, dc in offsets:
                if marker_color == 3:       # preserve signed offsets
                    rr, cc = mr + dr, mc + dc
                elif marker_color == 4:     # rotate clockwise around the marker
                    rr, cc = mr + dc, mc - dr
                else:                       # mirror across the marker's vertical axis
                    rr, cc = mr + dr, mc - dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 8
    return out
