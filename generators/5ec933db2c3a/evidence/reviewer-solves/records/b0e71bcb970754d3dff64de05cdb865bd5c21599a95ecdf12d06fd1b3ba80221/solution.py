from __future__ import annotations


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _rotations(grid: list[list[int]]) -> list[list[list[int]]]:
    result: list[list[list[int]]] = []
    current = [row[:] for row in grid]
    for _ in range(4):
        if current not in result:
            result.append([row[:] for row in current])
        current = _rotate_ccw(current)
    return result


def _compatible_with_two_missing(
    fragment: list[list[int]], target: list[list[int]]
) -> bool:
    missing = 0
    for fragment_row, target_row in zip(fragment, target):
        for observed, expected in zip(fragment_row, target_row):
            if observed != 0 and observed != expected:
                return False
            if observed == 0 and expected != 0:
                missing += 1
    return missing == 2


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete the two-cell-deficient rotated copies to the right of color 9."""
    height = len(grid)
    width = len(grid[0])

    separator = next(
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    )
    key_panel = [row[:separator] for row in grid]
    result = [row[separator + 1 :] for row in grid]

    key = _crop_nonzero(key_panel)
    key_height = len(key)
    key_width = len(key[0])
    candidates = _rotations(key)

    # The right panel is a 2x2 display of key-sized corner cells, with blank
    # separator rows/columns between them.
    row_starts = [0, len(result) - key_height]
    col_starts = [0, len(result[0]) - key_width]

    for row_start in row_starts:
        for col_start in col_starts:
            fragment = [
                row[col_start : col_start + key_width]
                for row in result[row_start : row_start + key_height]
            ]
            matches = [
                candidate
                for candidate in candidates
                if len(candidate) == key_height
                and len(candidate[0]) == key_width
                and _compatible_with_two_missing(fragment, candidate)
            ]
            if len(matches) == 1:
                completed = matches[0]
                for r in range(key_height):
                    for c in range(key_width):
                        result[row_start + r][col_start + c] = completed[r][c]

    return result
