from collections import defaultdict


def solve(grid):
    """Compress the colored objects' spatial quadrants into a 2x2 grid."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height == 0 or width == 0:
        return []

    cells_by_color = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                cells_by_color[color].append((row_index, column_index))

    result = [[0, 0], [0, 0]]
    quadrant_candidates = defaultdict(list)
    for color, cells in cells_by_color.items():
        mean_row = sum(row for row, _ in cells) / len(cells)
        mean_column = sum(column for _, column in cells) / len(cells)
        output_row = 0 if mean_row < height / 2 else 1
        output_column = 0 if mean_column < width / 2 else 1
        quadrant_candidates[(output_row, output_column)].append((len(cells), color))

    for (output_row, output_column), candidates in quadrant_candidates.items():
        # Valid instances have at most one colored object per quadrant.  The
        # deterministic fallback makes malformed/ambiguous inputs predictable.
        _, color = max(candidates, key=lambda item: (item[0], -item[1]))
        result[output_row][output_column] = color

    return result
