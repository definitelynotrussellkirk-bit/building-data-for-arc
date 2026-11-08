"""Execute a canonical-fitting color-priority shortcut on a real production draw."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import load_selected_generator

TASK = "323fded12174"
PIN = "035b7441095f4343524ddf1b8f6dee67e9b5ab013024dc530a1d43d69eb6785e"
RULE = "d6c95e66f9b7"
ROOT = Path(__file__).resolve().parents[2] / "repo"

RIVAL = """(rule! (lambda (g)
  (let ((score (lambda (row)
          (let ((colors (unique (filter (lambda (v) (!= v 0)) row))))
            (+ (* 31 (length colors))
               (max-of (lambda (c) (count-where (lambda (v) (= v c)) row)) colors))))))
    (sort g (lambda (a b) (> (score a) (score b)))))))"""


def decode(grid):
    return [[int(v) for v in row] for row in grid]


def occupancy(row):
    return sum(v != 0 for v in row)


def color_priority(row):
    frequencies = Counter(v for v in row if v != 0)
    return len(frequencies), max(frequencies.values())


def reference(grid):
    return [list(row) for row in sorted(grid, key=occupancy, reverse=True)]


def rival_reference(grid):
    return [list(row) for row in sorted(grid, key=color_priority, reverse=True)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    generator, source, observed = load_selected_generator(TASK)
    if observed != PIN or generator.RULE_HASH != RULE:
        raise ValueError("Selected production identity differs")
    record = Catalog(ROOT).get(TASK)
    programs = {v["program_solution"] for v in record["variants"]}
    if len(programs) != 1:
        raise ValueError("Expected one canonical rule")
    canonical = programs.pop()
    demos = [{k: decode(pair[k]) for k in ("input", "output")}
             for pair in record["variants"][0]["train"]]
    replayed = []
    calls = 0
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, Path(__file__).parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for pair in demos:
                intended, other = apply(canonical, pair["input"]), apply(RIVAL, pair["input"])
                calls += 2
                if intended != pair["output"] or other != intended:
                    raise ValueError("Canonical demonstration does not support this rival")
                if intended != reference(pair["input"]) or other != rival_reference(pair["input"]):
                    raise ValueError("Independent meaning mismatch")
                replayed.append({**pair, "rival_output": other})
            fit = {"reference": True, "color_count_then_dominant": True}
            # The fitted alternatives are frozen before selecting or inspecting the witness.
            draw = {"seed": 323, "sample_index": 0, "difficulty": "medium",
                    "profile": "5x8x4", "cell_layout": "runs"}
            grid = generator.generate(**draw)
            errors = generator.self_check(grid)
            intended, other = apply(canonical, grid), apply(RIVAL, grid)
            calls += 2
            if errors or intended == other:
                raise ValueError("Expected a generated lawful distinguishing input")
            if intended != reference(grid) or other != rival_reference(grid):
                raise ValueError("Generated witness meaning mismatch")
        finally:
            bridge.close()
    if hashlib.sha256(Path(source).read_bytes()).hexdigest() != PIN:
        raise ValueError("Production source changed during the check")
    report = {
        "schema": "arcpuzzles-canonical-shortcut-replay-v1", "task_id": TASK,
        "status": "replayed_generated_counterexample", "visibility": "controller_private",
        "generator_sha256": PIN, "rule_hash": RULE,
        "canonical_program": canonical,
        "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "rival": "color_count_then_dominant", "rival_program": RIVAL,
        "rival_program_sha256": hashlib.sha256(RIVAL.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "demonstrations": replayed, "demo_fit": fit, "fit_frozen_before_witness": True,
        "racket": identity, "racket_evaluations": calls,
        "witness": {"origin": "actual_selected_production_draw", "request": draw,
                    "input": grid, "output": intended, "rival_output": other,
                    "self_check_errors": errors,
                    "row_occupancies": [occupancy(row) for row in grid],
                    "row_color_priority_keys": [list(color_priority(row)) for row in grid]},
        "limits": "Four canonical training demonstrations and one exact production draw; this is not a universal rival search, new production repair, or training admission.",
        "production_changed": False, "training_admitted": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "racket_evaluations": calls,
                      "train_count": len(demos), "draw": draw, "out": str(args.out)}))


if __name__ == "__main__":
    main()
