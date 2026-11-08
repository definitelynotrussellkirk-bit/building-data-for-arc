#!/usr/bin/env python3
"""Bounded small-zero-region shortcut audit with protected Racket labels.

From the packet root:
  WORK/.venv/bin/python review.py run python3 \
    ../checks/additional-ticket-001/border_probe.py \
    --out ../checks/additional-ticket-001/before.json
Optional --source loads an explicit, separate proposed generator file.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator

TASK = "36343a80035c"
RIVAL = """(rule!
 (for/fold ((out (empty-grid (rows g) (cols g) 0)))
           ((region (in-list (filter (lambda (cells) (<= (length cells) 4))
                                     (find-0-regions g 0)))))
   (paint-cells out region 8)))"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = Path.cwd()
    folder = Path(__file__).resolve().parent
    draw = json.loads((folder / "draw.json").read_bytes())
    if draw["ticket"]["task_id"] != TASK:
        raise ValueError("Wrong frozen ticket")
    baseline, source, source_sha = load_selected_generator(TASK, root=root)
    if source_sha != draw["ticket"]["source"]["generator_sha256"]:
        raise ValueError("Frozen baseline source changed")
    gen = baseline
    if args.source:
        source = args.source.resolve(strict=True)
        source_sha = sha(source.read_bytes())
        spec = importlib.util.spec_from_file_location("border_proposal", source)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
    programs = {row["program_solution"] for row in Catalog(root)._variants()[TASK]}
    if len(programs) != 1:
        raise ValueError("Expected exactly one canonical program")
    program = programs.pop()
    seeds = [0, 1, 17, int(draw["ticket"]["probe_seed"][:16], 16)]
    apply, runtime, bridge = _real_evaluator(root / "shared/runtime")
    started = time.monotonic()
    report = {
        "schema": "bounded-border-region-probe-v1", "task_id": TASK,
        "ticket_id": draw["ticket"]["ticket_id"],
        "generator_sha256": source_sha,
        "baseline_generator_sha256": draw["ticket"]["source"]["generator_sha256"],
        "probe_sha256": sha(Path(__file__).read_bytes()),
        "draw_sha256": sha((folder / "draw.json").read_bytes()),
        "canonical_program": program, "canonical_program_sha256": sha(program.encode()),
        "rival_program": RIVAL, "rival_program_sha256": sha(RIVAL.encode()),
        "runtime_identity": runtime,
        "bounds": {"seeds": seeds, "difficulty": ["easy", "medium", "hard"],
                   "sample_indices": [0, 1, 2, 3], "ordinary_ordered_query_index": 3,
                   "candidate_rivals": ["paint_zero_components_of_area_at_most_four"]},
        "lessons": [], "production_ambiguities": [], "rotation_ambiguities": [],
        "surviving_lessons": [], "racket_evaluations": 0,
        "mirror_disagreements": [], "errors": [],
        "scope": "Fixed finite samples, one executable rival. Rotations are counterfactual lessons; only query slot 3 is ordinary production order. No training admission.",
    }
    try:
        for seed in seeds:
            for difficulty in report["bounds"]["difficulty"]:
                pairs = []
                for index in range(4):
                    grid = gen.generate(seed, index, difficulty=difficulty)
                    errors = gen.self_check(grid)
                    if errors:
                        report["errors"].append({"seed": seed, "difficulty": difficulty, "index": index, "errors": errors})
                    label = apply(program, grid)
                    prediction = apply(RIVAL, grid)
                    report["racket_evaluations"] += 2
                    if label != gen.rule_mirror(grid):
                        report["mirror_disagreements"].append([seed, difficulty, index])
                    h, w = len(grid), len(grid[0])
                    pairs.append({"sample_index": index, "input": grid, "output": label,
                                  "rival_output": prediction, "rival_matches": label == prediction,
                                  "regions": [{"area": len(region), "touches_border": gen._touches_border(region, h, w)}
                                              for region in gen._zero_regions(grid)],
                                  "observed_axes": gen.observe_overrides(grid)})
                lesson_index = len(report["lessons"])
                report["lessons"].append({"seed": seed, "difficulty": difficulty, "pairs": pairs})
                if all(pair["rival_matches"] for pair in pairs):
                    report["surviving_lessons"].append(lesson_index)
                for query_index in range(4):
                    if not pairs[query_index]["rival_matches"] and all(
                        pair["rival_matches"] for i, pair in enumerate(pairs) if i != query_index
                    ):
                        witness = {"lesson_index": lesson_index, "seed": seed, "difficulty": difficulty,
                                   "demo_indices": [i for i in range(4) if i != query_index],
                                   "query_index": query_index,
                                   "existing_gate_reasons": gen.lesson_identifiable(
                                       [pair for i, pair in enumerate(pairs) if i != query_index], pairs[query_index])}
                        report["rotation_ambiguities"].append(witness)
                        if query_index == 3:
                            report["production_ambiguities"].append(witness)
    finally:
        bridge.close()
    report["elapsed_seconds"] = time.monotonic() - started
    report["status"] = "finding" if report["production_ambiguities"] else "no_ordered_query_ambiguity_in_bound"
    report["lesson_count"] = len(report["lessons"])
    report["example_count"] = sum(len(row["pairs"]) for row in report["lessons"])
    report["examples_refuting_rival"] = sum(not pair["rival_matches"] for row in report["lessons"] for pair in row["pairs"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in (
        "status", "lesson_count", "example_count", "examples_refuting_rival", "racket_evaluations",
        "production_ambiguities", "rotation_ambiguities", "surviving_lessons", "mirror_disagreements", "errors", "elapsed_seconds")}, indent=2))
    return int(bool(report["errors"] or report["mirror_disagreements"]))


if __name__ == "__main__":
    raise SystemExit(main())
