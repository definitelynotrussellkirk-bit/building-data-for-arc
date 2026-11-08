from collections import deque


def _normalize(cells):
    cells = list(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate_cw(shape):
    return _normalize((c, -r) for r, c in shape)


def _rotations(shape):
    out = []
    current = _normalize(shape)
    for _ in range(4):
        if current not in out:
            out.append(current)
        current = _rotate_cw(current)
    return set(out)


def _components(grid, row_start, row_end, excluded=(0, 9)):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for r in range(max(0, row_start), min(height, row_end)):
        for c in range(width):
            if (r, c) in seen or grid[r][c] in excluded:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if not (row_start <= nr < row_end and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            result.append((color, cells))
    return result


def solve(grid):
    """Recolor the lower object that is a rotation of the upper template."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    width = len(grid[0])
    separator = next(
        r for r, row in enumerate(grid)
        if len(row) == width and all(value == 9 for value in row)
    )

    upper = _components(grid, 0, separator)
    lower = _components(grid, separator + 1, len(grid))
    if len(upper) != 1:
        raise ValueError(f"expected one upper template, found {len(upper)}")

    template_shape = _normalize(upper[0][1])
    accepted = _rotations(template_shape)
    matches = [cells for _color, cells in lower if _normalize(cells) in accepted]
    if len(matches) != 1:
        raise ValueError(f"expected one rotational match, found {len(matches)}")

    result = [row[:] for row in grid]
    for r, c in matches[0]:
        result[r][c] = 2
    return result
