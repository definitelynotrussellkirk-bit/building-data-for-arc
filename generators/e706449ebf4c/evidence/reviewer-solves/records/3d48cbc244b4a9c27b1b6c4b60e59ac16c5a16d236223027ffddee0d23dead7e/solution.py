def _red_components(grid):
    """Return all 4-connected components of red (2) cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                current_row, current_col = stack.pop()
                cells.add((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 2 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(cells)

    return components


def solve(grid):
    """Paint a cyan Manhattan aura around every red bar.

    For a bar with inclusive bounding-box length L, use its exact bounding-box
    midpoint (which may lie between cells). A cell belongs to the aura when its
    Manhattan distance from that midpoint is at most L/2. The doubled-coordinate
    form below avoids fractions. Existing nonzero cells, especially red bars,
    are preserved.
    """
    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for component in _red_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        length = max(bottom - top + 1, right - left + 1)
        center_row_doubled = top + bottom
        center_col_doubled = left + right

        for row in range(height):
            for col in range(width):
                distance_doubled = (
                    abs(2 * row - center_row_doubled)
                    + abs(2 * col - center_col_doubled)
                )
                if distance_doubled <= length and output[row][col] == 0:
                    output[row][col] = 8

    return output
