def solve(grid):
    """Count sliding 2x2 all-1 windows and encode the count in a 1x5 bar."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    count = 0
    for row in range(height - 1):
        for col in range(width - 1):
            if all(
                grid[row + dr][col + dc] == 1
                for dr in (0, 1)
                for dc in (0, 1)
            ):
                count += 1
    if not 0 <= count <= 5:
        raise ValueError(f"visible task encodes only counts 0..5; found {count}")
    return [[1] * count + [0] * (5 - count)]
