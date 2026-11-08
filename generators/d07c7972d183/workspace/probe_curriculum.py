#!/usr/bin/env python3
"""Count input-only curriculum features; never derive or substitute labels.

Run from any directory. ``--generator`` selects alternate source bytes while
canonical examples and runtime helpers remain bound to this probe's checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import types


def support():
    # Library checkouts keep the portable helper in shared/runtime; copied
    # runtimes expose it at their root. Discover that helper before find_root.
    for ancestor in Path(__file__).resolve().parents:
        for candidate in (ancestor, ancestor / "shared/runtime"):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                from reviewer_support import canonical_pairs, canonical_path, find_root
                return canonical_pairs, canonical_path, find_root
    raise RuntimeError("Cannot locate local reviewer_support.py")


def minimal_period(grid):
    return next(
        p for p in range(1, len(grid) + 1)
        if all(row == grid[r % p] for r, row in enumerate(grid))
    )


def features(grid):
    p = minimal_period(grid)
    return {
        "top_left_foreground": grid[0][0] == 1,
        "first_row_repeated_before_period": any(row == grid[0] for row in grid[1:p]),
        "first_row_all_foreground": all(cell == 1 for cell in grid[0]),
        "absence_of_all_foreground_column": not any(
            all(row[c] == 1 for row in grid) for c in range(len(grid[0]))
        ),
        "canonical_size_6x3": len(grid) == 6 and len(grid[0]) == 3,
    }


def counts(grids):
    result = {name: 0 for name in features([[0]])}
    for grid in grids:
        for name, present in features(grid).items():
            result[name] += int(present)
    return result


def positive_int(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=positive_int, default=400)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, help="new JSON path; refuses overwrite")
    parser.add_argument("--require-canonical-features", action="store_true",
                        help="fail if any canonical input feature has zero witnesses in a band")
    args = parser.parse_args()
    canonical_pairs, canonical_path, find_root = support()
    root = find_root(__file__)
    generator = (args.generator or Path(__file__).resolve().parents[1] / "generator.py").resolve()
    source = generator.read_bytes()
    module = types.ModuleType("curriculum_probe_target")
    module.__file__ = str(generator)
    sys.modules[module.__name__] = module
    exec(compile(source, str(generator), "exec"), module.__dict__)

    ledger = canonical_path(root)
    canonical_bytes = ledger.read_bytes()
    pairs = canonical_pairs("d07c7972d183", root=root)
    if ledger.read_bytes() != canonical_bytes:
        raise RuntimeError("Canonical ledger changed during probe")
    report = {
        "schema": "d07c7972d183-input-feature-support-v1",
        "task_id": "d07c7972d183",
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "generator_path": str(generator),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "generator_version": getattr(module, "VERSION", None),
        "canonical_path": str(ledger),
        "canonical_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "settings": {
            "per_band": args.per_band,
            "bands": ["easy", "medium", "hard"],
            "seed_and_sample_index": {
                "seed": "i", "sample_index": "i", "i_start": 0,
                "i_stop_exclusive": args.per_band,
            },
            "overrides": {},
            "require_canonical_features": args.require_canonical_features,
        },
        "canonical": {
            "pair_count": len(pairs),
            "feature_counts": counts(pair["input"] for pair in pairs),
            "pairs": [
                {"variant": pair["variant"], "split": pair["split"],
                 "pair_index": pair["pair_index"],
                 "minimal_row_period": minimal_period(pair["input"]),
                 "features": features(pair["input"]),
                 "validator_errors": module.self_check(pair["input"])}
                for pair in pairs
            ],
        },
        "per_band": {},
        "limits": [
            "Input features only; no outputs generated, executed, or compared.",
            "Finite deterministic support counts do not prove rule identifiability or distribution completeness.",
            "Alternate generator uses this checkout's shared helpers and canonical ledger.",
        ],
    }
    for band in report["settings"]["bands"]:
        grids = []
        accepted = rejected = validator_exceptions = 0
        failures = []
        for i in range(args.per_band):
            try:
                grid = module.generate(i, i, difficulty=band)
                features(grid)  # Keep malformed results visible as failures.
            except Exception as exc:
                failures.append({"seed": i, "sample_index": i, "stage": "generate_or_features",
                                 "error": f"{type(exc).__name__}: {exc}"})
                continue
            grids.append(grid)
            try:
                errors = module.self_check(grid)
                if errors:
                    rejected += 1
                    failures.append({"seed": i, "sample_index": i, "stage": "self_check",
                                     "errors": errors})
                else:
                    accepted += 1
            except Exception as exc:
                validator_exceptions += 1
                failures.append({"seed": i, "sample_index": i, "stage": "self_check",
                                 "error": f"{type(exc).__name__}: {exc}"})
        report["per_band"][band] = {
            "attempted": args.per_band, "generated": len(grids),
            "validator_counts": {"accepted": accepted, "rejected": rejected,
                                 "exceptions": validator_exceptions},
            "generated_witness_counts": counts(grids),
            "failures": failures,
        }
    report["source_unchanged_at_finish"] = generator.read_bytes() == source
    report["missing_canonical_features"] = {
        band: [name for name, count in report["canonical"]["feature_counts"].items()
               if count and not values["generated_witness_counts"][name]]
        for band, values in report["per_band"].items()
    }
    failed = (not report["source_unchanged_at_finish"]
              or any(band["failures"] for band in report["per_band"].values())
              or (args.require_canonical_features
                  and any(report["missing_canonical_features"].values())))
    report["status"] = "failed" if failed else "passed"
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    print(payload, end="")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
