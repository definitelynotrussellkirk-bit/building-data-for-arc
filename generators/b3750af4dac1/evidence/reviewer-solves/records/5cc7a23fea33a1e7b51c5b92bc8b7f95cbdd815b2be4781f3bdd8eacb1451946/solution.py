from collections import deque


def solve(grid):
    """Infer the largest representable red population in a green-majority group.

    Blue lines partition the input into rooms.  Each orange 7 defines a local
    two-room group.  A maroon 9 is a junction: all orange-connected components
    incident to that junction form one additional group.  Count red (2) and green
    (3) cells in every candidate group, retain strict green majorities, and encode
    the largest red count as an 8 in a row of length (#rooms - 1).
    """
    h = len(grid)
    w = len(grid[0])
    wall_values = {1, 7, 9}
    wall_rows = [r for r in range(h) if all(grid[r][c] in wall_values for c in range(w))]
    wall_cols = [c for c in range(w) if all(grid[r][c] in wall_values for r in range(h))]
    nr = len(wall_rows) - 1
    nc = len(wall_cols) - 1
    n_rooms = nr * nc

    def rid(rr, cc):
        return rr * nc + cc

    red = [0] * n_rooms
    green = [0] * n_rooms
    for rr in range(nr):
        for cc in range(nc):
            idx = rid(rr, cc)
            for r in range(wall_rows[rr] + 1, wall_rows[rr + 1]):
                for c in range(wall_cols[cc] + 1, wall_cols[cc + 1]):
                    red[idx] += grid[r][c] == 2
                    green[idx] += grid[r][c] == 3

    row_at = {r: i for i, r in enumerate(wall_rows)}
    col_at = {c: i for i, c in enumerate(wall_cols)}

    def incident_rooms(r, c):
        rooms = []
        on_r = r in row_at
        on_c = c in col_at
        if on_r and on_c:
            wr, wc = row_at[r], col_at[c]
            for rr in (wr - 1, wr):
                for cc in (wc - 1, wc):
                    if 0 <= rr < nr and 0 <= cc < nc:
                        rooms.append(rid(rr, cc))
        elif on_r:
            wr = row_at[r]
            cc = next((j for j in range(nc) if wall_cols[j] < c < wall_cols[j + 1]), None)
            if cc is not None:
                for rr in (wr - 1, wr):
                    if 0 <= rr < nr:
                        rooms.append(rid(rr, cc))
        elif on_c:
            wc = col_at[c]
            rr = next((i for i in range(nr) if wall_rows[i] < r < wall_rows[i + 1]), None)
            if rr is not None:
                for cc in (wc - 1, wc):
                    if 0 <= cc < nc:
                        rooms.append(rid(rr, cc))
        return rooms

    seven_edges = []
    nine_incident = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value not in (7, 9):
                continue
            rooms = incident_rooms(r, c)
            if value == 7 and len(rooms) == 2:
                seven_edges.append(tuple(rooms))
            elif value == 9:
                nine_incident.append(rooms)

    # Components are used only to expand a maroon junction; ordinary orange
    # candidates remain local two-room groups.
    adj = [set() for _ in range(n_rooms)]
    for u, v in seven_edges:
        adj[u].add(v)
        adj[v].add(u)

    component_of = [-1] * n_rooms
    components = []
    for start in range(n_rooms):
        if component_of[start] != -1:
            continue
        ci = len(components)
        q = deque([start])
        component_of[start] = ci
        nodes = []
        while q:
            u = q.popleft()
            nodes.append(u)
            for v in adj[u]:
                if component_of[v] == -1:
                    component_of[v] = ci
                    q.append(v)
        components.append(nodes)

    candidates = [set(edge) for edge in seven_edges]
    for incident in nine_incident:
        joined = set()
        for room in incident:
            joined.update(components[component_of[room]])
        if joined:
            candidates.append(joined)

    limit = n_rooms - 1
    best = 0
    for nodes in candidates:
        rcount = sum(red[i] for i in nodes)
        gcount = sum(green[i] for i in nodes)
        if gcount > rcount and 1 <= rcount <= limit:
            best = max(best, rcount)

    if best == 0:
        # The generated examples always provide a positive candidate.  This
        # conservative fallback still returns a valid-shaped output if a novel
        # instance violates that observed contract.
        best = 1
    out = [0] * limit
    out[best - 1] = 8
    return [out]
