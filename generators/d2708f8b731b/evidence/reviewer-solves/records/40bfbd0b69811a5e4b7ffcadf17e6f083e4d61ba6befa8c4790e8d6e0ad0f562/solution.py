"""Visible-example solution for the blind ARC task."""


def _one_components(grid):
    """Return the 4-connected components made of color 1."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 1:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            components.append(component)

    return components


def _shape(component):
    """Translation-invariant, orientation-sensitive component signature."""
    top = min(row for row, _ in component)
    left = min(col for _, col in component)
    return tuple(sorted((row - top, col - left) for row, col in component))


def _labelled_component(marker_row, marker_col, components):
    """Find the color-1 exemplar immediately to the marker's left.

    In every visible example the non-1 marker is written to the right of one
    exemplar, sharing a row with at least one of its cells.  Prefer that exact
    layout relation.  The Manhattan fallback only makes the solver total for a
    malformed or edge-case grid; it is not needed by the visible examples.
    """
    same_row_left = []
    for index, component in enumerate(components):
        left_cells = [col for row, col in component if row == marker_row and col < marker_col]
        if left_cells:
            same_row_left.append((marker_col - max(left_cells), index))

    if same_row_left:
        return min(same_row_left)[1]

    return min(
        range(len(components)),
        key=lambda index: min(
            abs(marker_row - row) + abs(marker_col - col)
            for row, col in components[index]
        ),
    )


def solve(grid):
    """Color every unlabelled copy of each marker-labelled color-1 shape."""
    result = [row[:] for row in grid]
    components = _one_components(grid)
    if not components:
        return result

    shape_to_color = {}
    labelled_components = set()

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 1):
                continue
            component_index = _labelled_component(row, col, components)
            labelled_components.add(component_index)
            shape_to_color[_shape(components[component_index])] = value

    for index, component in enumerate(components):
        if index in labelled_components:
            continue
        color = shape_to_color.get(_shape(component))
        if color is None:
            continue
        for row, col in component:
            result[row][col] = color

    return result
