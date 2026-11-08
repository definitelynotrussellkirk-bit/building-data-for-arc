"""Bounded, real-Racket shortcut audit reusable by future frame-family authors."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_frame_self_audit_" + hashlib.sha256(str(_path).encode()).hexdigest(), _path)
prototype = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = prototype
_spec.loader.exec_module(prototype)


def _different(a, b):
    return sum(x != y for r, s in zip(a, b) for x, y in zip(r, s))


def audit_lesson(train, test, axis, apply):
    """Fit rivals ONLY to demos; inspect queries only after survivor selection."""
    selected = prototype.program({"axis": axis})
    labels = [apply(selected, grid) for grid in train]
    query_labels = [apply(selected, grid) for grid in test]
    records, ambiguous = {}, []
    for name, candidate in prototype.rivals(axis).items():
        elimination = None
        for i, (grid, expected) in enumerate(zip(train, labels)):
            predicted = apply(candidate, grid)
            if predicted != expected:
                elimination = {"demo_index": i, "different_cells": _different(predicted, expected)}
                break
        if elimination is not None:
            records[name] = {"status": "refuted_by_demo", **elimination}
        else:
            disagreements = [i for i, (grid, expected) in enumerate(zip(test, query_labels))
                             if apply(candidate, grid) != expected]
            records[name] = {"status": "ambiguous" if disagreements else "agrees_on_queries",
                             "query_disagreements": disagreements}
            if disagreements:
                ambiguous.append(name)
    return {"status": "ambiguous" if ambiguous else "passed", "axis": axis,
            "demos": len(train), "queries": len(test), "rivals": records,
            "ambiguous_rivals": ambiguous,
            "limitations": "Only the declared executable rivals and retained input sample; not universal uniqueness."}


def run(seeds, demos, queries):
    apply_raw, identity, bridge = prototype._real_evaluator(prototype.ROOT / "shared/runtime")
    cache = {}
    def apply(program, grid):
        key = (program, json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            cache[key] = prototype._grid(apply_raw(program, grid))
        return cache[key]
    lessons = []
    try:
        for seed in seeds:
            train, test = prototype.inputs(seed, demos, queries)
            for axis in prototype.AXES:
                report = audit_lesson(train, test, axis, apply)
                report["seed"] = seed
                lessons.append(report)
                print(json.dumps({"seed": seed, "axis": axis, "status": report["status"],
                                  "ambiguous_rivals": report["ambiguous_rivals"]}), flush=True)
    finally:
        bridge.close()
    return {"schema": "arcpuzzles-frame-axis-self-audit-v1",
            "status": "passed" if all(x["status"] == "passed" for x in lessons) else "ambiguous",
            "prototype_sha256": hashlib.sha256(_path.read_bytes()).hexdigest(),
            "racket": identity, "racket_evaluations": len(cache),
            "successful_lessons": sum(x["status"] == "passed" for x in lessons),
            "attempted_lessons": len(lessons), "lessons": lessons}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("Use a new output path")
    result = run(args.seed or [0, 17], args.demos, args.queries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
