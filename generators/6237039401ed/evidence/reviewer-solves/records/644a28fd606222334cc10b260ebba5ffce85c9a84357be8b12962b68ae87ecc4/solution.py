from collections import Counter


def _components(grid):
    """Return same-color 4-connected non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return []

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            min_row = min(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            shape = tuple(sorted((r - min_row, c - min_col) for r, c in cells))
            components.append((color, shape, cells))

    return components


def solve(grid):
    """Recolor every copy of the repeated object shape blue."""
    output = [row[:] for row in grid]
    components = _components(grid)
    if not components:
        return output

    groups = Counter((color, shape) for color, shape, _ in components)
    target = max(groups, key=lambda key: (groups[key], len(key[1])))

    for color, shape, cells in components:
        if (color, shape) == target:
            for row, col in cells:
                output[row][col] = 1
    return output
