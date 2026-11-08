from collections import deque


def _frames(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1}
    frames = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)

        top = min(r for r, _ in component)
        bottom = max(r for r, _ in component)
        left = min(c for _, c in component)
        right = max(c for _, c in component)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)
        }
        if component != border:
            continue
        crop = [row[left + 1 : right] for row in grid[top + 1 : bottom]]
        count = sum(value != 0 for row in crop for value in row)
        frames.append((count, crop))
    return frames


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    frames = _frames(grid)
    if not frames:
        raise ValueError("no hollow color-1 frame found")
    largest = max(count for count, _ in frames)
    winners = [crop for count, crop in frames if count == largest]
    if len(winners) != 1:
        raise ValueError("largest interior foreground count is not unique")
    return winners[0]
