"""Finite protected-Racket shortcut audit for the ba9d8eb0cd5a family.

A rival is harmful only when it fits every visible demonstration yet changes a
query. This is bounded evidence over declared rivals and seeds, not a universal
uniqueness or training-admission claim.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "ba9d8eb0cd5a"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.parametric_worker import _grid, _real_evaluator  # noqa: E402


def _load_family():
    spec = importlib.util.spec_from_file_location("audit_family_ba9d8eb0cd5a", HERE / "family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = _load_family()

SORT_THEN_PACK = r'''(rule!
  (for/list ((r (in-range (rows g))))
    (let* ((values (filter (lambda (v) (not (= v 0))) (row g r)))
           (ordered (sort values <)))
      (append ordered (make-list (- (cols g) (length ordered)) 0)))))'''

MARK_BEFORE_PACK = r'''(rule!
  (let ((marked
          (grid-from-fn (rows g) (cols g)
            (lambda (r c)
              (let ((v (at g r c)))
                (if (and (not (= v 0))
                         (or (and (> r 0)
                                  (not (= (at g (- r 1) c) 0)))
                             (and (< r (- (rows g) 1))
                                  (not (= (at g (+ r 1) c) 0)))))
                    2 v))))))
    (gravity marked "left")))'''

MARK_ALL_PACKED = r'''(rule!
  (let ((packed (gravity g "left")))
    (grid-from-fn (rows packed) (cols packed)
      (lambda (r c) (if (= (at packed r c) 0) 0 2)))))'''

MARK_FIRST_PACKED_COLUMN = r'''(rule!
  (let ((packed (gravity g "left")))
    (grid-from-fn (rows packed) (cols packed)
      (lambda (r c)
        (if (and (= c 0) (not (= (at packed r c) 0)))
            2 (at packed r c))))))'''

REVERSE_THEN_PACK = r'''(rule!
  (for/list ((r (in-range (rows g))))
    (let ((values (reverse (filter (lambda (v) (not (= v 0))) (row g r)))))
      (append values (make-list (- (cols g) (length values)) 0)))))'''


def rival_programs(selected: str) -> dict[str, str]:
    other = "mark_vertical_contacts" if selected == "pack_only" else "pack_only"
    return {
        "other_declared_setting": F.program({"finish_rule": other}),
        "sort_then_pack": SORT_THEN_PACK,
        "wrong_order_mark_then_pack": MARK_BEFORE_PACK,
        "mark_every_packed_cell": MARK_ALL_PACKED,
        "mark_first_packed_column": MARK_FIRST_PACKED_COLUMN,
        "reverse_then_pack": REVERSE_THEN_PACK,
    }


def run(out: Path, seeds=(0, 17)) -> dict:
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    episodes = []
    harmful = []
    evaluations = 0
    try:
        for seed in seeds:
            for finish_rule in F.FINISH_RULES:
                settings = {"finish_rule": finish_rule}
                episode = F.generate(seed, settings, 2, 4)
                intended = episode["program_solution"]
                rows = []
                for name, rival in rival_programs(finish_rule).items():
                    demo_matches = []
                    for pair in episode["train"]:
                        reference = _grid(apply(intended, pair["input"])); evaluations += 1
                        if reference != pair["output"]:
                            raise AssertionError("intended protected-Racket label differs from Python claim")
                        actual = _grid(apply(rival, pair["input"])); evaluations += 1
                        demo_matches.append(actual == reference)
                    survives = all(demo_matches)
                    query_differences = []
                    if survives:
                        for index, pair in enumerate(episode["test"]):
                            reference = _grid(apply(intended, pair["input"])); evaluations += 1
                            actual = _grid(apply(rival, pair["input"])); evaluations += 1
                            if actual != reference:
                                query_differences.append(index)
                    row = {
                        "name": name,
                        "program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
                        "demo_matches": demo_matches,
                        "survives_demonstrations": survives,
                        "query_differences": query_differences,
                    }
                    rows.append(row)
                    if survives and query_differences:
                        harmful.append({"seed": seed, "settings": settings, **row})
                episodes.append({"seed": seed, "settings": settings, "rivals": rows})
    finally:
        bridge.close()
    report = {
        "schema": "ba9d8eb0cd5a-protected-racket-shortcut-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not harmful else "failed",
        "racket": identity,
        "seeds": list(seeds),
        "settings": [{"finish_rule": value} for value in F.FINISH_RULES],
        "minimum_demonstrations": 2,
        "queries": 4,
        "racket_evaluations": evaluations,
        "episodes": episodes,
        "harmful_demo_survivors": harmful,
        "limits": "Finite declared rivals and seeds only; no universal uniqueness claim.",
        "training_admitted": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    if harmful:
        raise AssertionError(f"query-changing rivals survived demonstrations: {harmful}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "episodes": len(report["episodes"]),
        "racket_evaluations": report["racket_evaluations"],
        "harmful_demo_survivors": len(report["harmful_demo_survivors"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
