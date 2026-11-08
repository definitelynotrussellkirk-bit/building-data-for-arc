from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "repo" / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
GEN_PATH = ROOT / "repo" / "generators" / "bbbabb45042b" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_bbbabb45042b", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            comp = []
            while todo:
                rr, cc = todo.pop()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            out.append(comp)
    return out


def first_anchor_only(grid):
    out = copy.deepcopy(grid)
    template = max(components(grid, 2), key=len)
    r0 = min(r for r, _ in template)
    c0 = min(c for _, c in template)
    offsets = sorted((r - r0, c - c0) for r, c in template)
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    ar, ac = anchors[0]
    for dr, dc in offsets:
        out[ar + dr][ac + dc] = 1
    return out


seed = 10
difficulty = "medium"
sample_indices = [0, 1, 2, 3]
grids = [gen.generate(seed, i, difficulty=difficulty) for i in sample_indices]
record = {
    "schema": "arcpuzzles-audit-lesson-reproducer-v1",
    "task_id": "bbbabb45042b",
    "seed": seed,
    "sample_indices": sample_indices,
    "difficulty": difficulty,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "observed_axes": [gen.observe_overrides(grid) for grid in grids],
    "validator_findings": [gen.self_check(grid) for grid in grids],
    "inputs": grids,
    "rival": "preserve all input, but stamp the largest red template only at the first row-major blue anchor",
    "rival_outputs": [first_anchor_only(grid) for grid in grids],
}
OUT = Path(__file__).resolve().parent
(OUT / "input.json").write_text(json.dumps(grids, indent=2) + "\n", encoding="utf-8")
(OUT / "reproducer-preapply.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "anchor_counts": [x["n_anchors"] for x in record["observed_axes"]],
    "validator_findings": record["validator_findings"],
    "generator_sha256": record["generator_sha256"],
}, indent=2))
