"""Bounded protected-Racket teaching audit for the keyed-relocation family.

The audit fits executable wrong rules to only the first two demonstrations,
then records any disagreement on the four private queries.  It is finite
self-review evidence, not a uniqueness proof or owner acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1]
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


def _load_adapter():
    spec = importlib.util.spec_from_file_location("_6e4_audit_adapter", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("expected one rule! expression")
    return text[len("(rule!"):-1].strip()


def _replace_once(program: str, old: str, new: str) -> str:
    if program.count(old) != 1:
        raise ValueError(f"mutation anchor count {program.count(old)} for {old!r}")
    return program.replace(old, new, 1)


def rival_programs(reference: str, other: str, first_demo: dict) -> dict[str, str]:
    tabs = """(andmap (lambda (color)
                              (equal? (transform-side (source-side mover color) k)
                                      (target-side color target)))
                            tabs)"""
    first_only = """(if (empty? tabs)
                        #t
                        (let ((color (first tabs)))
                          (equal? (transform-side (source-side mover color) k)
                                  (target-side color target))))"""
    axis_only = """(andmap (lambda (color)
                              (equal?
                                (if (member (transform-side (source-side mover color) k) '(T B)) 'H 'V)
                                (if (member (target-side color target) '(T B)) 'H 'V)))
                            tabs)"""
    keep_anchor = """   (define erased
     (erase-cells g (apply append (append movers targets)) bg))"""
    no_stamp = """   (define state
     (foldl
       (lambda (mover acc)
         (let* ((out (first acc))
                (remaining (second acc))
                (target (find-first (lambda (x) (= (length x) (nine-count mover))) remaining))
                (stamp (orient mover target)))
           (list (paint-cells out stamp)
                 (remove target remaining))))
       (list erased targets)
       movers))"""
    bg = max(set(v for row in first_demo["input"] for v in row), key=lambda v: sum(x == v for row in first_demo["input"] for x in row))
    return {
        "declared_other_setting": other,
        "identity": "(rule! (lambda (g) g))\n",
        "ignore_all_guide_tabs": _replace_once(reference, tabs, "#t"),
        "use_only_first_guide_tab": _replace_once(reference, tabs, first_only),
        "match_only_guide_axis": _replace_once(reference, tabs, axis_only),
        "keep_source_objects": _replace_once(reference, keep_anchor, "   (define erased g)"),
        "erase_without_relocation": _replace_once(reference, no_stamp, "   (define state (list erased targets))"),
        "fixed_first_demo_background": f"(rule! (if (= (mode g -1) {bg}) {_body(reference)} g))\n",
    }


def run_audit(out: Path, seeds=(17, 43)) -> dict:
    adapter = _load_adapter()
    source_files = [p for p in sorted(TASK.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    binding = {
        "task_id": "public_eval_6e4f6532",
        "files": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in source_files
        ],
    }
    apply, identity, bridge = _real_evaluator(RUNTIME)
    evaluations = 0
    episodes = []
    try:
        for mode in ("toward", "away"):
            setting = {"orientation_mode": mode}
            other_setting = {"orientation_mode": "away" if mode == "toward" else "toward"}
            for seed in seeds:
                episode = adapter.generate(seed, setting, 2, 4)
                rivals = rival_programs(
                    episode["program_solution"], adapter.program(other_setting), episode["train"][0]
                )
                rows = []
                for name, program in rivals.items():
                    demo_results = []
                    error = None
                    try:
                        for pair in episode["train"]:
                            demo_results.append(apply(program, copy.deepcopy(pair["input"])) == pair["output"])
                            evaluations += 1
                    except Exception as exc:  # retained as invalid rival, not refutation
                        error = f"{type(exc).__name__}: {exc}"
                    survives = error is None and all(demo_results)
                    query_differences = []
                    if survives:
                        for index, pair in enumerate(episode["test"]):
                            actual = apply(program, copy.deepcopy(pair["input"]))
                            evaluations += 1
                            if actual != pair["output"]:
                                query_differences.append({
                                    "index": index,
                                    "changed_cells": sum(
                                        a != b for ra, rb in zip(actual, pair["output"]) for a, b in zip(ra, rb)
                                    ),
                                })
                    rows.append({
                        "name": name,
                        "survives_demonstrations": survives,
                        "demo_results": demo_results,
                        "execution_error": error,
                        "query_differences": query_differences,
                    })
                episodes.append({"settings": setting, "seed": seed, "rivals": rows})
    finally:
        bridge.close()
    unresolved = [
        {"settings": e["settings"], "seed": e["seed"], "name": r["name"], "query_differences": r["query_differences"]}
        for e in episodes for r in e["rivals"]
        if r["survives_demonstrations"] and r["query_differences"]
    ]
    invalid = [
        {"settings": e["settings"], "seed": e["seed"], "name": r["name"], "error": r["execution_error"]}
        for e in episodes for r in e["rivals"] if r["execution_error"]
    ]
    report = {
        "schema": "arcpuzzles-bounded-teaching-audit-v1",
        "task_id": "public_eval_6e4f6532",
        "status": "passed" if not unresolved and not invalid else "findings",
        "racket": identity,
        "source_binding": binding,
        "evaluations": evaluations,
        "episodes": episodes,
        "unresolved": unresolved,
        "invalid_rivals": invalid,
        "limits": "Two settings, two seeds, first two demonstrations, eight authored executable rivals; not a universal uniqueness proof.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_audit(args.out)
    print(json.dumps({"status": report["status"], "evaluations": report["evaluations"], "unresolved": len(report["unresolved"]), "invalid": len(report["invalid_rivals"])}))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
