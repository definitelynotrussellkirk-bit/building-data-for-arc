"""Visible-example-only solution for the blind ARC episode."""


def _components(grid):
    """Return 4-connected, same-colour components below the marker row."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(1, height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                cur_row, cur_col = stack.pop()
                cells.append((cur_row, cur_col))
                for next_row, next_col in (
                    (cur_row - 1, cur_col),
                    (cur_row + 1, cur_col),
                    (cur_row, cur_col - 1),
                    (cur_row, cur_col + 1),
                ):
                    if not (1 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != colour:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            components.append((colour, cells))

    return components


def _horizontal_distance(col, left, right):
    if col < left:
        return left - col
    if col > right:
        return col - right
    return 0


def solve(grid):
    """Extract the object most strongly indicated by the top-row 9 beacons."""
    marker_columns = [col for col, value in enumerate(grid[0]) if value == 9]
    if not marker_columns:
        raise ValueError("expected at least one colour-9 marker in the first row")

    candidates = []
    for colour, cells in _components(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)

        overlaps = sum(left <= marker <= right for marker in marker_columns)
        total_distance = sum(
            _horizontal_distance(marker, left, right) for marker in marker_columns
        )

        # More beacons vertically aligned with the object is strongest evidence.
        # For the one visible tie, the intended object is closer to the whole
        # beacon set, so total horizontal distance is the second criterion.
        key = (-overlaps, total_distance, -len(cells), top, left)
        candidates.append((key, colour, cells, (top, left, bottom, right)))

    if not candidates:
        raise ValueError("expected at least one object below the marker row")

    _, colour, cells, (top, left, bottom, right) = min(candidates, key=lambda item: item[0])
    occupied = set(cells)
    return [
        [colour if (row, col) in occupied else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
