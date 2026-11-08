#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

TASK = "eca9af4f6c53"

def load(root: Path):
    source = root / "generators" / TASK / "generator.py"
    sys.path.insert(0, str(root / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source

def summarize(grid):
    colors = sorted({v for row in grid for v in row if v != 0})
    return {
        "height": len(grid), "width": len(grid[0]),
        "foreground_colors": colors,
        "observed_blocks": len(colors),
        "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
    }

def main(root: Path, out: Path):
    gen, source = load(root)
    rows = []
    for seed in range(20):
        low_n = gen.generate(seed, 0, difficulty="medium", n_blocks=1)
        high_n = gen.generate(seed, 0, difficulty="medium", n_blocks=9)
        low_p = gen.generate(seed, 0, difficulty="medium", palette_size=1)
        high_p = gen.generate(seed, 0, difficulty="medium", palette_size=9)
        rows.append({
            "seed": seed,
            "n_blocks_1": summarize(low_n),
            "n_blocks_9": summarize(high_n),
            "n_blocks_outputs_equal": low_n == high_n,
            "palette_size_1": summarize(low_p),
            "palette_size_9": summarize(high_p),
            "palette_outputs_equal": low_p == high_p,
            "self_check_n1": gen.self_check(low_n),
            "self_check_n9": gen.self_check(high_n),
        })
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "finding": "advertised n_blocks and palette_size controls are accepted but ignored",
        "source_observation": "generate() draws key 'blocks' rather than AXES key 'n_blocks', and never reads palette_size",
        "summary": {
            "seeds": len(rows),
            "n_blocks_extremes_identical": sum(r["n_blocks_outputs_equal"] for r in rows),
            "palette_extremes_identical": sum(r["palette_outputs_equal"] for r in rows),
            "n_blocks_1_wrong_count": sum(r["n_blocks_1"]["observed_blocks"] != 1 for r in rows),
            "palette_size_1_wrong_count": sum(len(r["palette_size_1"]["foreground_colors"]) != 1 for r in rows),
        },
        "rows": rows,
        "command": {"cwd": "repo", "argv": ["python3", "../checks/audit/eca9af4f6c53/probe_declared_axes.py", "--root", ".", "--out", "../checks/audit/eca9af4f6c53/declared-axis-probe.json"]},
    }
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); main(a.root.resolve(), a.out)
