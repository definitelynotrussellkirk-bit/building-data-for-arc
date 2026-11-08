#!/usr/bin/env python3
"""Replay the initial two-demo farthest-object ambiguity in protected Racket.

Uses only retained self-audit-initial.json and this checkout's protected runtime;
no current native implementation, sampler, Python label mirror, or network.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "repo/shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

MARKER = """(define matches
            (filter (lambda (obj)
                      (and (eligible? obj) (= (obj-size obj) target-area)))
                    (objects after-a 0)))"""
REPLACEMENT = """(define (distance-squared obj)
            (define dr (- (+ (obj-r1 obj) (obj-r2 obj))
                          (+ (obj-r1 anchor) (obj-r2 anchor))))
            (define dc (- (+ (obj-c1 obj) (obj-c2 obj))
                          (+ (obj-c1 anchor) (obj-c2 anchor))))
            (+ (* dr dr) (* dc dc)))
          (define remaining (filter eligible? (objects after-a 0)))
          (define matches
            (if (empty? remaining) (list)
                (list (first (sort remaining
                  (lambda (a b) (> (distance-squared a) (distance-squared b))))))))"""


def grid(value):
    if (type(value) is not list or not value or type(value[0]) is not list or not value[0]
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in value)):
        raise ValueError("malformed exact-integer grid")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "initial-farthest-repro.json")
    args = parser.parse_args()
    initial_path = HERE / "self-audit-initial.json"
    initial = json.loads(initial_path.read_text())
    job = next(j for j in initial["jobs"] if j["seed"] == 0 and j["settings"]["selection_rule"] == "cross_area_cascade")
    gap = next(g for g in job["prefixes"][0]["teaching_gaps"] if g["rival"] == "cascade_target_farthest")
    case = gap["minimal_case"]
    program = next(p["program"] for p in initial["programs"] if p["settings"] == job["settings"])
    if hashlib.sha256(program.encode()).hexdigest() != job["program_sha256"] or program.count(MARKER) != 1:
        raise ValueError("retained program binding or exact rival mutation marker differs")
    rival = program.replace(MARKER, REPLACEMENT)
    report = {"schema": "13507b4f7614-protected-farthest-teaching-counterexample-v1",
              "source_binding": initial["source_binding"],
              "retained_audit_sha256": hashlib.sha256(initial_path.read_bytes()).hexdigest(),
              "reproduction_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "seed": 0, "settings": job["settings"], "demos": 2,
              "query_index": gap["query_index"], "program": program,
              "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "rival_program": rival, "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
              "rival": "retain A, then cross the farthest other eligible rectangle by squared center distance",
              "cases": [], "errors": [], "racket_evaluations": 0}
    bridge = None
    try:
        bridge = RacketBridge()
        report["racket"] = bridge.runtime_identity
        if report["racket"].get("backend") != "racket" or report["racket"].get("protected") is not True:
            raise ValueError("protected actual Racket required")
        def execute(source, inp):
            literal = "'( " + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid(inp)) + ")"
            report["racket_evaluations"] += 1
            return grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
        for index, pair in enumerate(case["train"] + [case["query"]]):
            actual = execute(program, pair["input"])
            alternative = execute(rival, pair["input"])
            if actual != pair["output"]:
                raise ValueError("retained label disagrees with freshly executed original program")
            report["cases"].append({"split": "train" if index < 2 else "test",
                                    "index": index if index < 2 else gap["query_index"],
                                    "input": pair["input"], "output": actual, "rival_output": alternative,
                                    "agree": actual == alternative})
        if [row["agree"] for row in report["cases"]] != [True, True, False]:
            raise ValueError("farthest rival did not fit both demonstrations and disagree on query")
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if bridge is not None:
            bridge.close()
    report["status"] = "confirmed_teaching_gap" if not report["errors"] else "failed_reproduction"
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "racket_evaluations": report["racket_evaluations"],
                      "agreements": [row["agree"] for row in report["cases"]], "errors": report["errors"]}))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
