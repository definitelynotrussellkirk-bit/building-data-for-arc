#!/usr/bin/env python3
"""Source-bound, input-only geometry diagnostics; does not execute Racket labels.

Run from any directory with --out NEW_PATH. The selected generator and canonical
data are found relative to this script, including ordinary copied runtimes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys


TASK_ID = "c68b56303c10"
BANDS = ("easy", "medium", "hard")


def _load_support():
    here = Path(__file__).resolve()
    for parent in here.parents:
        for candidate in (parent / "shared/runtime", parent):
            if (candidate / "reviewer_support.py").is_file():
                before = list(sys.path)
                try:
                    sys.path.insert(0, str(candidate))
                    import reviewer_support
                    return reviewer_support
                finally:
                    sys.path[:] = before
    raise FileNotFoundError("No local reviewer_support.py beside this source tree")


def _file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _describe(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("Expected a nonempty list grid")
    if any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("Expected nonempty list rows")
    if len({len(row) for row in grid}) != 1:
        raise ValueError("Ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("Expected exact integer colors 0..9")
    counts = Counter(value for row in grid for value in row)
    boxes = {}
    for color in (2, 3):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value == color]
        if not cells:
            raise ValueError(f"Missing color {color}; bbox is undefined")
        boxes[str(color)] = [min(r for r, _ in cells), min(c for _, c in cells),
                             max(r for r, _ in cells), max(c for _, c in cells)]
    red, green = boxes["2"], boxes["3"]
    overlap = [min(red[2], green[2]) - max(red[0], green[0]) + 1,
               min(red[3], green[3]) - max(red[1], green[1]) + 1]
    if min(overlap) <= 0:
        raise ValueError(f"Empty bbox intersection: {overlap}")
    return {"input_shape": [len(grid), len(grid[0])],
            "input_profile": [len(grid), len(grid[0]), len(counts)],
            "input_sha256": _grid_hash(grid),
            "color_counts": dict(sorted(counts.items())),
            "bboxes_top_left_bottom_right": boxes,
            "diagnostic_overlap_shape": overlap}


def _stats(values):
    return {"min": min(values), "median": statistics.median(values), "max": max(values)} if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=10007)
    parser.add_argument("--count", type=int, default=200, help="Consecutive indices 0..count-1 per band")
    parser.add_argument("--out", type=Path, required=True, help="New JSON output file; never overwritten")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    if args.out.exists():
        parser.error(f"Output already exists: {args.out}")

    support = _load_support()
    root = support.find_root(__file__)
    module, source_path, source_hash = support.load_selected_generator(TASK_ID, root=root)
    ledger = support.canonical_path(root)
    ledger_hash = _file_hash(ledger)
    pairs = support.canonical_pairs(TASK_ID, root=root, labeled_only=True)
    profiles = sorted({tuple(_describe(pair["input"])["input_profile"]) for pair in pairs})
    output_shapes = sorted({(len(pair["output"]), len(pair["output"][0])) for pair in pairs})
    envelope = [[min(profile[i] for profile in profiles), max(profile[i] for profile in profiles)]
                for i in range(3)]
    rules = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str):
                    raise ValueError("Selected canonical row lacks string program_solution")
                rules.append({"source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                              "normalized_rule_hash": hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]})

    report = {"schema": "c68b56303c10-distribution-probe-v1", "task_id": TASK_ID,
              "diagnostic_only": True,
              "label_basis": "BBox-intersection dimensions computed independently from input cells; no Racket execution or generated authoritative labels.",
              "bindings": {"generator_path": str(source_path.relative_to(root)),
                           "generator_sha256": source_hash,
                           "generator_version": getattr(module, "VERSION", None),
                           "declared_rule_hash": getattr(module, "RULE_HASH", None),
                           "canonical_path": str(ledger.relative_to(root)),
                           "canonical_sha256": ledger_hash, "selected_rules": rules,
                           "probe_sha256": _file_hash(__file__)},
              "settings": {"seed": args.seed, "count_per_band": args.count,
                           "bands": list(BANDS), "sample_indices": [0, args.count - 1]},
              "canonical": {"labeled_pairs": len(pairs), "input_profiles": profiles,
                            "input_profile_envelope": envelope, "output_shapes": output_shapes},
              "per_band": {}, "failures": [], "first_failure": None}
    all_hashes = set()
    for band in BANDS:
        rows = []
        band_failures = []
        first_draw = None
        first_failure = None
        for sample_index in range(args.count):
            grid = None
            try:
                grid = module.generate(args.seed, sample_index, difficulty=band)
                description = _describe(grid)
                rows.append(description)
                all_hashes.add(description["input_sha256"])
                if sample_index == 0:
                    first_draw = {"seed": args.seed, "sample_index": sample_index, **description,
                                  "input_rows": ["".join(map(str, row)) for row in grid]}
            except Exception as exc:
                failure = {"difficulty": band, "seed": args.seed, "sample_index": sample_index,
                           "exception_type": type(exc).__name__, "message": str(exc)[:600]}
                band_failures.append(failure)
                report["failures"].append(failure)
                if first_failure is None:
                    first_failure = dict(failure)
                    if grid is not None:
                        first_failure["input_preview"] = repr(grid)[:1200]
                if report["first_failure"] is None:
                    report["first_failure"] = first_failure
        exact_hits = sum(tuple(row["input_profile"]) in profiles for row in rows)
        envelope_hits = sum(all(lo <= value <= hi for value, (lo, hi) in zip(row["input_profile"], envelope))
                            for row in rows)
        output_hits = sum(tuple(row["diagnostic_overlap_shape"]) in output_shapes for row in rows)
        report["per_band"][band] = {
            "attempted": args.count, "successful": len(rows), "failure_count": len(band_failures),
            "distinct_input_hashes": len({row["input_sha256"] for row in rows}),
            "exact_canonical_input_profile_hits": exact_hits,
            "canonical_input_envelope_hits": envelope_hits,
            "canonical_output_shape_hits": output_hits,
            "input_height": _stats([row["input_shape"][0] for row in rows]),
            "input_width": _stats([row["input_shape"][1] for row in rows]),
            "diagnostic_overlap_height": _stats([row["diagnostic_overlap_shape"][0] for row in rows]),
            "diagnostic_overlap_width": _stats([row["diagnostic_overlap_shape"][1] for row in rows]),
            "output_shape_histogram": dict(sorted(Counter(f"{row['diagnostic_overlap_shape'][0]}x{row['diagnostic_overlap_shape'][1]}"
                                                         for row in rows).items())),
            "color_count_statistics": {str(color): _stats([row["color_counts"].get(color, 0) for row in rows])
                                       for color in range(10)},
            "red_green_count_histogram": dict(sorted(Counter(f"{row['color_counts'].get(2, 0)}x{row['color_counts'].get(3, 0)}"
                                                            for row in rows).items())),
            "first_draw": first_draw, "first_failure": first_failure}
    report["distinct_input_hashes_pooled"] = len(all_hashes)
    report["source_unchanged_after_sampling"] = _file_hash(source_path) == source_hash
    report["canonical_unchanged_after_sampling"] = _file_hash(ledger) == ledger_hash
    report["status"] = "pass" if not report["failures"] and report["source_unchanged_after_sampling"] and report["canonical_unchanged_after_sampling"] else "fail"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "out": str(args.out.resolve()),
                      "generator_sha256": source_hash,
                      "failure_count": len(report["failures"]),
                      "distinct_inputs": len(all_hashes)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
