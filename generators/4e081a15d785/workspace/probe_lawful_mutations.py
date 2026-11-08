"""Source-bound authoring diagnostics for generic tiny-shape lint warnings.

Uses the shared lint's exact pure helper and public Catalog.apply. No change to
the generator, shared lint, battery verdict, approval, or training admission.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from probe_compression import bootstrap, load_generator

TASK_ID = "4e081a15d785"
FAMILIES = ("singleton", "solid_2x2", "short_line")
PURE_FUNCTIONS = ("_is_grid", "_dims", "_palette", "_majority", "_minimal_impostors")


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_impostor_helper(root):
    path = next((path for path in (root / "shared/tools/generator_defect_lint.py",
                                  root / "scripts/generator_defect_lint.py") if path.is_file()), None)
    if path is None:
        raise FileNotFoundError("Selected shared generator_defect_lint.py not found")
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in PURE_FUNCTIONS]
    if {node.name for node in nodes} != set(PURE_FUNCTIONS):
        raise ValueError("Shared helper dependencies changed; review this probe")
    # Compile unmodified function ASTs, with exactly their stdlib dependency.
    namespace = {"Counter": Counter}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    extracted = {node.name: ast.get_source_segment(text, node) for node in nodes}
    return namespace["_minimal_impostors"], {
        "path": str(path), "sha256": hash_file(path),
        "execution_method": "Unmodified ASTs of five exact pure functions; Counter from stdlib",
        "extracted_functions": extracted,
    }


def declared_domain(grid):
    """Independent domain checks, not a Python output/reference implementation."""
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        return False
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        return False
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return False
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return False
    return len({value for row in grid for value in row}) >= 2


def validator_observation(module, grid):
    try:
        reasons = module.self_check(deepcopy(grid), difficulty="easy")
        if not isinstance(reasons, (list, tuple)):
            raise TypeError(f"Expected reason list, got {reasons!r}")
        return {"accepted": not reasons, "reasons": list(reasons)}
    except Exception as exc:
        return {"accepted": False, "exception": f"{type(exc).__name__}: {exc}"}


def run(output, timeout, report):
    _, find_root, normalize_grid, Catalog = bootstrap()
    root = find_root(__file__)
    module, source = load_generator(root)
    source_hash = hash_file(source)
    helper, helper_identity = exact_impostor_helper(root)
    prelude = next((path for path in (root / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
                                      root / "arc_repl/racket_prelude/arc-prelude.rkt")
                    if path.is_file()), None)
    if prelude is None:
        raise FileNotFoundError("Selected compress-grid prelude not found")
    report.update(generator_sha256=source_hash, helper=helper_identity,
                  reference_implementation={"path": str(prelude), "sha256": hash_file(prelude),
                                            "function": "compress-grid"})
    sources = []
    cases = []
    for seed in (0, 1):
        grid = normalize_grid(module.generate(seed, 0, difficulty="easy"))
        observation = validator_observation(module, grid)
        if not observation["accepted"]:
            raise ValueError(f"Source draw rejected: {observation}")
        sources.append({"seed": seed, "sample_index": 0, "difficulty": "easy", "input": grid,
                        "modal_background": Counter(c for row in grid for c in row).most_common(1)[0][0]})
        exact = dict(helper(deepcopy(grid)))
        for family in FAMILIES:
            mutated = exact[family]
            observation = validator_observation(module, mutated)
            lawful = declared_domain(mutated)
            case = {"family": family, "source_seed": seed, "input": mutated,
                    "validator": observation, "source_provable_declared_domain": lawful}
            cases.append(case)
            if not observation["accepted"] or not lawful:
                report["errors"].append({"kind": "expected_lawful_diagnostic_rejected", **case})
    input_record = {"schema": "arcpuzzles-lawful-mutation-inputs-v1", "task_id": TASK_ID,
                    "generator_sha256": source_hash, "sources": sources, "cases": cases,
                    "inputs": [case["input"] for case in cases]}
    write_new(output / "input.json", input_record)
    report["cases"] = cases
    invalids = (("ragged", [[1, 2], [1]]), ("out_of_range", [[1, 10], [1, 2]]),
                ("monochrome_training_exclusion", [[1, 1], [1, 1]]))
    report["invalid_domain_checks"] = []
    for name, grid in invalids:
        observation = validator_observation(module, grid)
        row = {"name": name, "input": grid, "validator": observation,
               "source_provable_declared_domain": declared_domain(grid),
               "reference_execution": "Not requested: negative domain check only"}
        report["invalid_domain_checks"].append(row)
        if observation["accepted"]:
            report["errors"].append({"kind": "invalid_domain_accepted", **row})
    applied = Catalog(root).apply(TASK_ID, input_record["inputs"], reference="canonical",
                                 allow_unapproved=True, timeout=timeout)
    write_new(output / "racket.json", applied)
    report["authority_identity"] = {key: applied[key] for key in (
        "generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256",
        "rule_hash_matches_catalog")}
    if applied["generator_sha256"] != source_hash or not applied["rule_hash_matches_catalog"]:
        report["errors"].append({"kind": "authority_source_or_rule_mismatch"})
    for case, result in zip(cases, applied["results"], strict=True):
        case["reference"] = result["output"]
        case["reference_valid"] = result["valid_output"]
        if not result["valid_output"] or result.get("error"):
            report["errors"].append({"kind": "authority_case_error", "family": case["family"],
                                      "source_seed": case["source_seed"], "result": result})
    if hash_file(source) != source_hash:
        report["errors"].append({"kind": "generator_changed_during_probe"})
    report["semantic_reason"] = (
        "For every valid rectangle, compress-grid removes adjacent identical full rows and full columns. "
        "Deleting a duplicate line preserves at least one representative of every line and every color, "
        "so output remains nonempty, rectangular and multicolor. Singleton, solid_2x2 and short_line "
        "geometry introduces no forbidden task feature. This is source reasoning corroborated by six "
        "actual Racket executions; it is not a Python reference-label check.")
    report["proposed_disposition"] = {
        "selfcheck_minimal_impostor": (
            "For this exact generator/rule/helper identity, attach semantic evidence for the three named "
            "accepted families. Consider a source-bound reviewed semantic disposition that preserves "
            "the detector's findings and requires renewed review when source/rule changes. Do not infer "
            "a per-task blanket exemption or invent a new shape restriction."),
        "selfcheck_power": (
            "Keep the reported 12/50 mutation rejection warning. The generic 30% target is not a "
            "semantic requirement for a broad rectangle-compression domain: geometry changes can "
            "remain lawful. Calibrate this warning using source-bound domain reasoning and actual "
            "invalid-domain rejection evidence, rather than increasing rejection of lawful inputs."),
        "battery_status": (
            "This diagnostic does not override, waive, suppress or rerun the gate. Root's reported "
            "11/12 battery result and two defect-lint warnings remain unchanged.")}


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New diagnostic directory")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be a new directory")
    args.out.mkdir(parents=True)
    commands = {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
                "packet_command": "python3 review.py run python3 generators/4e081a15d785/workspace/probe_lawful_mutations.py --out ../checks/lawful-mutations",
                "reference_method": "Public Catalog.apply; one batch of six diagnostic inputs"}
    report = {"schema": "arcpuzzles-lawful-mutation-evidence-v1", "task_id": TASK_ID,
              "errors": [], "gate_override": False}
    try:
        run(args.out, args.timeout, report)
    except Exception as exc:
        error = {"kind": "probe_error", "error": f"{type(exc).__name__}: {exc}"}
        if isinstance(getattr(exc, "run", None), dict):
            error["process_receipt"] = exc.run
        report["errors"].append(error)
    code = 2 if report["errors"] else 0
    report.update(status="ERROR" if code else "PASS", exit_code=code)
    commands["exit_code"] = code
    write_new(args.out / "evidence.json", report)
    write_new(args.out / "commands.json", commands)
    print(json.dumps({"status": report["status"], "out": str(args.out), "errors": len(report["errors"])}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
