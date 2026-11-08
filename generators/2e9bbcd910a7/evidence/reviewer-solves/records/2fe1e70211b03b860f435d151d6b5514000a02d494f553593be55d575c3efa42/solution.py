def solve(grid):
    """Highlight the longest clear diagonal, breaking ties toward the centre."""
    height = len(grid)
    width = len(grid[0])
    candidates = []

    # A candidate is a maximal contiguous run of zero cells along a diagonal.
    for dr, dc, central_signature in (
        (1, 1, (width - height) / 2),
        (1, -1, (height + width - 2) / 2),
    ):
        for row in range(height):
            for col in range(width):
                if grid[row][col] != 0:
                    continue
                prev_row, prev_col = row - dr, col - dc
                if (
                    0 <= prev_row < height
                    and 0 <= prev_col < width
                    and grid[prev_row][prev_col] == 0
                ):
                    continue

                cells = []
                r, c = row, col
                while 0 <= r < height and 0 <= c < width and grid[r][c] == 0:
                    cells.append((r, c))
                    r += dr
                    c += dc

                signature = col - row if dc == 1 else row + col
                distance_from_central_diagonal = abs(signature - central_signature)
                candidates.append(
                    (len(cells), -distance_from_central_diagonal, cells)
                )

    _, _, chosen = max(candidates, key=lambda item: (item[0], item[1]))
    result = [row[:] for row in grid]
    for row, col in chosen:
        result[row][col] = 8
    return result
