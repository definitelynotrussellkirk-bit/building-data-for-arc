"""Visible-example solution for aa0b08801e61."""


def solve(grid):
    """Recolor each monochrome object by its tight-mask reflection symmetries."""
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            mask = {(rr - top, cc - left) for rr, cc in cells}
            max_row = max(rr for rr, _ in mask)
            max_col = max(cc for _, cc in mask)

            left_right = {
                (rr, max_col - cc) for rr, cc in mask
            } == mask
            up_down = {
                (max_row - rr, cc) for rr, cc in mask
            } == mask

            if left_right and up_down:
                result_color = 8
            elif left_right:
                result_color = 2
            elif up_down:
                result_color = 3
            else:
                result_color = 4

            for rr, cc in cells:
                output[rr][cc] = result_color

    return output
