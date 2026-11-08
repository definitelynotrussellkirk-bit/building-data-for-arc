#!/usr/bin/env python3
"""Run a source-bound structural/semantic census for 0a9926d504f3."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from reference_probe import (
    center_always_visible,
    exactly_four_markers,
    grid_hash,
    intended_output,
    load_generator,
    observed,
    preserve_nonrole_markers,
    source_sha256,
)


def run(per_band: int) -> dict[str, Any]:
    gen = load_generator()
    report: dict[str, Any] = {
        "schema": "0a9926d504f3-stress-probe-v1",
        "task_id": "0a9926d504f3",
        "generator_sha256": source_sha256(),
        "per_band": per_band,
        "bands": {},
    }
    all_hashes: set[str] = set()
    for band in ("easy", "medium", "hard"):
        textures: Counter[str] = Counter()
        shapes: Counter[str] = Counter()
        rival_differences: Counter[str] = Counter()
        failures: list[dict[str, Any]] = []
        hashes: set[str] = set()
        for index in range(per_band):
            seed = 10_000 + index * 37
            try:
                grid = gen.generate(seed, index, difficulty=band)
                diagnostics = list(gen.self_check(grid))
                actual = observed(grid)
                expected_profile = gen.schedule_profile(seed, index, difficulty=band)
                if diagnostics:
                    raise AssertionError("; ".join(diagnostics))
                if actual["texture"] != expected_profile:
                    raise AssertionError(
                        f"profile={expected_profile!r}, observed={actual['texture']!r}"
                    )
                truth = intended_output(grid)
                rivals = {
                    "exactly_four_markers": exactly_four_markers(grid),
                    "center_always_visible": center_always_visible(grid),
                    "preserve_nonrole_markers": preserve_nonrole_markers(grid),
                }
                for name, output in rivals.items():
                    rival_differences[name] += int(output != truth)
                digest = grid_hash(grid)
                hashes.add(digest)
                all_hashes.add(digest)
                textures[str(actual["texture"])] += 1
                shapes[f"{actual['grid_h']}x{actual['grid_w']}"] += 1
            except Exception as exc:  # bounded evidence, never silent
                if len(failures) < 20:
                    failures.append({
                        "index": index,
                        "seed": seed,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
        report["bands"][band] = {
            "draws": per_band,
            "unique_inputs": len(hashes),
            "textures": dict(sorted(textures.items())),
            "shapes": dict(sorted(shapes.items())),
            "rival_differences": dict(sorted(rival_differences.items())),
            "failures": failures,
        }
    report["total_unique_inputs"] = len(all_hashes)
    report["ok"] = not any(row["failures"] for row in report["bands"].values())
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=400)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = run(args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
