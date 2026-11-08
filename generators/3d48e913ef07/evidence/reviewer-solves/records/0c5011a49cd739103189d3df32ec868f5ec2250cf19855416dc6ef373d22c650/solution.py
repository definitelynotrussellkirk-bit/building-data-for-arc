from collections import deque


def _gray_components(grid):
    """Return 4-connected color-3 components as coordinate lists."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 3 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(component)

    return components


def solve(grid):
    # The non-gray singleton cells in the left column form the output palette,
    # read from top to bottom. Gray objects are ranked by area, largest first.
    colors = [row[0] for row in grid if row[0] not in (0, 3)]
    components = _gray_components(grid)
    components.sort(key=lambda cells: (-len(cells), min(cells)))

    if not components:
        return []

    crops = []
    max_width = 0
    for color, cells in zip(colors, components):
        min_row = min(row for row, _ in cells)
        max_row = max(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        max_col = max(col for _, col in cells)
        crop_height = max_row - min_row + 1
        crop_width = max_col - min_col + 1
        crop = [[0] * crop_width for _ in range(crop_height)]
        for row, col in cells:
            crop[row - min_row][col - min_col] = color
        crops.append(crop)
        max_width = max(max_width, crop_width)

    output = []
    for index, crop in enumerate(crops):
        output.extend(row + [0] * (max_width - len(row)) for row in crop)
        if index + 1 < len(crops):
            output.append([0] * max_width)
    return output
