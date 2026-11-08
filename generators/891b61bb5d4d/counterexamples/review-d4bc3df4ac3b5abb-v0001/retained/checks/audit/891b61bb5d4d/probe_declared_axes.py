#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

TASK = "891b61bb5d4d"

def load(root: Path):
    source = root / "generators" / TASK / "generator.py"
    sys.path.insert(0, str(root / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source

def summarize(grid):
    return {
        "height": len(grid), "width": len(grid[0]),
        "palette": sorted({v for row in grid for v in row}),
        "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
    }

def main(root: Path, out: Path):
    gen, source = load(root)
    rows = []
    for seed in range(20):
        h8 = gen.generate(seed, 0, difficulty="medium", grid_h=8)
        h16 = gen.generate(seed, 0, difficulty="medium", grid_h=16)
        w9 = gen.generate(seed, 0, difficulty="medium", grid_w=9)
        w16 = gen.generate(seed, 0, difficulty="medium", grid_w=16)
        small = gen.generate(seed, 0, difficulty="medium", texture="small_overlap")
        large = gen.generate(seed, 0, difficulty="medium", texture="large_overlap")
        rows.append({
            "seed": seed,
            "grid_h_8": summarize(h8), "grid_h_16": summarize(h16),
            "height_outputs_equal": h8 == h16,
            "grid_w_9": summarize(w9), "grid_w_16": summarize(w16),
            "width_outputs_equal": w9 == w16,
            "small_overlap": summarize(small), "large_overlap": summarize(large),
            "texture_outputs_equal": small == large,
            "self_check_h8": gen.self_check(h8),
            "self_check_small": gen.self_check(small),
        })
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "finding": "advertised grid size and helpful texture controls are accepted but ignored",
        "source_observation": "generate() uses rng.randint for dimensions and only branches on degenerate texture values",
        "summary": {
            "seeds": len(rows),
            "height_extremes_identical": sum(r["height_outputs_equal"] for r in rows),
            "width_extremes_identical": sum(r["width_outputs_equal"] for r in rows),
            "texture_extremes_identical": sum(r["texture_outputs_equal"] for r in rows),
            "grid_h_8_wrong_height": sum(r["grid_h_8"]["height"] != 8 for r in rows),
            "grid_h_16_wrong_height": sum(r["grid_h_16"]["height"] != 16 for r in rows),
            "grid_w_9_wrong_width": sum(r["grid_w_9"]["width"] != 9 for r in rows),
            "grid_w_16_wrong_width": sum(r["grid_w_16"]["width"] != 16 for r in rows),
        },
        "rows": rows,
        "command": {"cwd": "repo", "argv": ["python3", "../checks/audit/891b61bb5d4d/probe_declared_axes.py", "--root", ".", "--out", "../checks/audit/891b61bb5d4d/declared-axis-probe.json"]},
    }
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); main(a.root.resolve(), a.out)
