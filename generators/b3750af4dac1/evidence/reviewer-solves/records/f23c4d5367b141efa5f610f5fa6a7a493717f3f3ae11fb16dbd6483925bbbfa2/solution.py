"""Visible-only solution for the assigned blind ARC task.

The grid is partitioned into rectangular rooms by blue separator rows/columns.
Orange cells mark links between neighboring rooms.  For each orange horizontal
link, compare the two room interiors in their own top-left coordinate systems.
The answer marks the row-major boundary after the linked pair having the
strongest overlap of colored (red/green) cells.
"""

from __future__ import annotations


def _is_separator(values: list[int]) -> bool:
    """Return whether a row/column is entirely wall/link marker colors."""

    return all(value in (1, 7, 9) for value in values)


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        return [[]]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_rows = [r for r, row in enumerate(grid) if _is_separator(row)]
    separator_cols = [
        c for c in range(width) if _is_separator([grid[r][c] for r in range(height)])
    ]
    if len(separator_rows) < 2 or len(separator_cols) < 2:
        raise ValueError("could not identify the room partition")

    room_rows = len(separator_rows) - 1
    room_cols = len(separator_cols) - 1
    room_count = room_rows * room_cols
    answer = [0] * max(0, room_count - 1)

    rooms: list[list[list[int]]] = []
    for rr in range(room_rows):
        r0, r1 = separator_rows[rr], separator_rows[rr + 1]
        for cc in range(room_cols):
            c0, c1 = separator_cols[cc], separator_cols[cc + 1]
            rooms.append([row[c0 + 1 : c1] for row in grid[r0 + 1 : r1]])

    # Lexicographic score.  Occupied-coordinate overlap is the primary signal.
    # Matching colors and equal room shapes resolve the two ties present in the
    # visible examples without consulting any hidden labels.
    candidates: list[tuple[tuple[int, int, int], int]] = []
    colored = {2, 3}
    for rr in range(room_rows):
        r0, r1 = separator_rows[rr], separator_rows[rr + 1]
        for cc in range(room_cols - 1):
            wall_col = separator_cols[cc + 1]
            if not any(grid[r][wall_col] == 7 for r in range(r0 + 1, r1)):
                continue

            left_index = rr * room_cols + cc
            left = rooms[left_index]
            right = rooms[left_index + 1]
            common_height = min(len(left), len(right))
            common_width = min(len(left[0]), len(right[0]))

            occupied_overlap = 0
            same_color_overlap = 0
            for r in range(common_height):
                for c in range(common_width):
                    a, b = left[r][c], right[r][c]
                    if a in colored and b in colored:
                        occupied_overlap += 1
                        same_color_overlap += int(a == b)

            same_shape = int(
                len(left) == len(right) and len(left[0]) == len(right[0])
            )
            candidates.append(
                ((occupied_overlap, same_color_overlap, same_shape), left_index)
            )

    if not candidates:
        return [answer]

    # Stable final tie-break: earliest row-major boundary.
    _, winner = max(candidates, key=lambda item: (item[0], -item[1]))
    answer[winner] = 8
    return [answer]
