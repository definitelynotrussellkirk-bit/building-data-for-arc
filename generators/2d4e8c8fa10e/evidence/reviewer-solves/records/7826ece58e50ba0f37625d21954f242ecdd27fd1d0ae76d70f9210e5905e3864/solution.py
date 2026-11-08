def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            component = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                component.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [row for row, _ in component]
            cols = [col for _, col in component]
            is_solid_2x2 = (
                len(component) == 4
                and max(rows) - min(rows) == 1
                and max(cols) - min(cols) == 1
            )
            if is_solid_2x2:
                for row, col in component:
                    output[row][col] = color

    return output
