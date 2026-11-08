#!/usr/bin/env python3
"""Replay generic mutations while testing the mirror completion domain.

prepare captures exact shared-helper mutations and validator decisions. verify
labels only accepted lawful inputs through public Catalog.apply. This diagnostic
does not change, exempt, or waive any existing gate. Run verify through the
packet's review.py run wrapper. The adjacent mirror probe is a local dependency.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types


TASK_ID = "f8b3586f1d58"


def domain_reasons(grid, mirror):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["expected nonempty integer row arrays"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["expected rectangular row arrays"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["expected integer colors 0..9, excluding booleans"]
    output = mirror(grid)
    if any(value and output[r][c] != value for r, row in enumerate(grid) for c, value in enumerate(row)):
        return ["mirror execution changes an original pigment: outside completion grammar"]
    if output != [list(reversed(row)) for row in output]:
        return ["mirror execution does not produce symmetric completion"]
    return []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_digest(grid):
    return digest(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())


def extract_actual(path, names, globals_extra=None):
    """Execute unchanged selected AST bodies, avoiding legacy-layout imports."""
    source = path.read_text()
    selected = []
    for node in ast.parse(source).body:
        declared = {node.name} if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else set()
        if isinstance(node, ast.Assign):
            declared = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if declared.intersection(names):
            selected.append(node)
    found = {node.name for node in selected if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    found.update(target.id for node in selected if isinstance(node, ast.Assign)
                 for target in node.targets if isinstance(target, ast.Name))
    if set(names) - found:
        raise ValueError(f"Missing actual helper declarations: {set(names) - found}")
    module = types.ModuleType("validator_contract_" + path.stem)
    module.__dict__.update(globals_extra or {})
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), module.__dict__)
    segments = "\n\n".join(ast.get_source_segment(source, node) for node in selected)
    info = {"path": str(path), "file_sha256": digest(path.read_bytes()),
            "selected_names": sorted(names), "selected_source_sha256": digest(segments.encode()),
            "execution": "Unchanged AST bodies from this file; no shared-source edits."}
    return module, info


def load_actual_helpers(root):
    directory = root / "shared/tools" if (root / "shared/tools").is_dir() else root / "scripts"
    generic, generic_info = extract_actual(directory / "generator_selfcheck.py",
        ("DIFFICULTIES", "Report", "_grid", "_mutations", "check_mutation_sensitivity"))
    minimal, minimal_info = extract_actual(directory / "generator_defect_lint.py",
        ("_is_grid", "_dims", "_palette", "_majority", "_norm", "_minimal_impostors",
         "_call_self_check", "_canonical_minimal_kinds", "probe_selfcheck_minimal_impostors"),
        {"Counter": Counter})
    return generic, minimal, {"selfcheck": generic_info, "defect_lint": minimal_info}


def negative_fixtures():
    return {
        "null_array": None, "empty_grid": [], "empty_row": [[]], "flat_array": [0, 1],
        "ragged_rows": [[0, 1], [0]], "scalar_row": [[0, 1], 0],
        "string_rows": ["00", "01"], "mapping": {"grid": [[0]]},
        "negative_color": [[-1]], "color_above_9": [[10]], "boolean_color": [[True]],
        "float_color": [[1.0]], "string_color": [["1"]], "null_color": [[None]],
        "nested_color": [[[1]]], "odd_reflected_collision": [[1, 0, 2]],
        "even_reflected_collision": [[0, 3, 4, 0]],
    }


RATIONALE = {
    "blank_grid": "Deleting all seeds yields lawful identity completion.",
    "absent_color_cell": "Every pigment 1..9 is legal; the domain check separately tests reflected conflicts.",
    "drop_minority_color": "Deleting a pigment cannot introduce a reflected color conflict.",
    "duplicate_first_row": "The rule acts independently on rows; copying a lawful row remains lawful.",
    "invert_fg_bg_roles": "One foreground pigment and zero still permit collision-free completion after inversion.",
    "swap_two_colors": "A global pigment permutation preserves equality of reflected endpoints.",
    "all_background": "A zero grid is a lawful no-seed identity endpoint.",
    "full_one_color": "A uniform pigment grid already equals its reflection; original pigments remain.",
    "singleton": "A single seed is copied, or retained on the centerline.",
    "solid_2x2": "Adjacent cells and blocks are mirrored cell by cell.",
    "short_line": "A short line is mirrored cell by cell; no object-count restriction is part of the rule.",
}


def validator_result(generator, grid, difficulty):
    try:
        reasons = generator.self_check(deepcopy(grid), difficulty=difficulty, meta=None)
    except Exception as exc:
        return {"accepted": False, "return_contract_valid": False,
                "exception": f"{type(exc).__name__}: {exc}"}
    valid = isinstance(reasons, list) and all(isinstance(reason, str) for reason in reasons)
    return {"accepted": valid and not reasons, "return_contract_valid": valid,
            "reasons": reasons if valid else repr(reasons)}


def prepare(args):
    mirror = load_mirror_probe()
    root, canonical_pairs = mirror.support_imports()
    generator, generator_path, source = mirror.load_generator(root)
    source_hash = digest(source)
    if args.expect_source and source_hash != args.expect_source:
        raise ValueError("Generator differs from --expect-source")
    generic, minimal, helpers = load_actual_helpers(root)
    pool, cases, inputs, bands = {}, [], [], []
    generation_errors = []

    def capture(family, kind, grid, difficulty=None, seed=None, expect=None):
        semantic_reasons = domain_reasons(grid, mirror.mirror_all)
        expected = not semantic_reasons if expect is None else expect
        if expected == bool(semantic_reasons):
            raise AssertionError(f"Literal fixture disagrees with independent domain: {kind}")
        key = grid_digest(grid)
        pool.setdefault(key, grid)
        decision = validator_result(generator, grid, difficulty)
        cases.append({"family": family, "kind": kind, "seed": seed,
                      "sample_index": seed, "difficulty": difficulty, "input_sha256": key,
                      "expected_acceptance": expected, "semantic_reasons": semantic_reasons,
                      "rationale": RATIONALE.get(kind, "Rectangular integer-color input satisfying symmetric completion without changing originals."
                                                   if expected else "Malformed grid/color, or reflected pigments conflict with completion grammar."),
                      "validator": decision,
                      "validator_contract_pass": decision["return_contract_valid"] and decision["accepted"] == expected})

    for difficulty in generic.DIFFICULTIES:
        for seed in range(args.samples):
            try:
                grid = generic._grid(generator.generate(seed=seed, sample_index=seed, difficulty=difficulty))
            except Exception as exc:
                generation_errors.append({"seed": seed, "difficulty": difficulty, "error": f"{type(exc).__name__}: {exc}"})
                continue
            inputs.append(grid); bands.append(difficulty)
            capture("generated", "baseline", grid, difficulty, seed, True)
            for kind, mutation in generic._mutations(grid):
                capture("actual_generic_mutation", kind, mutation, difficulty, seed)
            for kind, mutation in minimal._minimal_impostors(grid):
                capture("actual_minimal_impostor", kind, mutation, difficulty, seed)
    for kind, grid in negative_fixtures().items():
        capture("negative_grammar_fixture", kind, grid, expect=False)
    for kind, grid in {"single_zero": [[0]], "single_pigment": [[5]],
                       "same_color_mirrored_pair": [[2, 0, 2]],
                       "mixed_sources": [[1, 0, 0, 0], [0, 0, 0, 3]]}.items():
        capture("positive_grammar_fixture", kind, grid, expect=True)
    report = generic.Report(TASK_ID)
    generic.check_mutation_sensitivity(generator, report, samples=args.samples, require=True)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_train = [(pair["input"], pair["output"]) for pair in canonical if pair["split"] == "train"]
    minimal_warnings = minimal.probe_selfcheck_minimal_impostors(generator, inputs, bands, canonical_train)
    medium_checks = [generator.generate(seed, seed, difficulty=None) == generator.generate(seed, seed, difficulty="medium")
                     for seed in range(args.samples)]
    by_family, by_kind = {}, {}
    for case in cases:
        for table, key in ((by_family, case["family"]), (by_kind, case["family"] + ":" + case["kind"])):
            row = table.setdefault(key, {"cases": 0, "expected_accept": 0, "accepted": 0, "contract_failures": 0})
            row["cases"] += 1; row["expected_accept"] += case["expected_acceptance"]
            row["accepted"] += case["validator"]["accepted"]
            row["contract_failures"] += not case["validator_contract_pass"]
    return {"schema": "arcpuzzles-validator-contract-prepared-v1", "task_id": TASK_ID,
            "generator_path": str(generator_path), "generator_sha256": source_hash,
            "generator_version": generator.VERSION, "helper_sources": helpers,
            "mirror_probe_sha256": digest(Path(mirror.__file__).read_bytes()),
            "probe_sha256": digest(Path(__file__).read_bytes()), "arguments": vars(args), "argv": sys.argv,
            "sample_policy": {"seeds": list(range(args.samples)), "sample_index": "same as seed",
                              "actual_generic_difficulties": generic.DIFFICULTIES,
                              "explicit_medium_equals_None_per_seed": medium_checks,
                              "minimal_impostor_capture": "All five named shapes for every generated base input.",
                              "minimal_warning_replay": "Actual helper retains its own first-six-accepted-input cap."},
            "existing_gate_components": {
                "mutation_sensitivity": {"require": True, "exit_code": report.exit_code,
                                         "errors": report.errors, "warnings": report.warnings, "notes": report.notes},
                "minimal_impostors": {"warnings": minimal_warnings},
                "full_battery_verdict": "Not rerun or replaced by this tool; existing failed gate verdicts remain in force."},
            "domain_evidence_status": "Python domain classification and validator decisions; Racket verification pending.",
            "preliminary_contract_pass": not generation_errors and all(case["validator_contract_pass"] for case in cases),
            "by_family": by_family, "by_kind": by_kind, "generation_errors": generation_errors,
            "input_pool": pool, "cases": cases}


def write_json(path, data):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")


def verify(args):
    mirror = load_mirror_probe()
    root, _ = mirror.support_imports()
    prepared_path = Path(args.prepared)
    prepared = json.loads(prepared_path.read_text())
    if prepared["task_id"] != TASK_ID:
        raise ValueError("Prepared task differs")
    _, _, current_source = mirror.load_generator(root)
    if digest(current_source) != prepared["generator_sha256"]:
        raise ValueError("Generator changed after prepare; recapture on the final source")
    if digest(Path(mirror.__file__).read_bytes()) != prepared["mirror_probe_sha256"]:
        raise ValueError("Independent mirror probe changed after prepare")
    _, _, helper_sources = load_actual_helpers(root)
    if helper_sources != prepared["helper_sources"]:
        raise ValueError("Shared helper sources changed after prepare")
    selected = sorted({case["input_sha256"] for case in prepared["cases"]
                       if case["expected_acceptance"] and case["validator"]["accepted"]})
    grids = [prepared["input_pool"][key] for key in selected]
    if any(grid_digest(grid) != key or domain_reasons(grid, mirror.mirror_all) for key, grid in zip(selected, grids)):
        raise ValueError("Selected lawful input is invalid or its hash changed")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles import Catalog
    catalog = Catalog(root)
    receipt_files, mismatches, labeled_hashes = [], [], set()
    identities = []
    for start in range(0, len(grids), 64):
        receipt = catalog.apply(TASK_ID, grids[start:start + 64], reference="canonical", timeout=args.timeout)
        path = out / f"apply-{start // 64:03}.json"
        write_json(path, receipt)
        receipt_files.append({"path": path.name, "sha256": digest(path.read_bytes()), "results": len(receipt["results"])})
        identities.append({key: receipt[key] for key in
                           ("generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")})
        if receipt["generator_sha256"] != prepared["generator_sha256"] or receipt["rule_hash_matches_catalog"] is not True:
            raise ValueError("Public reference source identity differs from prepared source")
        if len(receipt["results"]) != len(grids[start:start + 64]):
            raise ValueError("Public reference result count differs")
        for key, expected_input, row in zip(selected[start:start + 64], grids[start:start + 64], receipt["results"]):
            if row["input"] != expected_input or row["input_sha256"] != key:
                raise ValueError("Public reference input identity differs")
            if row["error"] is not None or row["valid_output"] is not True:
                mismatches.append({"input_sha256": key, "error": row["error"], "valid_output": row["valid_output"]})
            elif row["output"] != mirror.mirror_all(expected_input):
                mismatches.append({"input_sha256": key, "error": "Independent original-read Python mirror differs from Racket"})
            elif grid_digest(row["output"]) != row["output_sha256"]:
                mismatches.append({"input_sha256": key, "error": "Output hash differs"})
            else:
                labeled_hashes.add(key)
    lawful_cases = [case for case in prepared["cases"] if case["expected_acceptance"]]
    all_labeled = all(case["input_sha256"] in labeled_hashes for case in lawful_cases)
    passed = prepared["preliminary_contract_pass"] and all_labeled and not mismatches
    result = {"schema": "arcpuzzles-validator-contract-verified-v1", "task_id": TASK_ID,
              "generator_sha256": prepared["generator_sha256"],
              "prepared_path": str(prepared_path), "prepared_sha256": digest(prepared_path.read_bytes()),
              "probe_sha256": digest(Path(__file__).read_bytes()), "mirror_probe_sha256": prepared["mirror_probe_sha256"],
              "helper_sources": prepared["helper_sources"], "arguments": vars(args), "argv": sys.argv,
              "validator_domain_verdict": "PASS" if passed else "FAIL",
              "lawful_cases": len(lawful_cases), "unique_lawful_inputs_labeled": len(labeled_hashes),
              "lawful_cases_all_labeled": all_labeled,
              "negative_cases_not_sent_to_Racket": sum(not case["expected_acceptance"] for case in prepared["cases"]),
              "negative_cases_all_rejected_without_crash": all(case["validator_contract_pass"] for case in prepared["cases"] if not case["expected_acceptance"]),
              "reference_mismatches": mismatches, "public_apply_receipts": receipt_files,
              "reference_identities": identities, "by_family": prepared["by_family"], "by_kind": prepared["by_kind"],
              "existing_gate_components": prepared["existing_gate_components"],
              "gate_disposition": "Preserved unchanged. This task-local validator-domain result never waives or upgrades a shared gate or aggregate battery verdict.",
              "evidence_basis": "Public canonical Racket labels for every accepted lawful case (deduplicated by exact input hash), compared with independently tested original-read mirror_all. Negative grammar fixtures were not submitted."}
    write_json(out / "verified.json", result)
    return result


def self_test():
    mirror = load_mirror_probe()
    assert mirror.self_test()["self_test"] == "pass"
    # Missing array/color validation and collision acceptance must fail these.
    for grid in ([], [[]], [[0], [0, 1]], [[True]], [[1.0]], [[10]], [[-1]], [["1"]]):
        assert domain_reasons(grid, mirror.mirror_all), grid
    for grid in ([[0]], [[5]], [[0, 2, 0]], [[1, 0, 1]],
                 [[2, 2, 0, 0], [2, 2, 0, 0]], [[3, 3], [3, 3]]):
        assert domain_reasons(grid, mirror.mirror_all) == [], grid
    assert domain_reasons([[1, 0, 2]], mirror.mirror_all)
    generic, minimal, _ = load_actual_helpers(mirror.support_imports()[0])
    grid = [[1, 0, 0, 0], [0, 0, 2, 0]]
    mutations = dict(generic._mutations(grid))
    assert mutations["blank_grid"] == [[0, 0, 0, 0], [0, 0, 0, 0]]
    assert mutations["absent_color_cell"] == [[1, 0, 0, 0], [0, 0, 3, 0]]
    assert mutations["drop_minority_color"] == [[0, 0, 0, 0], [0, 0, 2, 0]]
    assert mutations["duplicate_first_row"] == [[1, 0, 0, 0], [1, 0, 0, 0]]
    assert mutations["swap_two_colors"] == [[2, 0, 0, 0], [0, 0, 1, 0]]
    impostors = dict(minimal._minimal_impostors([[1, 0, 0, 0, 0], [0] * 5, [0] * 5]))
    assert impostors["singleton"] == [[0] * 5, [0, 0, 1, 0, 0], [0] * 5]
    assert impostors["solid_2x2"] == [[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0] * 5]
    assert impostors["short_line"] == [[0] * 5, [1, 1, 1, 1, 0], [0] * 5]
    return {"self_test": "pass", "actual_mutation_helpers_exercised": True}


def load_mirror_probe():
    path = Path(__file__).with_name("probe_mirror_curriculum.py")
    spec = importlib.util.spec_from_file_location("validator_contract_mirror_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("self-test")
    preparing = commands.add_parser("prepare")
    preparing.add_argument("--samples", type=int, default=5)
    preparing.add_argument("--expect-source")
    preparing.add_argument("--out", required=True)
    verifying = commands.add_parser("verify")
    verifying.add_argument("--prepared", required=True)
    verifying.add_argument("--out-dir", required=True)
    verifying.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.command == "self-test":
        print(json.dumps(self_test(), sort_keys=True)); return 0
    self_test()
    if args.command == "prepare":
        if args.samples < 1:
            parser.error("--samples must be positive")
        result = prepare(args)
        path = Path(args.out); path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, result)
        summary = {"prepared": args.out, "generator_sha256": result["generator_sha256"],
                   "preliminary_contract_pass": result["preliminary_contract_pass"],
                   "by_family": result["by_family"], "existing_gate_components": result["existing_gate_components"]}
        exit_code = int(not result["preliminary_contract_pass"])
    else:
        result = verify(args)
        summary = {key: result[key] for key in ("generator_sha256", "validator_domain_verdict", "lawful_cases",
                   "unique_lawful_inputs_labeled", "negative_cases_not_sent_to_Racket", "existing_gate_components")}
        exit_code = int(result["validator_domain_verdict"] != "PASS")
    print(json.dumps(summary, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
