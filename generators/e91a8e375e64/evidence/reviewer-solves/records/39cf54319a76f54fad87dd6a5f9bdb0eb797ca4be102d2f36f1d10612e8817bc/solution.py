"""Visible-example solution for e91a8e375e64."""


def _identity(matrix):
    return [row[:] for row in matrix]


def _rot90(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def _rot180(matrix):
    return [row[::-1] for row in matrix[::-1]]


def _rot270(matrix):
    return [list(row) for row in zip(*matrix)][::-1]


def _flip_lr(matrix):
    return [row[::-1] for row in matrix]


def _flip_ud(matrix):
    return matrix[::-1]


def _transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def _anti_transpose(matrix):
    return _rot180(_transpose(matrix))


_TRANSFORMS = (
    _identity,
    _rot90,
    _rot180,
    _rot270,
    _flip_lr,
    _flip_ud,
    _transpose,
    _anti_transpose,
)


def solve(grid):
    side = len(grid)
    if side == 0 or any(len(row) != 5 * side + 4 for row in grid):
        raise ValueError("expected five square panels separated by one column")

    panels = []
    for index in range(5):
        left = index * (side + 1)
        panels.append([row[left:left + side] for row in grid])
    a_panel, b_panel, c_panel, d_panel, query = panels

    transform = next((fn for fn in _TRANSFORMS if fn(a_panel) == b_panel), None)
    if transform is None:
        raise ValueError("could not infer the A-to-B transform")

    color_map = {}
    for source_row, target_row in zip(c_panel, d_panel):
        for source, target in zip(source_row, target_row):
            if source != 0 and target != 0:
                if source in color_map and color_map[source] != target:
                    raise ValueError("inconsistent C-to-D color map")
                color_map[source] = target

    transformed = transform(query)
    return [
        [color_map.get(value, value) if value != 0 else 0 for value in row]
        for row in transformed
    ]
