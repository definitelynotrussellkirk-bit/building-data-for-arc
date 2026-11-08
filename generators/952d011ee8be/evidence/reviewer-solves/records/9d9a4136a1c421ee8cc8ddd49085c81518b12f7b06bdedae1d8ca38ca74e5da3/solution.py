from __future__ import annotations


def solve(grid):
    """Fill each wall-bounded chamber from its blue-dot count and top legend."""
    out = [list(row) for row in grid]
    if not out:
        return out
    legend = [value for value in out[0] if value != 0]
    if len(legend) != 3:
        raise ValueError("expected three nonzero legend entries in the first row")

    height = len(out)
    width = len(out[0])
    remaining = {
        (row, col)
        for row in range(2, height)
        for col in range(width)
        if out[row][col] != 5
    }
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = []
        queue = [start]
        for row, col in queue:
            component.append((row, col))
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)

        dot_count = sum(grid[row][col] == 1 for row, col in component)
        fill = legend[-1] if dot_count == 0 else legend[dot_count - 1]
        for row, col in component:
            out[row][col] = fill
    return out
