from collections import Counter, deque


def _components(grid, background):
    """Return monochrome 4-connected non-background components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    owner = {}

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            cells = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))

            component_id = len(components)
            components.append((color, cells))
            for cell in cells:
                owner[cell] = component_id

    return components, owner


def solve(grid):
    """Slide each upper touching object left and each lower object right."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    components, owner = _components(grid, background)

    # A vertical contact between differently colored components identifies a pair.
    # The upper member moves one column left; the lower member moves one right.
    horizontal_votes = [0] * len(components)
    for row in range(height - 1):
        for col in range(width):
            upper = owner.get((row, col))
            lower = owner.get((row + 1, col))
            if upper is None or lower is None or upper == lower:
                continue
            horizontal_votes[upper] -= 1
            horizontal_votes[lower] += 1

    result = [[background for _ in range(width)] for _ in range(height)]
    for component_id, (color, cells) in enumerate(components):
        vote = horizontal_votes[component_id]
        shift = -1 if vote < 0 else 1 if vote > 0 else 0
        for row, col in cells:
            target_col = col + shift
            # Generated examples provide a one-cell horizontal margin. Keeping an
            # out-of-range cell in place is safer than silently deleting it.
            if not 0 <= target_col < width:
                target_col = col
            result[row][target_col] = color

    return result
