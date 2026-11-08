from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand the zero-cell mask as its self-Kronecker product.

    Every zero in the input selects a block.  Each selected block repeats the
    input's zero pattern, painted with the input's nonzero color; unselected
    blocks and non-zero cells inside selected blocks remain background zero.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    foregrounds = {value for row in grid for value in row if value != 0}
    if len(foregrounds) != 1:
        raise ValueError("expected exactly one nonzero color")
    foreground = next(iter(foregrounds))

    zero_mask = [[value == 0 for value in row] for row in grid]
    output: list[list[int]] = []
    for outer_row in range(height):
        for inner_row in range(height):
            expanded_row: list[int] = []
            for outer_col in range(width):
                if zero_mask[outer_row][outer_col]:
                    expanded_row.extend(
                        foreground if is_zero else 0
                        for is_zero in zero_mask[inner_row]
                    )
                else:
                    expanded_row.extend([0] * width)
            output.append(expanded_row)
    return output
