"""Visible-example solution for keyed prototype stamping."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    divider = next(r for r, row in enumerate(grid) if all(v == 9 for v in row))
    top = grid[:divider]
    body = grid[divider + 1 :]

    separators = [c for c in range(w) if all(top[r][c] == 9 for r in range(len(top)))]
    spans = []
    start = 0
    for cut in separators + [w]:
        if cut > start:
            spans.append((start, cut))
        start = cut + 1

    patterns = {}
    for left, right in spans:
        cells = [
            (r, c, top[r][c])
            for r in range(len(top))
            for c in range(left, right)
            if top[r][c] not in (0, 9)
        ]
        key = min(value for _, _, value in cells)
        anchor_r, anchor_c = next((r, c) for r, c, value in cells if value == key)
        patterns[key] = [
            (r - anchor_r, c - anchor_c, value)
            for r, c, value in cells
        ]

    out = [[0] * w for _ in body]
    for r, row in enumerate(body):
        for c, value in enumerate(row):
            if value not in patterns:
                continue
            for dr, dc, color in patterns[value]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < len(out) and 0 <= cc < w:
                    out[rr][cc] = color
    return out
