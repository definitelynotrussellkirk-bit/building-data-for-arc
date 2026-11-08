#!/usr/bin/env python3
"""Optional, generator-independent challenger check over saved labeled lessons.

This checks a supplied finite rival, not universal identifiability or label truth.
Only explicitly supplied local challenger code is loaded. No shared source changes.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_grid(grid, label):
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        raise ValueError(f"{label}: expected 1..30 rows")
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        raise ValueError(f"{label}: expected 1..30 columns")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError(f"{label}: ragged or non-list row")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError(f"{label}: cells must be literal integers in 0..9")


def score(lesson, rival, *, rotate):
    if not isinstance(lesson, dict):
        raise ValueError("lesson must be an object")
    train, test = lesson.get("train"), lesson.get("test")
    if not isinstance(train, list) or not train:
        raise ValueError("at least one demonstration is required")
    if not isinstance(test, list) or len(test) != 1:
        raise ValueError("exactly one labeled query is required")
    pairs = train + test
    predictions = []
    for i, pair in enumerate(pairs):
        if not isinstance(pair, dict) or not {"input", "output"} <= pair.keys():
            raise ValueError(f"pair {i}: input and reference output are required")
        check_grid(pair["input"], f"pair {i} input")
        check_grid(pair["output"], f"pair {i} output")
        predicted = rival(deepcopy(pair["input"]))
        check_grid(predicted, f"pair {i} rival output")
        predictions.append(predicted)

    def holdout(q):
        refutations = [i for i, pair in enumerate(pairs)
                       if i != q and predictions[i] != pair["output"]]
        differs = predictions[q] != pairs[q]["output"]
        result = {"query_position": q, "demonstration_count": len(pairs) - 1,
                  "refuting_demo_positions": refutations, "query_differs": differs,
                  "ambiguous": not refutations and differs}
        if result["ambiguous"]:
            result.update(query_input=pairs[q]["input"], reference_output=pairs[q]["output"],
                          rival_output=predictions[q])
        return result

    return {"production": holdout(len(pairs) - 1),
            "rotations": [holdout(i) for i in range(len(pairs))] if rotate else [],
            "rotation_policy": "require" if rotate else "not_tested"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lesson", type=Path, help="One lesson object or a nonempty list of lessons")
    parser.add_argument("--rival", type=Path, required=True, help="Explicit local Python plugin")
    parser.add_argument("--function", default="predict")
    parser.add_argument("--rotate-query", action="store_true", help="Require all single-query holdouts")
    parser.add_argument("--reference-receipt", type=Path, help="Hash a retained label-authority receipt")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("use a new --out path to preserve previous evidence")
    report = {"schema": "external-lesson-challenger-v1", "status": "execution_error",
              "scope": "Supplied rival only; supplied labels assumed authoritative. No universal induction claim.",
              "argv": sys.argv if argv is None else argv, "cwd": str(Path.cwd()),
              "checker_sha256": sha(__file__)}
    try:
        report["lesson_sha256"] = sha(args.lesson)
        report["rival_sha256"] = sha(args.rival)
        report["rival_function"] = args.function
        report["reference_receipt_sha256"] = sha(args.reference_receipt) if args.reference_receipt else None
        spec = importlib.util.spec_from_file_location("explicit_lesson_challenger", args.rival.resolve())
        if spec is None or spec.loader is None:
            raise ValueError("unable to load rival module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rival = getattr(module, args.function)
        if not callable(rival):
            raise ValueError("rival function is not callable")
        data = json.loads(args.lesson.read_text())
        lessons = data if isinstance(data, list) else [data]
        if not lessons:
            raise ValueError("no lessons supplied")
        rows = []
        for index, lesson in enumerate(lessons):
            row = score(lesson, rival, rotate=args.rotate_query)
            row.update(lesson_index=index, task_id=lesson.get("task_id"),
                       supplied_provenance=lesson.get("provenance"),
                       supplied_rule_hash=lesson.get("executed_rule_hash"))
            rows.append(row)
        production = sum(row["production"]["ambiguous"] for row in rows)
        rotations = sum(r["ambiguous"] for row in rows for r in row["rotations"])
        report.update(lessons=rows, lessons_checked=len(rows),
                      production_ambiguities=production, rotation_ambiguities=rotations,
                      rotations_checked=sum(len(row["rotations"]) for row in rows),
                      status="ambiguity_found" if production or rotations else "no_supplied_rival_ambiguity_found")
        code = 1 if production or rotations else 0
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        code = 2
    report["exit_code"] = code
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "exit_code")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
