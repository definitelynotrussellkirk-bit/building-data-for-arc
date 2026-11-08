"""Visible-example solution for ARC task 35368341e72e."""


def solve(grid):
    """Look up 3x3 prototypes by their top-row labels and answer the query."""
    if not grid or len(grid) < 5 or not grid[0]:
        raise ValueError("expected a non-empty prototype-dictionary grid")

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    prototypes = {}
    for col, key in enumerate(grid[0]):
        if key == 0:
            continue
        if col == 0 or col + 1 >= width:
            raise ValueError("prototype label is too close to an edge")
        prototypes[key] = [row[col - 1 : col + 2] for row in grid[1:4]]

    query = [key for key in grid[-1] if key != 0]
    if not query:
        return []

    out_width = 4 * len(query) - 1
    output = [[0 for _ in range(out_width)] for _ in range(3)]
    for index, key in enumerate(query):
        if key not in prototypes:
            raise ValueError(f"query key {key!r} has no prototype")
        left = 4 * index
        prototype = prototypes[key]
        for row in range(3):
            output[row][left : left + 3] = prototype[row]

    return output
