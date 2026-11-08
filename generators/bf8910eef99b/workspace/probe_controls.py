"""Exhaust every advertised joint control combination for bf8910eef99b."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import PALETTES, PROFILES, RIVALS, load_generator, observed, oracle_output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    generator_path = Path(args.generator or Path(__file__).resolve().parents[1] / "generator.py")
    failures = []
    counts = Counter()
    unique = set()
    bands = (None, "easy", "medium", "hard")
    for band_index, band in enumerate(bands):
        for h in range(6, 10):
            for w in range(6, 10):
                for profile_index, profile in enumerate(PROFILES):
                    for palette_id in range(len(PALETTES)):
                        controls = {"grid_h": h, "grid_w": w,
                                    "placement_profile": profile,
                                    "palette_id": palette_id}
                        counts["cases"] += 1
                        try:
                            grid = module.generate(8800 + band_index, counts["cases"],
                                                   difficulty=band, **controls)
                            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
                            errors = module.self_check(grid)
                            if errors:
                                raise AssertionError(f"self_check: {errors}")
                            if observed(grid) != controls:
                                raise AssertionError(f"observed={observed(grid)} expected={controls}")
                            if module.observe_overrides(grid) != controls:
                                raise AssertionError("production observer disagrees")
                            truth = oracle_output(grid)
                            for name, rival in RIVALS.items():
                                if rival(grid) == truth:
                                    raise AssertionError(f"rival {name} survives")
                            counts[f"band:{band}"] += 1
                            counts[f"profile:{profile}"] += 1
                            counts[f"palette:{palette_id}"] += 1
                        except Exception as exc:  # retained row, never silently shrink coverage
                            failures.append({"difficulty": band, "controls": controls,
                                             "error": f"{type(exc).__name__}: {exc}"})
    invalid = (
        {"typo": 1}, {"grid_h": 5}, {"grid_h": 10}, {"grid_h": True},
        {"grid_w": 5}, {"grid_w": 10}, {"grid_w": 7.0},
        {"placement_profile": "center"}, {"placement_profile": 1},
        {"palette_id": -1}, {"palette_id": 6}, {"palette_id": "1"},
        {"texture": "too_close_to_edge"}, {"anchor_corner": True},
    )
    invalid_failures = []
    for controls in invalid:
        try:
            module.generate(0, 0, **controls)
        except (TypeError, ValueError):
            counts["invalid_rejected"] += 1
        else:
            invalid_failures.append(controls)
    report = {
        "schema": "bf8910eef99b-control-probe-v1",
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bands": [str(band) for band in bands],
        "counts": dict(counts),
        "unique_inputs": len(unique),
        "failures": failures,
        "invalid_failures": invalid_failures,
        "status": "passed" if not failures and not invalid_failures else "failed",
        "scope": "All 4x4x4x6 advertised joint controls in each of four difficulty settings; one seed/index per combination.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "unique_inputs": report["unique_inputs"]}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
