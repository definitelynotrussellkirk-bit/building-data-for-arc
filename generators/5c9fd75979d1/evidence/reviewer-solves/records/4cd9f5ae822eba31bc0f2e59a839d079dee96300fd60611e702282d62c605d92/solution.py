from itertools import combinations


def _partitions(length, count, minimum=2):
    """Yield boundary tuples for `count` contiguous nonempty spans."""
    if count == 1:
        if length >= minimum:
            yield (0, length)
        return
    for cuts in combinations(range(minimum, length - minimum + 1), count - 1):
        bounds = (0, *cuts, length)
        if all(bounds[i + 1] - bounds[i] >= minimum for i in range(count)):
            yield bounds


def _trim(grid):
    height, width = len(grid), len(grid[0])
    rows = [r for r in range(height) if any(grid[r][c] for c in range(width))]
    cols = [c for c in range(width) if any(grid[r][c] for r in range(height))]
    if not rows or not cols:
        return []
    r0, r1 = rows[0], rows[-1] + 1
    c0, c1 = cols[0], cols[-1] + 1
    return [row[c0:c1] for row in grid[r0:r1]]


def _decode_cells(trimmed, row_bounds, col_bounds):
    decoded = []
    for r0, r1 in zip(row_bounds, row_bounds[1:]):
        row = []
        for c0, c1 in zip(col_bounds, col_bounds[1:]):
            colors = {
                trimmed[r][c]
                for r in range(r0, r1)
                for c in range(c0, c1)
                if trimmed[r][c] != 0
            }
            if len(colors) != 1:
                return None
            row.append(next(iter(colors)))
        decoded.append(row)
    return decoded


def solve(grid):
    """Compress a noisy tile matrix to colors, then mirror its columns."""
    if not grid or not grid[0]:
        return []

    trimmed = _trim(grid)
    if not trimmed:
        return []
    height, width = len(trimmed), len(trimmed[0])

    candidates = []
    max_rows = min(6, height // 2)
    max_cols = min(6, width // 2)
    for row_count in range(1, max_rows + 1):
        for col_count in range(1, max_cols + 1):
            for row_bounds in _partitions(height, row_count):
                for col_bounds in _partitions(width, col_count):
                    decoded = _decode_cells(trimmed, row_bounds, col_bounds)
                    if decoded is None:
                        continue
                    row_sizes = [b - a for a, b in zip(row_bounds, row_bounds[1:])]
                    col_sizes = [b - a for a, b in zip(col_bounds, col_bounds[1:])]
                    imbalance = (max(row_sizes) - min(row_sizes)) + (max(col_sizes) - min(col_sizes))
                    key = (row_count * col_count, row_count + col_count, imbalance)
                    candidates.append((key, decoded))

    if not candidates:
        return []
    _, decoded = min(candidates, key=lambda item: item[0])
    return [list(reversed(row)) for row in decoded]
