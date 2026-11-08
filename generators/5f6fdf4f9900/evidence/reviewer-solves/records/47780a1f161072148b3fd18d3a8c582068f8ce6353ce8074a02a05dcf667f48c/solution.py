def solve(grid):
    """Magnify the grid and draw open-corner diagonal continuations in red."""
    height = len(grid)
    width = len(grid[0])
    scale = len({value for row in grid for value in row if value != 0})

    output = [[0 for _ in range(width * scale)] for _ in range(height * scale)]

    # A zero cell can be reached diagonally from several colored cells.  The
    # examples resolve ties by the first source in row-major order: NW, NE,
    # SW, then SE relative to the zero cell.
    diagonal_sources = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            out_row = row * scale
            out_col = col * scale

            if value != 0:
                for dr in range(scale):
                    output[out_row + dr][out_col : out_col + scale] = [value] * scale
                continue

            chosen = None
            for source_dr, source_dc in diagonal_sources:
                source_row = row + source_dr
                source_col = col + source_dc
                if not (0 <= source_row < height and 0 <= source_col < width):
                    continue
                if grid[source_row][source_col] == 0:
                    continue

                # The diagonal is exposed only when both orthogonal cells in
                # the 2x2 corner are background.
                if grid[source_row][col] == 0 and grid[row][source_col] == 0:
                    chosen = (source_dr, source_dc)
                    break

            if chosen is None:
                continue

            source_dr, source_dc = chosen
            for offset in range(scale):
                diagonal_col = offset if source_dr == source_dc else scale - 1 - offset
                output[out_row + offset][out_col + diagonal_col] = 2

    return output
