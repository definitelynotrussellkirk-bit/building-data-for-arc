def solve(grid):
    """Render nonzero colors as descending, top-aligned bbox-height bars."""
    bounds = {}
    for row_index, row in enumerate(grid):
        for value in row:
            if value == 0:
                continue
            if value not in bounds:
                bounds[value] = [row_index, row_index]
            else:
                bounds[value][0] = min(bounds[value][0], row_index)
                bounds[value][1] = max(bounds[value][1], row_index)

    bars = [
        (bottom - top + 1, color)
        for color, (top, bottom) in bounds.items()
    ]
    bars.sort(key=lambda item: (-item[0], item[1]))
    if not bars:
        return []

    height = max(length for length, _color in bars)
    return [
        [color if row < length else 0 for length, color in bars]
        for row in range(height)
    ]
