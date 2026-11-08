#!/usr/bin/env python3
"""Diagnose shorter lessons by reusing saved source-bound Racket labels.

Run through run_with_racket.py for portable Python import paths. This tool calls
neither generate nor Racket. For N=3 and N=4 it uses the first N saved pairs as
demonstrations and the next pair as query. It is a prefix reanalysis, not a new
run of the public generate/export defaults. For each ambiguous prefix length,
one exact witness is retained; unrefuted rivals are counted separately.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import find_root

TASK_ID = "57488f2a7c15"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence: {out}")
    root = find_root(__file__)
    candidates = (root / "generators" / TASK_ID / "generator.py",
                  root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py")
    source = next(path for path in candidates if path.is_file())
    source_hash = sha(source.read_bytes())
    raw = Path(args.census).read_bytes()
    census = json.loads(raw)
    if census["task_id"] != TASK_ID or census["generator_sha256"] != source_hash:
        raise ValueError("Census and loaded generator source differ")
    if census["status"] != "no_ambiguity_found" or census["summary"]["materialization_errors"]:
        raise ValueError("Require a complete successful ordered-lesson census")
    spec = importlib.util.spec_from_file_location("short_lesson_subject", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if module.RULE_HASH != census["declared_rule_hash"]:
        raise ValueError("Declared rule binding changed")
    rivals = {}
    alias_count = 0
    for declaration in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS"):
        for name, function in getattr(module, declaration).items():
            if not callable(function):
                raise ValueError(f"Unsupported rival declaration: {declaration}:{name}")
            alias_count += 1
            record = rivals.setdefault(id(function), {"name": name, "function": function, "aliases": []})
            record["aliases"].append(f"{declaration}:{name}")
    report = {
        "schema": "saved-lesson-prefix-diagnostic-v1", "task_id": TASK_ID,
        "argv": sys.argv, "cwd": str(Path.cwd()), "generator_sha256": source_hash,
        "rule_hash": module.RULE_HASH, "source_census_path": args.census,
        "source_census_sha256": sha(raw), "probe_sha256": sha(Path(__file__).read_bytes()),
        "new_generated_grids": 0, "new_racket_executions": 0,
        "assembly": "First N saved training pairs as demonstrations; saved training pair N as query; original held-out test pair unused.",
        "distinct_callable_rivals": len(rivals), "declaration_aliases": alias_count,
        "rivals": [{k:v for k,v in item.items() if k != "function"} for item in rivals.values()],
        "prefixes": {},
        "limits": ["Reanalysis of saved labels, not a fresh public generate/export invocation.",
                   "Counts describe these materialized prefix lessons and finite declared rivals only.",
                   "Different prefix lengths overlap in their source data and are not independent samples."],
    }
    for n_demos in (3, 4):
        total = Counter()
        bands = {}
        rival_counts = Counter()
        surviving_counts = Counter()
        unique = set()
        first = None
        for lesson in census["lessons"]:
            if lesson["errors"]:
                raise ValueError("Saved lesson contains errors")
            saved = lesson["instance"]["train"]
            if len(saved) != 5:
                raise ValueError("Require exactly five saved training pairs")
            demonstrations, query = saved[:n_demos], saved[n_demos]
            total["lessons"] += 1
            band = bands.setdefault(lesson["band"], Counter())
            band["lessons"] += 1
            unique.update(grid_key(pair["input"]) for pair in saved[:n_demos+1])
            ambiguous_rivals = []
            surviving_rivals = []
            for rival in rivals.values():
                fn = rival["function"]
                demo_predictions = [fn([row[:] for row in pair["input"]]) for pair in demonstrations]
                if demo_predictions != [pair["output"] for pair in demonstrations]:
                    continue
                surviving_rivals.append(rival["name"])
                surviving_counts[rival["name"]] += 1
                prediction = fn([row[:] for row in query["input"]])
                if prediction == query["output"]:
                    continue
                ambiguous_rivals.append(rival["name"])
                rival_counts[rival["name"]] += 1
                if first is None:
                    difference = [{"row": r, "column": c, "racket": value,
                                   "rival": prediction[r][c]}
                                  for r, row in enumerate(query["output"])
                                  for c, value in enumerate(row) if prediction[r][c] != value]
                    assert difference
                    first = {"band": lesson["band"], "lesson_index": lesson["index"],
                             "seed": lesson["seed"], "sample_index": lesson["sample_index"],
                             "overrides": {}, "source_instance_sha256": lesson["instance_sha256"],
                             "source_sampling": lesson["instance"]["sampling"],
                             "n_train": n_demos, "train": demonstrations, "query": query,
                             "rival_name": rival["name"], "rival_aliases": rival["aliases"],
                             "rival_training_outputs": demo_predictions, "rival_query_output": prediction,
                             "visible_pairs_matched": n_demos, "query_differences": difference}
            total["ambiguous_lessons"] += bool(ambiguous_rivals)
            total["lessons_with_unrefuted_rivals"] += bool(surviving_rivals)
            band["ambiguous_lessons"] += bool(ambiguous_rivals)
            band["lessons_with_unrefuted_rivals"] += bool(surviving_rivals)
        report["prefixes"][str(n_demos)] = {**dict(total), "unique_inputs": len(unique),
            "per_band": {k:dict(v) for k,v in bands.items()},
            "ambiguous_lessons_per_rival": dict(sorted(rival_counts.items())),
            "lessons_with_rival_unrefuted": dict(sorted(surviving_counts.items())),
            "first_counterexample": first}
    if sha(source.read_bytes()) != source_hash:
        raise ValueError("Generator changed during analysis")
    report["status"] = "diagnostic_complete"
    report["exit_code"] = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generator_sha256": source_hash, "distinct_rivals": len(rivals),
                     "new_racket_executions": 0, "prefixes": {
                         key:{k:v for k,v in value.items() if k != "first_counterexample"}
                         for key,value in report["prefixes"].items()}}, indent=2))


if __name__ == "__main__":
    main()
