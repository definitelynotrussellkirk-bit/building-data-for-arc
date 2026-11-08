from collections import deque


def _components(grid):
    """Return same-colour 4-connected nonzero components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != colour:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            found.append((colour, cells))

    return found


def _crop_component(colour, cells):
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    crop = [
        [0 for _ in range(min_col, max_col + 1)]
        for _ in range(min_row, max_row + 1)
    ]
    for row, col in cells:
        crop[row - min_row][col - min_col] = colour
    return crop


def solve(grid):
    """Pack cropped objects by ascending occupied-cell count.

    Objects are top-aligned from left to right with one zero column between
    adjacent crops.  Background is zero and object colours are preserved.
    """
    if not grid or not grid[0]:
        return [[0]]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    components = _components(grid)
    if not components:
        return [[0]]

    # Visible examples have distinct sizes.  The geometric tie-breakers keep
    # behaviour deterministic without affecting the inferred ordering rule.
    components.sort(
        key=lambda item: (
            len(item[1]),
            min(row for row, _ in item[1]),
            min(col for _, col in item[1]),
            item[0],
        )
    )
    crops = [_crop_component(colour, cells) for colour, cells in components]

    output_height = max(len(crop) for crop in crops)
    output_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0] * output_width for _ in range(output_height)]

    offset = 0
    for crop in crops:
        for row, crop_row in enumerate(crop):
            for col, value in enumerate(crop_row):
                output[row][offset + col] = value
        offset += len(crop[0]) + 1

    return output
