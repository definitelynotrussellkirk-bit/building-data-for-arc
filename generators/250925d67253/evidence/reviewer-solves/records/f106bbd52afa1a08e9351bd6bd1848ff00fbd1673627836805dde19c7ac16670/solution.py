from __future__ import annotations

from collections import Counter


def _bucket(value: float) -> int:
    if value < 1.5:
        return 0
    if value <= 2.5:
        return 1
    return 2


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reorder the nine 5x5 panels by the centroid of each panel's markers."""
    # The four all-zero rows and columns form a 3x3 array of 5x5 panels.
    # In visible examples the common panel background is the modal nonzero
    # color in the first panel row; every other nonzero color is a marker.
    row_one = [grid[1][column] for column in range(1, 18) if grid[1][column] != 0]
    background = Counter(row_one).most_common(1)[0][0]

    output = [[0 for _ in range(19)] for _ in range(19)]
    for source in range(9):
        source_panel_row, source_panel_column = divmod(source, 3)
        source_row = 1 + 6 * source_panel_row
        source_column = 1 + 6 * source_panel_column

        markers: list[tuple[int, int]] = []
        for local_row in range(5):
            for local_column in range(5):
                if grid[source_row + local_row][source_column + local_column] != background:
                    markers.append((local_row, local_column))

        mean_row = sum(row for row, _ in markers) / len(markers)
        mean_column = sum(column for _, column in markers) / len(markers)
        target = 3 * _bucket(mean_row) + _bucket(mean_column)
        target_panel_row, target_panel_column = divmod(target, 3)
        target_row = 1 + 6 * target_panel_row
        target_column = 1 + 6 * target_panel_column

        for local_row in range(5):
            output[target_row + local_row][target_column : target_column + 5] = (
                grid[source_row + local_row][source_column : source_column + 5]
            )

    return output
