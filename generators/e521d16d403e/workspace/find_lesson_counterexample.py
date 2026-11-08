"""Find a concrete canonical-fitting rival that a generated lesson fails to teach.

The structural model is used only to shortlist a candidate. A finding is emitted
only after the public Racket API verifies every demonstration and query label.
The selected generator can be an explicitly retained earlier source snapshot.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root
from semantic_probe import RIVALS, predict


TASK = "e521d16d403e"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-seeds", type=int, default=100)
    parser.add_argument("--band", choices=("easy", "medium", "hard"), default="easy")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new evidence path")
    if args.max_seeds < 1:
        parser.error("--max-seeds must be positive")
    root = find_root(__file__)
    source = args.generator.resolve()
    source_bytes = source.read_bytes()
    spec = importlib.util.spec_from_file_location("lesson_counterexample_source", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    rivals = [name for name in RIVALS
              if all(predict(p["input"], name) == p["output"] for p in canonical)]
    result = {
        "task_id": TASK, "generator_path": str(source),
        "generator_sha256": sha(source_bytes), "generator_version": gen.VERSION,
        "rule_scope": "unchanged selected canonical Racket authority",
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "canonical_records": len(canonical), "canonical_fitting_rivals": rivals,
        "search": {"seed_start": 0, "seed_stop_exclusive": args.max_seeds,
                   "band": args.band, "starts": [0, 1, 2, 3],
                   "n_train": 3, "n_test": 1},
        "examined_windows": 0, "rejected_windows": 0, "finding": None,
    }
    catalog = Catalog(root)
    for seed in range(args.max_seeds):
        if result["finding"]:
            break
        grids = [gen.generate(seed, index, difficulty=args.band) for index in range(7)]
        for start in range(4):
            result["examined_windows"] += 1
            window = grids[start:start+4]
            if any(gen.self_check(g, difficulty=args.band) for g in window):
                result["rejected_windows"] += 1
                continue
            expected = [predict(g) for g in window]
            for name in rivals:
                rival_outputs = [predict(g, name) for g in window]
                if not (rival_outputs[:3] == expected[:3] and rival_outputs[3] != expected[3]):
                    continue
                authority = catalog.apply(TASK, window, timeout=180)
                actual = [item["output"] for item in authority["results"]]
                if actual != expected:
                    raise RuntimeError("Shortlisting model disagrees with actual Racket outputs")
                result["finding"] = {
                    "kind": "reproduced_teaching_ambiguity", "rival": name,
                    "seed": seed, "difficulty": args.band,
                    "sample_indices": list(range(start, start+4)), "overrides": {},
                    "train": [{"input": deepcopy(g), "output": y}
                              for g, y in zip(window[:3], actual[:3])],
                    "test": {"input": deepcopy(window[3]), "output": actual[3],
                             "rival_output": rival_outputs[3]},
                    "rival_fits_every_demo": True, "rival_disagrees_with_query": True,
                    "reference_execution": authority,
                }
                break
            if result["finding"]:
                break
    if source.read_bytes() != source_bytes:
        raise RuntimeError("Input generator snapshot changed during the search")
    result["status"] = "counterexample_found" if result["finding"] else "none_in_finite_search"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "status": result["status"],
                      "generator_sha256": result["generator_sha256"],
                      "examined_windows": result["examined_windows"],
                      "rival": result["finding"]["rival"] if result["finding"] else None}))


if __name__ == "__main__":
    main()
