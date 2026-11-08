"""Reproduce one ordinary beam lesson with independently executed Racket labels.

Run through the packet's run_with_racket.py wrapper (with an absolute payload
Python path). This authoring probe imports only the public reviewer helpers;
neither the selected generator's private geometry nor old reviewer scripts are
used to construct the rival.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0b8ba9bb3c63"
BASELINE_SHA256 = "06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965"


def blue_only_rival(grid):
    """Only blue stops a ray; all colored blockers are restored afterward."""
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 8]
    if not cyan:
        raise ValueError("Expected a cyan source rectangle")
    top = min(r for r, _ in cyan)
    bottom = max(r for r, _ in cyan)
    left = min(c for _, c in cyan)
    right = max(c for _, c in cyan)
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    rays = []
    for row in range(top, bottom + 1):
        rays.extend(([(row, c) for c in range(left - 1, -1, -1)],
                     [(row, c) for c in range(right + 1, width)]))
    for col in range(left, right + 1):
        rays.extend(([(r, col) for r in range(top - 1, -1, -1)],
                     [(r, col) for r in range(bottom + 1, height)]))
    for ray in rays:
        for row, col in ray:
            if grid[row][col] == 1:
                break
            output[row][col] = 4
    for row, cells in enumerate(grid):
        for col, color in enumerate(cells):
            if color not in (0, 2):
                output[row][col] = color
    return output


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path,
                        help="New evidence directory; never overwrites a prior run")
    parser.add_argument("--seed", type=int, default=8)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--difficulty", choices=("default", "easy", "medium", "hard"),
                        default="default")
    parser.add_argument("--family", choices=("public", "generalized"))
    parser.add_argument("--expect-baseline", action="store_true")
    parser.add_argument("--require-rotation-evidence", action="store_true")
    args = parser.parse_args()
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
    if args.expect_baseline and source_hash != BASELINE_SHA256:
        raise RuntimeError(f"Expected baseline bytes, found {source_hash}")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    difficulty = None if args.difficulty == "default" else args.difficulty
    overrides = {"scene_family": args.family} if args.family else {}
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_matches = [blue_only_rival(pair["input"]) == pair["output"]
                         for pair in canonical]
    cases = []
    for index in range(args.start, args.start + 4):
        grid = generator.generate(args.seed, index, difficulty=difficulty, **overrides)
        problems = generator.self_check(grid)
        if problems:
            raise AssertionError(problems)
        cases.append({"seed": args.seed, "sample_index": index,
                      "difficulty": difficulty, "overrides": overrides,
                      "family": generator.canonical_profile_signature(grid),
                      "input": grid, "rival_output": blue_only_rival(grid),
                      "mirror_output": generator.rule_mirror(grid),
                      "validator_errors": problems})
    inputs_path = out / "inputs.json"
    racket_path = out / "racket.json"
    write_json(inputs_path, {"inputs": [case["input"] for case in cases]})
    command = [sys.executable, "-m", "arcpuzzles", "--library", str(root),
               "apply", TASK_ID, "--input", str(inputs_path),
               "--check-generator-domain", "--out", str(racket_path)]
    started = datetime.now(timezone.utc).isoformat()
    before = time.monotonic()
    process = subprocess.run(command, cwd=root, text=True, capture_output=True,
                             timeout=150)
    command_record = {
        "schema": "lesson-regression-command-v1", "argv": command,
        "cwd": str(root), "started_at": started,
        "elapsed_seconds": round(time.monotonic() - before, 3),
        "exit_code": process.returncode, "stdout": process.stdout,
        "stderr": process.stderr,
        "probe_argv": [sys.executable, *sys.argv],
        "generator_sha256_before": source_hash,
        "generator_sha256_after": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    write_json(out / "command.json", command_record)
    if process.returncode:
        raise RuntimeError(f"Racket apply failed; see {out / 'command.json'}")
    receipt = json.loads(racket_path.read_text(encoding="utf-8"))
    if receipt["generator_sha256"] != source_hash:
        raise RuntimeError("The generator changed between sampling and reference execution")
    if command_record["generator_sha256_after"] != source_hash:
        raise RuntimeError("The generator changed during the probe")
    for case, result in zip(cases, receipt["results"], strict=True):
        if not result["valid_output"] or result["error"]:
            raise AssertionError(result)
        if result["generator_domain"]["status"] != "valid":
            raise AssertionError(result["generator_domain"])
        expected = result["output"]
        case["racket_output"] = expected
        case["racket_matches_mirror"] = expected == case["mirror_output"]
        case["rival_differences"] = [
            {"row": row, "col": col, "racket": color,
             "rival": case["rival_output"][row][col]}
            for row, cells in enumerate(expected) for col, color in enumerate(cells)
            if case["rival_output"][row][col] != color
        ]
        case["rival_refuted"] = bool(case["rival_differences"])
    rotations = []
    for query in range(4):
        fitting_demos = all(not cases[i]["rival_refuted"] for i in range(4) if i != query)
        rotations.append({"query_position": query, "rival_fits_all_demos": fitting_demos,
                          "rival_changes_query": cases[query]["rival_refuted"],
                          "ambiguous": fitting_demos and cases[query]["rival_refuted"]})
    report = {
        "schema": "blue-only-lesson-regression-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "selected_source": str(source.relative_to(root)),
        "declared_rule_hash": generator.RULE_HASH,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "rule_task_id": receipt["rule_task_id"], "rule_file": receipt["rule_file"],
        "seed": args.seed, "sample_indices": list(range(args.start, args.start + 4)),
        "difficulty": difficulty, "overrides": overrides,
        "canonical_pairs": len(canonical),
        "canonical_unique_inputs": len({json.dumps(pair["input"]) for pair in canonical}),
        "rival_fits_all_canonical_pairs": all(canonical_matches),
        "cases": cases, "rotations": rotations,
        "counterexample_count": sum(case["rival_refuted"] for case in cases),
        "all_rotations_have_demo_counterexamples": all(
            not row["rival_fits_all_demos"] for row in rotations),
        "original_order_ambiguous": rotations[-1]["ambiguous"],
        "all_racket_labels_match_mirror": all(case["racket_matches_mirror"] for case in cases),
        "limits": "Four specified ordinary draws; a concrete reproduction, not a prevalence estimate or a claim about all possible rival rules.",
    }
    write_json(out / "lesson.json", report)
    summary = {key: report[key] for key in (
        "generator_sha256", "executed_rule_hash", "rule_text_sha256",
        "canonical_pairs", "rival_fits_all_canonical_pairs", "counterexample_count",
        "original_order_ambiguous", "all_rotations_have_demo_counterexamples",
        "all_racket_labels_match_mirror")}
    summary["families"] = [case["family"] for case in cases]
    summary["rival_mismatch_cells"] = [len(case["rival_differences"]) for case in cases]
    print(json.dumps(summary, sort_keys=True))
    if not report["all_racket_labels_match_mirror"]:
        return 1
    if args.require_rotation_evidence and not report["all_rotations_have_demo_counterexamples"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
