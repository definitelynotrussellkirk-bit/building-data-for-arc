def solve(grid):
    """Select the panel indexed by the number of 7s and recolor it azure."""
    separator_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if row and all(cell == 9 for cell in row)
    ]
    if not separator_rows:
        raise ValueError("expected horizontal separator rows of color 9")

    selector = sum(cell == 7 for row in grid[: separator_rows[0]] for cell in row)
    panel_starts = [row_index + 1 for row_index in separator_rows]
    panel_ends = separator_rows[1:] + [len(grid)]
    panels = [grid[start:end] for start, end in zip(panel_starts, panel_ends)]

    if not 1 <= selector <= len(panels):
        raise ValueError("selector count must identify one panel")

    selected = panels[selector - 1]
    return [[8 if cell != 0 else 0 for cell in row] for row in selected]
