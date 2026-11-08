"""Transfer the demonstrated panel edits using the objects' top-left anchors."""


def solve(grid):
    height = len(grid)
    panel_width = (len(grid[0]) - 2) // 3
    first = [row[:panel_width] for row in grid]
    second = [row[panel_width + 1:2 * panel_width + 1] for row in grid]
    target = [row[2 * panel_width + 2:] for row in grid]

    def anchor(panel):
        cells = [(r, c) for r, row in enumerate(panel)
                 for c, value in enumerate(row) if value != 0]
        return min(r for r, _ in cells), min(c for _, c in cells)

    source_top, source_left = anchor(first)
    target_top, target_left = anchor(target)
    dr, dc = target_top - source_top, target_left - source_left
    output = [row[:] for row in target]
    for r in range(height):
        for c in range(panel_width):
            if second[r][c] != first[r][c]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < panel_width:
                    output[rr][cc] = second[r][c]
    return output
