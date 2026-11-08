from collections import Counter, deque


def solve(grid):
    """Move each connected 5 along its 3-path to just before a 0-3-0 goal."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    if not height or not width:
        return out

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    def inside(r, c):
        return 0 <= r < height and 0 <= c < width

    # A goal is the 3 in a 0-3-0 bar. The travel path meets it from the
    # perpendicular axis, as in every visible example.
    goals = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 3:
                continue
            horizontal_bar = c > 0 and c + 1 < width and grid[r][c - 1] == 0 and grid[r][c + 1] == 0
            vertical_bar = r > 0 and r + 1 < height and grid[r - 1][c] == 0 and grid[r + 1][c] == 0
            if horizontal_bar or vertical_bar:
                allowed_arrivals = set()
                if horizontal_bar:
                    allowed_arrivals.update(((-1, 0), (1, 0)))
                if vertical_bar:
                    allowed_arrivals.update(((0, -1), (0, 1)))
                goals.append(((r, c), allowed_arrivals))

    used_sources = set()
    used_path_cells = set()

    for goal, allowed_arrivals in goals:
        gr, gc = goal

        # Search outward only through 3-cells, starting on a legal arrival
        # side. Stop at a 5. This prevents a decorative/incomplete goal from
        # changing unless it has a complete 5-to-goal path.
        queue = deque()
        parent = {}
        for dr, dc in allowed_arrivals:
            nr, nc = gr + dr, gc + dc
            if inside(nr, nc) and grid[nr][nc] in (3, 5):
                pos = (nr, nc)
                queue.append(pos)
                parent[pos] = goal

        source = None
        while queue and source is None:
            pos = queue.popleft()
            r, c = pos
            if grid[r][c] == 5 and pos not in used_sources:
                source = pos
                break
            for dr, dc in directions:
                nxt = (r + dr, c + dc)
                if not inside(*nxt) or nxt in parent or nxt == goal:
                    continue
                nr, nc = nxt
                if grid[nr][nc] not in (3, 5):
                    continue
                parent[nxt] = pos
                queue.append(nxt)

        if source is None:
            continue

        # Reconstruct source -> ... -> goal. Avoid processing overlapping
        # structures twice if a malformed instance joins two goals.
        path = [source]
        cursor = source
        while cursor != goal:
            cursor = parent[cursor]
            path.append(cursor)
        if len(path) < 2 or any(cell in used_path_cells for cell in path[:-1]):
            continue

        for r, c in path[:-1]:
            out[r][c] = background
        pr, pc = path[-2]
        out[pr][pc] = 5
        out[gr][gc] = 3

        used_sources.add(source)
        used_path_cells.update(path[:-1])

    return out
