#!/usr/bin/env python3
"""Source-bound, Racket-free regression probe for 9cea0e6444f1.

Checks observable controls, per-input shortcut witnesses, and every consecutive
three-example window's ability to refute the include-all-colors rival. The
Racket-backed lesson census remains the authority for labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

TASK = "9cea0e6444f1"
HERE = Path(__file__).resolve().parents[1]


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=40)
    parser.add_argument("--seed", type=int, default=90210)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE / "generator.py")).resolve()
    gen = load_generator(path)
    core = (
        "absolute_coordinates",
        "color_1_only",
        "color_2_only",
        "intersection_only",
        "xor_only",
        "solid_bbox",
    )
    report = {
        "schema": "9cea0e6444f1-semantic-probe-v1",
        "task_id": TASK,
        "generator": str(path),
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "per_band": args.per_band,
        "draws": 0,
        "core_rival_agreements": [],
        "all_nonzero_windows_survived": [],
        "axis_values": {name: set() for name in gen.AXES},
    }

    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = []
        for index in range(args.per_band):
            sample_index = index + band_index * args.per_band
            grid = gen.generate(args.seed + band_index, sample_index, difficulty=band)
            grids.append(grid)
            report["draws"] += 1
            observed = gen.observe_overrides(grid)
            for name, value in observed.items():
                report["axis_values"][name].add(value)
            expected = gen._reference_output(grid)
            for name in core:
                if gen.LESSON_COMPETITORS[name](grid) == expected:
                    report["core_rival_agreements"].append(
                        {"band": band, "sample_index": sample_index, "rival": name}
                    )
        for start in range(max(0, len(grids) - 2)):
            window = grids[start : start + 3]
            if all(
                gen.LESSON_COMPETITORS["all_nonzero_colors"](grid)
                == gen._reference_output(grid)
                for grid in window
            ):
                report["all_nonzero_windows_survived"].append(
                    {"band": band, "window_start": start}
                )

    report["axis_values"] = {
        name: sorted(values, key=lambda value: (type(value).__name__, repr(value)))
        for name, values in report["axis_values"].items()
    }
    report["passed"] = not report["core_rival_agreements"] and not report["all_nonzero_windows_survived"]
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
