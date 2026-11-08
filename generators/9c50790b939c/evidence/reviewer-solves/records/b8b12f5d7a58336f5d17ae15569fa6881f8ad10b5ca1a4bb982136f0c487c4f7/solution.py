"""Infer the transfer between vertical bars from the visible demonstrations."""


def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    bars = []
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] not in (8, 9):
                row += 1
                continue
            start = row
            while row < height and grid[row][col] in (8, 9):
                row += 1
            marks = [r for r in range(start, row) if grid[r][col] == 9]
            bars.append((row - start, col, start, row, marks))
    marked = [bar for bar in bars if bar[4]]
    if len(marked) != 1:
        raise ValueError("Expected exactly one marked vertical bar")
    length, source_col, source_start, source_end, marks = marked[0]
    longer = [bar for bar in bars if bar[0] > length]
    if not longer:
        raise ValueError("No longer bar is visible")
    target_length = min(bar[0] for bar in longer)
    targets = [bar for bar in longer if bar[0] == target_length]
    if len(targets) != 1:
        raise ValueError("The next longer bar is not unique")
    _, col, start, end, _ = targets[0]
    for row in marks:
        out[row][source_col] = 8
    count = len(marks) + 1
    if marks[0] == source_start:
        positions = range(start, start + count)
    elif marks[-1] == source_end - 1:
        positions = range(end - count, end)
    else:
        raise ValueError("The highlighted segment is not at a bar endpoint")
    for row in positions:
        out[row][col] = 9
    return out
