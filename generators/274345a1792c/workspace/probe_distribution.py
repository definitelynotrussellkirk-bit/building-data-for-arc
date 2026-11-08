"""Compare two source-bound input populations without claiming reference labels.

Run through review.py run with the selected Python interpreter. This probe uses
public generation and validation hooks, and saves every materialized input.
"""
import argparse
from collections import Counter
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

from reviewer_support import find_root


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def collect(source, per_band):
    raw = source.read_bytes()
    spec = spec_from_file_location("distribution_" + digest(raw)[:12], source)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for band in ("easy", "medium", "hard"):
        for index in range(per_band):
            seed = 70000 + index
            grid = module.generate(seed, index, difficulty=band)
            proto = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
            origin = (min(r for r, _ in proto), min(c for _, c in proto))
            shape = [(r - origin[0], c - origin[1]) for r, c in proto]
            anchors = [(r, c, grid[r - 1][c]) for r, row in enumerate(grid)
                       for c, v in enumerate(row) if v == 6 and r > 0]
            rows.append({"seed": seed, "sample_index": index, "difficulty": band,
                         "overrides": {}, "input": grid,
                         "input_sha256": digest(json.dumps(grid, separators=(",", ":")).encode()),
                         "shape": shape, "origin": list(origin),
                         "dimensions": [len(grid), len(grid[0])],
                         "palette_size": len({v for row in grid for v in row}),
                         "anchors": anchors,
                         "repeated_control": len({a[2] for a in anchors}) < len(anchors),
                         "self_check": module.self_check(grid, difficulty=band)})
    if source.read_bytes() != raw:
        raise RuntimeError("source changed during distribution collection")
    summary = {}
    for band in ("easy", "medium", "hard", "all"):
        population = [row for row in rows if band == "all" or row["difficulty"] == band]
        summary[band] = {
            "draws": len(population),
            "unique_inputs": len({row["input_sha256"] for row in population}),
            "unique_normalized_shapes": len({tuple(map(tuple, row["shape"])) for row in population}),
            "unique_prototype_origins": len({tuple(row["origin"]) for row in population}),
            "unique_dimensions": len({tuple(row["dimensions"]) for row in population}),
            "prototype_cell_counts": dict(Counter(len(row["shape"]) for row in population)),
            "anchor_counts": dict(Counter(len(row["anchors"]) for row in population)),
            "palette_sizes": dict(Counter(row["palette_size"] for row in population)),
            "repeated_control_draws": sum(row["repeated_control"] for row in population),
            "self_check_failures": sum(bool(row["self_check"]) for row in population),
        }
    return {"source_path": str(source), "generator_sha256": digest(raw),
            "version": module.VERSION, "summary": summary, "samples": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=200)
    args = parser.parse_args()
    if args.out.exists() or args.per_band < 1:
        parser.error("use a new output path and positive per-band count")
    root = find_root(__file__)
    current = root / "generators/274345a1792c/generator.py"
    result = {"schema": "arcpuzzles-distribution-comparison-v1", "task_id": "274345a1792c",
              "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "label_scope": "input features and self_check only; no Racket outputs inferred",
              "sampling": {"bands": ["easy", "medium", "hard"],
                           "indices": [0, args.per_band - 1], "seed": "70000 + sample_index",
                           "per_band": args.per_band, "overrides": {}},
              "before": collect(args.baseline.resolve(), args.per_band),
              "after": collect(current, args.per_band)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({phase: result[phase]["summary"] for phase in ("before", "after")}, indent=2))


if __name__ == "__main__":
    main()
