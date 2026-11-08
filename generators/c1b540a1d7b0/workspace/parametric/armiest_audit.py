"""Protected-Racket finite shortcut audit for the c1b540a1d7b0 family.

The audit freezes rivals from demonstrations only.  It is source-local,
deterministic, and deliberately finite; it does not claim universal rule
uniqueness or owner acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "c1b540a1d7b0"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles.parametric_worker import _grid, _real_evaluator  # noqa: E402


def _load_prototype():
    path = HERE / "armiest_family.py"
    spec = importlib.util.spec_from_file_location("_c1_armiest_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _load_prototype()
ALT = (HERE / "highlight_armiest.rkt").read_text()
WINNER = "(winner (pick-max objs red-count))"
RED_PREDICATE = "(= (cell-at stage (first p) (second p)) 2)"


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"expected one replacement site for {old!r}, got {source.count(old)}")
    return source.replace(old, new, 1)


def _raw_tip_selector() -> str:
    return """(winner
                (pick-max objs
                  (lambda (o)
                    (count-where
                      (lambda (p)
                        (let ((r (first p)) (c (second p)))
                          (and (= (cell-at g r c) 5)
                               (= 1
                                  (count-where
                                    (lambda (d)
                                      (let ((rr (+ r (car d))) (cc (+ c (cdr d))))
                                        (and (>= rr 0) (< rr (rows g))
                                             (>= cc 0) (< cc (cols g))
                                             (= (cell-at g rr cc) 5))))
                                    (list (cons -1 0) (cons 0 -1)
                                          (cons 1 0) (cons 0 1)))))))
                      (obj-cells o)))))"""


def rival_programs() -> dict[str, str]:
    return {
        "canonical_other_setting": (HERE / "canonical.rkt").read_text(),
        "composed_other_setting": ALT,
        "highlight_largest_total": _replace_once(ALT, WINNER, "(winner (pick-max objs obj-size))"),
        "highlight_smallest_total": _replace_once(ALT, WINNER, "(winner (pick-min objs obj-size))"),
        "highlight_largest_cyan": _replace_once(ALT, RED_PREDICATE, RED_PREDICATE[:-2] + "8)"),
        "highlight_first_component": _replace_once(ALT, WINNER, "(winner (first objs))"),
        "highlight_last_component": _replace_once(ALT, WINNER, "(winner (last objs))"),
        "highlight_most_raw_tips": _replace_once(ALT, WINNER, _raw_tip_selector()),
        "identity": "(rule! (lambda (g) g))",
    }


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(out: Path, seeds: tuple[int, ...] = (0, 17)) -> dict[str, Any]:
    rivals = rival_programs()
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations = 0
    episodes: list[dict[str, Any]] = []
    harmful: list[dict[str, Any]] = []
    try:
        for seed in seeds:
            for setting in P.FINISH_RULES:
                settings = {"finish_rule": setting}
                episode = P.generate(seed, settings, 2, 4)
                intended_program = episode["program_solution"]
                rows = []
                for name, source in rivals.items():
                    if source == intended_program:
                        continue
                    demo_matches: list[bool] = []
                    for pair in episode["train"]:
                        reference = _grid(apply(intended_program, pair["input"])); evaluations += 1
                        if reference != pair["output"]:
                            raise AssertionError("selected Racket program disagrees with generated label")
                        actual = _grid(apply(source, pair["input"])); evaluations += 1
                        demo_matches.append(actual == reference)
                    survives = all(demo_matches)
                    query_diffs: list[int] = []
                    if survives:
                        for index, pair in enumerate(episode["test"]):
                            reference = _grid(apply(intended_program, pair["input"])); evaluations += 1
                            actual = _grid(apply(source, pair["input"])); evaluations += 1
                            if actual != reference:
                                query_diffs.append(index)
                    row = {
                        "name": name,
                        "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                        "demo_matches": demo_matches,
                        "survives_demonstrations": survives,
                        "query_differences": query_diffs,
                    }
                    rows.append(row)
                    if survives and query_diffs:
                        harmful.append({"seed": seed, "settings": settings, **row})
                episodes.append({
                    "seed": seed,
                    "settings": settings,
                    "input_sha256": [_sha(pair["input"]) for pair in episode["train"] + episode["test"]],
                    "rivals": rows,
                    "survivors": [row["name"] for row in rows if row["survives_demonstrations"]],
                })
    finally:
        bridge.close()
    report = {
        "schema": "c1b540a1d7b0-protected-racket-finite-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not harmful else "failed",
        "racket": identity,
        "seeds": list(seeds),
        "episodes": episodes,
        "racket_evaluations": evaluations,
        "harmful_demo_survivors": harmful,
        "finite_scope": {
            "settings": list(P.FINISH_RULES),
            "minimum_demonstrations": 2,
            "queries_checked_only_for_survivors": 4,
            "declared_rivals": sorted(rivals),
        },
        "training_admitted": False,
    }
    if harmful:
        raise AssertionError(f"query-changing rivals survived: {harmful}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
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
