from copy import deepcopy


def solve(grid):
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        emitter = next(
            (
                (column, value)
                for column, value in enumerate(row)
                if value not in (0, 8)
            ),
            None,
        )
        if emitter is None:
            continue
        emitter_column, color = emitter
        blocker = next(
            (
                column
                for column in range(emitter_column + 1, len(row))
                if row[column] == 8
            ),
            None,
        )
        if blocker is None:
            continue
        for column in range(emitter_column + 1, blocker):
            output[row_index][column] = color
    return output
