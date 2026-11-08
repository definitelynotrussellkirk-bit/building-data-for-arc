from __future__ import annotations


def _spans(length: int, separators: list[int]) -> list[tuple[int, int]]:
    bounds = [-1, *separators, length]
    return [(left + 1, right) for left, right in zip(bounds, bounds[1:]) if right > left + 1]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Return the unique separator-delimited block with one nonzero color."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    height, width = len(grid), len(grid[0])
    full_rows: dict[int, list[int]] = {}
    for r, row in enumerate(grid):
        if row[0] != 0 and all(value == row[0] for value in row):
            full_rows.setdefault(row[0], []).append(r)

    full_cols: dict[int, list[int]] = {}
    for c in range(width):
        color = grid[0][c]
        if color != 0 and all(grid[r][c] == color for r in range(height)):
            full_cols.setdefault(color, []).append(c)

    shared = set(full_rows) & set(full_cols)
    if not shared:
        raise ValueError("no shared full-row/full-column separator color")
    separator = max(shared, key=lambda color: (len(full_rows[color]) * len(full_cols[color]), -color))

    candidates: list[list[list[int]]] = []
    for r0, r1 in _spans(height, full_rows[separator]):
        for c0, c1 in _spans(width, full_cols[separator]):
            block = [row[c0:c1] for row in grid[r0:r1]]
            colors = {value for row in block for value in row if value not in (0, separator)}
            if len(colors) == 1:
                candidates.append(block)

    if len(candidates) != 1:
        raise ValueError(f"expected one single-color block, found {len(candidates)}")
    return candidates[0]
