#!/usr/bin/env python3
"""Reproduce the selected task's retained scene-level shortcut witness."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "089c14df9952"
EXPECTED_GENERATOR_SHA256 = "029aff1e3ba3c7cc48e45ef32d24dd3e4bbe466549b2b75b91538cfb863e4041"
RIVAL = "scene_uniform_hint_policy"


def sha(value) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()

    root = find_root(__file__)
    out = Path(__file__).resolve().parent
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_GENERATOR_SHA256:
        raise AssertionError(f"unexpected generator source {source_sha}")

    fixture_path = root / "generators" / TASK_ID / "workspace" / "scene_uniform_hint_policy_counterexample.json"
    fixture = json.loads(fixture_path.read_text())
    case = fixture["case"]
    grid = generator.generate(
        case["seed"], case["sample_index"],
        difficulty=case["difficulty"], **case["overrides"],
    )
    if grid != case["input"]:
        raise AssertionError("current generator no longer reproduces retained input")
    errors = generator.self_check(grid)
    if errors:
        raise AssertionError(errors)
    rival = generator.SEMANTIC_RIVALS[RIVAL](grid)
    if rival != case["rival_output"]:
        raise AssertionError("declared rival no longer reproduces retained rival output")

    write_json(out / "input.json", grid)
    build = {
        "schema": "arcpuzzles-selected-shortcut-build-v1",
        "task_id": TASK_ID,
        "generator_path": Path(source_path).relative_to(root).as_posix(),
        "generator_sha256": source_sha,
        "fixture_path": fixture_path.relative_to(root).as_posix(),
        "seed": case["seed"],
        "sample_index": case["sample_index"],
        "difficulty": case["difficulty"],
        "overrides": case["overrides"],
        "input_sha256": sha(grid),
        "self_check": errors,
        "rival": RIVAL,
        "rival_definition": fixture["rival_definition"],
        "rival_output": rival,
        "rival_output_sha256": sha(rival),
    }
    write_json(out / "build.json", build)

    if args.racket is None:
        print(json.dumps({
            "status": "built",
            "generator_sha256": source_sha,
            "input_sha256": sha(grid),
            "rival_output_sha256": sha(rival),
        }, indent=2, sort_keys=True))
        return

    racket = json.loads(args.racket.read_text())
    authoritative = racket["results"][0]["output"]
    diffs = [
        {"row": r, "col": c, "intended": authoritative[r][c], "rival": rival[r][c]}
        for r in range(len(grid)) for c in range(len(grid[0]))
        if authoritative[r][c] != rival[r][c]
    ]
    report = {
        "schema": "arcpuzzles-selected-shortcut-verification-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
        "seed": case["seed"],
        "sample_index": case["sample_index"],
        "difficulty": case["difficulty"],
        "overrides": case["overrides"],
        "input": grid,
        "input_sha256": sha(grid),
        "self_check": errors,
        "intended_output": authoritative,
        "intended_output_sha256": sha(authoritative),
        "rival": RIVAL,
        "rival_definition": fixture["rival_definition"],
        "rival_output": rival,
        "rival_output_sha256": sha(rival),
        "diffs": diffs,
        "authoritative_matches_retained_fixture": authoritative == case["intended_output"],
        "rival_matches_retained_fixture": rival == case["rival_output"],
        "current_generator_emits_case": True,
        "commands": {
            "build": "python3 review.py run python3 ../checks/selected-shortcut/verify.py",
            "apply": "python3 review.py run python3 -m arcpuzzles apply 089c14df9952 --input ../checks/selected-shortcut/input.json --out ../checks/selected-shortcut/racket.json",
            "analyze": "python3 review.py run python3 ../checks/selected-shortcut/verify.py --racket ../checks/selected-shortcut/racket.json",
        },
    }
    if not report["authoritative_matches_retained_fixture"]:
        raise AssertionError("authoritative output differs from retained fixture")
    if not diffs:
        raise AssertionError("rival does not disagree with intended output")
    write_json(out / "report.json", report)
    print(json.dumps({
        "status": "pass",
        "generator_sha256": source_sha,
        "executed_rule_hash": racket["executed_rule_hash"],
        "differences": len(diffs),
        "current_generator_emits_case": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
