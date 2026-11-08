#!/usr/bin/env python3
"""Reproduce lawful low-information inputs and genuine domain violations.

Run from the packet root with the selected source explicitly pinned::

    python3 run_with_racket.py python3 generators/84def340ce03/workspace/domain_probe.py \
        --expected-generator-sha256 8ea98607c8e772a16787bab201e6ce235f339d25bcf5e4f5f6c560db8b0eff61 \
        --out ../checks/domain-probe

Reference outputs come only from public Catalog.apply, in a batch below its
64-grid limit. Small expected outputs are literal independent fixtures, not
calls to generator geometry helpers or a copied Python reference transform.
This diagnostic never changes shared gate policy, labels, or source files.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[3]
TASK_ID = "84def340ce03"
RULE_HASH = "e27cc4c77443"
RULE_TEXT_SHA256 = "62c5fc046981a1b0ec964b0e241a4ba0f69f93d6c927a132e5478821259fb94c"
# Catalog.apply reports the executable callable's hash in rule_text_sha256;
# it is a different byte representation from stored program_solution.
CALLABLE_TEXT_SHA256 = "fb16aadc7df5599322f53177a8cc8425fc55732091fe5e44a4b85535f3edec9e"
sys.dont_write_bytecode = True
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]

from arcpuzzles import Catalog


def packed(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def hand_cases():
    """Fixed matrices chosen before execution; no generator sampling or retry."""
    valid = [
        {"name": "blank_2x2", "input": [[0, 0], [0, 0]],
         "expected_output": [[0, 0], [0, 0]],
         "information": "Lawful but low-information: a blank identity case."},
        {"name": "blank_4x4", "input": [[0] * 4 for _ in range(4)],
         "expected_uniform_color": 0,
         "information": "Lawful but low-information: zero is an ordinary data color."},
        {"name": "one_color_2x4", "input": [[7, 7, 7, 7], [7, 7, 7, 7]],
         "expected_output": [[7, 7, 7, 7], [7, 7, 7, 7],
                             [7, 7, 7, 7], [7, 7, 7, 7]],
         "information": "Lawful but low-information: no contrast between quadrants."},
        {"name": "singleton_4x4", "input": [[0, 0, 0, 0], [0, 0, 0, 0],
                                               [0, 0, 5, 0], [0, 0, 0, 0]],
         "information": "Lawful sparse input; its instructional value depends on the lesson."},
        {"name": "solid_2x2_within_4x4", "input": [[0, 0, 0, 0], [0, 5, 5, 0],
                                                       [0, 5, 5, 0], [0, 0, 0, 0]],
         "information": "Lawful simple shape; simplicity does not make the input invalid."},
        {"name": "short_line_4x4", "input": [[0, 0, 0, 0], [0, 0, 0, 0],
                                                [0, 4, 4, 4], [0, 0, 0, 0]],
         "information": "Lawful simple shape; may be low-information in isolation."},
        {"name": "arbitrary_permuted_colors_4x6",
         "input": [[9, 0, 3, 8, 4, 1], [2, 7, 5, 6, 0, 9],
                   [1, 4, 8, 3, 7, 2], [6, 5, 9, 0, 2, 8]],
         "information": "Lawful arbitrary arrangement; no object grammar is required."},
        {"name": "four_quadrant_identity_2x2", "input": [[0, 9], [4, 7]],
         "expected_output": [[0, 9], [4, 7]],
         "information": "Lawful but low-information about nesting: one tile gives identity."},
        {"name": "two_tiles_four_quadrants_2x4",
         "input": [[1, 2, 5, 6], [3, 4, 7, 8]],
         "expected_output": [[5, 5, 6, 6], [5, 1, 2, 6],
                             [7, 3, 4, 8], [7, 7, 8, 8]],
         "information": "Literal witness for tile order and all four quadrant positions."},
        {"name": "two_tiles_four_colors_2x4",
         "input": [[1, 2, 3, 4], [3, 4, 1, 2]],
         "expected_output": [[3, 3, 4, 4], [3, 1, 2, 4],
                             [1, 3, 4, 2], [1, 1, 2, 2]],
         "information": "Literal four-color routing witness with different inner and outer tiles."},
        {"name": "max_bound_2x30",
         "input": [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] * 3,
                   [9, 8, 7, 6, 5, 4, 3, 2, 1, 0] * 3],
         "expected_output_shape": [30, 30],
         "information": "Lawful wide boundary fixture; 60 input cells yield side 30."},
        {"name": "max_bound_30x2", "input": [[9, 4] for _ in range(30)],
         "expected_output_shape": [30, 30],
         "information": "Lawful tall boundary fixture with repeated tiles; not a diversity claim."},
    ]
    invalid = [
        {"name": "odd_height", "input": [[0, 1], [2, 3], [4, 5]],
         "reason": "Height is odd."},
        {"name": "odd_width", "input": [[0, 1, 2], [3, 4, 5]],
         "reason": "Width is odd."},
        {"name": "ragged", "input": [[0, 1], [2]],
         "reason": "Rows have unequal lengths."},
        {"name": "boolean_color", "input": [[0, 1], [2, True]],
         "reason": "Boolean pixels are not plain integer colors."},
        {"name": "color_10", "input": [[0, 1], [2, 10]],
         "reason": "Color exceeds 9."},
        {"name": "float_color", "input": [[0, 1], [2, 3.0]],
         "reason": "Floating-point pixels are not plain integers."},
        {"name": "output_overflow_8x8", "input": [[0] * 8 for _ in range(8)],
         "reason": "64 input cells would require output side 32, outside the ARC bound."},
        {"name": "empty_grid", "input": [], "reason": "A grid must be nonempty."},
    ]
    return valid, invalid


def inspect_validator(module, case, expected_acceptance):
    original = copy.deepcopy(case["input"])
    candidate = copy.deepcopy(original)
    result = {"name": case["name"], "input_sha256": sha(packed(original)),
              "expected_acceptance": expected_acceptance}
    try:
        errors = module.self_check(candidate)
        result.update(diagnostics=errors, accepted=not bool(errors), exception=None,
                      input_unchanged=packed(candidate) == packed(original))
        result["passed"] = (isinstance(errors, list)
                            and all(isinstance(error, str) and error for error in errors)
                            and result["accepted"] == expected_acceptance
                            and result["input_unchanged"])
    except Exception as exc:
        result.update(passed=False, accepted=None, exception=f"{type(exc).__name__}: {exc}")
    return result


def run(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    generator_path = REPO / "generators" / TASK_ID / "generator.py"
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    source_hash = sha(generator_path.read_bytes())
    if source_hash != args.expected_generator_sha256:
        raise ValueError("Generator differs from the explicitly requested frozen source")
    canonical_bytes = canonical_path.read_bytes()
    canonical_hash = sha(canonical_bytes)
    canonical_locations = []
    for line_number, line in enumerate(canonical_bytes.splitlines(), 1):
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        source = row["program_solution"]
        if sha(source.encode()) != RULE_TEXT_SHA256 or sha(" ".join(source.split()).encode())[:12] != RULE_HASH:
            raise ValueError("Selected canonical source differs from the pinned rule")
        canonical_locations.append(f"shared/data/canonical/puzzles.jsonl:{line_number}")
    if not canonical_locations:
        raise ValueError("Selected canonical source is missing")
    probe_hash = sha(SCRIPT.read_bytes())
    spec = importlib.util.spec_from_file_location("task_domain_probe_generator", generator_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if module.TASK_ID != TASK_ID or module.RULE_HASH != RULE_HASH:
        raise ValueError("Generator task/rule binding is unexpected")
    valid, invalid = hand_cases()
    fixtures = [{"name": name, "input": grid}
                for name, grid in module.mutation_fixtures()]
    if not fixtures:
        raise ValueError("No public mutation_fixtures were declared")
    identity = {
        "schema": "84def340ce03-domain-probe-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "probe_sha256": probe_hash,
        "canonical_file_sha256": canonical_hash, "canonical_rule_hash": RULE_HASH,
        "canonical_program_solution_exact_sha256": RULE_TEXT_SHA256,
        "canonical_locations": canonical_locations,
        "public_apply_callable_text_sha256": CALLABLE_TEXT_SHA256,
        "hash_scope_note": "The stored program_solution and public apply's rule_callable_text have distinct exact byte hashes. The latter is reported as rule_text_sha256 by Catalog.apply; executed_rule_hash binds normalized stored source.",
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "sampling": "Fixed hand matrices plus the generator's public mutation_fixtures; no random draws, retries, selection, or replacements.",
        "domain": "Every nonempty rectangular grid with even dimensions 2..30, area <= 60, and plain integer colors 0..9 is lawful.",
        "domain_reason": "An even input has h*w/4 complete 2x2 tiles. The canonical rule routes their pixels to an output of side h*w/2. Each referenced row/column stays within its source tile; no pixel-value or object-shape precondition is needed. The area bound limits output side to 30.",
        "oracle": "Public arcpuzzles.Catalog.apply(TASK_ID, valid_grids, reference='canonical', timeout=120); no private runner imports.",
        "limitations": "Finite witnesses establish these cases and literal expectations, not universal execution equivalence or teaching adequacy. Invalid cases test self_check only; they are not sent to Racket. The output bound is a task domain constraint, not a claim that Racket itself cannot allocate a larger output.",
    }
    save(out / "plan.json", identity)
    save(out / "cases.json", {"valid": valid, "invalid": invalid,
                              "declared_mutation_fixtures": fixtures})
    save(out / "inputs.json", {"inputs": [case["input"] for case in valid]})
    positive = [inspect_validator(module, case, True) for case in valid]
    negative = [inspect_validator(module, case, False) for case in invalid]
    declared = [inspect_validator(module, case, False) for case in fixtures]
    for case, record in zip(valid, positive, strict=True):
        record["information"] = case["information"]
        record["strict_canonical_like_diagnostics"] = module.strict_canonical_like(copy.deepcopy(case["input"]))

    if len(valid) > 64:
        raise ValueError("Public apply batch exceeds 64 grids")
    applied = Catalog(REPO).apply(TASK_ID, [case["input"] for case in valid],
                                  reference="canonical", timeout=120)
    save(out / "racket.json", applied)
    if (applied["generator_sha256"] != source_hash
            or applied["executed_rule_hash"] != RULE_HASH
            or applied["rule_text_sha256"] != CALLABLE_TEXT_SHA256
            or not applied["rule_hash_matches_catalog"]):
        raise RuntimeError("Public apply source/rule provenance differs from the frozen plan")
    reference_checks = []
    for index, (case, answer) in enumerate(zip(valid, applied["results"], strict=True)):
        grid, output = case["input"], answer.get("output")
        expected_side = len(grid) * len(grid[0]) // 2
        shape = case.get("expected_output_shape", [expected_side, expected_side])
        shape_ok = (isinstance(output, list) and len(output) == shape[0]
                    and all(isinstance(row, list) and len(row) == shape[1] for row in output))
        checks = {"input_hash_matches": answer["input_sha256"] == sha(packed(grid)),
                  "output_present_and_expected_shape": shape_ok}
        if shape_ok:
            colors = {pixel for row in grid for pixel in row}
            checks["output_uses_only_input_colors"] = all(type(pixel) is int and pixel in colors
                                                          for row in output for pixel in row)
        if "expected_output" in case:
            checks["matches_independent_literal_output"] = output == case["expected_output"]
        if "expected_uniform_color" in case:
            checks["matches_uniform_color_expectation"] = bool(shape_ok) and all(
                pixel == case["expected_uniform_color"] for row in output for pixel in row)
        reference_checks.append({"name": case["name"], "reference_result_index": index,
                                 "expected_output_shape": shape, "checks": checks,
                                 "output_sha256": sha(packed(output)), "passed": all(checks.values())})

    unchanged = (sha(generator_path.read_bytes()) == source_hash
                 and sha(canonical_path.read_bytes()) == canonical_hash
                 and sha(SCRIPT.read_bytes()) == probe_hash)
    passed = unchanged and all(row["passed"] for rows in (positive, negative, declared, reference_checks)
                               for row in rows)
    report = {**identity, "status": "PASS" if passed else "FAIL",
              "finished_utc": datetime.now(timezone.utc).isoformat(),
              "sources_unchanged_throughout_probe": unchanged,
              "counts": {"lawful_hand_cases_accepted": sum(row.get("accepted") is True for row in positive),
                         "lawful_hand_cases_total": len(positive),
                         "reference_cases_passed": sum(row["passed"] for row in reference_checks),
                         "reference_cases_total": len(reference_checks),
                         "literal_output_cases_passed": sum(row["checks"].get("matches_independent_literal_output") is True for row in reference_checks),
                         "literal_output_cases_total": sum("expected_output" in case for case in valid),
                         "invalid_hand_cases_rejected": sum(row.get("accepted") is False for row in negative),
                         "invalid_hand_cases_total": len(negative),
                         "declared_fixtures_rejected": sum(row.get("accepted") is False for row in declared),
                         "declared_fixtures_total": len(declared)},
              "counting_note": "Hand invalid cases and declared fixtures overlap; their totals are reported separately and must not be added as independent coverage.",
              "lawful_cases": positive, "invalid_cases": negative,
              "declared_mutation_fixtures": declared, "reference_checks": reference_checks,
              "evidence": {"cases": "cases.json", "reference_inputs": "inputs.json",
                           "reference_outputs_and_public_provenance": "racket.json"}}
    save(out / "report.json", report)
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "generator_sha256": source_hash, "report": str(out / "report.json")}))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory")
    parser.add_argument("--expected-generator-sha256", required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must name a new evidence directory")
    try:
        return run(args)
    except Exception as exc:
        if args.out.is_dir() and not (args.out / "failure.json").exists():
            save(args.out / "failure.json", {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}",
                                            "traceback": traceback.format_exc()})
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
