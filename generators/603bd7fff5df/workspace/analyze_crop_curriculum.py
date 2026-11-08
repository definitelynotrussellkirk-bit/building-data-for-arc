#!/usr/bin/env python3
"""Reproducible curriculum census for generator 603bd7fff5df.

The repository-wide battery answers whether the generator passes shared gates.
This task-local tool answers *why*: it reports recoverable-axis coverage, the
minimum amount of blue evidence in each rule-relevant region, semantic witness
rates, and how often each declared rival disagrees with the authoritative
Python mirror.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
GENERATOR_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if RUNTIME_ROOT.exists() and str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "curriculum_generator_603bd7fff5df", GENERATOR_ROOT / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load task generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
BANDS = ("easy", "medium", "hard")


def _sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def analyze(*, draws_per_band: int = 24, seed: int = 20261002) -> dict[str, Any]:
    if draws_per_band < 1:
        raise ValueError("draws_per_band must be at least 1")

    report: dict[str, Any] = {
        "task_id": GEN.TASK_ID,
        "generator_version": GEN.VERSION,
        "seed": int(seed),
        "draws_per_band": int(draws_per_band),
        "invalid_draws": 0,
        "invalid_examples": [],
        "per_band": {},
        "witness_hits": {name: 0 for name in sorted(GEN.SEMANTIC_WITNESSES)},
        "rival_disagreements": {name: 0 for name in sorted(GEN.SEMANTIC_RIVALS)},
    }

    for band_index, band in enumerate(BANDS):
        axes = {name: Counter() for name in GEN.AXES}
        output_shapes: Counter[str] = Counter()
        region_minima = {
            "top_halo": None,
            "bottom_halo": None,
            "inside": None,
            "outside_crop": None,
        }

        for sample_index in range(draws_per_band):
            # Keep one fixed family seed per band.  The varying sample index is
            # the public curriculum sequence; the band offset prevents clones.
            draw_seed = int(seed) + band_index * 100_003
            try:
                grid = GEN.generate(draw_seed, sample_index, difficulty=band)
                errors = GEN.self_check(grid)
            except Exception as exc:  # retained rather than hiding a bad seed
                report["invalid_draws"] += 1
                if len(report["invalid_examples"]) < 10:
                    report["invalid_examples"].append(
                        {
                            "band": band,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                continue

            if errors:
                report["invalid_draws"] += 1
                if len(report["invalid_examples"]) < 10:
                    report["invalid_examples"].append(
                        {
                            "band": band,
                            "sample_index": sample_index,
                            "error": "; ".join(errors),
                        }
                    )
                continue

            observed = GEN.observe_overrides(grid)
            semantic = GEN.semantic_observables(grid)
            truth = GEN.rule_mirror(grid)

            for name, value in observed.items():
                axes[name][str(value)] += 1
            shape = f"{len(truth)}x{len(truth[0])}"
            output_shapes[shape] += 1

            for region, count in semantic["blue_region_counts"].items():
                old = region_minima[region]
                region_minima[region] = count if old is None else min(old, count)

            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    report["witness_hits"][name] += 1
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                if rival(grid) != truth:
                    report["rival_disagreements"][name] += 1

        report["per_band"][band] = {
            "axes": {name: _sorted_counter(values) for name, values in axes.items()},
            "output_shapes": _sorted_counter(output_shapes),
            "minimum_blue_region_counts": {
                name: (0 if value is None else value)
                for name, value in region_minima.items()
            },
        }

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    report = analyze(draws_per_band=args.draws_per_band, seed=args.seed)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["invalid_draws"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
