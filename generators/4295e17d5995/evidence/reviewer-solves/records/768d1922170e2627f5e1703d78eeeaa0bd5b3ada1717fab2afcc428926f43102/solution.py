from collections import Counter


def _components(grid, color):
    """Return the 4-connected components containing ``color``."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue

            component = set()
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(component)

    return result


def solve(grid):
    """Slide each colored component horizontally toward its matching side rail.

    The first and last columns are solid colored rails.  Disconnected pieces of
    the left-rail color move left; pieces of the right-rail color move right.
    A piece preserves its shape and moves one column at a time until the next
    step would hit its rail or an already-settled piece of the same color.
    Pieces nearer their destination rail settle first.
    """
    if not grid or not grid[0]:
        return grid

    height = len(grid)
    width = len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    left_color = Counter(row[0] for row in grid).most_common(1)[0][0]
    right_color = Counter(row[-1] for row in grid).most_common(1)[0][0]

    output = [row[:] for row in grid]
    groups = []

    for color, side in ((left_color, "left"), (right_color, "right")):
        fixed = []
        movable = []
        target_col = 0 if side == "left" else width - 1

        for component in _components(grid, color):
            if any(col == target_col for _, col in component):
                fixed.append(component)
            else:
                movable.append(component)
                for row, col in component:
                    output[row][col] = background

        groups.append((color, side, fixed, movable))

    for color, side, fixed, movable in groups:
        settled = set().union(*fixed) if fixed else set()

        if side == "left":
            movable.sort(
                key=lambda component: (
                    min(col for _, col in component),
                    min(row for row, _ in component),
                )
            )
            step = -1
        else:
            movable.sort(
                key=lambda component: (
                    -max(col for _, col in component),
                    min(row for row, _ in component),
                )
            )
            step = 1

        for component in movable:
            shift = 0
            while True:
                candidate_shift = shift + step
                candidate = {
                    (row, col + candidate_shift) for row, col in component
                }
                if (
                    any(col < 0 or col >= width for _, col in candidate)
                    or candidate & settled
                ):
                    break
                shift = candidate_shift

            moved = {(row, col + shift) for row, col in component}
            for row, col in moved:
                output[row][col] = color
            settled.update(moved)

    return output
