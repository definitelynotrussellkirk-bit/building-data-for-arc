from __future__ import annotations


_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _frame_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _DIRS4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
                    cells.append(nxt)
        components.append(cells)
    return components


def _crop_figure(
    grid: list[list[int]], bbox: tuple[int, int, int, int]
) -> list[list[int]]:
    r0, c0, r1, c1 = bbox
    cells = [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] != 0
    ]
    if not cells:
        return []
    fr0 = min(r for r, _ in cells)
    fc0 = min(c for _, c in cells)
    fr1 = max(r for r, _ in cells)
    fc1 = max(c for _, c in cells)
    return [row[fc0 : fc1 + 1] for row in grid[fr0 : fr1 + 1]]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Sort tightly cropped framed figures by their keys and center them."""
    records: list[tuple[int, list[list[int]]]] = []

    for component in _frame_components(grid):
        r0 = min(r for r, _ in component)
        c0 = min(c for _, c in component)
        r1 = max(r for r, _ in component)
        c1 = max(c for _, c in component)
        keys = [
            grid[r0 - 1][c]
            for c in range(c0, c1 + 1)
            if r0 > 0 and grid[r0 - 1][c] not in (0, 9)
        ]
        if len(keys) != 1:
            continue
        crop = _crop_figure(grid, (r0, c0, r1, c1))
        if crop:
            records.append((keys[0], crop))

    records.sort(key=lambda item: item[0])
    max_height = max(len(crop) for _, crop in records)
    width = sum(len(crop[0]) for _, crop in records) + len(records) - 1
    out = [[0] * width for _ in range(max_height)]

    left = 0
    for _, crop in records:
        top = (max_height - len(crop)) // 2
        for r, row in enumerate(crop):
            out[top + r][left : left + len(row)] = row
        left += len(crop[0]) + 1

    return out
