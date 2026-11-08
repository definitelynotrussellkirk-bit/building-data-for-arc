#!/usr/bin/env python3
"""Reproducible public-API four-query and authority-parity check for this family."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.demos < 3 or args.queries < 1:
        parser.error("use at least 3 demonstrations and at least 1 query")
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator("dc155169ea57", root=root)
    catalog = Catalog(root)
    rivals = dict(gen.LESSON_COMPETITORS)
    canonical = canonical_pairs(gen.TASK_ID, root=root)
    canonical_fit = {name: all(fn(pair["input"]) == pair["output"] for pair in canonical)
                     for name, fn in gen.CANONICAL_SHORTCUTS.items()}
    summary = {"task_id": gen.TASK_ID, "generator_sha256": source_hash,
               "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "seed": args.seed, "demos": args.demos, "queries": args.queries,
               "canonical_pairs": len(canonical), "canonical_shortcut_fit": canonical_fit,
               "training_admitted": False, "episodes": [], "failures": []}
    for band in ("easy", "medium", "hard"):
        episode = catalog.generate(gen.TASK_ID, count=1, seed=args.seed, difficulty=band,
                                   n_train=args.demos, n_test=args.queries, allow_unapproved=True,
                                   timeout=180)[0]
        (args.out / (band + "-private.json")).write_text(json.dumps(episode, indent=2) + "\n")
        demos, queries = episode["train"], episode["test"]
        challenge = {"train": demos, "test": [{"input": pair["input"]} for pair in queries]}
        (args.out / (band + "-challenge.json")).write_text(json.dumps(challenge, indent=2) + "\n")
        pairs = demos + queries
        hashes = [digest(pair["input"]) for pair in pairs]
        refuting = {name: [i for i, pair in enumerate(demos) if fn(pair["input"]) != pair["output"]]
                    for name, fn in rivals.items()}
        surviving = [name for name, indices in refuting.items() if not indices]
        query_checks = [{"index": i,
                         "ambiguous_rivals": [name for name in surviving
                                               if rivals[name](pair["input"]) != pair["output"]],
                         "python_racket_equal": gen.rule_mirror(pair["input"]) == pair["output"]}
                        for i, pair in enumerate(queries)]
        row = {"band": band, "demonstrations": len(demos), "queries": len(queries),
               "unique_inputs": len(set(hashes)), "input_sha256": hashes,
               "refuting_demo_indices": refuting, "query_checks": query_checks,
               "all_labels_python_racket_equal": all(gen.rule_mirror(p["input"]) == p["output"] for p in pairs),
               "provenance": episode.get("provenance"), "sampler": episode.get("sampler")}
        if (len(demos) != args.demos or len(queries) != args.queries or
                len(set(hashes)) != len(pairs) or not row["all_labels_python_racket_equal"] or
                any(q["ambiguous_rivals"] for q in query_checks)):
            summary["failures"].append(band)
        summary["episodes"].append(row)
    summary["status"] = "pass" if not summary["failures"] and all(canonical_fit.values()) else "fail"
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"status": summary["status"], "episodes": len(summary["episodes"]),
                      "queries": sum(row["queries"] for row in summary["episodes"]),
                      "source_sha256": source_hash}))
    return int(summary["status"] != "pass")

if __name__ == "__main__":
    raise SystemExit(main())
