from collections import Counter


def _components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and
                                grid[nr][nc] != 0 and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            out.append(cells)
    return out


def _crop(grid, cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cell_set = set(cells)
    return tuple(
        tuple(grid[r][c] if (r, c) in cell_set else 0 for c in range(c0, c1 + 1))
        for r in range(r0, r1 + 1)
    )


def solve(grid):
    """Return the sole 8-connected colored object without an exact duplicate."""
    if not grid or not grid[0]:
        return []
    crops = [_crop(grid, cells) for cells in _components8(grid)]
    counts = Counter(crops)
    unique = [crop for crop in crops if counts[crop] == 1]
    if len(unique) != 1:
        raise ValueError(f"expected one unmatched object, found {len(unique)}")
    return [list(row) for row in unique[0]]
