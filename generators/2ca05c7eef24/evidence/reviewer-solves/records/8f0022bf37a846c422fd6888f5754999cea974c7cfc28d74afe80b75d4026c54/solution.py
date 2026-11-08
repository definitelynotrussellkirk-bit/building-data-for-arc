from collections import Counter


def solve(grid):
    """Combine equal-width panels separated by solid columns of color 5."""
    height = len(grid)
    if height == 0:
        return []

    separators = [
        col
        for col in range(len(grid[0]))
        if all(row[col] == 5 for row in grid)
    ]
    boundaries = [-1, *separators, len(grid[0])]
    panels = [
        [row[left + 1 : right] for row in grid]
        for left, right in zip(boundaries, boundaries[1:])
        if right > left + 1
    ]
    if not panels or any(len(panel[0]) != len(panels[0][0]) for panel in panels):
        raise ValueError("expected equal-width panels separated by solid 5-columns")

    width = len(panels[0][0])
    output = []
    for row in range(height):
        output_row = []
        for col in range(width):
            values = [panel[row][col] for panel in panels]
            counts = Counter(values)
            best_count = max(counts.values())
            output_row.append(max(value for value, count in counts.items() if count == best_count))
        output.append(output_row)
    return output
