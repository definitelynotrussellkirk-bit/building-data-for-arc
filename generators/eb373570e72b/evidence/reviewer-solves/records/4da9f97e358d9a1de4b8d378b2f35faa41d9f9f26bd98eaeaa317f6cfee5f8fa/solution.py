from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Simulate the visible right-falling domino chains.

    Nonzero columns are vertical dominoes resting on the bottom row.  Green
    dominoes (1) are already activated.  A fallen domino reaches the domino
    exactly three columns to its right, so activation propagates through runs
    with spacing three.  Activated dominoes lie on the bottom row; inactive red
    dominoes (2) remain standing and are drawn for the full grid height.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])

    # Each object is a bottom-anchored nonzero vertical column.  The bottom cell
    # gives its color in every visible example.
    columns = [c for c in range(width) if any(grid[r][c] != 0 for r in range(height))]
    colors = {c: grid[height - 1][c] for c in columns}

    toppled = {c for c in columns if colors[c] == 1}
    column_set = set(columns)

    # A falling domino has a three-cell horizontal footprint and therefore
    # triggers the next domino when its anchor is exactly three cells away.
    frontier = list(toppled)
    while frontier:
        c = frontier.pop()
        nxt = c + 3
        if nxt in column_set and nxt not in toppled:
            toppled.add(nxt)
            frontier.append(nxt)

    standing = sorted(c for c in columns if c not in toppled)
    out = [[0 for _ in range(width)] for _ in range(height)]

    # Red dominoes not reached by a green chain remain vertical.
    for c in standing:
        for r in range(height):
            out[r][c] = colors[c]

    # Draw each toppled domino on the bottom.  A final domino stops one blank
    # cell before the next standing domino; otherwise it occupies up to three
    # cells or the remaining width.
    for c in sorted(toppled):
        next_standing = next((s for s in standing if s > c), None)
        end = min(width, c + 3)
        if next_standing is not None:
            end = min(end, max(c + 1, next_standing - 1))
        for x in range(c, end):
            out[height - 1][x] = colors[c]

    return out
