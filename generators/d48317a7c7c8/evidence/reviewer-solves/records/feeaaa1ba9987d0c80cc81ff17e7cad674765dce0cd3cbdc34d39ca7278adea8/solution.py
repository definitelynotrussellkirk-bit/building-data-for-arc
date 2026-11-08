def solve(grid):
    """Mark the two missing cells implied by the marker and line motifs."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    def inside(row, col):
        return 0 <= row < height and 0 <= col < width

    def components_of(color):
        remaining = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        }
        components = []
        while remaining:
            seed = remaining.pop()
            component = {seed}
            stack = [seed]
            while stack:
                row, col = stack.pop()
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (row + drow, col + dcol)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
            components.append(component)
        return components

    # Color 4 forms the candidate motifs.  The other non-background color has
    # one straight triple and one isolated cell; its singleton is the pointer.
    counts = {}
    for row in grid:
        for color in row:
            if color:
                counts[color] = counts.get(color, 0) + 1
    marker_colors = [color for color, count in counts.items() if color != 4 and count == 4]
    if not marker_colors:
        return result
    marker_color = marker_colors[0]
    marker_components = components_of(marker_color)
    singleton_components = [component for component in marker_components if len(component) == 1]
    if len(singleton_components) != 1:
        return result
    marker_singleton = next(iter(singleton_components[0]))

    # Enumerate maximal horizontal and vertical runs of exactly three 4s.
    runs = []
    for row in range(height):
        col = 0
        while col < width:
            if grid[row][col] != 4:
                col += 1
                continue
            start = col
            while col < width and grid[row][col] == 4:
                col += 1
            if col - start == 3:
                runs.append(((row, start), (0, 1)))
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 4:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 4:
                row += 1
            if row - start == 3:
                runs.append(((start, col), (1, 0)))

    additions = set()
    for (start_row, start_col), (drow, dcol) in runs:
        end_row = start_row + 2 * drow
        end_col = start_col + 2 * dcol
        for anchor_row, anchor_col, outward_row, outward_col in (
            (start_row, start_col, -drow, -dcol),
            (end_row, end_col, drow, dcol),
        ):
            beyond = (anchor_row + outward_row, anchor_col + outward_col)
            if not inside(*beyond):
                continue

            # A marker singleton touching one end points to an extension at the
            # opposite end of the three-cell run.
            if beyond == marker_singleton:
                opposite_anchor = (end_row, end_col) if (anchor_row, anchor_col) == (start_row, start_col) else (start_row, start_col)
                opposite = (
                    opposite_anchor[0] - outward_row,
                    opposite_anchor[1] - outward_col,
                )
                if inside(*opposite) and grid[opposite[0]][opposite[1]] == 0:
                    additions.add(opposite)

            # A blank just beyond a run, with an isolated 4 diagonally beside
            # that blank, is the missing elbow that joins the pieces.
            if grid[beyond[0]][beyond[1]] != 0:
                continue
            perpendiculars = ((-outward_col, outward_row), (outward_col, -outward_row))
            for prow, pcol in perpendiculars:
                side = (beyond[0] + prow, beyond[1] + pcol)
                if not inside(*side) or grid[side[0]][side[1]] != 4:
                    continue
                same_color_neighbors = 0
                for nrow, ncol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (side[0] + nrow, side[1] + ncol)
                    if inside(*neighbor) and grid[neighbor[0]][neighbor[1]] == 4:
                        same_color_neighbors += 1
                if same_color_neighbors == 0:
                    additions.add(beyond)

    for row, col in additions:
        result[row][col] = 8
    return result
