"""Visible-example solution: translate complementary components into rectangles.

No generator, reference implementation, hidden answers, or third-party package
is imported. The background and repeated anchor color are inferred from input.
"""
from collections import Counter


def _components(grid, background):
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == background or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((color, cells))
    return result


def _normalized(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r-r0, c-c0) for r, c in cells)


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    background = Counter(v for row in grid for v in row).most_common(1)[0][0]
    components = _components(grid, background)
    color_counts = Counter(color for color, _ in components)
    repeated = [color for color, count in color_counts.items() if count > 1]
    if len(repeated) != 1:
        raise ValueError('Expected one repeated anchor color')
    anchor_color = repeated[0]
    anchors = sorted((cells for color, cells in components if color == anchor_color),
                     key=lambda cells: min(cells))
    candidates = [(color, cells) for color, cells in components if color != anchor_color]
    if len(anchors) != len(candidates):
        raise ValueError('Expected one complement per anchor')
    heights = {max(r for r, _ in cells)-min(r for r, _ in cells)+1 for cells in anchors}
    if len(heights) != 1:
        raise ValueError('Anchors must have a common rectangle height')
    height = heights.pop()
    total_cells = sum(len(cells) for _, cells in components)
    denominator = len(anchors) * height
    if total_cells % denominator:
        raise ValueError('Cell count does not determine an integral rectangle width')
    width = total_cells // denominator
    target = {(r, c) for r in range(height) for c in range(width)}
    out = [[background] * len(grid[0]) for _ in grid]
    unused = set(range(len(candidates)))
    for cells in anchors:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        anchor = _normalized(cells)
        if not anchor <= target:
            raise ValueError('Anchor exceeds inferred rectangle')
        missing = target - anchor
        matches = [j for j in unused if _normalized(candidates[j][1]) == _normalized(missing)]
        if len(matches) != 1:
            raise ValueError('Complement must be unique')
        chosen = matches[0]
        unused.remove(chosen)
        color = candidates[chosen][0]
        if r0+height > len(grid) or c0+width > len(grid[0]):
            raise ValueError('Completed rectangle exceeds the canvas')
        for r, c in target:
            out[r0+r][c0+c] = anchor_color if (r, c) in anchor else color
    return out
