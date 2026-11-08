#!/usr/bin/env python3
"""Bounded protected-Racket self-audit for the gallery-order family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root

TASK_ID = "1216927d148b"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SETTINGS = (
    {"gallery_order": "fixed_pairs"},
    {"gallery_order": "largest_overlap_first"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_audit_gallery_order_adapter", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _common(body: str) -> str:
    return f"""(rule! (let ((dummy 0))
  (define (paste grid pat top left)
    (for*/fold ((out grid)) ((r (in-range (rows pat))) (c (in-range (cols pat))))
      (let ((v (at pat r c)) (rr (+ top r)) (cc (+ left c)))
        (if (and (not (= v 0)) (in-bounds? rr cc (rows out) (cols out)))
            (set-cell out rr cc v) out))))
  (define (hstack grids (gap 1))
    (let* ((h (apply max (map rows grids)))
           (w (+ (apply + (map cols grids)) (* gap (- (length grids) 1)))))
      (let loop ((xs grids) (left 0) (out (empty-grid h w 0)))
        (if (empty? xs) out
            (let* ((piece (first xs)) (top (quotient (- h (rows piece)) 2)))
              (loop (rest xs) (+ left (cols piece) gap)
                    (paste out piece top left)))))))
  (define (inter a b)
    (grid-from-fn (rows a) (cols a)
      (lambda (r c) (if (and (not (= (at a r c) 0))
                              (not (= (at b r c) 0))) 8 0))))
  (define (union-mask a b)
    (grid-from-fn (rows a) (cols a)
      (lambda (r c) (if (or (not (= (at a r c) 0))
                             (not (= (at b r c) 0))) 8 0))))
  (define (triple a b c)
    (grid-from-fn (rows a) (cols a)
      (lambda (r col) (if (and (not (= (at a r col) 0))
                                (not (= (at b r col) 0))
                                (not (= (at c r col) 0))) 8 0))))
  (define (occupied grid)
    (length (filter (lambda (v) (not (= v 0))) (apply append grid))))
  (define (first-color grid)
    (first (filter (lambda (v) (not (= v 0))) (apply append grid))))
  (define (descending a b)
    (if (= (third a) (third b)) (< (first a) (first b)) (> (third a) (third b))))
  (define (ascending a b)
    (if (= (third a) (third b)) (< (first a) (first b)) (< (third a) (third b))))
  (define (reverse-ties a b)
    (if (= (third a) (third b)) (> (first a) (first b)) (> (third a) (third b))))
  (let* ((panels (for/list ((i (in-range 3)))
                   (subgrid g 0 (* i 6) (- (rows g) 1) (+ (* i 6) 4))))
         (a (first panels)) (b (second panels)) (c (third panels))
         (ab (inter a b)) (ac (inter a c)) (bc (inter b c)))
    {body})))"""


def rival_programs() -> dict[str, str]:
    return {
        "reverse_fixed_pairs": _common("(hstack (list bc ac ab) 1)"),
        "ascending_overlap": _common(
            "(let ((items (list (list 0 ab (occupied ab)) "
            "(list 1 ac (occupied ac)) (list 2 bc (occupied bc))))) "
            "(hstack (map second (sort items ascending)) 1))"
        ),
        "largest_overlap_reverse_ties": _common(
            "(let ((items (list (list 0 ab (occupied ab)) "
            "(list 1 ac (occupied ac)) (list 2 bc (occupied bc))))) "
            "(hstack (map second (sort items reverse-ties)) 1))"
        ),
        "panel_sum_descending": _common(
            "(let ((items (list "
            "(list 0 ab (+ (occupied a) (occupied b))) "
            "(list 1 ac (+ (occupied a) (occupied c))) "
            "(list 2 bc (+ (occupied b) (occupied c)))))) "
            "(hstack (map second (sort items descending)) 1))"
        ),
        "panel_max_descending": _common(
            "(let ((items (list "
            "(list 0 ab (max (occupied a) (occupied b))) "
            "(list 1 ac (max (occupied a) (occupied c))) "
            "(list 2 bc (max (occupied b) (occupied c)))))) "
            "(hstack (map second (sort items descending)) 1))"
        ),
        "numeric_color_pair_order": _common(
            "(let ((items (list "
            "(list 0 ab (+ (first-color a) (first-color b))) "
            "(list 1 ac (+ (first-color a) (first-color c))) "
            "(list 2 bc (+ (first-color b) (first-color c)))))) "
            "(hstack (map second (sort items descending)) 1))"
        ),
        "pairwise_union_fixed": _common(
            "(hstack (list (union-mask a b) (union-mask a c) (union-mask b c)) 1)"
        ),
        "triple_intersection_repeated": _common(
            "(let ((t (triple a b c))) (hstack (list t t t) 1))"
        ),
        "largest_intersection_repeated": _common(
            "(let* ((items (list (list 0 ab (occupied ab)) "
            "(list 1 ac (occupied ac)) (list 2 bc (occupied bc)))) "
            "(winner (second (first (sort items descending))))) "
            "(hstack (list winner winner winner) 1))"
        ),
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
    setting_reports = []
    receipt = {"schema": "arcpuzzles-gallery-order-self-audit-v1", "task_id": TASK_ID,
               "seed": args.seed, "demos": args.demos, "queries": args.queries,
               "racket": identity, "settings": [], "rivals": sorted(rivals)}
    try:
        for settings in SETTINGS:
            episode = adapter.generate(args.seed, settings, args.demos, args.queries)
            chosen_program = adapter.program(settings)
            for split in ("train", "test"):
                for pair in episode[split]:
                    actual = apply(chosen_program, pair["input"]); evaluations += 1
                    if actual != pair["output"]:
                        raise AssertionError(f"chosen Racket label mismatch: {settings} {split}")

            rival_rows = []
            for name, source in rivals.items():
                demo_outputs = []
                for pair in episode["train"]:
                    demo_outputs.append(apply(source, pair["input"])); evaluations += 1
                survives = all(got == pair["output"]
                               for got, pair in zip(demo_outputs, episode["train"], strict=True))
                query_disagreements = []
                if survives:
                    for index, pair in enumerate(episode["test"]):
                        got = apply(source, pair["input"]); evaluations += 1
                        if got != pair["output"]:
                            query_disagreements.append(index)
                rival_rows.append({"name": name, "survives_demos": survives,
                                   "query_disagreements": query_disagreements,
                                   "program_sha256": hashlib.sha256(source.encode()).hexdigest()})
            harmful = [row for row in rival_rows
                       if row["survives_demos"] and row["query_disagreements"]]
            if harmful:
                raise AssertionError(f"harmful visible-demo survivors for {settings}: {harmful}")
            setting_reports.append({"settings": settings, "rivals": rival_rows})
            receipt["settings"].append({
                "settings": settings,
                "program": chosen_program,
                "program_sha256": hashlib.sha256(chosen_program.encode()).hexdigest(),
                "episode": episode,
                "rivals": rival_rows,
            })

        # Retain a source-exact causal case from the alternate's largest query.
        alt = adapter.generate(args.seed, SETTINGS[1], args.demos, args.queries)
        pair = alt["test"][-1]
        program = adapter.program(SETTINGS[1])
        counterfactual = adapter.program(SETTINGS[0])
        output = apply(program, pair["input"]); evaluations += 1
        counter_output = apply(counterfactual, pair["input"]); evaluations += 1
        if output == counter_output:
            raise AssertionError("causal case did not change under fixed pseudo-ranking")
        analysis = adapter.analyze_input(pair["input"])
        causal = {
            "schema": "arcpuzzles-gallery-order-audited-case-v1",
            "task_id": TASK_ID,
            "settings": SETTINGS[1],
            "input": pair["input"],
            "program": program,
            "output": output,
            "counterfactual_program": counterfactual,
            "counterfactual_output": counter_output,
            "intermediate_value": {
                "pair_names": ["AB", "AC", "BC"],
                "intersection_counts": analysis["intersection_counts"],
                "ranked_pair_names": analysis["ranked_pair_names"],
                "counterfactual_fixed_order": ["AB", "AC", "BC"],
            },
            "ablation": "wrong_intermediate",
        }
    finally:
        bridge.close()

    receipt["racket_evaluations"] = evaluations
    report = {
        "schema": "arcpuzzles-gallery-order-self-audit-report-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": "Two settings, minimum two-demo lessons, four queries, and nine finite executable rivals; not universal uniqueness.",
        "racket": identity,
        "racket_evaluations": evaluations,
        "settings": setting_reports,
        "causal_case": "causal_case.json",
    }
    (out / "report.json").write_bytes(_raw(report))
    (out / "racket_receipt.json").write_bytes(_raw(receipt))
    (out / "causal_case.json").write_bytes(_raw(causal))
    print(json.dumps({"status": "passed", "racket_evaluations": evaluations,
                      "settings": len(SETTINGS), "rivals": len(rivals),
                      "out": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
