#!/usr/bin/env python3
"""Source-bound audit probe for 8bc82608e55f."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "8bc82608e55f"
DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def load_module(repo: Path):
    sys.path.insert(0, str(repo / "shared" / "runtime"))
    source = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "cells": sorted(cells), "first": (r, c)})
    return out


def has_true_hole(component):
    cells = set(map(tuple, component["cells"]))
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    open_cells = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if (r, c) not in cells}
    if not open_cells:
        return False
    queue = [p for p in open_cells if p[0] in (r1, r2) or p[1] in (c1, c2)]
    seen = set(queue)
    while queue:
        r, c = queue.pop()
        for dr, dc in DIRS4:
            p = (r + dr, c + dc)
            if p in open_cells and p not in seen:
                seen.add(p)
                queue.append(p)
    return len(seen) < len(open_cells)


def paint_only(grid, component):
    out = [[0 for _ in row] for row in grid]
    for r, c in component["cells"]:
        out[r][c] = component["color"]
    return out


def canonical_output(grid):
    out = [[0 for _ in row] for row in grid]
    for comp in components(grid):
        if has_true_hole(comp):
            for r, c in comp["cells"]:
                out[r][c] = comp["color"]
    return out


def largest_component_output(grid):
    comps = components(grid)
    if not comps:
        return [[0 for _ in row] for row in grid]
    largest = max(comps, key=lambda x: (len(x["cells"]), -x["first"][0], -x["first"][1]))
    return paint_only(grid, largest)


def compact_canonical_grid(raw):
    if raw and isinstance(raw[0], str):
        return [[int(ch) for ch in row] for row in raw]
    return raw


def main():
    root = Path(__file__).resolve().parents[3]
    repo = root / "repo"
    module, source = load_module(repo)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    census = {}
    for band in ("easy", "medium", "hard"):
        stats = {
            "draws": 0,
            "exactly_one_holed": 0,
            "unique_largest_is_holed": 0,
            "largest_rival_fits": 0,
            "component_count_hist": {},
            "structural_anomalies": [],
        }
        for seed in range(300):
            grid = module.generate(seed, seed, difficulty=band)
            comps = components(grid)
            holes = [comp for comp in comps if has_true_hole(comp)]
            sizes = [len(comp["cells"]) for comp in comps]
            stats["draws"] += 1
            stats["component_count_hist"][str(len(comps))] = stats["component_count_hist"].get(str(len(comps)), 0) + 1
            if len(holes) == 1:
                stats["exactly_one_holed"] += 1
                max_size = max(sizes)
                if len(holes[0]["cells"]) == max_size and sizes.count(max_size) == 1:
                    stats["unique_largest_is_holed"] += 1
            else:
                stats["structural_anomalies"].append({"seed": seed, "hole_count": len(holes), "sizes": sizes})
            if largest_component_output(grid) == canonical_output(grid):
                stats["largest_rival_fits"] += 1
        census[band] = stats

    canonical_support = []
    canonical_file = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in canonical_file.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        pairs = list(row.get("train", []))
        test = row.get("test", [])
        if isinstance(test, dict):
            pairs.append(test)
        else:
            pairs.extend(test)
        for index, pair in enumerate(pairs):
            grid = compact_canonical_grid(pair["input"])
            comps = components(grid)
            holes = [comp for comp in comps if has_true_hole(comp)]
            canonical_support.append({
                "pair_index": index,
                "component_sizes": [len(comp["cells"]) for comp in comps],
                "hole_sizes": [len(comp["cells"]) for comp in holes],
                "largest_rival_fits_label": largest_component_output(grid) == compact_canonical_grid(pair["output"]),
            })
        break

    counterexample = [[0] * 12 for _ in range(10)]
    for r, c in ((1,1),(1,2),(1,3),(2,1),(2,3),(3,1),(3,2),(3,3)):
        counterexample[r][c] = 2
    for r in range(5, 9):
        for c in range(7, 11):
            counterexample[r][c] = 4

    payload = {
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": source_sha,
        "rival": "keep only the unique largest nonzero 4-connected component",
        "ordinary_census": census,
        "canonical_support": canonical_support,
        "counterexample": {
            "input": counterexample,
            "self_check": module.self_check(counterexample),
            "component_sizes": [len(comp["cells"]) for comp in components(counterexample)],
            "canonical_python": canonical_output(counterexample),
            "largest_rival": largest_component_output(counterexample),
            "predictions_differ": canonical_output(counterexample) != largest_component_output(counterexample),
        },
        "limits": "Finite census over 300 seed/index pairs per band and one named rival; Python mirror is corroborated by separate canonical Racket apply evidence for the counterexample.",
    }
    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(payload, indent=2) + "\n")
    Path(__file__).with_name("input.json").write_text(json.dumps({"inputs": [counterexample]}, indent=2) + "\n")
    Path(__file__).with_name("rival-output.json").write_text(json.dumps({"outputs": [payload["counterexample"]["largest_rival"]]}, indent=2) + "\n")
    print(json.dumps({"report": str(out), "sha256": source_sha, "census": census, "canonical_support": canonical_support}, indent=2))


if __name__ == "__main__":
    main()
