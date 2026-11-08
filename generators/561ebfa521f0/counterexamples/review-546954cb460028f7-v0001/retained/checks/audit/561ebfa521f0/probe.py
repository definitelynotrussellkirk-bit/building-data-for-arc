from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "561ebfa521f0"
root = find_root(Path.cwd())
module, source_path, source_sha256 = load_selected_generator(TASK, root=root)


def marker(grid, color):
    return next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color)


def distances(grid, start):
    h, w = len(grid), len(grid[0])
    dist = {start: 0}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5 and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return dist


def union_shortest(grid, a, b):
    da = distances(grid, a)
    db = distances(grid, b)
    if b not in da:
        return set()
    total = da[b]
    return {p for p in da.keys() & db.keys() if da[p] + db[p] == total}


def intended(grid):
    out = deepcopy(grid)
    m2, m4, m3 = marker(grid, 2), marker(grid, 4), marker(grid, 3)
    cells = union_shortest(grid, m2, m4) | union_shortest(grid, m4, m3)
    for r, c in cells:
        if out[r][c] == 0:
            out[r][c] = 8
    return out


def rectangle_rival(grid):
    out = deepcopy(grid)
    for a, b in ((marker(grid, 2), marker(grid, 4)), (marker(grid, 4), marker(grid, 3))):
        r0, r1 = sorted((a[0], b[0]))
        c0, c1 = sorted((a[1], b[1]))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if out[r][c] == 0:
                    out[r][c] = 8
    return out


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


lesson = [module.generate(40, i, difficulty="easy") for i in range(5)]
lesson_rows = []
for i, grid in enumerate(lesson):
    truth = intended(grid)
    rival = rectangle_rival(grid)
    diffs = [
        [r, c, truth[r][c], rival[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if truth[r][c] != rival[r][c]
    ]
    lesson_rows.append({
        "sample_index": i,
        "input_sha256": grid_hash(grid),
        "self_check": module.self_check(grid, difficulty="easy"),
        "rival_matches": not diffs,
        "differences": diffs,
    })

# Structurally valid under self_check, but an interior wall barrier disconnects green.
disconnected = [
    [5,5,5,5,5,5,5,5,5],
    [5,0,0,0,5,0,0,0,5],
    [5,0,2,0,5,0,0,0,5],
    [5,0,0,0,5,0,3,0,5],
    [5,0,4,0,5,0,0,0,5],
    [5,0,0,0,5,0,0,0,5],
    [5,5,5,5,5,5,5,5,5],
]
m2, m4, m3 = marker(disconnected, 2), marker(disconnected, 4), marker(disconnected, 3)
reach = {
    "2_to_4": m4 in distances(disconnected, m2),
    "4_to_3": m3 in distances(disconnected, m4),
    "2_to_3": m3 in distances(disconnected, m2),
}

report = {
    "schema": "review-audit-shortest-path-probe-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(root)),
    "generator_sha256": source_sha256,
    "lesson": {
        "difficulty": "easy",
        "seed": 40,
        "demonstration_indices": [0, 1, 2],
        "query_indices": [3, 4],
        "rows": lesson_rows,
        "demonstrations_all_fit_rectangle_rival": all(row["rival_matches"] for row in lesson_rows[:3]),
        "at_least_one_query_refutes_rectangle_rival": any(not row["rival_matches"] for row in lesson_rows[3:]),
    },
    "disconnected_validator_probe": {
        "grid": disconnected,
        "input_sha256": grid_hash(disconnected),
        "self_check": module.self_check(disconnected),
        "reachability": reach,
        "documented_invariant_satisfied": all(reach.values()),
    },
}

out_dir = Path("../checks/audit/561ebfa521f0")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "probe-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
(out_dir / "input.json").write_text(json.dumps(lesson + [disconnected], indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK,
    "generator_sha256": source_sha256,
    "lesson_matches": [row["rival_matches"] for row in lesson_rows],
    "query_4_differences": lesson_rows[4]["differences"],
    "disconnected_self_check": report["disconnected_validator_probe"]["self_check"],
    "disconnected_reachability": reach,
}, indent=2))
