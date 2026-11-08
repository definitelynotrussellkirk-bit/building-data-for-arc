"""Visible-example solution for reviewer task 5a85abd1e231."""


def _components(grid):
    """Return 4-connected non-zero components as coordinate lists."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 0 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            result.append(component)
    return result


def _direction(value):
    """Map a signed displacement to the corresponding 0/1/2 output band."""
    if value < 0:
        return 0
    if value > 0:
        return 2
    return 1


def solve(grid):
    """Arrange the nine 3x3 tiles according to each tile's accent direction."""
    output = [[0 for _ in range(9)] for _ in range(9)]
    occupied = set()

    for component in _components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, left = min(rows), min(cols)
        bottom, right = max(rows), max(cols)
        if bottom - top != 2 or right - left != 2 or len(component) != 9:
            raise ValueError("expected every non-zero component to be a filled 3x3 tile")

        tile = [source_row[left : left + 3] for source_row in grid[top : top + 3]]
        accent = [
            (row, col)
            for row in range(3)
            for col in range(3)
            if tile[row][col] != 5
        ]

        if accent:
            row_displacement = sum(row - 1 for row, _ in accent)
            col_displacement = sum(col - 1 for _, col in accent)
            target_row = _direction(row_displacement)
            target_col = _direction(col_displacement)
        else:
            target_row = target_col = 1

        target = (target_row, target_col)
        if target in occupied:
            raise ValueError(f"two tiles map to output position {target}")
        occupied.add(target)

        for row in range(3):
            for col in range(3):
                output[3 * target_row + row][3 * target_col + col] = tile[row][col]

    if occupied != {(row, col) for row in range(3) for col in range(3)}:
        raise ValueError("input must provide exactly one tile for each output position")
    return output
