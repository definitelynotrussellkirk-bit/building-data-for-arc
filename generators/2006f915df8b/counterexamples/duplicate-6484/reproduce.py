"""Reproduce the duplicate-filtered lesson failure in the frozen generator.

Run with PYTHONPATH=/dev/shm/arcpuzzles-22d801-share/local-runtime.
Outputs are independent Python BFS results, pending Racket authority validation.
"""
from collections import deque
import hashlib
import importlib.util
from pathlib import Path


path = Path(__file__).with_name("frozen_generator.py")
assert hashlib.sha256(path.read_bytes()).hexdigest() == (
    "71e41a5d785f0dd50b18f315af279c3ad22274c1ab37e0b6d601cfa46309df84"
)
spec = importlib.util.spec_from_file_location("review_maze_snapshot", path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def independent_bfs(grid):
    start, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    goal, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    queue = deque([start])
    distance, ways, parent = {start: 0}, {start: 1}, {}
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = r + dr, c + dc
            nr, nc = nxt
            if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])) or grid[nr][nc] == 5:
                continue
            depth = distance[r, c] + 1
            if nxt not in distance:
                distance[nxt], ways[nxt], parent[nxt] = depth, ways[r, c], (r, c)
                queue.append(nxt)
            elif distance[nxt] == depth:
                ways[nxt] += ways[r, c]
    assert ways[goal] == 1
    output, at = [row[:] for row in grid], goal
    while at != start:
        r, c = at
        if output[r][c] == 0:
            output[r][c] = 8
        at = parent[at]
    return output


grids = {i: gen.generate(6484, i, difficulty="easy", grid_h=7, grid_w=8)
         for i in (1, 2, 3, 4, 5)}
assert grids[2] == grids[4]
accepted, seen = [], set()
for index, grid in grids.items():
    key = tuple(map(tuple, grid))
    if key not in seen:
        seen.add(key)
        accepted.append(index)
assert accepted == [1, 2, 3, 5]
reference = {i: independent_bfs(grid) for i, grid in grids.items()}
rival = gen.LESSON_COMPETITORS["fewest_turns"]
assert all(rival(grids[i]) == reference[i] for i in (1, 3, 5))
assert rival(grids[2]) != reference[2]
print("Confirmed: accepted indices [1, 2, 3, 5], holdout position 1; "
      "fewest_turns matches every demo and fails the query.")
