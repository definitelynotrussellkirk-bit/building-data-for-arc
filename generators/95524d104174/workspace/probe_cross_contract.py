#!/usr/bin/env python3
"""Reproduce cross coverage and rivals with actual canonical Racket labels.

Run through review.py run. This is authoring evidence, never a blind-solve tool.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "95524d104174"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def expected_ring(grid):
    """Independent pixel specification: eight neighbors, original center/outside."""
    h, w = len(grid), len(grid[0])
    row = next(r for r in range(h) if all(grid[r]))
    col = next(c for c in range(w) if all(grid[r][c] for r in range(h)))
    return [[4 if max(abs(r - row), abs(c - col)) == 1 else value
             for c, value in enumerate(line)] for r, line in enumerate(grid)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1 or args.out.exists():
        parser.error("--per-band must be positive and --out must be a new path")
    root = find_root(__file__)
    gen, source_path, source_hash = load_selected_generator(TASK_ID, root=root)
    ledger = canonical_path(root)
    records = [json.loads(line) for line in ledger.read_text().splitlines()
               if line.strip() and json.loads(line).get("task_id") == TASK_ID]
    if len(records) != 1:
        raise ValueError("This task probe expects exactly one canonical variant")
    rule = records[0]["program_solution"]
    canonical = canonical_pairs(TASK_ID, root=root)
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row})) for p in canonical}
    envelope = [(min(p[i] for p in profiles), max(p[i] for p in profiles)) for i in range(3)]
    report = {"schema": "cross-contract-probe-v1", "task_id": TASK_ID,
              "argv": sys.argv, "cwd": str(Path.cwd()), "seed": args.seed,
              "sample_indices": [0, args.per_band - 1], "per_band": args.per_band,
              "source_path": str(source_path.relative_to(root)), "generator_sha256": source_hash,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "canonical_file_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
              "rule_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
              "declared_rule_hash": gen.RULE_HASH, "canonical_pairs": [],
              "bands": {}, "failures": [], "first_generated_witnesses": {}}
    hashes = set()
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define cross_probe_rule {strip_rule_wrapper(rule)})")

        def apply(grid):
            bridge.define_grid("cross_probe_input", grid)
            return bridge.eval_text("(cross_probe_rule cross_probe_input)")

        for pair in canonical:
            output = apply(pair["input"])
            entry = {"split": pair["split"], "pair_index": pair["pair_index"],
                     "label_matches": output == pair["output"],
                     "self_check": gen.self_check(pair["input"]),
                     "rival_fits": {name: rival(pair["input"]) == output
                                    for name, rival in gen.LESSON_COMPETITORS.items()}}
            report["canonical_pairs"].append(entry)
            if not entry["label_matches"] or entry["self_check"]:
                report["failures"].append({"kind": "canonical", **entry})

        for band in ("easy", "medium", "hard"):
            counts, band_hashes, rows = Counter(), set(), []
            for index in range(args.per_band):
                grid = gen.generate(args.seed, index, difficulty=band)
                h, w = len(grid), len(grid[0])
                row = next(r for r in range(h) if all(grid[r]))
                col = next(c for c in range(w) if all(grid[r][c] for r in range(h)))
                errors, output = gen.self_check(grid), apply(grid)
                counts["draws"] += 1
                counts["self_check_passed"] += not errors
                counts["reference_matches_pixel_spec"] += output == expected_ring(grid)
                counts["four_by_four"] += h == w == 4
                counts["margin_one"] += min(row, col, h - 1 - row, w - 1 - col) == 1
                counts["rectangular"] += h != w
                counts["horizontal_wins"] += grid[row][col] == grid[row][0]
                counts["input_color_4"] += any(4 in line for line in grid)
                p = (h, w, len({v for line in grid for v in line}))
                counts["exact_profile_hits"] += p in profiles
                counts["envelope_hits"] += all(lo <= value <= hi for value, (lo, hi) in zip(p, envelope))
                ih = digest(grid)
                hashes.add(ih)
                band_hashes.add(ih)
                rows.append({"sample_index": index, "input_sha256": ih,
                             "output_sha256": digest(output), "height": h, "width": w,
                             "crossing": [row, col], "original_center": grid[row][col]})
                if errors or output != expected_ring(grid):
                    report["failures"].append({"kind": "generated", "band": band,
                                               "sample_index": index, "input": grid,
                                               "output": output, "self_check": errors})
                for name, rival in gen.LESSON_COMPETITORS.items():
                    disagrees = rival(grid) != output
                    counts["refutes_" + name] += disagrees
                    if disagrees and name not in report["first_generated_witnesses"]:
                        report["first_generated_witnesses"][name] = {
                            "band": band, "seed": args.seed, "sample_index": index,
                            "input": grid, "output": output, "rival_output": rival(grid)}
            report["bands"][band] = {"counts": dict(counts), "unique_inputs": len(band_hashes), "samples": rows}

        witness = [[0, 0, 1, 0, 0, 0], [2, 2, 1, 2, 2, 2],
                   [0, 0, 1, 0, 0, 0], [0, 0, 1, 0, 0, 0]]
        actual = apply(witness)
        wanted = [[0, 4, 4, 4, 0, 0], [2, 4, 1, 4, 2, 2],
                  [0, 4, 4, 4, 0, 0], [0, 0, 1, 0, 0, 0]]
        rival = gen.CANONICAL_SHORTCUTS["modal_center"](witness)
        report["minimal_modal_counterexample"] = {"input": witness, "output": actual,
                                                   "rival_output": rival, "self_check": gen.self_check(witness),
                                                   "verified": actual == wanted and rival != actual}
        if not report["minimal_modal_counterexample"]["verified"]:
            report["failures"].append({"kind": "modal_counterexample"})
    report["unique_inputs"] = len(hashes)
    report["total_generated"] = 3 * args.per_band
    report["status"] = "passed" if not report["failures"] else "failed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "total_generated": report["total_generated"],
                      "unique_inputs": report["unique_inputs"],
                      "bands": {b: v["counts"] for b, v in report["bands"].items()},
                      "out": str(args.out)}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
