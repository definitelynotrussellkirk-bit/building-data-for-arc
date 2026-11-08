from __future__ import annotations


def _border_side(grid: list[list[int]]) -> str:
    """Return the edge marked by the solid line of 1s."""
    height = len(grid)
    width = len(grid[0])

    if all(grid[0][column] == 1 for column in range(width)):
        return "top"
    if all(grid[height - 1][column] == 1 for column in range(width)):
        return "bottom"
    if all(grid[row][0] == 1 for row in range(height)):
        return "left"
    if all(grid[row][width - 1] == 1 for row in range(height)):
        return "right"
    raise ValueError("expected one edge to be a solid line of 1s")


def _macro_grid(grid: list[list[int]], side: str) -> list[list[int]]:
    """Decode the seven-by-seven lattice of hollow 3x3 tiles."""
    row_offset = 2 if side == "top" else 1
    column_offset = 2 if side == "left" else 1

    macro: list[list[int]] = []
    for macro_row in range(7):
        row: list[int] = []
        top = row_offset + 4 * macro_row
        for macro_column in range(7):
            left = column_offset + 4 * macro_column
            color = 0
            for r in range(top, top + 3):
                for c in range(left, left + 3):
                    if grid[r][c] != 0:
                        color = grid[r][c]
                        break
                if color:
                    break
            row.append(color)
        macro.append(row)
    return macro


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Remove the central gutter and compact tiles in the marked direction."""
    side = _border_side(grid)
    macro = _macro_grid(grid, side)

    if side in {"top", "bottom"}:
        # The seven-by-seven lattice contains a blank middle column separating
        # the two three-column panels.
        panel = [row[:3] + row[4:] for row in macro]
        result: list[list[int]] = []
        for row in panel:
            colors = [value for value in row if value != 0]
            padding = [0] * (6 - len(colors))
            result.append(
                padding + colors if side == "top" else colors + padding
            )
        return result

    # Left/right markers use a blank middle row between two three-row panels.
    panel = macro[:3] + macro[4:]
    result = [[0] * 7 for _ in range(6)]
    for column in range(7):
        colors = [panel[row][column] for row in range(6) if panel[row][column] != 0]
        start = 0 if side == "left" else 6 - len(colors)
        for offset, color in enumerate(colors):
            result[start + offset][column] = color
    return result
