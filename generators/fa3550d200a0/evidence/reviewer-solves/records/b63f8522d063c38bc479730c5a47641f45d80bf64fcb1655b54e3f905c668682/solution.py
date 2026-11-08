"""Visible-example-only solution for the blind ARC episode."""


def _components(grid, background=0):
    """Return 4-connected non-background components as coordinate lists."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                cur_row, cur_col = stack.pop()
                component.append((cur_row, cur_col))
                for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt_row = cur_row + d_row
                    nxt_col = cur_col + d_col
                    if not (0 <= nxt_row < height and 0 <= nxt_col < width):
                        continue
                    if grid[nxt_row][nxt_col] == background:
                        continue
                    if (nxt_row, nxt_col) in seen:
                        continue
                    seen.add((nxt_row, nxt_col))
                    stack.append((nxt_row, nxt_col))
            components.append(component)

    return components


def solve(grid):
    """Stamp each matching blue template onto the large colored rectangle."""
    if not grid or not grid[0]:
        return []

    components = _components(grid)
    if not components:
        return []

    # The output canvas is the largest nonzero component: a fully occupied
    # rectangle whose rare colors serve as anchors for the detached templates.
    canvas = max(components, key=len)
    canvas_cells = set(canvas)
    top = min(row for row, _ in canvas)
    bottom = max(row for row, _ in canvas)
    left = min(col for _, col in canvas)
    right = max(col for _, col in canvas)

    output = [row[left : right + 1] for row in grid[top : bottom + 1]]

    counts = {}
    for row in output:
        for color in row:
            counts[color] = counts.get(color, 0) + 1
    canvas_color = max(counts, key=counts.get)

    anchors = {}
    for row in range(len(output)):
        for col in range(len(output[0])):
            color = output[row][col]
            if color != canvas_color:
                anchors.setdefault(color, []).append((row, col))

    # Every detached template consists of blue (2) cells plus one colored
    # anchor.  Preserve the template's offsets and align its anchor with the
    # same-colored cell inside the output canvas.  Distractor templates whose
    # anchor color is absent from the canvas are ignored.
    for component in components:
        if any(cell in canvas_cells for cell in component):
            continue

        non_blue = [
            (row, col, grid[row][col])
            for row, col in component
            if grid[row][col] != 2
        ]
        blue = [(row, col) for row, col in component if grid[row][col] == 2]
        if len(non_blue) != 1 or not blue:
            continue

        anchor_row, anchor_col, anchor_color = non_blue[0]
        if anchor_color not in anchors:
            continue

        offsets = [
            (row - anchor_row, col - anchor_col)
            for row, col in blue
        ]
        for target_row, target_col in anchors[anchor_color]:
            for d_row, d_col in offsets:
                row = target_row + d_row
                col = target_col + d_col
                if 0 <= row < len(output) and 0 <= col < len(output[0]):
                    output[row][col] = 2

    return output
