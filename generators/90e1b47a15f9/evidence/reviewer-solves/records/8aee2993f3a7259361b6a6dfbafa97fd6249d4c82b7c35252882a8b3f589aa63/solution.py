"""Visible-example solution for ARC task 90e1b47a15f9."""
from collections import deque


def solve(grid):
    """Paint the first shortest lawful key/door path from 2 to 3 with 9s.

    Colors 8 are walls. Color 4 is the key for door 6; color 5 is the
    key for door 7. If no lawful route reaches color 3, return all zeros.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    start = next(
        ((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2),
        None,
    )
    goal = next(
        ((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3),
        None,
    )
    out = [[0 for _ in range(w)] for _ in range(h)]
    if start is None or goal is None:
        return out

    initial = (start[0], start[1], False, False)
    queue = deque([initial])
    parent = {initial: None}
    end = None

    # The visible examples are consistent with the usual U, D, L, R BFS order.
    for_current = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while queue:
        state = queue.popleft()
        r, c, has4, has5 = state
        if (r, c) == goal:
            end = state
            break

        # Picking up a key changes the search state without changing position.
        next4 = has4 or grid[r][c] == 4
        next5 = has5 or grid[r][c] == 5
        updated = (r, c, next4, next5)
        if updated != state and updated not in parent:
            parent[updated] = state
            queue.appendleft(updated)

        for dr, dc in for_current:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            value = grid[nr][nc]
            if value == 8:
                continue
            if value == 6 and not next4:
                continue
            if value == 7 and not next5:
                continue
            nxt = (nr, nc, next4, next5)
            if nxt in parent:
                continue
            parent[nxt] = state
            queue.append(nxt)

    if end is None:
        return out

    current = end
    while current is not None:
        r, c, _has4, _has5 = current
        out[r][c] = 9
        current = parent[current]
    return out
