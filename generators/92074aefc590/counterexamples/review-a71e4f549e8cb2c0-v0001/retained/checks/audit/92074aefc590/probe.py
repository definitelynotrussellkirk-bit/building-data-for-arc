#!/usr/bin/env python3
"""Bounded, findings-only audit for 92074aefc590.

Run prepare/report through the packet's run_with_racket.py wrapper. Obtain
reference outputs between those steps using the public arcpuzzles apply CLI.
This file never imports a Racket runner or modifies target/shared source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
TASK = "92074aefc590"
HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
GENERATOR = REPO / "generators" / TASK / "generator.py"
PREFIX = f"checks/audit/{TASK}"
SEED = 17


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def write_json(name, value):
    path = HERE / name
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n")


def load_target():
    spec = importlib.util.spec_from_file_location(f"audit_target_{TASK}", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_identity(module):
    rows = []
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    assert len(rows) == 1, "Reassess this audit if canonical variants change"
    rule = rows[0]["program_solution"]
    return {
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_path": f"repo/generators/{TASK}/generator.py",
        "generator_sha256": digest(GENERATOR.read_bytes()),
        "rule_source": "repo/shared/data/canonical/puzzles.jsonl:program_solution",
        "rule_sha256": digest(rule.encode()),
        "canonical_row_sha256": digest(rows[0]),
        "phase": "final_unchanged_audit_source",
    }


def frames(grid):
    """Independent ordinary monochromatic 4-connected frame detector."""
    height, width = len(grid), len(grid[0])
    seen, found = set(), []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if not color or (row, col) in seen:
                continue
            stack, cells = [(row, col)], []
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
            c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
            h, w = r2-r1+1, c2-c1+1
            if (h >= 3 and w >= 3 and len(cells) == 2*h+2*w-4
                    and all(r in (r1, r2) or c in (c1, c2) for r, c in cells)):
                found.append({"bbox": [r1, c1, r2, c2], "color": color,
                              "cells": cells})
    return found


def contents(grid, frame):
    r1, c1, r2, c2 = frame["bbox"]
    cells = [(r, c) for r in range(r1+1, r2) for c in range(c1+1, c2)
             if grid[r][c] != 0]
    if not cells:
        return [[0]]
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right+1] for row in grid[top:bottom+1]]


def transform(grid, *, swap_extremes=False):
    """Expected full reversal, or the explicitly labelled audit rival."""
    found = frames(grid)
    shapes = [contents(grid, frame) for frame in found]
    if swap_extremes:
        if len(shapes) >= 2:
            shapes[0], shapes[-1] = shapes[-1], shapes[0]
    else:
        shapes.reverse()
    output = [[0] * len(grid[0]) for _ in grid]
    for frame in found:
        for r, c in frame["cells"]:
            output[r][c] = frame["color"]
    for frame, shape in zip(found, shapes):
        r1, c1, r2, c2 = frame["bbox"]
        top = r1+1 + (r2-r1-1-len(shape))//2
        left = c1+1 + (c2-c1-1-len(shape[0]))//2
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value:
                    output[top+r][left+c] = value
    return output


def four_frame_witness():
    grid = [[0] * 13 for _ in range(13)]
    # Same quadrant geometry, moat, sizes, color policy and shape vocabulary as
    # the generator. Only K=4 differs from its summary's K=2..3 restriction.
    for index, (r0, c0) in enumerate(((0, 0), (0, 7), (7, 0), (7, 7))):
        border, content = index+1, index+5
        for d in range(5):
            grid[r0][c0+d] = grid[r0+4][c0+d] = border
            grid[r0+d][c0] = grid[r0+d][c0+4] = border
        for dr, dc in ((0, 0), (0, 1), (1, 0)):
            grid[r0+1+dr][c0+1+dc] = content
    return grid


def prepare():
    from reviewer_support import canonical_pairs

    module = load_target()
    identity = source_identity(module)
    cases = []
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(4):
            grid = module.generate(SEED, sample_index, difficulty=difficulty)
            cases.append({
                "name": f"generated_{difficulty}_{sample_index}",
                "kind": "generated", "seed": SEED,
                "sample_index": sample_index, "difficulty": difficulty,
                "overrides": {}, "input": grid,
                "validator_errors": module.self_check(grid, difficulty=difficulty),
                "documented_generator_domain": True,
            })
    for pair in canonical_pairs(TASK, root=REPO):
        cases.append({
            "name": f"canonical_{pair['variant']}_{pair['split']}_{pair['pair_index']}",
            "kind": "canonical", "input": pair["input"],
            "canonical_expected": pair["output"],
            "canonical_identity": {key: pair[key] for key in
                                   ("variant", "split", "pair_index")},
            "validator_errors": module.self_check(pair["input"]),
            "documented_generator_domain": False,
            "domain_reason": "Canonical geometry includes frame sides below 5 and/or contents above the generated 2x2 bound.",
        })
    witness = four_frame_witness()
    cases.append({
        "name": "four_frame_swap_extremes_witness", "kind": "constructed",
        "input": witness, "seed": None, "sample_index": None, "overrides": None,
        "validator_errors": module.self_check(witness),
        "documented_generator_domain": False,
        "domain_reason": "K=4 is outside SUMMARY K=2..3 and unreachable through generate; AXES nevertheless declares n=2..5. All other stated frame/content invariants hold.",
    })
    baseline = module.generate(SEED, 0, difficulty="medium")
    override_results = []
    overrides_to_check = [
        {"n": 2}, {"n": 4}, {"n": 5},
        {"n_distinct_colors": 2}, {"n_distinct_colors": 5},
        {"palette_size": 2}, {"palette_size": 5},
        {"palette_kind": "warm"}, {"texture": "cool"},
        {"grid_h": 7}, {"grid_w": 9},
    ]
    for overrides in overrides_to_check:
        record = {"seed": SEED, "sample_index": 0, "difficulty": "medium",
                  "overrides": overrides,
                  "declared_axes": {k: module.AXES[k] for k in overrides}}
        try:
            grid = module.generate(SEED, 0, difficulty="medium", **overrides)
            record.update({
                "status": "returned", "input_sha256": digest(grid),
                "same_as_baseline": grid == baseline,
                "frame_count": len(frames(grid)),
                "distinct_nonzero_colors": len({v for row in grid for v in row}-{0}),
                "validator_errors": module.self_check(grid, difficulty="medium"),
                "grid_evidence_case": "generated_medium_0" if grid == baseline else None,
            })
            if grid != baseline:
                record["input"] = grid
        except Exception as error:
            record.update({"status": "error", "exception_type": type(error).__name__,
                           "message": str(error)})
        override_results.append(record)
    # Inspect the actual declarations. Do not invent a claimed task contract.
    declarations = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        value = getattr(module, namespace, None)
        declarations[namespace] = {"present": value is not None,
                                   "names": list(value) if isinstance(value, dict) else []}
        assert value is None, "A new declared rival contract needs a fresh audit"
    write_json("input.json", [case["input"] for case in cases])
    write_json("prepared.json", {"source": identity, "cases": cases,
                                 "override_results": override_results,
                                 "actual_rival_declarations": declarations})
    print(json.dumps({"status": "prepared", "source": identity,
                      "racket_input_count": len(cases),
                      "generated_attempts": 16, "override_attempts": len(override_results)}))


def report():
    prepared = json.loads((HERE / "prepared.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    identity = source_identity(load_target())
    assert identity == prepared["source"], "Source changed between prepare and report"
    assert racket["generator_sha256"] == identity["generator_sha256"]
    assert racket["task_id"] == TASK and racket["rule_hash_matches_catalog"]
    # Public apply's receipt is authoritative for actual Racket outputs.
    records = racket.get("results", racket.get("cases", []))
    if not records:
        raise ValueError(f"Unrecognized public apply receipt keys: {list(racket)}")
    cases = prepared["cases"]
    assert len(records) == len(cases)
    results = []
    failures = []
    counterexamples = []
    for case, actual_record in zip(cases, records):
        assert actual_record["valid_output"] and not actual_record["error"], actual_record
        actual = actual_record.get("output", actual_record.get("actual_output"))
        if actual is None:
            raise ValueError(f"Missing actual output: {actual_record}")
        expected = transform(case["input"])
        rival = transform(case["input"], swap_extremes=True)
        result = {key: value for key, value in case.items()
                  if key not in ("input", "canonical_expected")}
        result.update({"input_sha256": digest(case["input"]),
                       "actual_output_sha256": digest(actual),
                       "frame_count": len(frames(case["input"])),
                       "expected_matches_racket": expected == actual,
                       "swap_extremes_matches_racket": rival == actual})
        if "canonical_expected" in case:
            result["canonical_matches_racket"] = case["canonical_expected"] == actual
            result["swap_extremes_matches_canonical"] = rival == case["canonical_expected"]
        if expected != actual or result.get("canonical_matches_racket") is False:
            failures.append({"case": case, "actual": actual, "expected": expected})
        results.append(result)
        if case["name"] in ("generated_medium_0", "four_frame_swap_extremes_witness"):
            counterexamples.append({**case, "actual_racket_output": actual,
                                    "expected_full_reversal": expected,
                                    "rival_swap_extremes_output": rival,
                                    "difference_cells": [[r, c] for r in range(len(actual))
                                                         for c in range(len(actual[0]))
                                                         if rival[r][c] != actual[r][c]]})
    generated = [result for result in results if result["kind"] == "generated"]
    canonical = [result for result in results if result["kind"] == "canonical"]
    commands = [
        {"cwd": "packet_root", "effective_cwd": "repo",
         "argv": ["python3", "run_with_racket.py", "python3", f"../{PREFIX}/probe.py", "prepare"],
         "exit_code": 0, "evidence_paths": [f"{PREFIX}/prepared.json", f"{PREFIX}/input.json", f"{PREFIX}/prepare.log"]},
        {"cwd": "packet_root", "effective_cwd": "repo",
         "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                  "--input", f"../{PREFIX}/input.json", "--out", f"../{PREFIX}/racket.json"],
         "exit_code": 0, "evidence_paths": [f"{PREFIX}/racket.json", f"{PREFIX}/apply.log"]},
        {"cwd": "packet_root", "effective_cwd": "repo",
         "argv": ["python3", "run_with_racket.py", "python3", f"../{PREFIX}/probe.py", "report"],
         "exit_code": 0, "evidence_paths": [f"{PREFIX}/evidence.json", f"{PREFIX}/report.log"]},
    ]
    evidence = {
        "source": identity, "scope": "findings_only_no_target_or_rule_changes",
        "reference_execution": {key: racket[key] for key in
                                ("schema", "task_id", "reference", "rule_file",
                                 "executed_rule_hash", "catalog_rule_hash",
                                 "rule_hash_matches_catalog", "rule_text_sha256",
                                 "generator_sha256", "command", "cwd")},
        "actual_rival_declarations": prepared["actual_rival_declarations"],
        "audit_rival": {"name": "swap_extremes", "declared_by_generator": False,
                        "definition": "Detect/crop/recenter contents normally, but swap only the first and last frame contents; recenter middle contents in place.",
                        "reason_for_probe": "Reversing a list of length 2 or 3 is exactly an endpoint swap. Four frames distinguish the policies."},
        "counts": {
            "source_phase": "final_unchanged_audit_source",
            "generated_seed": SEED, "generated_sample_indices": [0, 1, 2, 3],
            "generated_difficulties": [None, "easy", "medium", "hard"],
            "generated_attempts": len(generated),
            "generated_unique_inputs": len({result["input_sha256"] for result in generated}),
            "generated_expected_matches_racket": sum(result["expected_matches_racket"] for result in generated),
            "generated_swap_extremes_matches_racket": sum(result["swap_extremes_matches_racket"] for result in generated),
            "canonical_pairs": len(canonical),
            "canonical_swap_extremes_matches": sum(result["swap_extremes_matches_canonical"] for result in canonical),
            "racket_inputs": len(results),
            "racket_unique_inputs": len({result["input_sha256"] for result in results}),
            "override_attempts": len(prepared["override_results"]),
        },
        "findings": [
            {"id": "A920-F1", "category": "reproduced_defect",
             "summary": "Declared n, color-count and palette controls are silently ignored; declared lower size bounds are rejected.",
             "expected": {"n=4": "four frames", "n=5": "five frames",
                          "n_distinct_colors=2": "two distinct nonzero colors",
                          "grid_h=7": "accepted within declared AXES valid range"},
             "actual": "n=4/n=5/n_distinct_colors=2 return baseline with 2 frames and 4 nonzero colors; grid_h=7 raises outside [11,14].",
             "counterexample": "generated_medium_0"},
            {"id": "A920-F2", "category": "domain_question_and_proven_population_equivalence",
             "summary": "The K=2..3 population cannot distinguish full reversal from swapping only endpoint contents.",
             "canonical_fit": "All usable canonical pairs checked; finite results recorded below.",
             "witness": "four_frame_swap_extremes_witness",
             "limitation": "The four-frame witness passes self_check but is outside SUMMARY K=2..3. This is not a claim of an incorrect in-domain Racket label or measured production-lesson ambiguity."},
        ],
        "override_results": prepared["override_results"],
        "results": results, "counterexamples": counterexamples,
        "failures": failures, "verification_commands": commands,
        "limits": "One seed; four indices in each of four bands; no exhaustive override matrix, production lesson assembly, cyclic lesson audit, or four-frame generation claim. No declared rival/lesson contract exists in this source."
    }
    commands[-1]["exit_code"] = int(bool(failures))
    write_json("evidence.json", evidence)
    print(json.dumps({"status": "complete" if not failures else "failed",
                      "counts": evidence["counts"], "unexpected_semantic_failures": len(failures),
                      "four_frame_difference_cells": counterexamples[-1]["difference_cells"]}))
    return bool(failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "report"))
    args = parser.parse_args()
    raise SystemExit(prepare() if args.stage == "prepare" else report())
