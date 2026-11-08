def solve(grid):
    """Trace each color-2 ray from left to right and paint its route cyan."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    def turn(color, dr, dc):
        if color == 4:       # slash mirror: /
            return -dc, -dr
        if color == 5:       # backslash mirror: \
            return dc, dr
        return dr, dc

    for source_row in range(height):
        for source_col in range(width):
            if grid[source_row][source_col] != 2:
                continue
            row, col = source_row, source_col
            dr, dc = 0, 1
            seen = set()
            while True:
                row += dr
                col += dc
                if not (0 <= row < height and 0 <= col < width):
                    break
                state = (row, col, dr, dc)
                if state in seen:
                    break
                seen.add(state)
                value = grid[row][col]
                if value in (2, 6):
                    break
                output[row][col] = 8
                if value in (4, 5):
                    dr, dc = turn(value, dr, dc)
    return output
