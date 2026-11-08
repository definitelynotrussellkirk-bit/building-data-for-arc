"""Infer a marked panel's edge-anchored pattern from a visible ARC grid."""

from collections import Counter, deque


def solve(grid):
    """Copy the widest marked panel onto the sole unmarked panel's canvas."""
    if not grid or not grid[0]:
        raise ValueError("Expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")

    background = grid[0][0]
    seen = set()
    panels = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] != background
                            and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        queue.append((rr, cc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            panel_height = bottom - top + 1
            panel_width = right - left + 1
            if len(cells) != panel_height * panel_width:
                raise ValueError("Expected separated, filled rectangular panels")
            base = Counter(grid[r][c] for r, c in cells).most_common(1)[0][0]
            markers = [(r - top, c - left, grid[r][c])
                       for r, c in cells if grid[r][c] != base]
            panels.append((panel_height, panel_width, base, markers))

    blanks = [panel for panel in panels if not panel[3]]
    donors = [panel for panel in panels if panel[3]]
    if len(blanks) != 1 or not donors:
        raise ValueError("Expected one unmarked panel and at least one marked panel")
    out_height, out_width, out_color, _ = blanks[0]
    donor_height, donor_width, _, markers = max(donors, key=lambda p: (p[1], p[0]))
    output = [[out_color] * out_width for _ in range(out_height)]

    def edge_positions(position, source_size, destination_size):
        opposite = source_size - 1 - position
        positions = set()
        if position <= opposite:
            positions.add(position)
        if opposite <= position:
            positions.add(destination_size - 1 - opposite)
        return [p for p in positions if 0 <= p < destination_size]

    for row, col, color in markers:
        for out_row in edge_positions(row, donor_height, out_height):
            for out_col in edge_positions(col, donor_width, out_width):
                output[out_row][out_col] = color
    return output
