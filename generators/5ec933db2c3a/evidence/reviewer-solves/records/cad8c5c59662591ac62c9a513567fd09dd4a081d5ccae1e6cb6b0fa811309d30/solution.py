from __future__ import annotations

from copy import deepcopy


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid: list[list[int]]) -> list[list[list[int]]]:
    variants = []
    current = deepcopy(grid)
    for _ in range(4):
        variants.append(deepcopy(current))
        current = _rotate_cw(current)
    return variants


def _split_and_crop(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    height = len(grid)
    width = len(grid[0])
    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected one full-height color-9 divider, got {dividers}")
    divider = dividers[0]
    left = [row[:divider] for row in grid]
    board = [row[divider + 1 :] for row in grid]

    occupied = [
        (row, col)
        for row, values in enumerate(left)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    if not occupied:
        raise ValueError("left panel has no visible template")
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left_col = min(col for _, col in occupied)
    right_col = max(col for _, col in occupied)
    template = [row[left_col : right_col + 1] for row in left[top : bottom + 1]]
    return template, board


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Repair rotated template copies missing exactly two occupied cells."""
    template, board = _split_and_crop(grid)
    output = deepcopy(board)

    for variant in _rotations(template):
        template_h = len(variant)
        template_w = len(variant[0])
        for row0 in range(len(board) - template_h + 1):
            for col0 in range(len(board[0]) - template_w + 1):
                missing: list[tuple[int, int, int]] = []
                compatible = True
                for row, values in enumerate(variant):
                    for col, expected in enumerate(values):
                        actual = board[row0 + row][col0 + col]
                        if expected == 0:
                            if actual != 0:
                                compatible = False
                                break
                        elif actual == expected:
                            continue
                        elif actual == 0:
                            missing.append((row0 + row, col0 + col, expected))
                        else:
                            compatible = False
                            break
                    if not compatible:
                        break
                if compatible and len(missing) == 2:
                    for row, col, color in missing:
                        output[row][col] = color
    return output
