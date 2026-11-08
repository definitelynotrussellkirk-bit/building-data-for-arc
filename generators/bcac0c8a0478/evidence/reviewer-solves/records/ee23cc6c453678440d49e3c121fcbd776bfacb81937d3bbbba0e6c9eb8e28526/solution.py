from __future__ import annotations

from collections import deque


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Paint the shortest start-to-goal route that visits the checkpoint.

    Portal colors 6 and 7 are directional: entering the first occurrence in
    row-major order moves to the second occurrence; the second is an ordinary
    traversable endpoint.  Walls are 8.  Only background route cells become 4.
    """
    h = len(grid)
    w = len(grid[0])

    positions: dict[int, list[tuple[int, int]]] = {}
    start = checkpoint = goal = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3, 5, 6, 7):
                positions.setdefault(value, []).append((r, c))
            if value == 2:
                start = (r, c)
            elif value == 3:
                goal = (r, c)
            elif value == 5:
                checkpoint = (r, c)

    if start is None or checkpoint is None or goal is None:
        return [row[:] for row in grid]

    portal_jump: dict[tuple[int, int], tuple[int, int]] = {}
    for color in (6, 7):
        ends = positions.get(color, [])
        if len(ends) == 2:
            portal_jump[ends[0]] = ends[1]

    portal_bits = {pos: 1 << index for index, pos in enumerate(portal_jump)}
    required_portals = (1 << len(portal_jump)) - 1

    initial = (start[0], start[1], start == checkpoint, 0)
    queue = deque([initial])
    parent: dict[tuple[int, int, bool, int], tuple[int, int, bool, int] | None] = {
        initial: None
    }
    target: tuple[int, int, bool, int] | None = None

    # The visible examples resolve shortest-path ties in this order.
    for_pop = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while queue:
        state = queue.popleft()
        r, c, seen_checkpoint, used_portals = state
        if (r, c) == goal and seen_checkpoint and used_portals == required_portals:
            target = state
            break

        for dr, dc in for_pop:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if grid[nr][nc] == 8:
                continue

            entered = (nr, nc)
            landing = portal_jump.get(entered, entered)
            lr, lc = landing
            next_seen = seen_checkpoint or landing == checkpoint
            next_used = used_portals | portal_bits.get(entered, 0)
            nxt = (lr, lc, next_seen, next_used)
            if nxt in parent:
                continue
            parent[nxt] = state
            queue.append(nxt)

    if target is None:
        return [row[:] for row in grid]

    path_cells: set[tuple[int, int]] = set()
    state = target
    while state is not None:
        path_cells.add((state[0], state[1]))
        state = parent[state]

    out = [row[:] for row in grid]
    for r, c in path_cells:
        if out[r][c] == 0:
            out[r][c] = 4
    return out
