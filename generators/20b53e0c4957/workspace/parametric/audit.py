"""Finite protected-Racket shortcut audit for the 20b53e0c4957 family.

Rivals are fit on visible demonstrations only.  A rival is harmful when it fits
all demonstrations but changes at least one query.  This bounded audit does not
claim universal identifiability or owner acceptance.
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
TASK_ID = "20b53e0c4957"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.parametric_worker import _grid, _real_evaluator  # noqa: E402


def _load_family():
    spec = importlib.util.spec_from_file_location("audit_family_20b53e0c4957", HERE / "family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = _load_family()
_SPLIT = """
    (define (split-panel-row grid count)
      (let ((pw (quotient (- (cols grid) (- count 1)) count)))
        (for/list ((i (in-range count)))
          (let ((left (* i (+ pw 1))))
            (grid-from-fn (rows grid) pw
              (lambda (r c) (at grid r (+ left c))))))))
    (define (nonzero-cells grid)
      (filter (lambda (p) (not (= (at grid (first p) (second p)) 0)))
              (grid-positions grid)))
"""

RETURN_C = f"""(rule! (let ((dummy 0)) {_SPLIT}
  (third (split-panel-row g 3))))"""

REPAIR_C = f"""(rule! (let ((dummy 0)) {_SPLIT}
  (let* ((cgrid (third (split-panel-row g 3)))
         (cells-c (nonzero-cells cgrid))
         (bb (bbox-of-cells cells-c))
         (color (at cgrid (first (first cells-c)) (second (first cells-c)))))
    (grid-from-fn (rows cgrid) (cols cgrid)
      (lambda (r c)
        (if (and (>= r (first bb)) (<= r (third bb))
                 (>= c (second bb)) (<= c (fourth bb)))
            color (at cgrid r c)))))))"""

ABSOLUTE_TRANSFER = f"""(rule! (let ((dummy 0)) {_SPLIT}
  (let* ((panels (split-panel-row g 3))
         (a (first panels)) (b (second panels)) (cgrid (third panels))
         (cells-a (nonzero-cells a)) (cells-b (nonzero-cells b))
         (removed (filter (lambda (p) (not (member? p cells-b))) cells-a)))
    (for/fold ((out cgrid)) ((p (in-list removed)))
      (if (in-bounds? (first p) (second p) (rows out) (cols out))
          (set-cell out (first p) (second p) 0) out)))))"""

COPY_B_RECOLOR = f"""(rule! (let ((dummy 0)) {_SPLIT}
  (let* ((panels (split-panel-row g 3))
         (b (second panels)) (cgrid (third panels))
         (cells-c (nonzero-cells cgrid))
         (color (at cgrid (first (first cells-c)) (second (first cells-c)))))
    (grid-from-fn (rows b) (cols b)
      (lambda (r c) (if (= (at b r c) 0) 0 color))))))"""


def rival_programs(selected: str) -> dict[str, str]:
    other = "repair_then_transfer" if selected == "preserve" else "preserve"
    return {
        "other_declared_setting": F.program({"hole_policy": other}),
        "skip_a_return_c": RETURN_C,
        "skip_a_repair_c": REPAIR_C,
        "raw_panel_coordinates": ABSOLUTE_TRANSFER,
        "copy_b_and_recolor": COPY_B_RECOLOR,
    }


def run(out: Path, seeds=(0, 17)) -> dict:
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    episodes = []
    harmful = []
    evaluations = 0
    try:
        for seed in seeds:
            for policy in F.POLICIES:
                settings = {"hole_policy": policy}
                episode = F.generate(seed, settings, 2, 4)
                intended = episode["program_solution"]
                rows = []
                for name, rival in rival_programs(policy).items():
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
        "schema": "20b53e0c4957-protected-racket-shortcut-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not harmful else "failed",
        "racket": identity,
        "seeds": list(seeds),
        "settings": [{"hole_policy": p} for p in F.POLICIES],
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
