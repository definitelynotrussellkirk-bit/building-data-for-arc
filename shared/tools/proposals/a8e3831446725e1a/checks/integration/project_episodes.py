#!/usr/bin/env python3
"""Project source-bound generation receipts into public review examples.

Run through review.py run. The input JSONL files must already have been produced
by arcpuzzles generate with canonical Racket execution. This helper verifies
current source/program identity, distinct inputs, any declared lesson hook, and
public/private separation. It does not execute Racket or grant approval.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episodes", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    if args.queries < 1 or args.out.exists():
        parser.error("Use a positive query count and a new output directory")
    root = find_root(__file__)
    programs = {}
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                programs.setdefault(row["task_id"], set()).add(row["program_solution"])
    prepared, seen = [], set()
    for source in args.episodes:
        for line_index, line in enumerate(source.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            episode = json.loads(line)
            tid = episode["task_id"]
            module, _, digest = load_selected_generator(tid, root=root)
            if episode["provenance"]["generator_sha256"] != digest:
                raise ValueError(f"{tid}: source changed after generation")
            if episode["provenance"]["reference"] != "canonical":
                raise ValueError(f"{tid}: canonical generation is required")
            if episode["program"] not in programs.get(episode["rule_task_id"], set()):
                raise ValueError(f"{tid}: exact program is not a current canonical authority")
            if len(episode["test"]) != args.queries:
                raise ValueError(f"{tid}: wrong number of queries")
            raw = public_challenge_bytes(episode)
            identity = public_challenge_id(episode)
            inputs = [json.dumps(pair["input"], separators=(",", ":"))
                      for pair in episode["train"] + episode["test"]]
            if len(inputs) != len(set(inputs)) or identity in seen:
                raise ValueError(f"{tid}: duplicate input or visible episode")
            seen.add(identity)
            poisoned = copy.deepcopy(episode)
            poisoned.update(seed="private sentinel", program="private sentinel",
                            provenance={"private": True})
            for pair in poisoned["test"]:
                pair["output"] = [[9]]
                pair["private_parameter"] = "private sentinel"
            if public_challenge_bytes(poisoned) != raw or public_challenge_id(poisoned) != identity:
                raise ValueError(f"{tid}: private fields affected the public export")
            hook = getattr(module, "lesson_identifiable", None)
            lesson = {"status": "not_declared"}
            if callable(hook):
                labelled = [hook(copy.deepcopy(episode["train"]), copy.deepcopy(query))
                            for query in episode["test"]]
                masked = [hook(copy.deepcopy(episode["train"]), {"input": copy.deepcopy(query["input"])})
                          for query in episode["test"]]
                if any(result != [] for result in labelled):
                    raise ValueError(f"{tid}: labelled lesson hook rejected a query: {labelled}")
                lesson = {"status": "checked", "labelled_query_reasons": labelled,
                          "masked_query_reasons": masked,
                          "scope": "declared competitors only; not universal identifiability"}
            row = {"task_id": tid, "input_file": source.name, "line": line_index + 1,
                   "public_id": identity, "generator_sha256": digest,
                   "program_sha256": hashlib.sha256(episode["program"].encode()).hexdigest(),
                   "executed_rule_hash": episode["executed_rule_hash"],
                   "demonstrations": len(episode["train"]), "queries": len(episode["test"]),
                   "distinct_inputs": len(set(inputs)), "sample_indices": episode["sample_indices"],
                   "rejections": episode["rejections"], "private_fields_invariant": True,
                   "query_sizes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                   "lesson": lesson}
            prepared.append((identity, raw, row))
    if not prepared:
        raise ValueError("No episodes were supplied")
    args.out.mkdir(parents=True)
    public = args.out / "public"
    public.mkdir()
    rows = []
    for identity, raw, row in sorted(prepared):
        (public / f"{identity}.json").write_bytes(raw)
        rows.append(row)
    report = {"schema": "arcpuzzles-review-four-query-projection-v1", "status": "passed",
              "episodes": rows,
              "limits": ["Racket was executed by upstream generation, not by this projector.",
                         "Only this finite saved population is checked.",
                         "Missing lesson hooks are explicitly not_declared.",
                         "This report grants no approval or training admission."]}
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
