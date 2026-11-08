from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "c29d882947ce"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            out.append((min(cells), color, cells))
    out.sort(key=lambda row: row[0])
    return out


def normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r-r0, c-c0) for r, c in cells)


def rotate(cells):
    norm = normalize(cells)
    h = max(r for r, _ in norm) + 1
    return normalize((c, h - 1 - r) for r, c in norm)


def orbit(cells):
    value = normalize(cells)
    values = set()
    for _ in range(4):
        values.add(value)
        value = rotate(value)
    return values


def solve(grid):
    comps = components(grid)
    orbits = [orbit(cells) for _anchor, _color, cells in comps]
    normalized = [normalize(cells) for _anchor, _color, cells in comps]
    return [
        [1 if i == j else 2 if normalized[j] in orbits[i] else 0 for j in range(len(comps))]
        for i in range(len(comps))
    ]


def identity(n):
    return [[1 if r == c else 0 for c in range(n)] for r in range(n)]


def is_identity(output):
    return output == identity(len(output))


selected = None
searched = 0
for seed in range(2000):
    outputs = []
    grids = []
    for index in range(24):
        grid = gen.generate(seed, index, difficulty="easy")
        errors = gen.self_check(grid, difficulty="easy")
        if errors:
            raise AssertionError((seed, index, errors))
        grids.append(grid)
        outputs.append(solve(grid))
        searched += 1
    for start in range(20):
        if all(is_identity(outputs[i]) for i in range(start, start + 3)) and not is_identity(outputs[start + 3]):
            selected = (seed, start, grids[start:start+4], outputs[start:start+4])
            break
    if selected:
        break

if selected is None:
    raise SystemExit(f"no witness found after {searched} generated grids")
seed, start, grids, outputs = selected
cases = []
for offset, (grid, output) in enumerate(zip(grids, outputs, strict=True)):
    index = start + offset
    cases.append({
        "role": "demo" if offset < 3 else "query",
        "seed": seed,
        "sample_index": index,
        "difficulty": "easy",
        "overrides": {},
        "input": grid,
        "self_check": gen.self_check(grid, difficulty="easy"),
        "python_rotation_matrix": output,
        "identity_rival_output": identity(len(output)),
        "is_identity": is_identity(output),
        "component_count": len(output),
    })

(OUT / "inputs.json").write_text(json.dumps({"inputs": grids}, indent=2) + "\n")
pre = {
    "schema": "arcpuzzles-audit-c29d882947ce-pre-v1",
    "task_id": TASK_ID,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "search": {
        "seed_range": [0, seed],
        "indices_per_seed": 24,
        "windows_per_seed": 20,
        "generated_grids_examined": searched,
        "selection": "first consecutive 3-demo identity window followed by non-identity query",
    },
    "lesson": {"seed": seed, "start_index": start, "cases": cases},
}
(OUT / "pre-evidence.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "generator_sha256": source_sha256,
    "seed": seed,
    "start_index": start,
    "identity_flags": [c["is_identity"] for c in cases],
    "generated_grids_examined": searched,
}, indent=2))
