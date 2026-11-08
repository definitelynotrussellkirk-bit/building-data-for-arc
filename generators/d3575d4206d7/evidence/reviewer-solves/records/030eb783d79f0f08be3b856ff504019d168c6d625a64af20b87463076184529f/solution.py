from collections import Counter
from typing import Iterable

Grid = list[list[int]]


def _runs_between_separators(length: int, separators: Iterable[int]) -> list[tuple[int, int]]:
    blocked = set(separators)
    runs: list[tuple[int, int]] = []
    i = 0
    while i < length:
        while i < length and i in blocked:
            i += 1
        if i >= length:
            break
        j = i
        while j < length and j not in blocked:
            j += 1
        runs.append((i, j))
        i = j
    return runs


def _special_signature(
    grid: Grid,
    row_run: tuple[int, int],
    col_run: tuple[int, int],
    background: int,
    base: int,
) -> tuple[int | None, tuple[tuple[int, int], ...]]:
    """Return the uniform accent color and its within-panel coordinates.

    A panel with no accent, or with several accent colors, is not a usable
    selector/candidate and returns ``(None, ())``.
    """

    r0, r1 = row_run
    c0, c1 = col_run
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r in range(r0, r1):
        for c in range(c0, c1):
            color = grid[r][c]
            if color not in (background, base):
                by_color.setdefault(color, []).append((r - r0, c - c0))
    if len(by_color) != 1:
        return None, ()
    color, positions = next(iter(by_color.items()))
    return color, tuple(positions)


def _paint_signature(
    output: Grid,
    row_run: tuple[int, int],
    col_run: tuple[int, int],
    positions: tuple[tuple[int, int], ...],
    color: int,
) -> None:
    r0, _ = row_run
    c0, _ = col_run
    for dr, dc in positions:
        output[r0 + dr][c0 + dc] = color


def solve(grid: Grid) -> Grid:
    """Propagate the 8-colored panel selectors through the panel lattice.

    Four-pixel selectors perform a row/column rectangle completion using panels
    with the same accent shape and signal color.  A three-pixel horizontal-line
    selector recolors horizontal-line signal panels in its own panel column,
    independent of the line's vertical offset.
    """

    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    base = counts.most_common(2)[1][0]

    separator_rows = [r for r, row in enumerate(grid) if all(v == background for v in row)]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == background for r in range(height))
    ]
    row_runs = _runs_between_separators(height, separator_rows)
    col_runs = _runs_between_separators(width, separator_cols)
    data_rows = [i for i, (start, end) in enumerate(row_runs) if end - start == 3]
    data_cols = [j for j, (start, end) in enumerate(col_runs) if end - start == 3]

    signatures: dict[tuple[int, int], tuple[int | None, tuple[tuple[int, int], ...]]] = {}
    for i in data_rows:
        for j in data_cols:
            signatures[i, j] = _special_signature(
                grid, row_runs[i], col_runs[j], background, base
            )

    output = [row[:] for row in grid]
    marker_panels = [
        (i, j, positions)
        for (i, j), (color, positions) in signatures.items()
        if color == 8 and positions
    ]

    for marker_row, marker_col, marker_shape in marker_panels:
        is_horizontal_line = (
            len(marker_shape) == 3
            and len({r for r, _ in marker_shape}) == 1
            and {c for _, c in marker_shape} == {0, 1, 2}
        )

        if is_horizontal_line:
            # Secondary selector: retain the panel column as scope, but accept
            # a horizontal line in any of the three within-panel rows.
            for i in data_rows:
                color, shape = signatures[i, marker_col]
                if color in (None, 8) or len(shape) != 3:
                    continue
                if len({r for r, _ in shape}) == 1 and {c for _, c in shape} == {0, 1, 2}:
                    _paint_signature(output, row_runs[i], col_runs[marker_col], shape, 8)
            continue

        # Primary selector: choose a signal color represented with the same
        # shape on both the marker's row and its column.  This prevents an
        # unrelated accent from defining either axis by itself.
        row_colors = {
            color
            for j in data_cols
            for color, shape in [signatures[marker_row, j]]
            if color not in (None, 8) and shape == marker_shape
        }
        col_colors = {
            color
            for i in data_rows
            for color, shape in [signatures[i, marker_col]]
            if color not in (None, 8) and shape == marker_shape
        }
        signal_colors = row_colors & col_colors

        for signal_color in signal_colors:
            selected_rows = {marker_row} | {
                i
                for i in data_rows
                if signatures[i, marker_col] == (signal_color, marker_shape)
            }
            selected_cols = {marker_col} | {
                j
                for j in data_cols
                if signatures[marker_row, j] == (signal_color, marker_shape)
            }
            for i in selected_rows:
                for j in selected_cols:
                    if signatures.get((i, j)) == (signal_color, marker_shape):
                        _paint_signature(output, row_runs[i], col_runs[j], marker_shape, 8)

    return output
