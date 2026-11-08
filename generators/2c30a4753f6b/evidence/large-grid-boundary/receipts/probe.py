#!/usr/bin/env python3
"""Bounded canonical boundary witness finder and saved-reference verifier."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import find_root, load_selected_generator


TASK = "2c30a4753f6b"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def facts(grid):
    foreground = [value for row in grid for value in row if value != 0]
    return {"height": len(grid), "width": len(grid[0]), "nonzero_count": len(foreground),
            "zero_count": sum(value == 0 for row in grid for value in row),
            "nonzero_colors": sorted(set(foreground)), "lr_asymmetric": any(row != row[::-1] for row in grid)}


def find_witness(output):
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK, root=root)
    attempts = []
    for seed in range(120):
        grid = generator.generate(seed, 0, difficulty="hard", scene_profile="tall_asymmetric")
        shape = [len(grid), len(grid[0])]
        attempts.append({"seed": seed, "shape": shape})
        if shape != [30, 15]:
            continue
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"Selected boundary input failed generator self_check: {errors}")
        selection = {"schema": "arc-canonical-boundary-witness-v1", "status": "found", "task_id": TASK,
                     "generator_version": generator.VERSION, "source_path": source.relative_to(root).as_posix(),
                     "source_sha256": source_sha, "seed": seed, "sample_index": 0, "difficulty": "hard",
                     "overrides": {"scene_profile": "tall_asymmetric"},
                     "observed_overrides": generator.observe_overrides(grid), "self_check_errors": errors,
                     "search": {"seed_min": 0, "seed_max_inclusive": 119, "attempts": attempts,
                                "attempt_count": len(attempts), "first_match": True},
                     "input_sha256": digest(grid), "input_facts": facts(grid), "input_file": "input.json",
                     "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     "invocation": {"command": [sys.executable, *sys.argv], "cwd": str(Path.cwd())}}
        write(output / "input.json", {"inputs": [grid]})
        write(output / "selection.json", selection)
        print(json.dumps({"status": "found", "seed": seed, "attempt_count": len(attempts), "shape": shape, "source_sha256": source_sha}))
        return 0
    write(output / "selection.json", {"status": "not_found", "source_sha256": source_sha, "attempts": attempts,
                                      "search_limit": 120})
    print("No 30x15 hard tall_asymmetric draw found among seeds 0..119", file=sys.stderr)
    return 1


def verify(selection_path, applied_path, output):
    selection = json.loads(selection_path.read_text())
    grid = json.loads((selection_path.parent / selection["input_file"]).read_text())["inputs"][0]
    applied = json.loads(applied_path.read_text())
    generator, _, current_sha = load_selected_generator(TASK, root=find_root(__file__))
    results = applied["results"]
    actual = results[0]["output"] if len(results) == 1 else None
    expected = [row + row[::-1] for row in grid]
    source_facts = facts(grid)
    output_facts = facts(actual) if actual else None
    checks = {
        "exact_current_source": current_sha == selection["source_sha256"] == applied["generator_sha256"],
        "same_probe_source": selection["probe_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "same_input_hash": digest(grid) == selection["input_sha256"],
        "input_is_30x15": [len(grid), len(grid[0])] == [30, 15],
        "generator_domain_accepts": not generator.self_check(grid),
        "observed_profile_is_tall": generator.observe_overrides(grid) == {"scene_profile": "tall_asymmetric"},
        "nontrivial_foreground": 0 < source_facts["nonzero_count"] < 450 and source_facts["lr_asymmetric"],
        "one_successful_reference_output": len(results) == 1 and results[0]["error"] is None,
        "selected_canonical_authority": applied["reference"] == "canonical" and applied["rule_hash_matches_catalog"] is True,
        "output_is_30x30": bool(actual) and [len(actual), len(actual[0])] == [30, 30],
        "python_mirror_parity": actual == expected,
        "foreground_count_doubled": bool(output_facts) and output_facts["nonzero_count"] == 2 * source_facts["nonzero_count"],
    }
    report = {"schema": "arc-canonical-boundary-verification-v1", "status": "pass" if all(checks.values()) else "fail",
              "task_id": TASK, "seed": selection["seed"], "sample_index": 0, "difficulty": "hard",
              "overrides": selection["overrides"], "source_sha256": current_sha,
              "input_sha256": digest(grid), "output_sha256": digest(actual), "input_facts": source_facts,
              "output_facts": output_facts, "checks": checks,
              "catalog_rule_hash": applied["catalog_rule_hash"], "executed_rule_hash": applied["executed_rule_hash"],
              "executed_rule_text_sha256": applied["rule_text_sha256"],
              "reference_receipt_sha256": hashlib.sha256(applied_path.read_bytes()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "limitation": "One source-bound upper-size witness, selected by a bounded deterministic search; not exhaustive boundary coverage or approval.",
              "invocation": {"command": [sys.executable, *sys.argv], "cwd": str(Path.cwd())}}
    write(output, report)
    print(json.dumps({"status": report["status"], "seed": selection["seed"], "input_shape": [30, 15],
                      "output_shape": [output_facts["height"], output_facts["width"]] if output_facts else None,
                      "checks_passed": sum(checks.values()), "checks_total": len(checks)}))
    return 0 if report["status"] == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    finder = commands.add_parser("find")
    finder.add_argument("--out", type=Path, required=True)
    verifier = commands.add_parser("verify")
    verifier.add_argument("--selection", type=Path, required=True)
    verifier.add_argument("--applied", type=Path, required=True)
    verifier.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return find_witness(args.out) if args.action == "find" else verify(args.selection, args.applied, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
