"""Recolor occurrences of the enlarged corner stencil in the small panels."""

def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    a = [list(row) for row in grid]
    h, w = len(a), len(a[0])
    accents = {v for row in a for v in row} - {0, 1, 4}
    if len(accents) != 1:
        raise ValueError('Expected one stencil color')
    color = accents.pop()
    candidates = []
    for top in (0, h - 8):
        for left in (0, w - 8):
            if top < 0 or left < 0:
                continue
            border = [(r,c) for r in range(top, top+8) for c in range(left, left+8)
                      if r in (top,top+7) or c in (left,left+7)]
            if not all(a[r][c] == 4 for r,c in border):
                continue
            mask = [[a[top+1+2*r][left+1+2*c] == color for c in range(3)]
                    for r in range(3)]
            if any(any(row) for row in mask):
                candidates.append((top, left, mask))
    if len(candidates) != 1:
        raise ValueError('Expected one framed corner stencil')
    top, left, mask = candidates[0]
    positions = [(r,c) for r in range(3) for c in range(3) if mask[r][c]]
    out = [row[:] for row in a]
    for r in range(0, h-2, 4):
        for c in range(0, w-2, 4):
            if r < top+8 and r+3 > top and c < left+8 and c+3 > left:
                continue
            if all(a[r+i][c+j] == 1 for i,j in positions):
                for i,j in positions:
                    out[r+i][c+j] = color
    return out
