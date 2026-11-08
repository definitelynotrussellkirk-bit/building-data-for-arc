#!/usr/bin/env python3
"""Exhaustively stress exact overrides across bands and schedule residues.

Run from any directory inside an extracted review packet, for example:

    python3 repo/generators/56169a1e5c1d/workspace/stress_exact_overrides.py \
        --replicas 10 --out checks/override-stress-final.json

The script imports the selected generator directly from the packet, checks every
height/width in 7..16, both pair counts, all three difficulty bands, every decoy
schedule residue, and a configurable number of independent seed replicas.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

TASK_ID = "56169a1e5c1d"
BANDS = ("easy", "medium", "hard")
HEIGHTS = tuple(range(7, 17))
WIDTHS = tuple(range(7, 17))
PAIR_COUNTS = (2, 3)
RESIDUES = (0, 1, 2)


def packet_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (
            (parent / "repo/shared/runtime").is_dir()
            and (parent / f"repo/generators/{TASK_ID}/generator.py").is_file()
        ):
            return parent
    raise RuntimeError("could not locate packet root above this script")


def load_generator(root: Path):
    runtime = root / "repo/shared/runtime"
    sys.path.insert(0, str(runtime))
    path = root / f"repo/generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location(f"stress_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def run(replicas: int) -> dict:
    root = packet_root()
    gen, source = load_generator(root)
    failures: list[dict] = []
    mode_counts = {mode: 0 for mode in gen.DECOY_MODES}
    band_counts = {band: 0 for band in BANDS}
    started = time.perf_counter()
    draws = 0

    for replica in range(replicas):
        for band_index, band in enumerate(BANDS):
            for height in HEIGHTS:
                for width in WIDTHS:
                    for pair_count in PAIR_COUNTS:
                        for residue in RESIDUES:
                            sample_index = 3 * replica + residue
                            seed = (
                                561_690_000
                                + replica * 100_000
                                + band_index * 10_000
                                + height * 100
                                + width * 10
                                + pair_count
                            )
                            draws += 1
                            try:
                                grid = gen.generate(
                                    seed,
                                    sample_index,
                                    difficulty=band,
                                    grid_h=height,
                                    grid_w=width,
                                    pair_count=pair_count,
                                )
                                observed = gen.observe_overrides(grid)
                                errors = gen.self_check(grid)
                                mode = gen.decoy_mode(sample_index)
                                mode_counts[mode] += 1
                                band_counts[band] += 1
                                if (len(grid), len(grid[0])) != (height, width):
                                    raise AssertionError(
                                        f"dimensions {(len(grid), len(grid[0]))}"
                                    )
                                if observed.get("pair_count") != pair_count:
                                    raise AssertionError(
                                        f"pair_count {observed.get('pair_count')}"
                                    )
                                if errors:
                                    raise AssertionError(f"self_check {errors}")
                            except Exception as exc:  # retain every exact case
                                failures.append(
                                    {
                                        "replica": replica,
                                        "band": band,
                                        "height": height,
                                        "width": width,
                                        "pair_count": pair_count,
                                        "residue": residue,
                                        "seed": seed,
                                        "sample_index": sample_index,
                                        "error": f"{type(exc).__name__}: {exc}",
                                    }
                                )

    return {
        "schema": "56169a1e5c1d-exact-override-stress-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "parameters": {
            "replicas": replicas,
            "bands": list(BANDS),
            "heights": [HEIGHTS[0], HEIGHTS[-1]],
            "widths": [WIDTHS[0], WIDTHS[-1]],
            "pair_counts": list(PAIR_COUNTS),
            "schedule_residues": list(RESIDUES),
            "seed_formula": (
                "561690000 + replica*100000 + band_index*10000 + "
                "height*100 + width*10 + pair_count"
            ),
            "sample_index_formula": "3*replica + residue",
        },
        "draws": draws,
        "expected_draws": replicas * len(BANDS) * len(HEIGHTS) * len(WIDTHS)
        * len(PAIR_COUNTS) * len(RESIDUES),
        "band_counts": band_counts,
        "mode_counts": mode_counts,
        "failures": failures,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicas", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.replicas < 1:
        parser.error("--replicas must be positive")
    report = run(args.replicas)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "draws": report["draws"],
        "failures": len(report["failures"]),
        "generator_sha256": report["generator_sha256"],
        "out": str(args.out),
    }))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
