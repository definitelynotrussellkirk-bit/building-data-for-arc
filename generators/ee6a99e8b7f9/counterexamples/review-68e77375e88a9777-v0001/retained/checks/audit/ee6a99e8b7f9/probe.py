#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path[:0] = [str(ROOT / "shared" / "runtime"), str(ROOT / "src")]
from reviewer_support import canonical_pairs

TASK = "ee6a99e8b7f9"
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_ee6", SOURCE)
g = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(g)

# Accepted-domain witness: a 2x4 pink rectangle. The selected rule uses floor
# midpoint; a plausible rival uses the other central column on even widths.
grid = [[8] * 9 for _ in range(9)]
for r in range(2, 4):
    for c in range(2, 6):
        grid[r][c] = 6
grid[2][1] = 9

def ceil_midpoint_rival(inp):
    out = [row[:] for row in inp]
    out[2][1] = 8
    out[2][4] = 9
    return out

intended = g.rule_mirror(grid)
rival = ceil_midpoint_rival(grid)
canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical_ok = all(g.self_check(p["input"]) == [] and g.rule_mirror(p["input"]) == p["output"] for p in canonical)

shape_sizes = set()
generated = 0
errors = []
for band_index, band in enumerate(("easy", "medium", "hard")):
    for offset in range(200):
        seed = 640_000 + band_index * 10_000 + offset
        sample_index = 31 * offset + 7
        sample = g.generate(seed, sample_index, difficulty=band)
        generated += 1
        e = g.self_check(sample)
        if e:
            errors.append({"band": band, "seed": seed, "sample_index": sample_index, "errors": e})
        for shape in g._shape_components(sample):
            r1,c1,r2,c2 = shape["bbox"]
            shape_sizes.add((r2-r1+1,c2-c1+1))

report = {
    "task_id": TASK,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "canonical_pairs": len(canonical),
    "canonical_ok": canonical_ok,
    "accepted_witness": {
        "self_check": g.self_check(grid),
        "input": grid,
        "intended_output": intended,
        "rival_output": rival,
        "outputs_differ": intended != rival,
        "differing_cells": [
            [r,c,intended[r][c],rival[r][c]]
            for r in range(9) for c in range(9)
            if intended[r][c] != rival[r][c]
        ],
    },
    "generated_census": {
        "draws": generated,
        "self_check_failures": errors,
        "observed_shape_sizes": [list(x) for x in sorted(shape_sizes)],
        "even_dimension_shape_seen": any(h % 2 == 0 or w % 2 == 0 for h,w in shape_sizes),
    },
}
Path(__file__).with_name("probe.json").write_text(json.dumps(report, indent=2) + "\n")
Path(__file__).with_name("input.json").write_text(json.dumps(grid, indent=2) + "\n")
Path(__file__).with_name("rival_output.json").write_text(json.dumps(rival, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(0 if canonical_ok and not g.self_check(grid) and intended != rival and not errors else 1)
