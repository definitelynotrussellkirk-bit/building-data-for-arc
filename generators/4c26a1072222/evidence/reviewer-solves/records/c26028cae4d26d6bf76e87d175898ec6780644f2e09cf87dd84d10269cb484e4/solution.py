"""Visible-example solution for task 4c26a1072222.

Each nonzero two-row band contains a 2x2 source block A (columns 0-1), a
2x2 transformed/recolored example B (columns 3-4), and a 2x2 query block C
(columns 7-8).  Infer the best functional D4-transform/color-map relation
A -> B and apply it to C.
"""
from __future__ import annotations


def _source_position(transform: int, row: int, col: int) -> tuple[int, int]:
    """Return the source cell used by one of the eight 2x2 D4 transforms."""
    if transform == 0:      # identity
        return row, col
    if transform == 1:      # horizontal mirror
        return row, 1 - col
    if transform == 2:      # vertical mirror
        return 1 - row, col
    if transform == 3:      # 180-degree rotation
        return 1 - row, 1 - col
    if transform == 4:      # clockwise rotation
        return 1 - col, row
    if transform == 5:      # counter-clockwise rotation
        return col, 1 - row
    if transform == 6:      # main-diagonal transpose
        return col, row
    return 1 - col, 1 - row  # anti-diagonal transpose


def _transform(block: list[list[int]], transform: int) -> list[list[int]]:
    result: list[list[int]] = []
    for row in range(2):
        result_row: list[int] = []
        for col in range(2):
            source_row, source_col = _source_position(transform, row, col)
            result_row.append(block[source_row][source_col])
        result.append(result_row)
    return result


def _infer_relation(
    source: list[list[int]], target: list[list[int]]
) -> tuple[int, dict[int, int]]:
    """Choose the consistent relation with most literal matches, then lowest id."""
    candidates: list[tuple[int, int, dict[int, int]]] = []
    for transform in range(8):
        moved = _transform(source, transform)
        mapping: dict[int, int] = {}
        consistent = True
        score = 0
        for row in range(2):
            for col in range(2):
                source_color = moved[row][col]
                target_color = target[row][col]
                if source_color in mapping and mapping[source_color] != target_color:
                    consistent = False
                    break
                mapping[source_color] = target_color
                score += int(source_color == target_color)
            if not consistent:
                break
        if consistent:
            candidates.append((-score, transform, mapping))
    if not candidates:
        raise ValueError("band has no functional transform/color-map relation")
    _negative_score, transform, mapping = min(candidates, key=lambda item: (item[0], item[1]))
    return transform, mapping


def _read_block(grid: list[list[int]], row0: int, col0: int) -> list[list[int]]:
    return [
        [grid[row0 + row][col0 + col] for col in range(2)]
        for row in range(2)
    ]


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or any(len(row) != 9 for row in grid):
        raise ValueError("expected a nonempty 9-column grid")

    output = [[0, 0] for _ in grid]
    row0 = 0
    while row0 < len(grid):
        if all(value == 0 for value in grid[row0]):
            row0 += 1
            continue
        if row0 + 1 >= len(grid):
            raise ValueError("incomplete two-row band")

        source = _read_block(grid, row0, 0)
        target = _read_block(grid, row0, 3)
        query = _read_block(grid, row0, 7)
        transform, mapping = _infer_relation(source, target)
        moved_query = _transform(query, transform)
        for row in range(2):
            for col in range(2):
                color = moved_query[row][col]
                output[row0 + row][col] = mapping.get(color, color)
        row0 += 2

    return output
