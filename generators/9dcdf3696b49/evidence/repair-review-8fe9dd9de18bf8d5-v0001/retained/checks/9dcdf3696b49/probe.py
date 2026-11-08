#!/usr/bin/env python3
"""One bounded learnability probe. Run from packet root:
WORK/.venv/bin/python review.py run python3 ../checks/9dcdf3696b49/probe.py

The public canonical train pairs are demonstrations. Query candidates are at
most sixteen unmodified selected-generator draws (seed 17, indices 0..15).
Both reference and rival outputs are computed by protected Racket. This is a
constructive ambiguity witness, not a blind solve or full generator audit.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator


TASK = "9dcdf3696b49"
SEED = 17
LIMIT = 16
OUT = Path(__file__).resolve().parent


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def bands(grid, axis):
    lines = grid if axis == 0 else list(zip(*grid))
    divs = [i for i, line in enumerate(lines) if all(v == 5 for v in line)]
    ends = [-1, *divs, len(lines)]
    return [[a + 1, b - 1] for a, b in zip(ends, ends[1:]) if a + 1 <= b - 1]


def run():
    root = find_root(__file__)
    generator, source, generator_hash = load_selected_generator(TASK, root=root)
    catalog = Catalog(root)
    record = catalog.get(TASK)
    rules = {v["program_solution"] for v in record["variants"] if v.get("program_solution")}
    assert len(rules) == 1, "Reference rule must be unambiguous"
    reference = rules.pop()
    assert reference.startswith("(rule!") and reference.endswith(")")
    rival = reference
    for ranges, size in [("row-ranges", "h"), ("col-ranges", "w")]:
        needle = f"(quotient (length {ranges}) 2)"
        replacement = (f"(index-of {ranges} (argmin (lambda (rr) "
                       f"(abs (- (+ (first rr) (second rr)) (- {size} 1)))) {ranges}))")
        assert rival.count(needle) == 1, f"Expected one median selector: {needle}"
        rival = rival.replace(needle, replacement)
    public = catalog.challenge(TASK, variant=0)
    report = {
        "schema": "bounded-learnability-rival-v1",
        "task_id": TASK,
        "selected_generator": str(source.relative_to(root)),
        "generator_sha256": generator_hash,
        "generator_source": source.read_text(),
        "reference_rule_sha256": sha(reference),
        "reference_catalog_rule_hash": record["rule_hash"],
        "reference_program": reference,
        "rival_rule_sha256": sha(rival),
        "rival_program": rival,
        "rival_rule": "Keep blue top-left and green bottom-right macro-cells; fill red the macro-cell with center closest to the physical image center on each axis (first range wins ties), rather than the median macro-cell by count.",
        "commands": ["WORK/.venv/bin/python review.py run --receipt checks/9dcdf3696b49/command.json python3 ../checks/9dcdf3696b49/probe.py", "WORK/.venv/bin/python review.py run --receipt checks/9dcdf3696b49/command-replay.json python3 ../checks/9dcdf3696b49/probe.py", "WORK/.venv/bin/python review.py run --receipt checks/9dcdf3696b49/command-final.json python3 ../checks/9dcdf3696b49/probe.py"],
        "development_note": "The first invocation stopped on a wrapper whitespace assertion before Racket execution. One duplicate receipt name was rejected before payload launch. The second invocation started Racket but stopped before candidate evaluations because runtime_identity is a property, not a method. Both integration errors were fixed for the Catalog-selected canonical program. The final invocation evaluates the same single rival within the original bound.",
        "execution": {"argv": sys.argv, "cwd": str(Path.cwd()), "python": sys.executable,
                      "PYTHONPATH": os.environ.get("PYTHONPATH"), "RACKET_PATH": os.environ.get("RACKET_PATH")},
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": {"canonical_variant": 0, "canonical_train_count": len(public["train"]),
                  "generated_seed": SEED, "sample_indices_limit": list(range(LIMIT)),
                  "difficulty": None, "overrides": {}, "stop": "first self-check-valid separating input"},
        "limits": ["One fixed plausible rival, one canonical variant, at most sixteen generated draws.",
                   "Demonstrations are canonical; the counterexample query is generated, not a replay of a native sampled episode.",
                   "No population frequency, full-suite result, blind-solve independence, safety approval, or native qualification claim.",
                   "Both exact programs are recorded; their outputs below were evaluated in protected Racket."],
        "demonstrations": [], "query_candidates": [],
    }
    started = time.monotonic()
    with RacketBridge(timeout=10.0) as bridge:
        report["execution"]["protected_runtime_identity"] = bridge.runtime_identity
        bridge.eval_text(reference.replace("(rule!", "(define reference", 1))
        bridge.eval_text(rival.replace("(rule!", "(define rival", 1))

        def outputs(grid):
            bridge.define_grid("probe_grid", grid)
            return bridge.eval_text("(reference probe_grid)"), bridge.eval_text("(rival probe_grid)")

        for i, pair in enumerate(public["train"]):
            ref_output, rival_output = outputs(pair["input"])
            report["demonstrations"].append({"index": i, **pair,
                "reference_output": ref_output, "rival_output": rival_output,
                "reference_matches_visible_output": ref_output == pair["output"],
                "rival_matches_visible_output": rival_output == pair["output"]})
        demos_fit = all(d["reference_matches_visible_output"] and d["rival_matches_visible_output"] for d in report["demonstrations"])
        if demos_fit:
            for i in range(LIMIT):
                grid = generator.generate(SEED, i)
                ref_output, rival_output = outputs(grid)
                errors = generator.self_check(grid)
                candidate = {"seed": SEED, "sample_index": i, "input": grid,
                    "row_bands": bands(grid, 0), "column_bands": bands(grid, 1),
                    "self_check_errors": errors, "reference_output": ref_output,
                    "rival_output": rival_output, "separates": ref_output != rival_output,
                    "difference_cells": [[r, c, ref_output[r][c], rival_output[r][c]]
                                         for r in range(len(grid)) for c in range(len(grid[0]))
                                         if ref_output[r][c] != rival_output[r][c]]}
                report["query_candidates"].append(candidate)
                if candidate["separates"] and not errors:
                    report["witness_sample_index"] = i
                    break
        found = demos_fit and "witness_sample_index" in report
        report["outcome"] = "bounded_finding" if found else "bounded_no_finding"
        report["interpretation"] = ("All visible canonical demonstrations fit a physical-center rival, while a current-generator query separates it from macro-count median. This demonstrates an extrapolation ambiguity relative to these demonstrations; it is not a reference-label error."
                                    if found else "No self-check-valid separating query found in this finite scope, or the proposed rival failed a visible demonstration.")
        report["suggested_next_step"] = ("If canonical demonstrations are reused with generated queries, include a band-asymmetric demonstration separating macro-count median from physical-center selection. If episodes use generated demonstrations, evaluate this witness against that episode policy before assigning a learnability defect."
                                         if found else "Retain as a bounded negative result; no repair proposed.")
    report["elapsed_seconds"] = time.monotonic() - started
    (OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"outcome": report["outcome"], "demos_fit": demos_fit,
                      "query_candidates": len(report["query_candidates"]),
                      "witness_sample_index": report.get("witness_sample_index"),
                      "result": str(OUT / "result.json")}, indent=2))


if __name__ == "__main__":
    run()
