"""Exposed, visible-example solve; no generator or reference imports."""

def _motifs(grid):
    seen = set()
    objects = []
    for r in range(1, len(grid)):
        for c in range(len(grid[r])):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 1 <= nr < len(grid) and 0 <= nc < len(grid[nr]) and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            height = max(rr for rr, _ in cells) - top + 1
            width = max(cc for _, cc in cells) - left + 1
            mask = [[0] * width for _ in range(height)]
            for rr, cc in cells:
                mask[rr-top][cc-left] = 1
            objects.append((left, top, color, mask))
    objects.sort(key=lambda obj: obj[:3])
    return [obj[3] for obj in objects[:2]]


def _transform(mask, name):
    if name == 'identity':
        return [row[:] for row in mask]
    if name == 'cw':
        return [list(row) for row in zip(*mask[::-1])]
    if name == 'ccw':
        return [list(row) for row in zip(*mask)][::-1]
    if name == 'half':
        return [row[::-1] for row in mask[::-1]]
    if name == 'lr':
        return [row[::-1] for row in mask]
    if name == 'ud':
        return [row[:] for row in mask[::-1]]
    if name == 'transpose':
        return [list(row) for row in zip(*mask)]
    if name == 'anti_transpose':
        return [list(row) for row in zip(*[row[::-1] for row in mask[::-1]])]
    raise ValueError(name)


def _combine(a, b, operation):
    height, width = max(len(a), len(b)), max(len(a[0]), len(b[0]))
    result = [[0] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            x = r < len(a) and c < len(a[0]) and bool(a[r][c])
            y = r < len(b) and c < len(b[0]) and bool(b[r][c])
            yes = (x or y) if operation == 'union' else (x and y) if operation == 'intersection' else (x != y)
            result[r][c] = 8 if yes else 0
    live = [(r, c) for r in range(height) for c in range(width) if result[r][c]]
    if not live:
        return [[0]]
    top, bottom = min(r for r, _ in live), max(r for r, _ in live)
    left, right = min(c for _, c in live), max(c for _, c in live)
    return [row[left:right+1] for row in result[top:bottom+1]]


def solve(grid):
    transform_key = next(color for color in grid[0] if color in (1, 2, 3))
    operation_key = next(color for color in grid[0] if color in (4, 5, 6))
    a, b = _motifs(grid)
    return _combine(_transform(a, {1: 'cw', 2: 'lr', 3: 'ud'}[transform_key]), b,
                    {4: 'union', 5: 'intersection', 6: 'xor'}[operation_key])
