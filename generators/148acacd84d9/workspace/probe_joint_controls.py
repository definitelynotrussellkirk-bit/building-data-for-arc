"""Exhaust exact normal control tuples; observes inputs only, never labels.

Run in a library or copied runtime. --limit bounds tuples per band for a
quick baseline; omit it for the full 6,480-tuples-per-band matrix.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

TASK = "148acacd84d9"


def load_generator():
    # Locate the public helper by its documented library/runtime homes; the
    # helper then determines the root. No fixed ancestor depth is assumed.
    here = Path(__file__).resolve()
    for candidate in here.parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            helper = candidate / relative
            if helper.is_file():
                sys.path.insert(0, str(helper.parent))
                from reviewer_support import find_root
                root = find_root(here)
                break
        else:
            continue
        break
    else:
        raise FileNotFoundError("Cannot locate public reviewer_support helper")
    for relative in (f"generators/{TASK}/generator.py",
                     f"puzzle_generators/per_puzzle/{TASK}/generator.py"):
        source = root / relative
        if source.is_file():
            break
    else:
        raise FileNotFoundError(f"Selected generator missing under {root}")
    for runtime in (root / "shared/runtime", root):
        sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("joint_controls_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


def observations(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("rows must be nonempty lists")
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        raise ValueError("ragged rows")
    colors = [cell for row in grid for cell in row]
    if any(type(cell) is not int or not 0 <= cell <= 9 for cell in colors):
        raise ValueError("colors must be integer 0..9")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "mark_count": sum(cell != 0 for cell in colors),
            "palette_size": len(set(colors))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--band", action="append", choices=("easy", "medium", "hard"))
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--sample-index", type=int, default=4)
    parser.add_argument("--limit", type=int, help="maximum tuples PER BAND")
    parser.add_argument("--witness-limit", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a NEW path")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.witness_limit < 1:
        parser.error("--witness-limit must be positive")
    bands = list(dict.fromkeys(args.band or ["easy", "medium", "hard"]))
    module, source = load_generator()
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    counts = Counter()
    band_counts = {band: Counter() for band in bands}
    failures = Counter()
    witnesses = defaultdict(list)

    def failure(kind, details):
        failures[kind] += 1
        if len(witnesses[kind]) < args.witness_limit:
            witnesses[kind].append(details)

    for band in bands:
        matrix = itertools.product(range(4, 13), range(4, 13), range(3, 13), range(3, 11))
        if args.limit is not None:
            matrix = itertools.islice(matrix, args.limit)
        for ordinal, values in enumerate(matrix):
            controls = dict(zip(("grid_h", "grid_w", "mark_count", "palette_size"), values))
            feasible = controls["palette_size"] <= controls["mark_count"] + 1
            detail = {"band": band, "ordinal": ordinal, "overrides": controls,
                      "feasible": feasible}
            category = "feasible" if feasible else "infeasible"
            counts["tuples"] += 1
            counts[category] += 1
            band_counts[band][category] += 1
            try:
                grid = module.generate(args.seed, args.sample_index, difficulty=band, **controls)
            except Exception as exc:
                incompatible_axes = getattr(exc, "incompatible_axes", ())
                detail.update(error_type=type(exc).__name__, error=str(exc),
                              incompatible_axes=list(incompatible_axes))
                if feasible:
                    failure("feasible_rejected", detail)
                elif not isinstance(exc, ValueError):
                    failure("wrong_rejection_type", detail)
                elif not {"mark_count", "palette_size"}.issubset(incompatible_axes):
                    failure("missing_incompatibility_declaration", detail)
                else:
                    counts["explicit_incompatible_rejections"] += 1
                continue
            if not feasible:
                detail["grid"] = grid
                failure("infeasible_accepted", detail)
                continue
            try:
                observed = observations(grid)
            except Exception as exc:
                detail.update(error=str(exc), grid=grid)
                failure("malformed_grid", detail)
                continue
            if observed != controls:
                failure("exact_control_mismatch", dict(detail, observed=observed, grid=grid))
            try:
                errors = module.self_check(grid)
                if errors:
                    failure("self_check_failure", dict(detail, errors=errors, grid=grid))
            except Exception as exc:
                failure("self_check_error", dict(detail, error=repr(exc), grid=grid))
            # Determinism at the first feasible tuple and every 257th tuple.
            if ordinal == 0 or ordinal % 257 == 0:
                counts["determinism_checks"] += 1
                try:
                    repeated = module.generate(args.seed, args.sample_index, difficulty=band, **controls)
                    if repeated != grid:
                        failure("nondeterministic", dict(detail, grid=grid, repeated=repeated))
                except Exception as exc:
                    failure("determinism_error", dict(detail, error=repr(exc)))
        print(f"{band}: {dict(band_counts[band])}; cumulative failures={sum(failures.values())}", flush=True)
    final_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if final_hash != source_hash:
        failure("source_changed_during_probe", {"before": source_hash, "after": final_hash})
    report = {
        "schema": "arcpuzzles-task-joint-controls-probe-v1", "task_id": TASK,
        "generator_sha256": source_hash, "final_generator_sha256": final_hash,
        "scope": "Input controls, determinism subset and self_check only; no labels or Racket inference claims.",
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "parameters": {"bands": bands, "seed": args.seed, "sample_index": args.sample_index,
                       "limit_per_band": args.limit, "witness_limit": args.witness_limit,
                       "grid_h": [4, 12], "grid_w": [4, 12], "mark_count": [3, 12],
                       "palette_size_total_including_zero": [3, 10],
                       "feasibility": "palette_size <= mark_count + 1"},
        "counts": dict(counts), "per_band": {b: dict(c) for b, c in band_counts.items()},
        "failure_counts": dict(failures), "first_witnesses": dict(witnesses),
        "complete_matrix": args.limit is None or args.limit >= 6480,
        "status": "fail" if failures else "pass", "exit_code": 1 if failures else 0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"{report['status']}: {dict(counts)}; failures={dict(failures)}; source={source_hash}")
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
