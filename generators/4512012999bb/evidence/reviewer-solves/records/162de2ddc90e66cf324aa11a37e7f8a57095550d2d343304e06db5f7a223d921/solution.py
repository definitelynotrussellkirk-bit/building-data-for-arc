"""Move a detached pattern between two capped rails, reflecting if needed."""
def solve(grid):
    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    positions = {}
    for y, row in enumerate(g):
        for x, color in enumerate(row):
            if color:
                positions.setdefault(color, []).append((y, x))
    candidates = []
    for color, cells in positions.items():
        if len(cells) != 4:
            continue
        top, bottom = min(y for y,x in cells), max(y for y,x in cells)
        left, right = min(x for y,x in cells), max(x for y,x in cells)
        if bottom-top < 2 or right-left < 3:
            continue
        if set(cells) != {(top,left),(top,right),(bottom,left),(bottom,right)}:
            continue
        if not all(g[y][left] and g[y][right] for y in range(top+1,bottom)):
            continue
        if any(g[y][x] for y in range(top,bottom+1) for x in range(left+1,right)):
            continue
        candidates.append((top,bottom,left,right))
    if len(candidates) != 1:
        raise ValueError('Expected one pair of capped rails')
    top,bottom,left,right = candidates[0]
    pattern_cells = [(y,x) for y in range(h) for x in range(w)
                     if g[y][x] and not (top <= y <= bottom and left <= x <= right)]
    if not pattern_cells:
        raise ValueError('Missing detached pattern')
    py0,py1 = min(y for y,x in pattern_cells),max(y for y,x in pattern_cells)
    px0,px1 = min(x for y,x in pattern_cells),max(x for y,x in pattern_cells)
    pattern = [g[y][px0:px1+1] for y in range(py0,py1+1)]
    if len(pattern) != bottom-top-1 or len(pattern[0]) != right-left-1:
        raise ValueError('Pattern does not fit rail interior')
    lc = {g[y][left] for y in range(top+1,bottom)}
    rc = {g[y][right] for y in range(top+1,bottom)}
    half = len(pattern[0])//2
    def orientation_score(rows):
        return sum((v in lc) for row in rows for v in row[:half] if v) + sum((v in rc) for row in rows for v in row[half:] if v)
    flipped = [row[::-1] for row in pattern]
    if orientation_score(flipped) > orientation_score(pattern):
        pattern = flipped
    out = [row[left:right+1] for row in g[top:bottom+1]]
    for y,row in enumerate(pattern,1):
        out[y][1:-1] = row
    return out
