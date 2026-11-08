from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "860252b77847"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_860252b77847", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "cells": cells})
    return out

rows = []
identical = 0
for seed in range(32):
    low = mod.generate(seed, 0, n_blobs=1, palette_size=1, n_distinct_colors=2)
    high = mod.generate(seed, 0, n_blobs=4, palette_size=4, n_distinct_colors=4)
    same = low == high
    identical += int(same)
    rows.append({
        "seed": seed,
        "identical_under_conflicting_exact_overrides": same,
        "requested_low": {"n_blobs": 1, "palette_size": 1, "n_distinct_colors": 2},
        "requested_high": {"n_blobs": 4, "palette_size": 4, "n_distinct_colors": 4},
        "observed_components": len(components(low)),
        "observed_colors": sorted({v for row in low for v in row if v}),
        "self_check_low": mod.self_check(low),
        "self_check_high": mod.self_check(high),
    })

sample = mod.generate(0, 0, n_blobs=1, palette_size=1, n_distinct_colors=2)
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "finding": "advertised exact count/color overrides are ignored",
    "summary": {
        "seeds": 32,
        "byte_identical_low_vs_high": identical,
        "all_self_check_clean": all(not r["self_check_low"] and not r["self_check_high"] for r in rows),
        "observed_component_counts": sorted({r["observed_components"] for r in rows}),
    },
    "sample_seed_0": {
        "overrides": {"n_blobs": 1, "palette_size": 1, "n_distinct_colors": 2},
        "observed_components": len(components(sample)),
        "grid": sample,
    },
    "cases": rows,
}
Path(__file__).with_name("override_probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["summary"], indent=2))
if identical != 32:
    raise SystemExit("expected exact overrides to be ignored on all paired draws")
