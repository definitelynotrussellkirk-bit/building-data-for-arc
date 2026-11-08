from __future__ import annotations


def _runs_between(separators: list[int], length: int) -> list[tuple[int, int]]:
    """Return inclusive non-separator runs between full separator lines."""
    runs: list[tuple[int, int]] = []
    previous = -1
    for separator in [*separators, length]:
        start = previous + 1
        end = separator - 1
        if start <= end:
            runs.append((start, end))
        previous = separator
    return runs


def _bucket(value: float) -> int:
    if value < 1.5:
        return 0
    if value <= 2.5:
        return 1
    return 2


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Move each 5x5 panel to the address encoded by its marker centroid."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and nonempty")

    separator_rows = [r for r, row in enumerate(grid) if all(value == 0 for value in row)]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == 0 for r in range(height))
    ]
    row_runs = _runs_between(separator_rows, height)
    col_runs = _runs_between(separator_cols, width)
    if len(row_runs) != 3 or len(col_runs) != 3:
        raise ValueError("expected a 3x3 lattice separated by full zero rows and columns")
    if any(end - start + 1 != 5 for start, end in [*row_runs, *col_runs]):
        raise ValueError("expected nine 5x5 panels")

    nonzero_counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value != 0:
                nonzero_counts[value] = nonzero_counts.get(value, 0) + 1
    if len(nonzero_counts) != 2:
        raise ValueError("expected exactly two nonzero colors")
    background = max(nonzero_counts, key=nonzero_counts.get)
    marker = next(color for color in nonzero_counts if color != background)

    output = [[0 for _ in range(width)] for _ in range(height)]
    destinations: set[tuple[int, int]] = set()

    for source_row, (r0, r1) in enumerate(row_runs):
        for source_col, (c0, c1) in enumerate(col_runs):
            panel = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
            points = [
                (local_r, local_c)
                for local_r in range(5)
                for local_c in range(5)
                if panel[local_r][local_c] == marker
            ]
            if not points:
                raise ValueError(
                    f"panel ({source_row}, {source_col}) has no marker-color cells"
                )
            mean_row = sum(r for r, _c in points) / len(points)
            mean_col = sum(c for _r, c in points) / len(points)
            destination = (_bucket(mean_row), _bucket(mean_col))
            if destination in destinations:
                raise ValueError(f"duplicate destination {destination}")
            destinations.add(destination)

            target_r0 = row_runs[destination[0]][0]
            target_c0 = col_runs[destination[1]][0]
            for local_r in range(5):
                for local_c in range(5):
                    output[target_r0 + local_r][target_c0 + local_c] = panel[local_r][local_c]

    if len(destinations) != 9:
        raise ValueError("marker centroids did not encode a complete 3x3 permutation")
    return output
