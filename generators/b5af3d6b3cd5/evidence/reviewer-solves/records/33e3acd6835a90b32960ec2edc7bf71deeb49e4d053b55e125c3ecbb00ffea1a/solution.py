def solve(grid):
    """Let every colored cell fall downward inside the gray-wall compartments."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    for col in range(width):
        row = 0
        while row < height:
            if out[row][col] == 5:
                row += 1
                continue

            start = row
            while row < height and out[row][col] != 5:
                row += 1
            end = row

            falling = [out[r][col] for r in range(start, end) if out[r][col] != 0]
            empty_count = (end - start) - len(falling)
            packed = [0] * empty_count + falling
            for offset, value in enumerate(packed):
                out[start + offset][col] = value

    return out
