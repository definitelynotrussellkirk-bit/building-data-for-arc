def solve(grid):
    """Infer A->B colors from two divider-separated panels and recolor cropped C."""
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")

    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 1 for row in range(height))
    ]
    if len(dividers) != 2:
        raise ValueError("expected two full-height color-1 dividers")
    first, second = dividers
    panels = (
        [row[:first] for row in grid],
        [row[first + 1 : second] for row in grid],
        [row[second + 1 :] for row in grid],
    )

    def crop(panel):
        occupied = [
            (r, c)
            for r, row in enumerate(panel)
            for c, value in enumerate(row)
            if value != 0
        ]
        if not occupied:
            raise ValueError("empty panel object")
        top = min(r for r, _ in occupied)
        bottom = max(r for r, _ in occupied)
        left = min(c for _, c in occupied)
        right = max(c for _, c in occupied)
        return [row[left : right + 1] for row in panel[top : bottom + 1]]

    analogy_source, analogy_target, query = map(crop, panels)
    if (len(analogy_source), len(analogy_source[0])) != (
        len(analogy_target),
        len(analogy_target[0]),
    ):
        raise ValueError("analogy crops have different dimensions")

    color_map = {}
    for r in range(len(analogy_source)):
        for c in range(len(analogy_source[0])):
            source = analogy_source[r][c]
            target = analogy_target[r][c]
            if (source == 0) != (target == 0):
                raise ValueError("analogy crops have different masks")
            if source == 0:
                continue
            if source in color_map and color_map[source] != target:
                raise ValueError("inconsistent analogy color map")
            color_map[source] = target

    return [
        [0 if value == 0 else color_map[value] for value in row]
        for row in query
    ]
