#!/usr/bin/env python3
"""Measure geometry shortcuts in a86a630485ac's ordinary curriculum.

Run from a review packet root:

    python3 run_with_racket.py python3 \
      generators/a86a630485ac/workspace/geometry_probe.py --seeds 40

The probe uses the Python semantic mirror only.  It does not read canonical
answers and is therefore suitable for repeated distribution regression checks.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("a86a630485ac_geometry_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scene_metrics(gen, grid):
    errors, analysis = gen._analyze_grid(grid)
    if errors or analysis is None:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    objects = analysis["objects"]
    symmetric = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in objects
        if obj["lr_symmetric"]
    }
    asymmetric = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in objects
        if not obj["lr_symmetric"]
    }
    rival = gen.SEMANTIC_RIVALS["keep_wide_or_square_objects"](grid)
    intended = gen.rule_mirror(grid)
    return {
        "aspect_rival_matches": rival == intended,
        "matched_role_geometry": bool(symmetric & asymmetric),
        "bbox_widths": [obj["bbox_w"] for obj in objects],
        "bbox_heights": [obj["bbox_h"] for obj in objects],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=40)
    parser.add_argument("--seed-base", type=int, default=9100)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    gen = _load_generator()
    sample_indices = (1, 2, 3, 4, 6, 7, 8, 9)
    report = {
        "schema": "a86a630485ac-geometry-probe-v1",
        "generator_version": gen.VERSION,
        "generator_path": str(Path(gen.__file__).resolve()),
        "seeds": args.seeds,
        "seed_base": args.seed_base,
        "sample_indices": list(sample_indices),
        "bands": {},
    }

    for band in ("easy", "medium", "hard"):
        rows = []
        for seed_offset in range(args.seeds):
            for sample_index in sample_indices:
                grid = gen.generate(
                    args.seed_base + seed_offset,
                    sample_index,
                    difficulty=band,
                )
                rows.append(_scene_metrics(gen, grid))
        width_hist = Counter(width for row in rows for width in row["bbox_widths"])
        height_hist = Counter(height for row in rows for height in row["bbox_heights"])
        report["bands"][band] = {
            "scenes": len(rows),
            "aspect_rival_matches": sum(row["aspect_rival_matches"] for row in rows),
            "matched_role_geometry": sum(row["matched_role_geometry"] for row in rows),
            "bbox_width_histogram": dict(sorted(width_hist.items())),
            "bbox_height_histogram": dict(sorted(height_hist.items())),
        }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
