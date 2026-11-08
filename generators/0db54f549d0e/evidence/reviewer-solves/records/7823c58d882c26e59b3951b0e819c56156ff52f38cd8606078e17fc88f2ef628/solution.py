def solve(grid):
    """Render the four occupancy intersections inferred from visible examples."""
    answer = [[0 for _ in range(7)] for _ in range(7)]
    for panel_row, input_row in enumerate((0, 4)):
        for panel_col, input_col in enumerate((4, 8)):
            for row in range(3):
                for col in range(3):
                    if grid[input_row + row][col] != 0 and grid[row][input_col + col] != 0:
                        answer[panel_row * 4 + row][panel_col * 4 + col] = 8
    return answer
