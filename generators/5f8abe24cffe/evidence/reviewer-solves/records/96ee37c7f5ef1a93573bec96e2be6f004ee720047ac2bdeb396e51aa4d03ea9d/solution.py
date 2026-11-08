from collections import deque


def _frame_boxes(grid):
    """Return rectangular color-1 frame boxes in reading order."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    boxes = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            r0 = min(r for r, _ in component)
            r1 = max(r for r, _ in component)
            c0 = min(c for _, c in component)
            c1 = max(c for _, c in component)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue

            border = (
                [(r0, c) for c in range(c0, c1 + 1)]
                + [(r1, c) for c in range(c0, c1 + 1)]
                + [(r, c0) for r in range(r0 + 1, r1)]
                + [(r, c1) for r in range(r0 + 1, r1)]
            )
            if all(grid[r][c] == 1 for r, c in border):
                boxes.append((r0, c0, r1, c1))

    boxes.sort(key=lambda box: (box[0], box[1]))
    return boxes


def _crop_nonzero(grid):
    rows = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    cols = [
        c
        for c in range(len(grid[0]))
        if any(grid[r][c] != 0 for r in range(len(grid)))
    ]
    if not rows or not cols:
        return [[0]]
    return [row[min(cols) : max(cols) + 1] for row in grid[min(rows) : max(rows) + 1]]


def _rotate_cw(grid):
    return [
        [grid[len(grid) - 1 - r][c] for r in range(len(grid))]
        for c in range(len(grid[0]))
    ]


def _apply(grid, quarter_turns, reflected):
    result = [row[:] for row in grid]
    if reflected:
        result = [list(reversed(row)) for row in result]
    for _ in range(quarter_turns):
        result = _rotate_cw(result)
    return result


def solve(grid):
    boxes = _frame_boxes(grid)
    if len(boxes) != 3:
        raise ValueError(f"expected three framed panels, found {len(boxes)}")

    panels = []
    for r0, c0, r1, c1 in boxes:
        interior = [row[c0 + 1 : c1] for row in grid[r0 + 1 : r1]]
        panels.append(_crop_nonzero(interior))

    before, after, target = panels
    for reflected in (False, True):
        for quarter_turns in range(4):
            if _apply(before, quarter_turns, reflected) == after:
                return _apply(target, quarter_turns, reflected)

    raise ValueError("the first two panels do not define a dihedral transform")
