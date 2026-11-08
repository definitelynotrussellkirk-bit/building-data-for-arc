def solve(grid):
    """Intersect the left mask with a selector-transformed right mask."""
    selector = grid[0][0]
    left = [[grid[row][col] != 0 for col in range(3)] for row in range(1, 4)]
    right = [[grid[row][col] != 0 for col in range(4, 7)] for row in range(1, 4)]

    if selector == 6:
        right = right[::-1]  # reflect top-to-bottom
    elif selector == 8:
        right = [
            [right[2 - col][2 - row] for col in range(3)]
            for row in range(3)
        ]  # reflect across the top-right/bottom-left diagonal
    elif selector != 1:
        raise ValueError(f"unsupported selector color: {selector}")

    return [
        [7 if left[row][col] and right[row][col] else 0 for col in range(3)]
        for row in range(3)
    ]
