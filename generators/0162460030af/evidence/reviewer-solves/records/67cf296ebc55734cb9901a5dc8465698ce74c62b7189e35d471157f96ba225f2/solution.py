"""Visible-example-only solution for task 0162460030af."""


def _components(grid):
    """Return 4-connected, same-colour non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + row_delta
                    next_col = current_col + col_delta
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != colour:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            result.append(cells)

    return result


def solve(grid):
    """Alternate object colours from the left-middle object outwards."""
    output = [row[:] for row in grid]
    components = _components(grid)
    if not components:
        return output

    components.sort(
        key=lambda cells: (
            sum(col for _, col in cells) / len(cells),
            sum(row for row, _ in cells) / len(cells),
        )
    )
    left_middle = (len(components) - 1) // 2

    for index, cells in enumerate(components):
        colour = 2 if (index - left_middle) % 2 == 0 else 8
        for row, col in cells:
            output[row][col] = colour

    return output
