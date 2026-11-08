#!/usr/bin/env python3
"""Replay the grouped-layer shortcut against the selected public Racket rule.

Run through review.py run. Output is private authoring evidence, not a public
challenge or a training approval. Existing output directories are never reused.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "cde6cd1740f9"


def count_ignoring_rival(grid):
    output = [[0] * len(grid[0]) for _ in grid]
    for column in range(len(grid[0])):
        values = [row[column] for row in reversed(grid) if row[column]]
        if not values:
            continue
        k = int(len(values) ** 0.5)
        order = list(dict.fromkeys(values))
        for layer in range(k):
            radius = k - layer - 1
            for col in range(column - radius, column + radius + 1):
                output[len(grid) - 1 - layer][col] = order[min(layer, len(order) - 1)]
    return output


def partitions(grid):
    result = []
    for col in range(len(grid[0])):
        values = [row[col] for row in reversed(grid) if row[col]]
        counts = Counter(values)
        if len(values) == 9 and len(counts) == 2:
            result.append(tuple(counts[c] for c in dict.fromkeys(values)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--per-band", type=int, default=20)
    parser.add_argument("--require-partitions", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.per_band <= 100:
        parser.error("--per-band must be in 1..100")
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
    cases = []
    seen = set()
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        key = json.dumps([pair["input"], pair["output"]], separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            cases.append({"kind": "canonical", "input": pair["input"], "canonical_output": pair["output"]})
    for band in ("easy", "medium", "hard"):
        for index in range(args.per_band):
            cases.append({"kind": "generated", "seed": args.seed, "sample_index": index,
                          "difficulty": band, "input": generator.generate(args.seed, index, difficulty=band)})
    witness = [[0] * 13 for _ in range(16)]
    witness[1][6] = 5
    for row in range(4, 12):
        witness[row][6] = 2
    cases.append({"kind": "authored_witness", "input": witness})
    catalog = Catalog(root)
    outputs = []
    receipts = []
    for start in range(0, len(cases), 64):
        receipt = catalog.apply(TASK_ID, [x["input"] for x in cases[start:start + 64]],
                                timeout=180, check_generator_domain=True)
        if receipt["generator_sha256"] != source_hash:
            raise RuntimeError("Generator changed during the probe")
        filename = f"racket-{start // 64}.json"
        (args.out / filename).write_text(json.dumps(receipt, indent=2) + "\n")
        receipts.append(filename)
        outputs.extend(row["output"] for row in receipt["results"])
    rows = []
    for case, output in zip(cases, outputs, strict=True):
        grid = case["input"]
        rows.append({**case, "output": output, "partitions_bottom_up": partitions(grid),
                     "self_check": generator.self_check(grid),
                     "strict_canonical_like": generator.strict_canonical_like(grid),
                     "mirror_matches_racket": generator.rule_mirror(grid) == output,
                     "count_ignoring_matches_racket": count_ignoring_rival(grid) == output})
    canonical = [row for row in rows if row["kind"] == "canonical"]
    generated = [row for row in rows if row["kind"] == "generated"]
    observed = {band: sorted({tuple(p) for row in generated if row["difficulty"] == band
                              for p in row["partitions_bottom_up"]}) for band in ("easy", "medium", "hard")}
    witness_output = rows[-1]["output"]
    rival_output = count_ignoring_rival(witness)
    differences = [{"row": r, "column": c, "racket": witness_output[r][c], "rival": rival_output[r][c]}
                   for r in range(16) for c in range(13) if witness_output[r][c] != rival_output[r][c]]
    summary = {
        "schema": "cde6cd1740f9-count-partition-probe-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "generator_version": generator.VERSION,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_hash": receipt["executed_rule_hash"], "rule_text_sha256": receipt["rule_text_sha256"],
        "argv": sys.argv, "cwd": str(Path.cwd()), "seed": args.seed,
        "sample_indices": [0, args.per_band - 1], "samples_per_band": args.per_band,
        "canonical_unique_pairs": len(canonical),
        "canonical_labels_match_racket": all(r["canonical_output"] == r["output"] for r in canonical),
        "canonical_count_ignoring_matches": sum(r["count_ignoring_matches_racket"] for r in canonical),
        "generated_count_ignoring_matches": sum(r["count_ignoring_matches_racket"] for r in generated),
        "generated_count": len(generated), "observed_partitions_by_band": observed,
        "all_mirrors_match_racket": all(r["mirror_matches_racket"] for r in rows),
        "all_inputs_pass_self_check": all(not r["self_check"] for r in rows),
        "generated_strict_passes": sum(not r["strict_canonical_like"] for r in generated),
        "declared_canonical_shortcut_matches": {
            name: sum(fn(r["input"]) == r["output"] for r in canonical)
            for name, fn in generator.CANONICAL_SHORTCUTS.items()},
        "witness_differences": differences, "racket_receipts": receipts,
        "limitations": "Finite emitted draws and declared rivals; no universal induction or training approval.",
    }
    success = (summary["canonical_labels_match_racket"] and summary["all_mirrors_match_racket"]
               and summary["all_inputs_pass_self_check"] and len(differences) == 3)
    if args.require_partitions:
        success &= all(set(values) == {(5, 4), (8, 1)} for values in observed.values())
    summary["passed"] = bool(success)
    (args.out / "cases.json").write_text(json.dumps(rows, indent=2) + "\n")
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
