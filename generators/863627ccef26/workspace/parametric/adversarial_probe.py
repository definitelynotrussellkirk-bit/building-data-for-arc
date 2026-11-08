"""Bounded protected-Racket self-review for the 863627ccef26 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "863627ccef26"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_863627ccef26", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_PREFIX = """(define (split-panels-row grid count)
    (let* ((panel-w (quotient (- (cols grid) (- count 1)) count)))
      (for/list ((i (in-range count)))
        (let ((left (* i (+ panel-w 1))))
          (subgrid grid 0 left (- (rows grid) 1) (+ left panel-w -1))))))
  (define transform-names
    (list 'id 'rot90 'rot180 'rot270 'flip-h 'flip-v 'transpose 'anti-transpose))
  (define (anti-transpose-grid grid) (rotate-180 (transpose grid)))
  (define (apply-transform-name name grid)
    (cond ((equal? name 'id) grid)
          ((equal? name 'rot90) (rotate-cw grid))
          ((equal? name 'rot180) (rotate-180 grid))
          ((equal? name 'rot270) (rotate-ccw grid))
          ((equal? name 'flip-h) (flip-lr grid))
          ((equal? name 'flip-v) (flip-ud grid))
          ((equal? name 'transpose) (transpose grid))
          (else (anti-transpose-grid grid))))
  (define (infer-transform-name a b)
    (first (filter (lambda (name) (equal? (apply-transform-name name a) b))
                   transform-names)))"""


def _rule(body):
    return f"""(rule! (let ((dummy 0))
  {_PREFIX}
  (let* ((panels (split-panels-row g 3))
         (q (third panels))
         (name (infer-transform-name (first panels) (second panels)))
         (tq (apply-transform-name name q)))
    {body})))"""


def _fixed_rule(transform_name, body):
    return f"""(rule! (let ((dummy 0))
  {_PREFIX}
  (let* ((panels (split-panels-row g 3))
         (q (third panels))
         (tq (apply-transform-name '{transform_name} q)))
    {body})))"""


_UNION = """(grid-from-fn (rows tq) (cols tq)
      (lambda (r c)
        (let ((a (at q r c)) (b (at tq r c)))
          (cond ((and (not (= a 0)) (not (= b 0))) 9)
                ((not (= a 0)) a)
                (else b)))))"""
_INTERSECTION = """(grid-from-fn (rows tq) (cols tq)
      (lambda (r c)
        (let ((a (at q r c)) (b (at tq r c)))
          (if (and (not (= a 0)) (not (= b 0))) 9 0))))"""


def rivals(proto):
    return {
        "canonical": proto.program({"merge_mode": "union_conflict_9"}),
        "sequential": proto.program({"merge_mode": "intersection_only"}),
        "query_only": _rule("q"),
        "transformed_only": _rule("tq"),
        "union_without_conflict": _rule(
            "(grid-from-fn (rows tq) (cols tq) "
            "(lambda (r c) (let ((a (at q r c)) (b (at tq r c))) "
            "(if (not (= a 0)) a b))))"
        ),
        "all_query_cells_9": _rule(
            "(cellmap q (r c v) (if (= v 0) 0 9))"
        ),
        "fixed_identity_union": _fixed_rule("id", _UNION),
        "fixed_rot180_union": _fixed_rule("rot180", _UNION),
        "fixed_identity_intersection": _fixed_rule("id", _INTERSECTION),
        "fixed_rot180_intersection": _fixed_rule("rot180", _INTERSECTION),
        "all_zero": _rule("(empty-grid (rows q) (cols q) 0)"),
    }


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def build_report(seeds=(0, 17, 91)):
    proto = _load_prototype()
    candidates = rivals(proto)
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    rows = []
    regressions = {}
    evaluations = 0
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for setting_name in ("union_conflict_9", "intersection_only"):
                expected_name = "canonical" if setting_name == "union_conflict_9" else "sequential"
                for seed in seeds:
                    episode = proto.generate(seed, {"merge_mode": setting_name}, 2, 4)
                    survivors = []
                    expected_outputs = [pair["output"] for pair in episode["train"]]
                    for name, source in candidates.items():
                        outputs = [apply(source, pair["input"]) for pair in episode["train"]]
                        evaluations += len(outputs)
                        if outputs == expected_outputs:
                            survivors.append(name)
                    if survivors != [expected_name]:
                        raise ValueError(
                            f"shortcut survivor set for {setting_name} seed {seed}: {survivors}"
                        )
                    for name, source in candidates.items():
                        if name == expected_name:
                            continue
                        for split in ("train", "test"):
                            found = False
                            for index, pair in enumerate(episode[split]):
                                actual = apply(source, pair["input"])
                                evaluations += 1
                                if actual != pair["output"]:
                                    regressions.setdefault(
                                        f"{setting_name}:{name}",
                                        {
                                            "setting": setting_name,
                                            "rival": name,
                                            "split": split,
                                            "index": index,
                                            "input": pair["input"],
                                            "expected": pair["output"],
                                            "rival_output": actual,
                                        },
                                    )
                                    found = True
                                    break
                            if found:
                                break
                    rows.append(
                        {
                            "setting": setting_name,
                            "seed": seed,
                            "survivors": survivors,
                            "transforms": [proto.stage_summary(pair["input"])["transform"] for pair in episode["train"]],
                            "input_hashes": [proto.digest(pair["input"]) for pair in episode["train"]],
                            "query_hashes": [proto.digest(pair["input"]) for pair in episode["test"]],
                        }
                    )
        finally:
            bridge.close()
    large = proto.generate(5, {"merge_mode": "intersection_only"}, 2, 4)["test"][-1]["input"]
    summary = proto.stage_summary(large)
    return {
        "schema": "arcpuzzles-parametric-adversarial-self-review-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "demos": 2,
        "queries": 4,
        "candidate_program_sha256": {
            name: hashlib.sha256(source.encode()).hexdigest() for name, source in candidates.items()
        },
        "checks": rows,
        "regressions": list(regressions.values()),
        "regression_count": len(regressions),
        "stress_9x29": {
            "input_sha256": digest(large),
            "nonzero_cells": sum(cell != 0 for row in large for cell in row),
            "panel_size": summary["panel_size"],
            "transform": summary["transform"],
            "overlap_cells": summary["overlap_cells"],
            "carry_cells": summary["carry_cells"],
            "domain_limit": "Three square panels plus two separators have width 3n+2; n=9 gives 29 and n=10 would exceed ARC's 30-column limit.",
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "limits": "Finite declared settings plus nine plausible shortcuts on three seeds; no universal uniqueness claim.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "racket_evaluations": report["racket_evaluations"],
        "regression_count": report["regression_count"],
        "stress_9x29": report["stress_9x29"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
