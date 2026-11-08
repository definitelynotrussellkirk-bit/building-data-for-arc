from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GEN_PATH = ROOT / "WORK/repo/generators/4a8c7e2bad04/generator.py"
spec = importlib.util.spec_from_file_location("audited_4a8c7e2bad04", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = {(r, c)}
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        queue.append((nr, nc))
            out.append((color, cells))
    return out


def crop(grid, cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return [row[min(cs): max(cs) + 1] for row in grid[min(rs): max(rs) + 1]]


grid = gen.generate(0, 0, texture="multiple_matches")
objects = components(grid)
query = next(cells for color, cells in objects if color == 8)
query_sig = gen._sig(query)
matches = [(color, cells) for color, cells in objects if color != 8 and gen._sig(cells) == query_sig]
report = {
    "task_id": "4a8c7e2bad04",
    "generator_path": str(GEN_PATH.relative_to(ROOT)),
    "case": "generate(seed=0, sample_index=0, texture='multiple_matches')",
    "self_check": gen.self_check(grid),
    "query_components": sum(color == 8 for color, _ in objects),
    "matching_non8_components": len(matches),
    "matching_colors_in_scan_order": [color for color, _ in matches],
    "candidate_outputs": [crop(grid, cells) for _, cells in matches],
    "grid": grid,
    "finding": "The declared ambiguous multiple_matches case is accepted by self_check despite two non-8 objects sharing the query signature.",
}
print(json.dumps(report, indent=2, sort_keys=True))
assert report["self_check"] == []
assert report["query_components"] == 1
assert report["matching_non8_components"] == 2
assert report["candidate_outputs"][0] != report["candidate_outputs"][1]
