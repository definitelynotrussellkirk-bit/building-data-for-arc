from __future__ import annotations

from collections import deque
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "b121b66ab1ce"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def component_count(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    count = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            count += 1
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return count


found = None
for seed in range(4096):
    for start in range(32):
        try:
            grids = [
                GEN.generate(seed, start + offset, difficulty="medium")
                for offset in range(4)
            ]
        except ValueError:
            continue
        green_counts = [component_count(grid, 3) for grid in grids]
        if green_counts == [1, 1, 1, 2]:
            found = (seed, start, grids, green_counts)
            break
    if found is not None:
        break
if found is None:
    raise RuntimeError("no three-demo shortcut window found")
seed, start, grids, green_counts = found
payload = {
    "schema": "arcpuzzles-audit-lesson-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "rule_hash_declared": getattr(GEN, "RULE_HASH", None),
    "lesson": {
        "seed": seed,
        "requested_start": start,
        "difficulty": "medium",
        "sample_indices": [start + offset for offset in range(4)],
        "n_demos": 3,
        "n_queries": 1,
        "green_component_counts": green_counts,
    },
    "self_checks": [GEN.self_check(grid) for grid in grids],
    "inputs": grids,
}
(HERE / "probe.json").write_text(json.dumps(payload, indent=2) + "\n")
(HERE / "inputs.json").write_text(json.dumps(grids, indent=2) + "\n")
print(json.dumps({k: payload[k] for k in ("generator_sha256", "rule_hash_declared", "lesson", "self_checks")}, indent=2))
