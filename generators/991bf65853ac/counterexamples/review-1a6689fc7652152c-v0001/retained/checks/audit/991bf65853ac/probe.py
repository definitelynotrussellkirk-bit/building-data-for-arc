#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "991bf65853ac"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = (r + dr, c + dc)
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        seen.add(p)
                        stack.append(p)
            out.append((color, cells))
    return out


def hole_count(grid, cells):
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    occupied = {(r - r1, c - c1) for r, c in cells}
    h, w = r2 - r1 + 1, c2 - c1 + 1
    bg = {(r, c) for r in range(h) for c in range(w) if (r, c) not in occupied}
    outside = {p for p in bg if p[0] in (0, h - 1) or p[1] in (0, w - 1)}
    stack = list(outside)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (r + dr, c + dc)
            if p in bg and p not in outside:
                outside.add(p)
                stack.append(p)
    enclosed = bg - outside
    regions = 0
    while enclosed:
        regions += 1
        stack = [enclosed.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in enclosed:
                    enclosed.remove(p)
                    stack.append(p)
    return regions


grid = GEN.generate(0, 0, texture="all_holed")
items = []
for index, (color, cells) in enumerate(components(grid)):
    items.append({
        "component_index": index,
        "color": color,
        "size": len(cells),
        "bbox": [min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)],
        "true_hole_count": hole_count(grid, cells),
    })

payload = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "seed": 0,
    "sample_index": 0,
    "overrides": {"texture": "all_holed"},
    "input": grid,
    "self_check_errors": GEN.self_check(grid),
    "components": items,
    "eligible_true_holed_components": sum(item["true_hole_count"] > 0 for item in items),
    "declared_invariant": "exactly one component has at least one background hole",
    "source_sha256_recheck": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
}
(HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(HERE / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: payload[k] for k in ("generator_sha256", "self_check_errors", "eligible_true_holed_components")}, sort_keys=True))
