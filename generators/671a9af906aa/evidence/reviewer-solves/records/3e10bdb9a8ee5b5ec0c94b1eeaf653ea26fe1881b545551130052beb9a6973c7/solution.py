from collections import deque


def solve(grid):
    """Paint the shortest lawful start-to-goal path through a key/door maze."""
    h = len(grid)
    w = len(grid[0])
    start = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    goal = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 3)

    start_state = (start[0], start[1], False)
    queue = deque([start_state])
    parent = {start_state: None}
    end = None

    # Fixed order makes equal-length choices deterministic.
    for_search = ((1, 0), (-1, 0), (0, 1), (0, -1))
    while queue:
        r, c, has_key = queue.popleft()
        if (r, c) == goal:
            end = (r, c, has_key)
            break
        for dr, dc in for_search:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            cell = grid[nr][nc]
            if cell == 8:
                continue
            new_has_key = has_key or cell == 4
            if cell == 5 and not new_has_key:
                continue
            state = (nr, nc, new_has_key)
            if state not in parent:
                parent[state] = (r, c, has_key)
                queue.append(state)

    out = [row[:] for row in grid]
    if end is None:
        return out

    state = end
    while state is not None:
        r, c, _ = state
        if grid[r][c] == 0:
            out[r][c] = 7
        state = parent[state]
    return out
