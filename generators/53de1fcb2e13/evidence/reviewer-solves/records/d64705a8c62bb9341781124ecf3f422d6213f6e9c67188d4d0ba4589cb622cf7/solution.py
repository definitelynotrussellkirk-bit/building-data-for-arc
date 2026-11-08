"""Infer a square symmetry from the first two panels and apply it to the third."""


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, reflected, turns):
    result = [row[::-1] if reflected else row[:] for row in grid]
    for _ in range(turns):
        result = _rotate_clockwise(result)
    return result


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    panel_width = (width - 2) // 3
    if width != 3 * panel_width + 2 or height != panel_width:
        raise ValueError("Expected three square panels separated by single columns")
    first = [row[:panel_width] for row in grid]
    second = [row[panel_width + 1:2 * panel_width + 1] for row in grid]
    third = [row[2 * panel_width + 2:] for row in grid]
    predictions = []
    for reflected in (False, True):
        for turns in range(4):
            if _transform(first, reflected, turns) == second:
                prediction = _transform(third, reflected, turns)
                if prediction not in predictions:
                    predictions.append(prediction)
    if len(predictions) != 1:
        raise ValueError("The first two panels do not identify one query prediction")
    return predictions[0]
