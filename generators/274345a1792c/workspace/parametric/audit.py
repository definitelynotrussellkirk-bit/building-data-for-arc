"""Bounded protected-Racket learnability audit for the stamp-transform family.

Every declared competitor is a complete executable rule. Fit decisions use only
visible demonstration outputs; queries are inspected only after that decision.
The tool is intentionally finite and reusable, not a uniqueness proof.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _load(filename):
    path = Path(__file__).resolve().with_name(filename)
    name = "_stamp_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load("prototype.py")


def _transform_body(kind):
    mixed = """(cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (flip-cells-lr cells))]
        [else (normalize-cells (rotate-cells-cw (flip-cells-lr cells)))])"""
    rotations = """(cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (rotate-cells-cw (rotate-cells-cw cells)))]
        [else (normalize-cells
                (rotate-cells-cw (rotate-cells-cw (rotate-cells-cw cells))))])"""
    bodies = {
        "mixed": mixed,
        "rotations": rotations,
        "identity_only": "(normalize-cells cells)",
        "swap_3_4": """(cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (rotate-cells-cw (flip-cells-lr cells)))]
        [else (normalize-cells (flip-cells-lr cells))])""",
        "counterclockwise_2": """(cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells
                      (rotate-cells-cw (rotate-cells-cw (rotate-cells-cw cells))))]
        [(= code 3) (normalize-cells (flip-cells-lr cells))]
        [else (normalize-cells (rotate-cells-cw (flip-cells-lr cells)))])""",
        "reverse_composition_4": """(cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (flip-cells-lr cells))]
        [else (normalize-cells (flip-cells-lr (rotate-cells-cw cells)))])""",
        "hybrid_rotation_3": """(cond
        [(= code 1) (normalize-cells cells)]
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (rotate-cells-cw (rotate-cells-cw cells)))]
        [else (normalize-cells (rotate-cells-cw (flip-cells-lr cells)))])""",
    }
    return bodies[kind]


def _rival_program(*, transform="mixed", shape="visible", anchors="all", paint="shape"):
    shape_expr = ("(normalize-cells (obj-cells proto))" if shape == "visible" else
                  "(list (list 0 0) (list 1 0) (list 2 0) (list 2 1))")
    anchor_expr = {
        "all": "base-anchors",
        "first_three": "(first-n base-anchors 3)",
        "once_per_code": "(unique-by-code base-anchors (list))",
    }[anchors]
    paint_expr = {
        "shape": "shp",
        "bbox": "(bbox-cells shp)",
        "preserve_anchor": "(filter (lambda (p) (not (same-pos? p (list 0 0)))) shp)",
    }[paint]
    return f"""(rule!
  (let ((dummy 0))
    (define (same-pos? a b)
      (and (= (fst a) (fst b)) (= (snd a) (snd b))))
    (define (pos-in? p cells)
      (any? (lambda (q) (same-pos? p q)) cells))
    (define proto
      (first
        (filter
          (lambda (obj) (and (= (obj-color obj) 9) (> (obj-size obj) 1)))
          (objects g 0))))
    (define shape {shape_expr})
    (define (transform code cells)
      {_transform_body(transform)})
    (define base-anchors
      (filter
        (lambda (p)
          (and (> (first p) 0)
               (= (third p) 6)
               (member? (cell-at g (- (first p) 1) (second p)) (list 1 2 3 4))))
        (grid-cells g)))
    (define (first-n xs n)
      (if (or (= n 0) (empty? xs))
          (list)
          (cons (first xs) (first-n (rest xs) (- n 1)))))
    (define (unique-by-code xs seen)
      (if (empty? xs)
          (list)
          (let* ((a (first xs))
                 (code (cell-at g (- (first a) 1) (second a))))
            (if (member? code seen)
                (unique-by-code (rest xs) seen)
                (cons a (unique-by-code (rest xs) (cons code seen)))))))
    (define (bbox-cells cells)
      (let ((maxr (apply max (map fst cells)))
            (maxc (apply max (map snd cells))))
        (for*/list ((r (in-range 0 (+ maxr 1)))
                    (c (in-range 0 (+ maxc 1))))
          (list r c))))
    (define anchors {anchor_expr})
    (define stamp-cells
      (flatmap
        (lambda (a)
          (let* ((ar (first a))
                 (ac (second a))
                 (code (cell-at g (- ar 1) ac))
                 (shp (transform code shape))
                 (painted {paint_expr}))
            (map (lambda (p) (list (+ ar (fst p)) (+ ac (snd p)))) painted)))
        anchors))
    (grid-from-fn h w
      (lambda (r c)
        (if (and (in-bounds? r c h w) (pos-in? (list r c) stamp-cells))
            8
            (cell-at g r c))))))"""


def rival_programs():
    return {
        "fixed_l_mixed": _rival_program(shape="fixed_l"),
        "fixed_l_rotations": _rival_program(shape="fixed_l", transform="rotations"),
        "identity_only": _rival_program(transform="identity_only"),
        "swap_codes_3_4": _rival_program(transform="swap_3_4"),
        "counterclockwise_code_2": _rival_program(transform="counterclockwise_2"),
        "reverse_code_4_composition": _rival_program(transform="reverse_composition_4"),
        "hybrid_rotate_code_3": _rival_program(transform="hybrid_rotation_3"),
        "first_three_anchors": _rival_program(anchors="first_three"),
        "once_per_control_code": _rival_program(anchors="once_per_code"),
        "fill_transformed_bbox": _rival_program(paint="bbox"),
        "preserve_anchor_cell": _rival_program(paint="preserve_anchor"),
    }


def _real_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("audit requires protected Racket")
    wrapped = {}

    def apply(program, grid):
        if program not in wrapped:
            wrapped[program] = wrap_rule(program)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped[program]} {literal})")

    return apply, {k: identity[k] for k in identity if k in {
        "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
        "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
    }}, bridge


def run(*, seeds=(0, 17), demo_counts=(2, 3, 6), queries=4, apply_program=None):
    seeds = list(seeds)
    demo_counts = list(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("at least one seed and demonstration count are required")
    for seed in seeds:
        P._integer(seed, 0, 2**63 - 1, "seed")
    for demos in demo_counts:
        P._integer(demos, 2, 6, "demos")
    P._integer(queries, 1, 4, "queries")

    bridge = None
    if apply_program is None:
        apply, identity, bridge = _real_apply()
    else:
        if not callable(apply_program):
            raise ValueError("apply_program must be callable")
        apply = apply_program
        identity = {"backend": "test", "protected": False}

    programs = {"setting_mixed": P.program(P.SETTINGS[0]),
                "setting_rotations": P.program(P.SETTINGS[1]),
                **rival_programs()}
    evaluations = 0

    def execute(program, grid):
        nonlocal evaluations
        evaluations += 1
        return apply(program, grid)

    jobs = []
    causal = None
    try:
        for seed in seeds:
            for demos in demo_counts:
                for settings in P.SETTINGS:
                    episode = P.generate(seed, settings, demos, queries)
                    chosen_name = "setting_" + settings["transform_family"]
                    chosen_program = programs[chosen_name]
                    racket_pairs = {split: [] for split in ("train", "test")}
                    for split in racket_pairs:
                        for pair in episode[split]:
                            output = execute(chosen_program, pair["input"])
                            if output != pair["output"]:
                                raise ValueError("Python claim differs from intended Racket label")
                            racket_pairs[split].append({"input": pair["input"], "output": output})
                    rivals = []
                    surviving = []
                    for name, source in programs.items():
                        if name == chosen_name:
                            continue
                        demo_outputs = [execute(source, pair["input"])
                                        for pair in racket_pairs["train"]]
                        demo_matches = sum(a == b["output"]
                                           for a, b in zip(demo_outputs, racket_pairs["train"]))
                        fits = demo_matches == len(racket_pairs["train"])
                        query_outputs = [execute(source, pair["input"])
                                         for pair in racket_pairs["test"]]
                        query_disagreements = sum(a != b["output"]
                                                  for a, b in zip(query_outputs, racket_pairs["test"]))
                        if fits:
                            surviving.append(name)
                        rivals.append({"name": name, "demo_matches": demo_matches,
                                       "demo_total": len(racket_pairs["train"]),
                                       "fits_all_demos": fits,
                                       "query_disagreements": query_disagreements,
                                       "query_total": len(racket_pairs["test"])})
                    jobs.append({"seed": seed, "demos": demos, "queries": queries,
                                 "settings": settings, "surviving_rivals": surviving,
                                 "rivals": rivals})
                    if causal is None and settings == P.SETTINGS[0]:
                        pair = racket_pairs["test"][0]
                        counter = programs["fixed_l_mixed"]
                        counter_output = execute(counter, pair["input"])
                        prototype = [(r, c) for r, row in enumerate(pair["input"])
                                     for c, value in enumerate(row) if value == 9]
                        causal = {"settings": settings, "program": chosen_program,
                                  "input": pair["input"], "output": pair["output"],
                                  "intermediate_value": [list(p) for p in P._normalize(prototype)],
                                  "counterfactual_program": counter,
                                  "counterfactual_output": counter_output,
                                  "ablation": "wrong_intermediate"}
    finally:
        if bridge is not None:
            bridge.close()
    if causal is None or causal["output"] == causal["counterfactual_output"]:
        raise ValueError("causal fixed-L ablation did not change the final output")
    passed = all(not job["surviving_rivals"] for job in jobs)
    return {"schema": "arcpuzzles-parametric-self-audit-v1", "task_id": P.TASK_ID,
            "scope": {"seeds": seeds, "demo_counts": demo_counts, "queries": queries,
                      "rival_names": sorted(programs)},
            "racket": identity, "racket_evaluations": evaluations,
            "job_count": len(jobs), "jobs": jobs, "causal_case": causal,
            "passed": passed,
            "limits": "Finite declared rivals and sampled episodes only; not universal uniqueness."}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", action="append", type=int, dest="demo_counts")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = run(seeds=args.seeds or [0, 17], demo_counts=args.demo_counts or [2, 3, 6],
                 queries=args.queries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "passed": report["passed"],
                      "jobs": report["job_count"],
                      "racket_evaluations": report["racket_evaluations"]}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
