from collections import deque


def solve(grid):
    """Return a one-hot count for the largest green-majority connected region.

    Blue (1) lines partition the board into rooms. Orange/maroon wall marks
    (7/9) connect every room incident to that wall position.  For each resulting
    connected component, count red cells (2) and green cells (3).  The answer is
    the largest red count among components with more green than red; encode that
    positive count as an 8 in a row of length (#rooms - 1).
    """
    h = len(grid)
    w = len(grid[0])

    wall_values = {1, 7, 9}
    wall_rows = [r for r in range(h) if all(grid[r][c] in wall_values for c in range(w))]
    wall_cols = [c for c in range(w) if all(grid[r][c] in wall_values for r in range(h))]

    n_room_rows = len(wall_rows) - 1
    n_room_cols = len(wall_cols) - 1
    n_rooms = n_room_rows * n_room_cols

    def room_id(rr, cc):
        return rr * n_room_cols + cc

    red = [0] * n_rooms
    green = [0] * n_rooms
    for rr in range(n_room_rows):
        r0, r1 = wall_rows[rr], wall_rows[rr + 1]
        for cc in range(n_room_cols):
            c0, c1 = wall_cols[cc], wall_cols[cc + 1]
            idx = room_id(rr, cc)
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    if grid[r][c] == 2:
                        red[idx] += 1
                    elif grid[r][c] == 3:
                        green[idx] += 1

    row_index = {r: i for i, r in enumerate(wall_rows)}
    col_index = {c: i for i, c in enumerate(wall_cols)}
    adj = [set() for _ in range(n_rooms)]

    def incident_rooms(r, c):
        rooms = []
        on_row_wall = r in row_index
        on_col_wall = c in col_index
        if on_row_wall and on_col_wall:
            wr = row_index[r]
            wc = col_index[c]
            for rr in (wr - 1, wr):
                for cc in (wc - 1, wc):
                    if 0 <= rr < n_room_rows and 0 <= cc < n_room_cols:
                        rooms.append(room_id(rr, cc))
        elif on_row_wall:
            wr = row_index[r]
            cc = next(
                (j for j in range(n_room_cols) if wall_cols[j] < c < wall_cols[j + 1]),
                None,
            )
            if cc is not None:
                for rr in (wr - 1, wr):
                    if 0 <= rr < n_room_rows:
                        rooms.append(room_id(rr, cc))
        elif on_col_wall:
            wc = col_index[c]
            rr = next(
                (i for i in range(n_room_rows) if wall_rows[i] < r < wall_rows[i + 1]),
                None,
            )
            if rr is not None:
                for cc in (wc - 1, wc):
                    if 0 <= cc < n_room_cols:
                        rooms.append(room_id(rr, cc))
        return rooms

    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (7, 9):
                continue
            rooms = incident_rooms(r, c)
            for i, u in enumerate(rooms):
                for v in rooms[i + 1 :]:
                    adj[u].add(v)
                    adj[v].add(u)

    best = 0
    seen = [False] * n_rooms
    for start in range(n_rooms):
        if seen[start]:
            continue
        queue = deque([start])
        seen[start] = True
        component_red = 0
        component_green = 0
        while queue:
            u = queue.popleft()
            component_red += red[u]
            component_green += green[u]
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    queue.append(v)
        if component_green > component_red:
            best = max(best, component_red)

    if not (1 <= best <= n_rooms - 1):
        raise ValueError(f"inferred count {best} is outside 1..{n_rooms - 1}")
    output = [0] * (n_rooms - 1)
    output[best - 1] = 8
    return [output]
