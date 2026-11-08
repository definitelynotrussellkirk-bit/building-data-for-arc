"""Protected-Racket finite shortcut audit for the 2ca05c7eef24 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "2ca05c7eef24"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.parametric_worker import _grid, _real_evaluator  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_vote_mode_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _load_prototype()
ALT = (HERE / "vote_then_keep_output_mode.rkt").read_text()
STAGE_B = """(let* ((colors (remove-duplicates nonzero))
               (keep
                (first
                 (sort colors
                   (lambda (a b)
                     (let ((ca (count-where (lambda (v) (= v a)) nonzero))
                           (cb (count-where (lambda (v) (= v b)) nonzero)))
                       (or (> ca cb) (and (= ca cb) (> a b)))))))))"""


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"expected one replacement site, got {source.count(old)}")
    return source.replace(old, new, 1)


def _replace_stage_b_keep(binding: str) -> str:
    replacement = f"""(let* ((colors (remove-duplicates nonzero))
               (keep {binding}))"""
    return _replace_once(ALT, STAGE_B, replacement)


def rival_programs() -> dict[str, str]:
    raw_mode = _replace_once(
        ALT,
        "(all-votes (apply append voted))",
        "(all-votes (apply append (apply append panels)))",
    )
    largest = _replace_stage_b_keep("(apply max colors)")
    smallest = _replace_stage_b_keep("(apply min colors)")
    first_seen = _replace_stage_b_keep("(first nonzero)")
    last_seen = _replace_stage_b_keep("(last nonzero)")
    rarest = _replace_stage_b_keep(
        """(first
                 (sort colors
                   (lambda (a b)
                     (let ((ca (count-where (lambda (v) (= v a)) nonzero))
                           (cb (count-where (lambda (v) (= v b)) nonzero)))
                       (or (< ca cb) (and (= ca cb) (> a b)))))))"""
    )
    return {
        "canonical_other_setting": (HERE / "canonical.rkt").read_text(),
        "composed_other_setting": ALT,
        "keep_raw_input_mode": raw_mode,
        "keep_largest_voted_color": largest,
        "keep_smallest_voted_color": smallest,
        "keep_rarest_voted_color": rarest,
        "keep_first_seen_voted_color": first_seen,
        "keep_last_seen_voted_color": last_seen,
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
        "schema": "2ca05c7eef24-protected-racket-finite-audit-v1",
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
