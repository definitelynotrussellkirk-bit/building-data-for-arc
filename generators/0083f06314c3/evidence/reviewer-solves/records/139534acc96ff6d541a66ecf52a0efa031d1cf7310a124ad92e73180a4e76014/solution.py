"""Visible-example Python solution. Standard library only; input is not mutated."""
from __future__ import annotations


def _scene(grid: list[list[int]]):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    separators = [c for c in range(width) if all(row[c] == 9 for row in grid)]
    boundaries = [-1, *separators, width]
    panels = [[row[left + 1:right] for row in grid]
              for left, right in zip(boundaries, boundaries[1:]) if right > left + 1]
    if len(panels) != 4:
        raise ValueError("expected four panels separated by color 9")
    selectors = [v for row in panels[2] for v in row if v]
    if len(selectors) != 1:
        raise ValueError("expected one selector cell")
    selected = panels[0] if selectors[0] == 2 else panels[1]
    filled = [(r, c, v) for r, row in enumerate(selected) for c, v in enumerate(row) if v]
    if not filled:
        raise ValueError("selected template is empty")
    r_min = min(r for r, c, v in filled)
    c_min = min(c for r, c, v in filled)
    h = max(r for r, c, v in filled) - r_min + 1
    w = max(c for r, c, v in filled) - c_min + 1
    mask = [(r - r_min, c - c_min, v) for r, c, v in filled]
    return panels[3], mask, h, w, selectors[0]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Find all exact-colored, unrotated template masks; union them in color 8."""
    board, mask, template_h, template_w, _ = _scene(grid)
    height, width = len(board), len(board[0])
    answer = [[0 for _ in range(width)] for _ in range(height)]
    for top in range(height - template_h + 1):
        for left in range(width - template_w + 1):
            if all(board[top + dr][left + dc] == value for dr, dc, value in mask):
                for dr, dc, value in mask:
                    answer[top + dr][left + dc] = 8
    return answer
