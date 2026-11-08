from collections import defaultdict


def solve(grid):
    """Connect exactly-two equal cells when they share a row or column.

    Colors are processed by the row-major position of their first occurrence,
    matching the visible examples' crossing behavior: a later-starting segment
    overwrites an earlier segment at an intersection.
    """
    out = [row[:] for row in grid]
    positions = defaultdict(list)

    # Python dictionaries preserve insertion order, so iterating positions
    # below follows the first row-major occurrence of each nonzero color.
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for value, cells in positions.items():
        if len(cells) != 2:
            continue

        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = value
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = value

    return out
