"""Visible-only solution for blind ARC task 1a5d49e539de."""


def _objects_8(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []
    directions = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    ]

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in directions:
                    neighbor = (current_row + dr, current_col + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            objects.append((color, cells))
    return objects


def _crop_object(color, cells):
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    cell_set = set(cells)
    return [
        [color if (row, col) in cell_set else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def solve(grid):
    """Return the unique 8-connected object lacking left-right symmetry."""
    candidates = []
    for color, cells in _objects_8(grid):
        crop = _crop_object(color, cells)
        if crop != [row[::-1] for row in crop]:
            candidates.append(crop)

    if len(candidates) != 1:
        raise ValueError(f"expected one horizontally asymmetric object, found {len(candidates)}")
    return candidates[0]
