from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mark each board window matching the left-panel template.

    The single full-height 9 column separates a template panel from the search
    board.  Crop the template to its nonzero bounding box; nonzero template
    cells must match exactly, while zero cells are wildcards.  For each match,
    mark the matched window's bottom-right corner with 8.
    """
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    dividers = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected one full-height 9 divider, got {dividers}")
    divider = dividers[0]
    panel = [row[:divider] for row in grid]
    board = [row[divider + 1 :] for row in grid]

    occupied = [
        (row, column)
        for row, values in enumerate(panel)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        raise ValueError("template panel is empty")
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(column for _, column in occupied)
    right = max(column for _, column in occupied)
    template = [row[left : right + 1] for row in panel[top : bottom + 1]]

    template_height = len(template)
    template_width = len(template[0])
    board_height = len(board)
    board_width = len(board[0])
    output = [[0] * board_width for _ in range(board_height)]
    for row0 in range(board_height - template_height + 1):
        for column0 in range(board_width - template_width + 1):
            if all(
                template[row][column] == 0
                or board[row0 + row][column0 + column] == template[row][column]
                for row in range(template_height)
                for column in range(template_width)
            ):
                output[row0 + template_height - 1][column0 + template_width - 1] = 8
    return output
