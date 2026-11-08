#!/usr/bin/env python3
"""Replay the fixed seed-17 hard lesson as 3 demos and 4 ordered queries."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator
from border_probe import RIVAL, TASK


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = Path.cwd()
    gen, path, digest = load_selected_generator(TASK, root=root)
    if args.source:
        path = args.source.resolve(strict=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        spec = importlib.util.spec_from_file_location("ordered_lesson_proposal", path)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
    programs = {r["program_solution"] for r in Catalog(root)._variants()[TASK]}
    assert len(programs) == 1
    program = programs.pop()
    apply, runtime, bridge = _real_evaluator(root / "shared/runtime")
    pairs = []
    try:
        for index in range(7):
            grid = gen.generate(17, index, difficulty="hard")
            assert gen.self_check(grid) == []
            answer, rival = apply(program, grid), apply(RIVAL, grid)
            assert answer == gen.rule_mirror(grid)
            pairs.append({"sample_index": index, "input": grid, "output": answer,
                          "rival_output": rival, "rival_matches": rival == answer})
    finally:
        bridge.close()
    disagreements = []
    demo_fit = all(p["rival_matches"] for p in pairs[:3])
    for index, pair in enumerate(pairs[3:]):
        if pair["rival_matches"]:
            continue
        disagreements.append({"query_index": index, "sample_index": pair["sample_index"],
                              "existing_gate_reasons": gen.lesson_identifiable(pairs[:3], pair),
                              "differing_cells": [[r, c] for r, row in enumerate(pair["output"])
                                                  for c, value in enumerate(row) if value != pair["rival_output"][r][c]]})
    report = {
        "schema": "ordered-border-region-witness-v1", "task_id": TASK,
        "seed": 17, "difficulty": "hard", "demo_sample_indices": [0, 1, 2],
        "query_sample_indices": [3, 4, 5, 6], "generator_sha256": digest,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_program": program, "rival_program": RIVAL, "runtime_identity": runtime,
        "racket_evaluations": 14, "pairs": pairs,
        "rival_fits_all_demos": demo_fit,
        "rival_matches_first_query": pairs[3]["rival_matches"],
        "query_disagreements": disagreements,
        "ambiguous_query_indices": [r["query_index"] for r in disagreements] if demo_fit else [],
        "scope": "Three unchanged demonstrations and four sequentially eligible generator inputs. Each query is judged from the demos. No predicted trajectory or training admission is asserted.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "racket_evaluations", "rival_fits_all_demos", "rival_matches_first_query", "ambiguous_query_indices", "query_disagreements")}, indent=2))


if __name__ == "__main__":
    main()
