def solve(grid):
    """Overlay each nonzero cell with its reflection across the main diagonal."""
    out = [row[:] for row in grid]
    height = len(grid)
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 0:
                continue
            if column_index < height and row_index < len(out[column_index]):
                # Visible examples never present conflicting nonzero colors at a
                # transposed pair. Preserve the explicit input value if one does.
                if out[column_index][row_index] == 0:
                    out[column_index][row_index] = value
    return out
