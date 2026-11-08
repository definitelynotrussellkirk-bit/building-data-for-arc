#!/usr/bin/env python3
"""Findings-only, exact-source audit of ignored frame controls and soft count.

Run through the packet wrapper. No target sources, tests, rules or status are
modified; all retained artifacts stay alongside this portable reproducer.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shlex
import sys
import traceback

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "1a2abf5aa05a"
ASSIGNED_SOURCE_SHA256 = "ede7336806a39e8c5c04e667731ffcbbd2806a90bc0c5ff2c4df2ad72504bb4a"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def frames(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            seen.add((r, c))
            cells = {(r, c)}
            todo = deque([(r, c)])
            while todo:
                rr, cc = todo.popleft()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        todo.append((nr, nc))
            r0, r1 = min(x for x, _ in cells), max(x for x, _ in cells)
            c0, c1 = min(y for _, y in cells), max(y for _, y in cells)
            perimeter = {(rr, cc) for rr in range(r0, r1 + 1) for cc in range(c0, c1 + 1)
                         if rr in (r0, r1) or cc in (c0, c1)}
            result.append({"color": color, "bbox": [r0, c0, r1, c1],
                           "height": r1 - r0 + 1, "width": c1 - c0 + 1,
                           "cells": len(cells),
                           "hollow_rectangle": r1 - r0 >= 2 and c1 - c0 >= 2 and cells == perimeter})
    return result


def hole_output(grid):
    """Independent geometric expectation for the sampled complete frames only."""
    descriptions = frames(grid)
    if not descriptions or not all(row["hollow_rectangle"] for row in descriptions):
        raise ValueError("geometric expectation is only defined on complete hollow frames")
    output = [[0 for _ in row] for row in grid]
    for frame in descriptions:
        r0, c0, r1, c1 = frame["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                output[r][c] = frame["color"]
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New directory for this execution")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK_ID, root=root)
    report = {
        "schema": "1a2abf5aa05a-findings-only-audit-v1", "status": "running",
        "task_id": TASK_ID, "generator_sha256": source_sha,
        "assigned_generator_sha256": ASSIGNED_SOURCE_SHA256,
        "source_path": str(source.relative_to(root)), "version": module.VERSION,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": "python3 review.py run ../.venv-review/bin/python " + shlex.join(sys.argv),
        "payload_cwd": str(Path.cwd()), "outer_cwd": str(root.parent.parent),
        "public_api": "Catalog.apply(reference='canonical', check_generator_domain=True)",
        "notes": {"current_notes_sha256": hashlib.sha256((source.parent / "notes.md").read_bytes()).hexdigest(),
                  "current_review_index_exists": (source.parent / "evidence/review_index.json").exists()},
        "declared_axes": module.AXES,
        "size_control_comparisons": [], "frame_count_search": [], "errors": [],
        "limitations": ["Bounded source audit, not a full battery or random lesson census.",
                        "Only seed 0 size-control comparisons and at most 32 explicit-count seeds.",
                        "No production wrong-label or lesson-ambiguity claim follows from ignored controls.",
                        "The one-cell validator observation concerns a hand-made out-of-domain input.",
                        "Target sources, rules, tests and audit status remain untouched."]}
    write_json(args.out / "report.json", report)
    try:
        if source_sha != ASSIGNED_SOURCE_SHA256:
            raise ValueError("Audited source no longer matches the drawn assignment")
        (args.out / "generator.snapshot.py").write_bytes(source.read_bytes())
        application_cases = []
        for difficulty, controls in (
            ("easy", {"grid_h": 11, "grid_w": 13, "n_frames": 2}),
            ("medium", {"grid_h": 15, "grid_w": 17, "n_frames": 3}),
            ("hard", {"grid_h": 22, "grid_w": 24, "n_frames": 4}),
        ):
            draws = []
            for frame_h, frame_w in ((None, None), (3, 3), (6, 6)):
                overrides = dict(controls)
                if frame_h is not None:
                    overrides.update(frame_h=frame_h, frame_w=frame_w)
                grid = module.generate(0, 0, difficulty=difficulty, **overrides)
                draws.append({"seed": 0, "sample_index": 0, "difficulty": difficulty,
                              "overrides": overrides, "input": grid, "input_sha256": digest(grid),
                              "observed_frames": frames(grid),
                              "self_check": module.self_check(deepcopy(grid), difficulty=difficulty)})
            same = draws[0]["input"] == draws[1]["input"] == draws[2]["input"]
            report["size_control_comparisons"].append({"difficulty": difficulty,
                                                     "all_three_inputs_identical": same,
                                                     "draws": draws})
            application_cases.append({"name": f"ignored_sizes_{difficulty}", "input": draws[1]["input"],
                                      "expected": hole_output(draws[1]["input"]),
                                      "expectation_type": "complete-frame geometry"})
        controls = {"grid_h": 9, "grid_w": 11, "n_frames": 3}
        for seed in range(32):
            grid = module.generate(seed, 0, difficulty="easy", **controls)
            description = frames(grid)
            row = {"seed": seed, "sample_index": 0, "difficulty": "easy", "overrides": controls,
                   "observed_count": len(description), "requested_count": 3,
                   "observed_frames": description, "input_sha256": digest(grid)}
            report["frame_count_search"].append(row)
            if len(description) != 3:
                report["minimal_count_witness"] = {**row, "input": grid,
                                                   "self_check": module.self_check(deepcopy(grid), difficulty="easy")}
                application_cases.append({"name": "explicit_count_shortfall", "input": grid,
                                          "expected": hole_output(grid),
                                          "expectation_type": "complete-frame geometry"})
                break
        report["advertised_n_frames_one"] = []
        for difficulty in ("easy", "medium", "hard"):
            try:
                grid = module.generate(0, 0, difficulty=difficulty, n_frames=1)
                observation = {"status": "returned", "observed_count": len(frames(grid))}
            except Exception as exc:
                observation = {"status": "rejected", "error_type": type(exc).__name__, "error": str(exc)}
            report["advertised_n_frames_one"].append({"seed": 0, "sample_index": 0,
                                                      "difficulty": difficulty, "overrides": {"n_frames": 1},
                                                      **observation})
        # Explicitly outside the normal hollow-frame contract; no training-poison claim.
        nonframe = [[1]]
        report["validator_observation"] = {"input": nonframe, "normal_frame_domain": False,
                                            "self_check": module.self_check(deepcopy(nonframe))}
        application_cases.append({"name": "out_of_domain_single_cell", "input": nonframe,
                                  "expected": None, "expectation_type": "no semantic claim; domain-gate observation only"})
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            application_cases.append({"name": f"canonical_v{pair['variant']}_{pair['split']}_{pair['pair_index']}",
                                      "input": pair["input"], "expected": pair["output"],
                                      "expectation_type": "canonical labeled pair"})
        report["application_cases"] = application_cases
        write_json(args.out / "report.json", report)
        catalog = Catalog(root)
        described = catalog.describe(TASK_ID)
        report["catalog_rule_hash"] = described["rule_hash"]
        report["catalog_approved"] = described["approved"]
        applied = catalog.apply(TASK_ID, [row["input"] for row in application_cases],
                                reference="canonical", allow_unapproved=True, timeout=120,
                                check_generator_domain=True)
        write_json(args.out / "catalog-apply.json", applied)
        report["public_apply_checks"] = []
        for case, actual in zip(application_cases, applied["results"], strict=True):
            report["public_apply_checks"].append({
                "case": case["name"], "valid_output": actual["valid_output"], "error": actual["error"],
                "generator_domain": actual.get("generator_domain"),
                "expectation_type": case["expectation_type"],
                "agrees": actual["output"] == case["expected"] if case["expected"] is not None else None,
            })
        checked = [row for row in report["public_apply_checks"] if row["agrees"] is not None]
        report["counts"] = {"size_control_draws": 9, "size_control_difficulties": 3,
                            "size_control_identical_groups": sum(row["all_three_inputs_identical"] for row in report["size_control_comparisons"]),
                            "count_search_draws": len(report["frame_count_search"]),
                            "declared_one_frame_control_checks": 3,
                            "public_racket_inputs": len(applied["results"]),
                            "checked_outputs": len(checked),
                            "checked_output_mismatches": sum(not row["agrees"] for row in checked),
                            "public_apply_errors": sum(row["error"] is not None for row in applied["results"])}
        report["findings"] = {
            "ignored_frame_h_and_frame_w": all(row["all_three_inputs_identical"] for row in report["size_control_comparisons"]),
            "explicit_n_frames_shortfall": "minimal_count_witness" in report,
            "advertised_n_frames_one_rejected_all_difficulties": all(row["status"] == "rejected" for row in report["advertised_n_frames_one"]),
            "wrong_labels_reproduced": any(not row["agrees"] for row in checked),
            "lesson_ambiguity": "not evaluated; no claim",
            "nonframe_passes_weak_self_check": report["validator_observation"]["self_check"] == [],
        }
        if applied["generator_sha256"] != source_sha or not applied["rule_hash_matches_catalog"]:
            raise ValueError("Public apply source/rule binding mismatch")
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
            raise ValueError("Audited source changed during execution")
        if any(row["error"] is not None for row in applied["results"]):
            raise ValueError("One or more public Racket applications failed; retain and inspect evidence")
        report["status"] = "completed_with_findings" if any(
            report["findings"][key] for key in ("ignored_frame_h_and_frame_w", "explicit_n_frames_shortfall")) else "completed_no_issue_reproduced"
    except Exception as exc:
        report["status"] = "blocked_or_failed"
        report["errors"].append({"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        if hasattr(exc, "run"):
            report["failed_public_apply_run"] = exc.run
    report["artifact_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in sorted(args.out.iterdir()) if path.is_file() and path.name != "report.json"}
    write_json(args.out / "report.json", report)
    print(json.dumps({"status": report["status"], "findings": report.get("findings"),
                      "counts": report.get("counts"), "report": str(args.out / "report.json"),
                      "errors": report["errors"]}, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
