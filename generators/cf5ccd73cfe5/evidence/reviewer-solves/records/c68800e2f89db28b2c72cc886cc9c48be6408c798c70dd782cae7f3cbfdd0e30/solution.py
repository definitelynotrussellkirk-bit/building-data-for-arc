"""Exposed reviewer solution; checks use only the public challenge."""

def solve(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                by_color.setdefault(color, set()).add((r, c))
    frames = []
    for color, cells in by_color.items():
        top, bottom = min(r for r, c in cells), max(r for r, c in cells)
        left, right = min(c for r, c in cells), max(c for r, c in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        edge = {(r, c) for r in range(top, bottom + 1)
                for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)}
        if cells == edge and all(grid[r][c] == 0
                                 for r in range(top + 1, bottom)
                                 for c in range(left + 1, right)):
            frames.append((color, top, bottom, left, right))
    if len(frames) != 1:
        raise ValueError("Expected one hollow rectangular frame")
    color, top, bottom, left, right = frames[0]
    marker = {(r, c): value for r, row in enumerate(grid)
              for c, value in enumerate(row) if value and value != color}
    mt, mb = min(r for r, c in marker), max(r for r, c in marker)
    ml, mr = min(c for r, c in marker), max(c for r, c in marker)
    mh, mw = mb - mt + 1, mr - ml + 1
    ih, iw = bottom - top - 1, right - left - 1
    if ih % mh or iw % mw:
        raise ValueError("Expected whole-number row and column replication")
    sh, sw = ih // mh, iw // mw
    result = [[color] * (iw + 2) for _ in range(ih + 2)]
    for r in range(ih):
        for c in range(iw):
            result[r + 1][c + 1] = marker.get((mt + r // sh, ml + c // sw), 0)
    return result
