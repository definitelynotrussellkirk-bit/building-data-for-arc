#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import os
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "aa538df09d67"
ROOT = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"audit_generator_{TASK}", GENERATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load {GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


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
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc)); stack.append((nr,nc))
            out.append((color, cells))
    return out


def per_color_global_bbox(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors = sorted({cell for row in grid for cell in row if cell != 0})
    for color in colors:
        cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color]
        r0 = min(r for r,_ in cells); r1 = max(r for r,_ in cells)
        c0 = min(c for _,c in cells); c1 = max(c for _,c in cells)
        for c in range(c0, c1+1):
            out[r0][c] = color; out[r1][c] = color
        for r in range(r0, r1+1):
            out[r][c0] = color; out[r][c1] = color
    return out


def main():
    here = Path(__file__).resolve().parent
    generator_path = Path(GEN.__file__).resolve()
    canonical = canonical_pairs(TASK, root=ROOT)
    canonical_results = [per_color_global_bbox(pair["input"]) == pair["output"] for pair in canonical]

    repeated_color_component_draws = 0
    draws = 0
    by_band = {}
    for band_i, band in enumerate(("easy", "medium", "hard")):
        band_repeated = 0
        for index in range(500):
            grid = GEN.generate(880000 + band_i * 10000 + index, index, difficulty=band)
            draws += 1
            counts = {}
            for color, _cells in components(grid):
                counts[color] = counts.get(color, 0) + 1
            if any(count > 1 for count in counts.values()):
                repeated_color_component_draws += 1
                band_repeated += 1
        by_band[band] = {"draws": 500, "repeated_color_component_draws": band_repeated}

    witness = [
        [0,0,0,0,0,0,0,0,0],
        [0,4,4,0,0,0,0,0,0],
        [0,4,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,4,4,0],
        [0,0,0,0,0,0,0,4,0],
        [0,0,0,0,0,0,0,0,0],
    ]
    validator = GEN.self_check(witness)
    rival = per_color_global_bbox(witness)
    (here / "input.json").write_text(json.dumps(witness, indent=2) + "\n")
    (here / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    report = {
        "schema": "audit-aa538df09d67-same-color-shortcut-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "canonical_pairs": len(canonical),
        "canonical_rival_matches": sum(canonical_results),
        "canonical_fit_vector": canonical_results,
        "sampled_draws": draws,
        "repeated_color_component_draws": repeated_color_component_draws,
        "by_band": by_band,
        "witness_validator_reasons": validator,
        "witness_component_colors": [color for color,_ in components(witness)],
        "rival": "paint one global bounding-box border per color rather than per connected component",
        "input_path": "checks/audit/aa538df09d67/input.json",
        "rival_path": "checks/audit/aa538df09d67/rival.json",
    }
    (here / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
