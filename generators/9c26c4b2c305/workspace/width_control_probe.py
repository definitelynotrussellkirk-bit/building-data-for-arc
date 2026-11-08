#!/usr/bin/env python3
"""Bounded width-control probe; optional actual-Racket and baseline replay checks.

Run through the packet wrapper from its outer directory. A baseline report records
the original API behavior and 18 lawful recipes. The after report rejects invalid
requests, compares the same lawful input bytes, and executes their Racket labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "9c26c4b2c305"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    authority = next(row for row in rows if row.get("task_id") == TASK_ID)
    rule = authority["program_solution"]
    report = {
        "schema": "9c26c4b2c305-width-control-probe-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(source.relative_to(root)),
            "generator_sha256": source_hash,
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "base_sha256": hashlib.sha256(
                (root / "shared/runtime/puzzle_generators/base.py").read_bytes()
            ).hexdigest(),
            "canonical_row_sha256": digest(authority),
            "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
            "declared_rule_hash": gen.RULE_HASH,
        },
        "invalid_requests": [],
        "lawful_cases": [],
        "limitations": [
            "One exact-width control only; not a complete generator audit.",
            "18 fixed lawful recipes; no universal distribution or teaching claim.",
            "Canonical generation remains 9 by 4..14; no parametric changes.",
        ],
    }
    for value in [4.0, 4.75, 14.0, 14.75, "4", "14", True, False, 3, 15]:
        result = {"value": value, "python_type": type(value).__name__}
        try:
            grid = gen.generate(17, 1, difficulty="medium", grid_w=value)
            result.update(accepted=True, observed_width=len(grid[0]))
        except (TypeError, ValueError) as error:
            result.update(accepted=False, exception=type(error).__name__, message=str(error))
        report["invalid_requests"].append(result)
    recipes = []
    for band in ("easy", "medium", "hard"):
        for slot in range(4):
            recipes.append({"seed": 9600 + slot, "sample_index": slot, "difficulty": band})
        for width in (4, 14):
            recipes.append({"seed": 9700 + width, "sample_index": 1, "difficulty": band, "grid_w": width})
    for recipe in recipes:
        grid = gen.generate(**recipe)
        errors = gen.strict_canonical_like(grid)
        if errors:
            raise AssertionError(errors)
        report["lawful_cases"].append({
            "recipe": recipe, "input_sha256": digest(grid),
            "observed": gen.observe_overrides(grid), "input": grid,
        })
    if args.racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        callable_text = wrap_rule(rule)
        report["source_binding"]["executed_callable_sha256"] = hashlib.sha256(callable_text.encode()).hexdigest()
        with RacketBridge() as bridge:
            bridge.eval_text(f"(define width_probe_rule {callable_text})")
            for case in report["lawful_cases"]:
                bridge.define_grid("width_probe_input", case["input"])
                output = bridge.eval_text("(width_probe_rule width_probe_input)")
                case["racket_output"] = output
                case["mirror_matches_racket"] = output == gen.rule_mirror(case["input"])
        report["racket_labels_checked"] = len(report["lawful_cases"])
        report["racket_label_mismatches"] = sum(not case["mirror_matches_racket"] for case in report["lawful_cases"])
    if args.baseline:
        baseline_bytes = args.baseline.read_bytes()
        before = json.loads(baseline_bytes)
        report["baseline_sha256"] = hashlib.sha256(baseline_bytes).hexdigest()
        report["baseline_generator_sha256"] = before["source_binding"]["generator_sha256"]
        report["lawful_input_bytes_unchanged"] = [
            (case["recipe"], case["input_sha256"]) for case in report["lawful_cases"]
        ] == [(case["recipe"], case["input_sha256"]) for case in before["lawful_cases"]]
    accepted = sum(case["accepted"] for case in report["invalid_requests"])
    report["accepted_invalid_requests"] = accepted
    report["status"] = "pass" if (
        accepted == 0 and report.get("racket_label_mismatches", 0) == 0
        and report.get("lawful_input_bytes_unchanged", True)
    ) else "finding"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "status", "accepted_invalid_requests", "source_binding"
    )}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
