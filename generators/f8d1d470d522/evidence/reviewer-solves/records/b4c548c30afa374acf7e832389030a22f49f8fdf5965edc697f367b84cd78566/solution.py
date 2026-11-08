from heapq import heappop, heappush


DIRS = ((-1, 0), (0, 1), (1, 0), (0, -1))


def solve(grid):
    """Recolor the best cyan route joining the two maroon endpoints.

    Orange cells forbid the orthogonally adjacent cyan route cells.  Among the
    remaining routes, choose the one with minimum length and then minimum turns.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]

    endpoints = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(endpoints) != 2:
        return out

    orange = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    }
    forbidden = set()
    for r, c in orange:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 8:
                forbidden.add((nr, nc))

    start, goal = endpoints

    # State includes the incoming direction so turn count is part of the cost.
    # Cost order is path length first, then number of turns.
    queue = []
    serial = 0
    heappush(queue, (0, 0, serial, start[0], start[1], -1))
    best = {(start[0], start[1], -1): (0, 0)}
    parent = {}
    final_state = None

    while queue:
        steps, turns, _, r, c, incoming = heappop(queue)
        state = (r, c, incoming)
        if best.get(state) != (steps, turns):
            continue
        if (r, c) == goal:
            final_state = state
            break

        for direction, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if (nr, nc) != goal:
                if grid[nr][nc] != 8 or (nr, nc) in forbidden:
                    continue
            next_steps = steps + 1
            next_turns = turns + (incoming != -1 and incoming != direction)
            next_state = (nr, nc, direction)
            next_cost = (next_steps, next_turns)
            if next_cost >= best.get(next_state, (10**9, 10**9)):
                continue
            best[next_state] = next_cost
            parent[next_state] = state
            serial += 1
            heappush(
                queue,
                (next_steps, next_turns, serial, nr, nc, direction),
            )

    if final_state is None:
        return out

    path = []
    state = final_state
    while True:
        path.append((state[0], state[1]))
        if state == (start[0], start[1], -1):
            break
        state = parent[state]

    for r, c in path:
        if out[r][c] == 8:
            out[r][c] = 9
    return out
