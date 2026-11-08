from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "de83dfd70673"
ROOT = Path(__file__).resolve().parents[3] / "repo"
spec = importlib.util.spec_from_file_location("audited_generator", ROOT / f"generators/{TASK}/generator.py")
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen and grid[q[0]][q[1]] == color:
                    unseen.remove(q)
                    cells.add(q)
                    stack.append(q)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        out.append((color, cells, (min(rs), min(cs), max(rs), max(cs))))
    return out


def bbox_fill(grid):
    out = [[0 for _ in row] for row in grid]
    for color, _cells, (r0, c0, r1, c1) in components(grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def closed_frame_only(grid):
    """Plausible shortcut: fill only exact one-cell rectangular frames."""
    out = deepcopy(grid)
    for color, cells, (r0, c0, r1, c1) in components(grid):
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if r1 - r0 >= 2 and c1 - c0 >= 2 and cells == perimeter:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    out[r][c] = color
    return out


canonical = None
for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        canonical = row
        break
assert canonical is not None
pairs = canonical["train"] + canonical["test"]
canonical_rival_matches = [closed_frame_only(p["input"]) == p["output"] for p in pairs]
canonical_oracle_matches = [bbox_fill(p["input"]) == p["output"] for p in pairs]

sampled = []
for band in (None, "easy", "medium", "hard"):
    for index in range(250):
        grid = gen.generate(30000 + index, index * 31 + 7, difficulty=band)
        intended = bbox_fill(grid)
        sampled.append({
            "band": band,
            "index": index,
            "rival_matches": closed_frame_only(grid) == intended,
            "component_count": len(components(grid)),
        })

open_l = json.loads((Path(__file__).with_name("open-l-input.json")).read_text())["input"]
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256((ROOT / f"generators/{TASK}/generator.py").read_bytes()).hexdigest(),
    "canonical_pairs": len(pairs),
    "canonical_bbox_oracle_matches": sum(canonical_oracle_matches),
    "canonical_closed_frame_rival_matches": sum(canonical_rival_matches),
    "generated_draws": len(sampled),
    "generated_closed_frame_rival_matches": sum(x["rival_matches"] for x in sampled),
    "generated_component_counts": {
        str(n): sum(x["component_count"] == n for x in sampled)
        for n in sorted({x["component_count"] for x in sampled})
    },
    "open_l": {
        "input": open_l,
        "bbox_fill": bbox_fill(open_l),
        "closed_frame_only": closed_frame_only(open_l),
        "rival_differs": bbox_fill(open_l) != closed_frame_only(open_l),
    },
    "finding": (
        "The exact closed-frame-only shortcut fits every canonical pair and every sampled "
        "generator draw, yet disagrees with the canonical executable rule on the open-L input."
    ),
}
print(json.dumps(report, indent=2))
