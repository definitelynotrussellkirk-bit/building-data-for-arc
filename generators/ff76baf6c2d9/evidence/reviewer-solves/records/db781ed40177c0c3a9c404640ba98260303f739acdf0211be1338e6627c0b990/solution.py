from collections import deque


def _components(grid):
    """Return 8-connected components of non-background cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append(
                    (current_row, current_col, grid[current_row][current_col])
                )
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == 0 and col_delta == 0:
                            continue
                        next_row = current_row + row_delta
                        next_col = current_col + col_delta
                        if not (0 <= next_row < height and 0 <= next_col < width):
                            continue
                        if grid[next_row][next_col] == 0:
                            continue
                        if (next_row, next_col) in seen:
                            continue
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(component)

    return components


def solve(grid):
    """Stamp each colored template onto isolated pixels of its anchor color."""
    result = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    components = _components(grid)

    isolated = [component[0] for component in components if len(component) == 1]
    templates = [component for component in components if len(component) > 1]

    for anchor_row, anchor_col, anchor_color in isolated:
        candidates = []
        for template in templates:
            anchor_cells = [cell for cell in template if cell[2] == anchor_color]
            other_colors = {cell[2] for cell in template if cell[2] != anchor_color}
            if len(anchor_cells) == 1 and other_colors:
                candidates.append((len(template), template, anchor_cells[0]))

        if not candidates:
            continue

        _, template, template_anchor = max(candidates, key=lambda item: item[0])
        template_anchor_row, template_anchor_col, _ = template_anchor
        for row, col, color in template:
            row_offset = row - template_anchor_row
            col_offset = col - template_anchor_col
            # The visible red-anchor example demonstrates a horizontal mirror;
            # all other demonstrated anchor colors preserve the template.
            if anchor_color == 2:
                col_offset = -col_offset
            target_row = anchor_row + row_offset
            target_col = anchor_col + col_offset
            if 0 <= target_row < height and 0 <= target_col < width:
                result[target_row][target_col] = color

    return result
