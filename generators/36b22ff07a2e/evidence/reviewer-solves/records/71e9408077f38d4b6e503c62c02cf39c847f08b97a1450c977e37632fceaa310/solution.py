from collections import Counter


def _max_run(values, color):
    best = current = 0
    for value in values:
        if value == color:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _consecutive_bands(indices):
    bands = []
    for index in indices:
        if not bands or index != bands[-1][1] + 1:
            bands.append([index, index])
        else:
            bands[-1][1] = index
    return [tuple(band) for band in bands]


def _separator_bands(grid, color):
    height, width = len(grid), len(grid[0])
    row_runs = [_max_run(row, color) for row in grid]
    col_runs = [
        _max_run([grid[row][col] for row in range(height)], color)
        for col in range(width)
    ]

    max_row_run = max(row_runs)
    max_col_run = max(col_runs)
    row_cutoff = max(2, (4 * max_row_run + 4) // 5)
    col_cutoff = max(2, (4 * max_col_run + 4) // 5)

    row_bands = _consecutive_bands(
        [row for row, run in enumerate(row_runs) if run >= row_cutoff]
    )
    col_bands = _consecutive_bands(
        [col for col, run in enumerate(col_runs) if run >= col_cutoff]
    )
    return row_bands, col_bands, max_row_run, max_col_run


def solve(grid):
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    candidates = []
    for color, count in counts.items():
        if color == background:
            continue
        row_bands, col_bands, max_row_run, max_col_run = _separator_bands(
            grid, color
        )
        if len(row_bands) >= 2 and len(col_bands) >= 2:
            score = max_row_run * max_col_run * count
            candidates.append((score, color, row_bands, col_bands))

    if not candidates:
        raise ValueError("no rectangular separator lattice found")

    _, separator, row_bands, col_bands = max(candidates)
    output = []
    for upper, lower in zip(row_bands, row_bands[1:]):
        row_start, row_stop = upper[1] + 1, lower[0]
        output_row = []
        for left, right in zip(col_bands, col_bands[1:]):
            col_start, col_stop = left[1] + 1, right[0]
            cell_counts = Counter(
                grid[row][col]
                for row in range(row_start, row_stop)
                for col in range(col_start, col_stop)
                if grid[row][col] not in (background, separator)
            )
            output_row.append(
                cell_counts.most_common(1)[0][0] if cell_counts else background
            )
        output.append(output_row)
    return output
