"""Finite recurrence audit: one reference call, exact old witness, all 12 starts.

Run through review.py run so the public runtime and Racket are available.
The retained grids are replayed directly, never regenerated from changed code.
Passing covers these finite lessons and named rivals, not universal correctness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from itertools import groupby
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "8e6c44aee812"
BANDS = ("easy", "medium", "hard")
RETAINED = ("counterexamples/review-35316dedd6e945e7-v0001/retained/"
            "checks/audit/8e6c44aee812/evidence.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_run_per_color(grid):
    """Wrong rule: retain each color's first complete run, drop later runs."""
    diagonal = [grid[i][i] for i in range(min(len(grid), len(grid[0])))]
    while diagonal and diagonal[-1] == 0:
        diagonal.pop()
    seen, sequence = set(), []
    for color, run in groupby(diagonal):
        if color not in seen:
            sequence.extend(run)
            seen.add(color)
    return [[sequence[max(r, c) % len(sequence)] for c in range(2 * len(grid[0]))]
            for r in range(2 * len(grid))]


def exercise(report, root, gen, args):
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    retained_path = Path(__file__).resolve().parents[1] / RETAINED
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    old = retained["generated"]
    if len(canonical) != 4 or [row["sample_index"] for row in old] != [5, 6, 7, 8]:
        raise ValueError("Expected four canonical pairs and the retained indices 5..8")
    report["retained_evidence"] = {"path": str(retained_path), "sha256": sha(retained_path),
                                   "generator_sha256": retained["generator_sha256"]}
    planned, expected = [], {}
    for number, pair in enumerate(canonical):
        identity = f"canonical/{number}"
        planned.append({"id": identity, "kind": "canonical", "input": pair["input"],
                        **{k: pair[k] for k in ("variant", "split", "pair_index")}})
        expected[identity] = pair["output"]
    for row in old:
        identity = f"old/{row['sample_index']}"
        planned.append({"id": identity, "kind": "old",
                        **{k: row[k] for k in ("input", "seed", "sample_index", "difficulty", "overrides")}})
        expected[identity] = row["output"]
    for band in BANDS:
        for index in range(17):
            planned.append({"id": f"{band}/{index}", "kind": "generated", "seed": args.seed,
                            "sample_index": index, "difficulty": band, "overrides": {},
                            "input": gen.generate(args.seed, index, difficulty=band)})
    report["reference_request"] = {"api": "Catalog(root).apply", "task_id": TASK,
                                    "input_count": len(planned), "timeout": 120}
    applied = Catalog(root).apply(TASK, [row["input"] for row in planned], timeout=120)
    report["reference"] = {key: value for key, value in applied.items() if key != "results"}
    if len(applied["results"]) != len(planned):
        raise ValueError("Reference returned an incomplete result batch")
    if applied["generator_sha256"] != report["generator_sha256"]:
        report["errors"].append("Reference execution selected a different generator source")
    if not applied["rule_hash_matches_catalog"] or applied["executed_rule_hash"] != gen.RULE_HASH:
        report["errors"].append("Reference rule identity does not match the generator/catalog")
    pairs = report["pairs"] = []
    for request, result in zip(planned, applied["results"], strict=True):
        if result.get("input") != request["input"]:
            raise ValueError(f"Reference input identity mismatch: {request['id']}")
        row = {**request, **result}
        row["self_check"] = gen.self_check(copy.deepcopy(row["input"]))
        row["observed_overrides"] = gen.observe_overrides(copy.deepcopy(row["input"]))
        if row["error"] is not None or not row["valid_output"]:
            report["errors"].append(f"Reference failure for {row['id']}: {row['error']}")
        if row["kind"] != "old" and row["self_check"]:
            report["errors"].append(f"Input self_check rejected {row['id']}: {row['self_check']}")
        if row["id"] in expected:
            row["retained_label_matches_reference"] = row["output"] == expected[row["id"]]
            if not row["retained_label_matches_reference"]:
                report["errors"].append(f"Reference disagrees with retained label for {row['id']}")
        pairs.append(row)
    if any(row["error"] is not None or not row["valid_output"] for row in pairs):
        return
    by_id = {row["id"]: row for row in pairs}
    rivals = {"independent.first_run_per_color": first_run_per_color}
    for collection in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        for name, rival in getattr(gen, collection, {}).items():
            if not callable(rival):
                raise TypeError(f"{collection}.{name} is not callable")
            rivals[f"{collection}.{name}"] = rival
    report["rivals"] = list(rivals)
    predictions = {name: {row["id"]: rival(copy.deepcopy(row["input"])) for row in pairs}
                   for name, rival in rivals.items()}
    matches = {name: {row["id"]: outputs[row["id"]] == row["output"] for row in pairs}
               for name, outputs in predictions.items()}
    canonical_ids = [row["id"] for row in pairs if row["kind"] == "canonical"]
    report["canonical_fit"] = {
        name: {"pair_ids": canonical_ids, "matches": [fit[key] for key in canonical_ids],
               "fit_count": sum(fit[key] for key in canonical_ids)}
        for name, fit in matches.items()}
    independent = "independent.first_run_per_color"
    old_ids = [f"old/{i}" for i in range(5, 9)]
    old_query = by_id[old_ids[-1]]["output"]
    old_prediction = predictions[independent][old_ids[-1]]
    differences = sum(a != b for left, right in zip(old_query, old_prediction, strict=True)
                      for a, b in zip(left, right, strict=True))
    cells = sum(map(len, old_query))

    def hook(demo_ids, query_id):
        minimal = lambda key: {k: copy.deepcopy(by_id[key][k]) for k in ("input", "output")}
        return gen.lesson_identifiable([minimal(key) for key in demo_ids], minimal(query_id))

    report["old_counterexample"] = {
        "demo_pair_ids": old_ids[:3], "query_pair_id": old_ids[3],
        "retained_hook_warnings": retained["lesson_identifiable_reasons"],
        "current_hook_warnings": hook(old_ids[:3], old_ids[3]),
        "rival_demo_matches": [matches[independent][key] for key in old_ids[:3]],
        "rival_query_output": old_prediction, "different_cells": differences, "query_cells": cells,
        "canonical_fit_count": report["canonical_fit"][independent]["fit_count"],
    }
    old_verified = (differences == 83 and cells == 100
                    and all(matches[independent][key] for key in old_ids[:3])
                    and report["canonical_fit"][independent]["fit_count"] == 4)
    report["old_counterexample"]["verified"] = old_verified
    if not old_verified:
        report["errors"].append("The retained 83/100 recurrence counterexample did not reproduce")
    report["first_exact_counterexample"] = None
    report["lessons"] = {kind: [] for kind in ("production", "rotations")}
    for band in BANDS:
        for start in range(12):
            ids = [f"{band}/{i}" for i in range(start, start + args.demos + 1)]
            selections = [("production", args.demos)]
            selections.extend(("rotations", offset) for offset in range(len(ids)))
            for kind, offset in selections:
                query_id = ids[offset]
                demo_ids = [key for key in ids if key != query_id]
                survivors = [name for name, fit in matches.items() if all(fit[key] for key in demo_ids)]
                ambiguous = [name for name in survivors if not matches[name][query_id]]
                row = {"difficulty": band, "start": start, "query_offset": offset,
                       "demo_pair_ids": demo_ids, "query_pair_id": query_id,
                       "surviving_rivals": survivors, "ambiguous_rivals": ambiguous,
                       "hook_warnings": hook(demo_ids, query_id)}
                report["lessons"][kind].append(row)
                if ambiguous and report["first_exact_counterexample"] is None:
                    name = ambiguous[0]
                    report["first_exact_counterexample"] = {
                        "category": kind, **row, "rival": name,
                        "rival_query_output": predictions[name][query_id],
                        "grid_location": "Input/reference grids occur once in pairs, keyed by id"}
    report["summary"] = {
        kind: {"lesson_count": len(rows),
               "ambiguous_lesson_count": sum(bool(row["ambiguous_rivals"]) for row in rows),
               "hook_warning_lesson_count": sum(bool(row["hook_warnings"]) for row in rows),
               "ambiguities_by_rival": {name: sum(name in row["ambiguous_rivals"] for row in rows)
                                         for name in rivals}}
        for kind, rows in report["lessons"].items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0, help="Signed integer family seed (default: 0)")
    parser.add_argument("--demos", type=int, choices=range(1, 6),
                        help="Demo count; defaults to the selected generator's EXAMPLES_NEEDED")
    parser.add_argument("--out", type=Path, required=True, help="New JSON evidence file; never overwritten")
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        parser.error(f"Refusing to overwrite {args.out}")
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    args.demos = gen.EXAMPLES_NEEDED if args.demos is None else args.demos
    if type(args.demos) is not int or not 1 <= args.demos <= 5:
        parser.error("Selected demo count must be in 1..5 for the fixed 17-index probe")
    report = {"schema": "arcpuzzles-recurrence-probe-v1", "task_id": TASK,
              "generator_sha256": digest, "generator_version": gen.VERSION,
              "declared_rule_hash": gen.RULE_HASH, "script_sha256": sha(Path(__file__)),
              "command": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                          "environment": {"TMPDIR": os.environ.get("TMPDIR")}},
              "settings": {"seed": args.seed, "demos": args.demos, "bands": BANDS,
                           "indices": list(range(17)), "starts": list(range(12)), "overrides": {}},
              "scope": "Finite lessons and named rivals; no universal correctness or training approval claim.",
              "errors": []}
    try:
        exercise(report, root, gen, args)
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["generator_sha256_after"] = sha(source)
    report["source_stable"] = digest == report["generator_sha256_after"]
    if not report["source_stable"]:
        report["errors"].append("Generator source changed during the probe")
    report["passed"] = (not report["errors"] and "summary" in report
                        and all(not row["ambiguous_lesson_count"] and not row["hook_warning_lesson_count"]
                                for row in report.get("summary", {}).values()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, separators=(",", ":"))
        handle.write("\n")
    print(json.dumps({"out": str(args.out.resolve()), "generator_sha256": digest,
                      "passed": report["passed"], "summary": report.get("summary"),
                      "errors": report["errors"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
