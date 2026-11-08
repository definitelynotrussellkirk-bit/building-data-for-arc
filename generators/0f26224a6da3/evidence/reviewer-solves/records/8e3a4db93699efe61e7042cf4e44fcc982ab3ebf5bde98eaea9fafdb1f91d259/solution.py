def solve(grid):
    """Expand each orthogonally isolated nonzero cell into a clipped plus."""
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    output = [row[:] for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0:
                continue
            has_orthogonal_neighbor = any(
                0 <= row + dr < height
                and 0 <= column + dc < width
                and grid[row + dr][column + dc] != 0
                for dr, dc in directions
            )
            if has_orthogonal_neighbor:
                continue
            for dr, dc in ((0, 0), *directions):
                rr, cc = row + dr, column + dc
                if 0 <= rr < height and 0 <= cc < width and output[rr][cc] == 0:
                    output[rr][cc] = color

    return output
