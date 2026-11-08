from collections import Counter


def _active_parity(grid, axis):
    """Return the row/column parity carrying the sparse non-zero lattice."""
    counts = Counter()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                counts[(r if axis == 0 else c) & 1] += 1
    # The examples use a single checkerboard parity.  Tie-break toward 1,
    # which also keeps the one-cell zero border seen in the task.
    return max((0, 1), key=lambda p: (counts[p], p))


def solve(grid):
    """Complete the sparse corner code into concentric square outlines."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    row_parity = _active_parity(grid, 0)
    col_parity = _active_parity(grid, 1)
    lattice_rows = list(range(row_parity, height, 2))
    lattice_cols = list(range(col_parity, width, 2))
    nr, nc = len(lattice_rows), len(lattice_cols)

    row_to_i = {r: i for i, r in enumerate(lattice_rows)}
    col_to_j = {c: j for j, c in enumerate(lattice_cols)}
    points = []
    for r, row in enumerate(grid):
        if r not in row_to_i:
            continue
        for c, value in enumerate(row):
            if value != 0 and c in col_to_j:
                points.append((row_to_i[r], col_to_j[c], value))

    if not points:
        return [row[:] for row in grid]

    # Find which physical corner contains the compact diagonal staircase.
    # In the correct orientation its coordinates are near u=v and as close
    # as possible to (0, 0).  Opposite-corner reflection preserves |u-v|,
    # so compactness toward the origin is the second score component.
    candidates = []
    for flip_r in (False, True):
        for flip_c in (False, True):
            mapped = []
            diagonal_violation = 0
            radial_sum = 0
            radial_max = 0
            for i, j, value in points:
                u = nr - 1 - i if flip_r else i
                v = nc - 1 - j if flip_c else j
                mapped.append((u, v, value))
                diagonal_violation += max(0, abs(u - v) - 1)
                radial_sum += u + v
                radial_max = max(radial_max, u, v)
            candidates.append(
                ((diagonal_violation, radial_sum, radial_max), mapped)
            )
    _, mapped = min(candidates, key=lambda item: item[0])
    clues = {(u, v): value for u, v, value in mapped}

    out = [[0 for _ in range(width)] for _ in range(height)]
    max_layers = (min(nr, nc) + 1) // 2

    for k in range(max_layers):
        bottom = nr - 1 - k
        right = nc - 1 - k
        if k > bottom or k > right:
            break

        corner = clues.get((k, k), 0)
        horizontal = clues.get((k, k + 1), 0) if k + 1 < nc else 0
        vertical = clues.get((k + 1, k), 0) if k + 1 < nr else 0

        # The demonstrated rule is fourfold symmetric.  If a generated
        # instance supplies just one of the two redundant edge clues, use it
        # for both directions; if both exist, retain each direction exactly.
        if horizontal and not vertical:
            vertical = horizontal
        elif vertical and not horizontal:
            horizontal = vertical

        top_r = lattice_rows[k]
        bottom_r = lattice_rows[bottom]
        left_c = lattice_cols[k]
        right_c = lattice_cols[right]

        if corner:
            for rr, cc in {
                (top_r, left_c),
                (top_r, right_c),
                (bottom_r, left_c),
                (bottom_r, right_c),
            }:
                out[rr][cc] = corner

        if horizontal and k < right:
            for j in range(k + 1, right):
                cc = lattice_cols[j]
                out[top_r][cc] = horizontal
                out[bottom_r][cc] = horizontal

        if vertical and k < bottom:
            for i in range(k + 1, bottom):
                rr = lattice_rows[i]
                out[rr][left_c] = vertical
                out[rr][right_c] = vertical

    return out
