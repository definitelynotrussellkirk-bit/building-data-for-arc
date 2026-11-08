#!/usr/bin/env python3
"""Bounded protected-Racket learnability audit for the row-fill bridge family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root

TASK_ID = "9da02d5e3ac0"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SETTINGS = (
    {"finish_rule": "row_fill_only"},
    {"finish_rule": "row_fill_then_vertical_bridge"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_audit_9da02d5e3ac0_adapter", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _program(*, key: str = "first_non5", bridge: str = "none") -> str:
    key_function = {
        "first_non5": "key-first-non5",
        "first_column": "key-first-column",
        "fixed_position": "key-fixed-position",
        "first_nonzero": "key-first-nonzero",
        "last_non5": "key-last-non5",
    }[key]
    body = {
        "none": "filled",
        "correct": "(bridge-vertical filled filled #f #t #f #f)",
        "raw_source": "(bridge-vertical filled g #f #t #f #f)",
        "include_five": "(bridge-vertical filled filled #t #t #f #f)",
        "ignore_color": "(bridge-vertical filled filled #f #f #f #f)",
        "first_color_only": "(bridge-vertical filled filled #f #t #f #t)",
        "short_span_only": "(bridge-vertical filled filled #f #t #t #f)",
        "horizontal": "(transpose (bridge-vertical (transpose filled) (transpose filled) #f #t #f #f))",
    }[bridge]
    return f'''(rule! (let ((dummy 0))
  (define (key-first-non5 grid r w)
    (let ((xs (filter (lambda (x) (!= x 5))
                      (map (lambda (c) (at grid r c)) (range 0 w)))))
      (if (null? xs) 5 (first xs))))
  (define (key-first-column grid r w) (at grid r 0))
  (define (key-fixed-position grid r w)
    (if (and (= (at grid r 0) 5) (> w 1)) (at grid r 1) (at grid r 0)))
  (define (key-first-nonzero grid r w)
    (let ((xs (filter (lambda (x) (and (!= x 0) (!= x 5)))
                      (map (lambda (c) (at grid r c)) (range 0 w)))))
      (if (null? xs) 5 (first xs))))
  (define (key-last-non5 grid r w)
    (let ((xs (filter (lambda (x) (!= x 5))
                      (map (lambda (c) (at grid r c)) (range 0 w)))))
      (if (null? xs) 5 (last xs))))
  (define (row-fill grid key-fn)
    (let ((w (cols grid)))
      (cellmap grid (r c v)
        (let ((key (key-fn grid r w)))
          (if (and (= v 5) (!= key 5)) key v)))))
  (define (bridge-vertical base source include-five require-same short-only first-only)
    (let* ((h (rows source))
           (global-signals
             (filter (lambda (x) (and (!= x 0) (!= x 5)))
                     (apply append base)))
           (global-first (if (null? global-signals) 5 (first global-signals))))
      (cellmap base (r c v)
        (if (= v 0)
            (let* ((signal-rows
                     (filter
                       (lambda (rr)
                         (let ((x (at source rr c)))
                           (and (!= x 0) (or include-five (!= x 5)))))
                       (range 0 h)))
                   (signal-values
                     (remove-duplicates
                       (map (lambda (rr) (at source rr c)) signal-rows)))
                   (candidate (if (null? signal-values) 5 (first signal-values))))
              (if (and (>= (length signal-rows) 2)
                       (or (not require-same) (= (length signal-values) 1))
                       (> r (first signal-rows))
                       (< r (last signal-rows))
                       (or (not short-only)
                           (<= (- (last signal-rows) (first signal-rows)) 3))
                       (or (not first-only) (= candidate global-first)))
                  candidate
                  v))
            v))))
  (let ((filled (row-fill g {key_function})))
    {body})))'''


def rival_programs() -> dict[str, str]:
    return {
        "first_column_fill": _program(key="first_column"),
        "fixed_position_fill": _program(key="fixed_position"),
        "first_nonzero_fill": _program(key="first_nonzero"),
        "last_non5_fill": _program(key="last_non5"),
        "raw_intermediate_bridge": _program(bridge="raw_source"),
        "bridge_including_five": _program(bridge="include_five"),
        "bridge_without_color_guard": _program(bridge="ignore_color"),
        "horizontal_instead_of_vertical": _program(bridge="horizontal"),
        "first_signal_color_only": _program(bridge="first_color_only"),
        "short_span_only": _program(bridge="short_span_only"),
        "last_non5_then_bridge": _program(key="last_non5", bridge="correct"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)

    adapter = _load_adapter()
    rivals = rival_programs()
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations = 0
    reports = []
    try:
        for settings in SETTINGS:
            episode = adapter.generate(args.seed, settings, args.demos, args.queries)
            chosen_program = adapter.program(settings)
            for split in ("train", "test"):
                for pair in episode[split]:
                    got = apply(chosen_program, pair["input"]); evaluations += 1
                    if got != pair["output"]:
                        raise AssertionError(f"chosen label mismatch: {settings} {split}")

            rival_rows = []
            for name, source in rivals.items():
                demo_outputs = []
                for pair in episode["train"]:
                    demo_outputs.append(apply(source, pair["input"])); evaluations += 1
                survives = all(
                    got == pair["output"]
                    for got, pair in zip(demo_outputs, episode["train"], strict=True)
                )
                disagreements = []
                if survives:
                    for index, pair in enumerate(episode["test"]):
                        got = apply(source, pair["input"]); evaluations += 1
                        if got != pair["output"]:
                            disagreements.append(index)
                rival_rows.append({
                    "name": name,
                    "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                    "survives_demos": survives,
                    "query_disagreements": disagreements,
                })
            harmful = [row for row in rival_rows
                       if row["survives_demos"] and row["query_disagreements"]]
            if harmful:
                raise AssertionError(f"harmful demo survivors for {settings}: {harmful}")
            reports.append({"settings": settings, "rivals": rival_rows})

        alternate = adapter.generate(args.seed, SETTINGS[1], args.demos, args.queries)
        pair = alternate["test"][-1]
        chosen_program = adapter.program(SETTINGS[1])
        counterfactual = rivals["raw_intermediate_bridge"]
        output = apply(chosen_program, pair["input"]); evaluations += 1
        counter_output = apply(counterfactual, pair["input"]); evaluations += 1
        if output == counter_output:
            raise AssertionError("wrong-intermediate causal case did not change output")
        analysis = adapter.analyze_input(pair["input"])
        audited_case = {
            "schema": "arcpuzzles-row-fill-bridge-audited-case-v1",
            "task_id": TASK_ID,
            "settings": SETTINGS[1],
            "input": pair["input"],
            "program": chosen_program,
            "output": output,
            "counterfactual_program": counterfactual,
            "counterfactual_output": counter_output,
            "intermediate_value": {
                "completed_bridge_cells": analysis["completed_bridge_cells"],
                "raw_bridge_cells": analysis["raw_bridge_cells"],
                "mixed_signal_columns": analysis["mixed_signal_columns"],
                "changed_final_cells": sum(
                    left != right
                    for row_left, row_right in zip(output, counter_output, strict=True)
                    for left, right in zip(row_left, row_right, strict=True)
                ),
            },
            "ablation": "wrong_intermediate",
        }
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-row-fill-bridge-self-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "seed": args.seed,
        "demos": args.demos,
        "queries": args.queries,
        "racket": identity,
        "racket_evaluations": evaluations,
        "rivals": sorted(rivals),
        "settings": reports,
        "scope": (
            "Two settings, minimum two-demo lessons, four queries, and eleven "
            "finite executable rivals; not universal uniqueness."
        ),
        "audited_case": "audited-case.json",
    }
    (out / "self-audit-report.json").write_bytes(_raw(report))
    (out / "audited-case.json").write_bytes(_raw(audited_case))
    print(json.dumps({
        "status": "passed",
        "racket_evaluations": evaluations,
        "harmful_survivors": 0,
        "audited_case": str((out / "audited-case.json").resolve()),
        "changed_final_cells": audited_case["intermediate_value"]["changed_final_cells"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
