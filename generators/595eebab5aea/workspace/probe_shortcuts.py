"""Prepare a declared-rival witness, then verify a separately executed Racket receipt.

Run through run_with_racket.py so the public reviewer helpers are importable.
Every source and artifact path is explicit. This script never creates reference
labels: all Python-produced output grids are declared rival predictions.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, normalize_grid

TASK_ID = "595eebab5aea"
DECLARATIONS = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_value(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def shape(grid):
    return {"rows": len(grid), "columns": len(grid[0])}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def load_subject(args):
    source = args.generator.resolve()
    root = find_root(source)
    source_hash = sha_file(source)
    require(source_hash == args.expect_source_sha256, "Current generator differs from the supplied source pin")
    spec = importlib.util.spec_from_file_location("probe_595eebab5aea_subject", source)
    require(spec is not None and spec.loader is not None, "Cannot import the explicit generator source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(sha_file(source) == source_hash, "Generator changed during import")
    require(module.TASK_ID == TASK_ID, "Explicit generator is for another task")
    declarations = {}
    for namespace in DECLARATIONS:
        entries = getattr(module, namespace, {})
        require(isinstance(entries, dict), f"{namespace} must be a dictionary")
        require(all(isinstance(name, str) and callable(fn) for name, fn in entries.items()),
                f"{namespace} contains an invalid declaration")
        declarations[namespace] = entries
    require("left_align" in declarations["CANONICAL_SHORTCUTS"], "No declared canonical left_align shortcut")
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    require(bool(pairs), "No labeled canonical pairs")
    binding = {"task_id": TASK_ID, "generator_sha256": source_hash,
               "generator_path": str(source.relative_to(root)),
               "declared_rule_hash": getattr(module, "RULE_HASH", None),
               "probe_sha256": sha_file(__file__), "canonical_pairs_sha256": sha_value(pairs),
               "canonical_pair_count": len(pairs),
               "canonical_pairs": [{"variant": p["variant"], "split": p["split"],
                                    "pair_index": p["pair_index"], "input_dimensions": shape(p["input"]),
                                    "output_dimensions": shape(p["output"])} for p in pairs]}
    return module, declarations, pairs, binding


def prediction(fn, grid):
    return normalize_grid(fn(deepcopy(grid)))


def canonical_scores(declarations, pairs):
    return {namespace: {name: {"matches": (matches := [prediction(fn, p["input"]) == p["output"]
                                                        for p in pairs]),
                              "matching_pairs": sum(matches), "total_pairs": len(pairs),
                              "fits_all": all(matches)}
                        for name, fn in entries.items()}
            for namespace, entries in declarations.items()}


def differences(reference, rival):
    cells = []
    for r in range(max(len(reference), len(rival))):
        for c in range(max(len(reference[0]), len(rival[0]))):
            actual = reference[r][c] if r < len(reference) and c < len(reference[0]) else None
            other = rival[r][c] if r < len(rival) and c < len(rival[0]) else None
            if actual != other:
                cells.append({"row": r, "column": c, "reference": actual, "rival": other})
    return cells


def prepare(args):
    module, declarations, pairs, binding = load_subject(args)
    grid = normalize_grid(module.generate(args.seed, args.sample_index, difficulty=args.difficulty))
    errors = list(module.self_check(deepcopy(grid), difficulty=args.difficulty) or [])
    rival = prediction(declarations["CANONICAL_SHORTCUTS"]["left_align"], grid)
    scores = canonical_scores(declarations, pairs)
    report = {"schema": "arcpuzzles-shortcut-witness-prepare-v1", "status": "prepared_pending_racket",
              **binding, "replay": {"seed": args.seed, "sample_index": args.sample_index,
                                     "difficulty": args.difficulty, "overrides": {}},
              "input_sha256": sha_value(grid), "input_dimensions": shape(grid),
              "left_align_sha256": sha_value(rival), "left_align_dimensions": shape(rival),
              "self_check": errors, "canonical_fit": scores,
              "note": "The saved output grid is a declared rival prediction; no reference output was computed in Python."}
    if callable(getattr(module, "schedule_profile", None)):
        report["schedule_profile"] = module.schedule_profile(args.seed, args.sample_index, args.difficulty)
    if callable(getattr(module, "observe_overrides", None)):
        report["observed_axes"] = module.observe_overrides(deepcopy(grid))
    report["canonical_shortcuts_all_fit"] = all(row["fits_all"] for row in scores["CANONICAL_SHORTCUTS"].values())
    if errors or not report["canonical_shortcuts_all_fit"]:
        report["status"] = "preparation_findings"
    require(sha_file(args.generator) == binding["generator_sha256"], "Generator changed during preparation")
    write(args.input, grid)
    write(args.rival_output, rival)
    write(args.out, report)
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "canonical_pair_count",
                      "input_dimensions", "left_align_dimensions", "self_check", "canonical_shortcuts_all_fit")}))
    return 0 if report["status"] == "prepared_pending_racket" else 1


def verify(args):
    module, declarations, pairs, binding = load_subject(args)
    prepared, receipt = read(args.prepared), read(args.receipt)
    grid, saved_rival = normalize_grid(read(args.input)), normalize_grid(read(args.rival_output))
    require(prepared["generator_sha256"] == binding["generator_sha256"] == receipt["generator_sha256"],
            "Preparation, current generator, and Racket receipt have different source hashes")
    require(prepared["canonical_pairs_sha256"] == binding["canonical_pairs_sha256"], "Canonical pairs changed")
    require(prepared["input_sha256"] == sha_value(grid), "Prepared input changed")
    require(prepared["left_align_sha256"] == sha_value(saved_rival), "Saved rival output changed")
    require(receipt.get("schema") == "arcpuzzles-apply-v1" and receipt.get("task_id") == TASK_ID,
            "Expected a supported apply receipt for this task")
    require(receipt.get("reference") == "canonical" and receipt.get("rule_hash_matches_catalog") is True,
            "Reference execution did not match the selected canonical authority")
    require(receipt["executed_rule_hash"] == binding["declared_rule_hash"], "Declared and executed rules differ")
    require(len(receipt["results"]) == 1, "Expected exactly one reference input")
    result = receipt["results"][0]
    require(result["input"] == grid, "Racket receipt describes another input")
    require(result.get("valid_output") is True and result.get("error") is None, "Invalid reference execution")
    require(result.get("generator_domain") == {"status": "valid", "errors": []}, "Reference domain check was not valid")
    output = normalize_grid(result["output"])
    scores = canonical_scores(declarations, pairs)
    require(scores == prepared["canonical_fit"], "Declared rival fits changed after preparation")
    comparisons = {}
    for namespace, entries in declarations.items():
        comparisons[namespace] = {}
        for name, fn in entries.items():
            rival = prediction(fn, grid)
            changed = differences(output, rival)
            comparisons[namespace][name] = {"matches_reference": rival == output,
                "output_dimensions": shape(rival), "output_sha256": sha_value(rival),
                "differing_cell_count": len(changed), "first_difference": changed[0] if changed else None}
    left = prediction(declarations["CANONICAL_SHORTCUTS"]["left_align"], grid)
    require(left == saved_rival, "Declared left_align prediction changed")
    require(scores["CANONICAL_SHORTCUTS"]["left_align"]["fits_all"], "left_align is not a canonical-fitting shortcut")
    require(left != output, "Input does not distinguish the declared left_align shortcut")
    require(not module.self_check(deepcopy(grid), difficulty=prepared["replay"]["difficulty"]), "Current validator rejects input")
    report = {"schema": "arcpuzzles-shortcut-witness-report-v1", "status": "verified_centering_witness", **binding,
              "replay": prepared["replay"], "schedule_profile": prepared.get("schedule_profile"),
              "input_dimensions": shape(grid), "reference_output_dimensions": shape(output),
              "rival_output_dimensions": shape(left), "input_sha256": sha_value(grid),
              "reference_output_sha256": sha_value(output), "rival_output_sha256": sha_value(left),
              "executed_rule_hash": receipt["executed_rule_hash"], "executed_rule_text_sha256": receipt["rule_text_sha256"],
              "generator_domain": result["generator_domain"], "canonical_fit": scores,
              "declared_rival_comparisons": comparisons, "left_align_differences": differences(output, left),
              "reference_receipt_sha256": sha_file(args.receipt),
              "reference_command": receipt.get("command"), "reference_cwd": receipt.get("cwd"),
              "limits": "One fixed generated input; all declared rivals are compared. No lesson coverage or universal-identifiability claim."}
    counterexample = {"schema": "arcpuzzles-centering-witness-v1", "task_id": TASK_ID,
        "status": report["status"], "generator_sha256": binding["generator_sha256"],
        "rule_hash": receipt["executed_rule_hash"], "rule_text_sha256": receipt["rule_text_sha256"],
        "replay": prepared["replay"], "input": grid, "racket_output": output,
        "rival_name": "CANONICAL_SHORTCUTS.left_align", "rival_output": left,
        "input_dimensions": shape(grid), "output_dimensions": shape(output), "rival_dimensions": shape(left),
        "canonical_rival_fit": scores["CANONICAL_SHORTCUTS"]["left_align"],
        "differing_cells": differences(output, left), "generator_domain": result["generator_domain"],
        "reference_receipt_sha256": report["reference_receipt_sha256"],
        "reference_command": report["reference_command"], "reference_cwd": report["reference_cwd"]}
    require(sha_file(args.generator) == binding["generator_sha256"], "Generator changed during verification")
    write(args.out, report)
    write(args.counterexample, counterexample)
    print(json.dumps({"status": report["status"], "generator_sha256": binding["generator_sha256"],
                      "canonical_pair_count": len(pairs), "left_align_differing_cells": len(report["left_align_differences"]),
                      "declaration_counts": {name: len(entries) for name, entries in declarations.items()},
                      "input_dimensions": shape(grid), "reference_output_dimensions": shape(output)}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="phase", required=True)
    for name in ("prepare", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--generator", type=Path, required=True, help="explicit selected generator file")
        p.add_argument("--expect-source-sha256", required=True)
        p.add_argument("--input", type=Path, required=True)
        p.add_argument("--rival-output", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True, help="new report path; existing files are preserved")
        if name == "prepare":
            p.add_argument("--seed", type=int, default=0)
            p.add_argument("--sample-index", type=int, default=1)
            p.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
        else:
            p.add_argument("--prepared", type=Path, required=True)
            p.add_argument("--receipt", type=Path, required=True)
            p.add_argument("--counterexample", type=Path, required=True)
    args = parser.parse_args()
    outputs = (args.input, args.rival_output, args.out) if args.phase == "prepare" else (args.out, args.counterexample)
    require(len({p.resolve() for p in outputs}) == len(outputs), "Output paths must be distinct")
    require(not any(p.exists() for p in outputs), "An output already exists; use new paths to preserve earlier evidence")
    try:
        return prepare(args) if args.phase == "prepare" else verify(args)
    except Exception as exc:
        if not args.out.exists():
            write(args.out, {"schema": "arcpuzzles-shortcut-probe-error-v1", "status": "error",
                             "phase": args.phase, "error_type": type(exc).__name__, "error": str(exc)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
