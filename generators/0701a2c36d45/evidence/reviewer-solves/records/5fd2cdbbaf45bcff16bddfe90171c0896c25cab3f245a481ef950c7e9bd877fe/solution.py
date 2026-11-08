from __future__ import annotations


def _tight_crop(mask: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in mask[r0 : r1 + 1]]


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate(grid: list[list[int]], quarter_turns: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    for _ in range(quarter_turns % 4):
        result = _rotate_clockwise(result)
    return result


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Rotate the three cropped shapes by their header codes and majority-vote."""
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    separators = [
        r for r, row in enumerate(grid)
        if len(row) == width and all(value == 9 for value in row)
    ]
    if len(separators) < 3:
        raise ValueError("expected three all-9 separator rows")

    codes = grid[0][:3]
    starts = [separators[0] + 1, separators[1] + 1, separators[2] + 1]
    ends = [separators[1], separators[2], len(grid)]
    panels = [grid[start:end] for start, end in zip(starts, ends)]
    panel_height = len(panels[0])
    if any(len(panel) != panel_height for panel in panels):
        raise ValueError("panel heights differ")

    aligned: list[list[list[int]]] = []
    for code, panel in zip(codes, panels):
        if code not in (1, 2, 3, 4):
            raise ValueError(f"unknown rotation code: {code!r}")
        crop = _tight_crop(panel)
        turned = _rotate(crop, code - 1)
        canvas = [[0 for _ in range(width)] for _ in range(panel_height)]
        for r, row in enumerate(turned):
            for c, value in enumerate(row):
                if r < panel_height and c < width and value != 0:
                    canvas[r][c] = 1
        aligned.append(canvas)

    return [
        [8 if sum(panel[r][c] for panel in aligned) >= 2 else 0 for c in range(width)]
        for r in range(panel_height)
    ]
