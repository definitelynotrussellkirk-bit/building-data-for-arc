"""Visible-example solution for the blind ARC episode."""

PALETTE = (5, 2, 8, 9, 6)
BACKGROUND = 7
OUTPUT_HEIGHT = 4


def _count_components_8(grid, color):
    """Count monochromatic components using king-move adjacency."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    count = 0

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            count += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == 0 and col_delta == 0:
                            continue
                        next_row = current_row + row_delta
                        next_col = current_col + col_delta
                        if not (0 <= next_row < height and 0 <= next_col < width):
                            continue
                        point = (next_row, next_col)
                        if point in seen or grid[next_row][next_col] != color:
                            continue
                        seen.add(point)
                        stack.append(point)
    return count


def solve(grid):
    """Render component counts as bottom-aligned palette columns."""
    output = [[BACKGROUND for _ in PALETTE] for _ in range(OUTPUT_HEIGHT)]
    for col, color in enumerate(PALETTE):
        component_count = _count_components_8(grid, color)
        for row in range(OUTPUT_HEIGHT - component_count, OUTPUT_HEIGHT):
            if 0 <= row < OUTPUT_HEIGHT:
                output[row][col] = color
    return output
