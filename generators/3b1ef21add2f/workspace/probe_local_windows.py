#!/usr/bin/env python3
"""Finite, source-bound authoring probe for simultaneous red-window recoloring.

Run in a review packet (the wrapper supplies the existing public CLI runtime):
  python3 run_with_racket.py python3 \
    generators/3b1ef21add2f/workspace/probe_local_windows.py \
    --out ../checks/local-windows/NEW_RUN \
    --expected-generator-sha SHA256 --expected-rule-hash 200a2c36d86e

The output directory must be new. --counterexamples optionally updates the
selected task's compact current witness file; earlier run evidence is untouched.
The probe itself uses only Python's standard library. Loading the selected
generator's public declarations uses its ordinary installed dependencies.

This is an authoring comparison, never a source of replacement training labels.
Every claimed actual output is obtained by public ``arcpuzzles apply`` in batches
of at most 64. No private runner calls, runtime copies, or imported Python rule
mirrors are used. The independent oracle gathers covered cells from an immutable
input snapshot. Self-check acceptance is reported separately: an operator-lawful
grid can intentionally be outside the generator's narrower teaching grammar.

Exhaustive means ONLY the 512 red/black 3x3 masks at offset (1,1) in a black 5x5
grid. Targeted grids extend that finite domain for colors, boundaries, tails,
and separate unequal window-bearing components. This does not establish
universal equivalence or lesson identifiability.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

TASK = "3b1ef21add2f"


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def json_sha(value):
    return sha_bytes(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def windows(grid, color=2):
    """Authoring-only observation of original monochromatic neighborhoods."""
    return [
        (r, c)
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]) - 1)
        if all(grid[r + dr][c + dc] == color for dr in (0, 1) for dc in (0, 1))
    ]


def snapshot_oracle(grid):
    """Independent comparison oracle: union original red windows, then write."""
    original = tuple(tuple(row) for row in grid)
    covered = set()
    for r in range(len(original) - 1):
        for c in range(len(original[0]) - 1):
            cells = ((r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1))
            if all(original[y][x] == 2 for y, x in cells):
                covered.update(cells)
    return [[3 if (r, c) in covered else value for c, value in enumerate(row)]
            for r, row in enumerate(original)]


def red_components(grid):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 2}
    result = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        component, queue = {seed}, deque([seed])
        while queue:
            r, c = queue.popleft()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    component.add(p)
                    queue.append(p)
        result.append(component)
    return result


def paint(grid, cells):
    out = [list(row) for row in grid]
    for r, c in cells:
        out[r][c] = 3
    return out


def exact_red_2x2_components(grid):
    cells = set()
    for component in red_components(grid):
        if len(component) == 4:
            rows = {r for r, _ in component}
            cols = {c for _, c in component}
            if len(rows) == len(cols) == 2:
                cells.update(component)
    return paint(grid, cells)


def red_components_mass_at_least_four(grid):
    return paint(grid, {p for component in red_components(grid)
                        if len(component) >= 4 for p in component})


def greedy_row_major_in_place(grid):
    out = deepcopy(grid)
    for r in range(len(out) - 1):
        for c in range(len(out[0]) - 1):
            cells = ((r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1))
            if all(out[y][x] == 2 for y, x in cells):
                for y, x in cells:
                    out[y][x] = 3
    return out


def largest_window_bearing_components(grid):
    covered = {p for r, c in windows(grid)
               for p in ((r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1))}
    bearing = [component for component in red_components(grid) if component & covered]
    if not bearing:
        return deepcopy(grid)
    largest = max(map(len, bearing))
    # All tied largest components are selected; a single winner fails canonical
    # pair train:0 and test:0, both of which contain two equal red squares.
    return paint(grid, {p for component in bearing if len(component) == largest
                        for p in component & covered})


def any_nonzero_solid_2x2(grid):
    cells = set()
    for color in range(1, 10):
        for r, c in windows(grid, color):
            cells.update(((r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)))
    return paint(grid, cells)


def all_red_to_green(grid):
    return [[3 if value == 2 else value for value in row] for row in grid]


AUTHORING_RIVALS = {
    "exact_red_2x2_components": exact_red_2x2_components,
    "red_components_mass_at_least_four": red_components_mass_at_least_four,
    "greedy_row_major_in_place": greedy_row_major_in_place,
    "largest_window_bearing_components": largest_window_bearing_components,
    "any_nonzero_solid_2x2": any_nonzero_solid_2x2,
    "all_red_to_green": all_red_to_green,
}

RIVAL_DESCRIPTIONS = {
    "exact_red_2x2_components": "Recolor only 4-connected red components that are exactly a solid 2x2 square.",
    "red_components_mass_at_least_four": "Recolor every cell of each 4-connected red component of mass >= 4.",
    "greedy_row_major_in_place": "Scan row-major, immediately recoloring each currently all-red 2x2; later windows read the modified grid.",
    "largest_window_bearing_components": "Recolor covered red cells only in maximum-mass 4-connected red components that contain a window; include every tied maximum.",
    "any_nonzero_solid_2x2": "Simultaneously recolor all cells of any solid nonzero-color 2x2 to 3, rather than requiring red 2.",
    "all_red_to_green": "Recolor every red cell; a default-sampler shortcut, explicitly not claimed to fit canonical labels.",
}


def local_cases():
    cases = []
    for mask in range(512):
        grid = [[0] * 5 for _ in range(5)]
        for bit in range(9):
            if mask & (1 << bit):
                grid[1 + bit // 3][1 + bit % 3] = 2
        cases.append({"id": f"mask:{mask:03d}", "kind": "local_mask",
                      "mask": mask, "input": grid})
    return cases


def targeted_cases():
    cases = [
        ("minimal_overlap_horizontal", [[2, 2, 2], [2, 2, 2]]),
        ("minimal_overlap_vertical", [[2, 2], [2, 2], [2, 2]]),
        ("minimal_attached_tail", [[2, 2, 2], [2, 2, 0]]),
        ("minimal_no_window_mass_four", [[2, 2, 2], [2, 0, 0]]),
        ("unequal_window_components_mass5_and4",
         [[2, 2, 2, 0, 2, 2], [2, 2, 0, 0, 2, 2]]),
    ]
    for color in (1, 3, 4, 5, 6, 7, 8, 9):
        cases.append((f"solid_nonred_color_{color}", [[color, color], [color, color]]))
    joint = [[0] * 7 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0),
                 (0, 5), (0, 6), (1, 5), (1, 6),
                 (5, 0), (5, 1), (5, 2), (5, 3)):
        joint[r][c] = 2
    for r, c in ((4, 5), (4, 6), (5, 5), (5, 6)):
        joint[r][c] = 1
    cases.append(("contrastful_joint_witness", joint))
    return [{"id": name, "kind": "targeted", "input": grid} for name, grid in cases]


def load_canonical(path):
    matches = []
    for raw in path.read_bytes().splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            matches.append((row, raw))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK}, got {len(matches)}")
    row, raw = matches[0]
    cases = [{"id": f"canonical:{split}:{i}", "kind": "canonical",
              "input": pair["input"], "canonical_output": pair["output"]}
             for split in ("train", "test") for i, pair in enumerate(row.get(split, []))
             if "output" in pair]
    return row, raw, cases


def load_generator(path):
    spec = importlib.util.spec_from_file_location("selected_local_window_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def minimal_key(case):
    grid = case["input"]
    return (sum(v != 0 for row in grid for v in row), len(grid) * len(grid[0]),
            len(grid), len(grid[0]), case["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-generator-sha")
    parser.add_argument("--expected-rule-hash", default="200a2c36d86e")
    parser.add_argument("--counterexamples")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 64:
        parser.error("--batch-size must be 1..64")
    repo = next((p for p in Path(__file__).resolve().parents
                 if (p / "shared/data/canonical/puzzles.jsonl").is_file()), None)
    if repo is None:
        raise SystemExit("Run this authoring probe from the selected task in a full repository.")
    out = Path(args.out).resolve()
    if out.exists():
        raise SystemExit(f"Refusing to overwrite prior run: {out}")
    out.mkdir(parents=True)
    generator_path = repo / "generators" / TASK / "generator.py"
    canonical_path = repo / "shared/data/canonical/puzzles.jsonl"
    source_hash = sha_bytes(generator_path.read_bytes())
    row, raw, canonical = load_canonical(canonical_path)
    source = {
        "task_id": TASK, "generator_path": str(generator_path.relative_to(repo)),
        "generator_sha256": source_hash,
        "canonical_file_sha256": sha_bytes(canonical_path.read_bytes()),
        "canonical_row_sha256": sha_bytes(raw),
        "canonical_program_string_sha256": sha_bytes(row["program_solution"].encode()),
        "expected_executed_rule_hash": args.expected_rule_hash,
        "probe_sha256": sha_bytes(Path(__file__).read_bytes()),
    }
    report = {"schema": "task-local-window-probe-v1", "source": source,
              "status": "running", "commands": [], "failures": [],
              "invocation": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())},
              "domain": {"local_masks": 512, "mask_dimensions": [3, 3],
                         "embedding_dimensions": [5, 5], "embedding_offset": [1, 1],
                         "mask_bit_order": "row-major, bit0 at (1,1), red2 when set; all other cells0",
                         "coverage_kind": "finite operator-domain authoring comparison",
                         "self_check_policy": "reported separately; rejection is not itself a rule defect",
                         "labels": "actual outputs from public Racket apply; Python oracle is comparison only"}}
    save_json(out / "report.json", report)
    try:
        if args.expected_generator_sha and source_hash != args.expected_generator_sha:
            raise ValueError("selected generator SHA does not match --expected-generator-sha")
        generator = load_generator(generator_path)
        source["generator_version"] = getattr(generator, "VERSION", None)
        rivals = {f"authoring:{name}": fn for name, fn in AUTHORING_RIVALS.items()}
        declarations = {}
        for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
            declared = getattr(generator, namespace, {})
            if not isinstance(declared, dict) or not all(callable(fn) for fn in declared.values()):
                raise TypeError(f"{namespace} must be a dictionary of callable rival functions")
            declarations[namespace] = sorted(declared)
            rivals.update({f"{namespace}:{name}": fn for name, fn in declared.items()})
        report["declared_rivals"] = declarations
        cases = local_cases() + targeted_cases() + canonical
        report["domain"].update({"targeted_cases": len(targeted_cases()),
                                 "canonical_labelled_pairs": len(canonical),
                                 "total_cases": len(cases),
                                 "unique_inputs": len({json_sha(c["input"]) for c in cases})})
        for case in cases:
            case["input_sha256"] = json_sha(case["input"])
            case["self_check_errors"] = list(generator.self_check(deepcopy(case["input"])))
        save_json(out / "case-index.json", [
            {k: v for k, v in case.items() if k not in ("input", "canonical_output")}
            for case in cases])
        # Batches run sequentially and check immutable-source identity each time.
        for start in range(0, len(cases), args.batch_size):
            if sha_bytes(generator_path.read_bytes()) != source_hash:
                raise RuntimeError("selected generator changed during run; partial evidence retained")
            batch_id = start // args.batch_size
            batch = cases[start:start + args.batch_size]
            input_path = out / f"batch-{batch_id:02d}-inputs.json"
            result_path = out / f"batch-{batch_id:02d}-racket.json"
            save_json(input_path, {"inputs": [case["input"] for case in batch]})
            argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
                    "--input", str(input_path), "--out", str(result_path),
                    "--timeout", str(args.timeout)]
            started = time.monotonic()
            proc = subprocess.run(argv, cwd=repo, capture_output=True, text=True,
                                  timeout=args.timeout + 60)
            command = {"argv": argv, "cwd": str(repo), "exit_code": proc.returncode,
                       "elapsed_seconds": round(time.monotonic() - started, 3),
                       "stdout": proc.stdout, "stderr": proc.stderr,
                       "input_path": str(input_path), "output_path": str(result_path),
                       "case_ids": [case["id"] for case in batch]}
            report["commands"].append(command)
            save_json(out / "report.json", report)
            if proc.returncode != 0:
                raise RuntimeError(f"public apply failed in batch {batch_id}: exit {proc.returncode}")
            receipt = json.loads(result_path.read_text())
            command["receipt_sha256"] = sha_bytes(result_path.read_bytes())
            if receipt.get("generator_sha256") != source_hash:
                raise RuntimeError("public apply receipt is bound to different generator bytes")
            if receipt.get("executed_rule_hash") != args.expected_rule_hash:
                raise RuntimeError("public apply receipt has unexpected executed Racket rule hash")
            if not receipt.get("rule_hash_matches_catalog"):
                raise RuntimeError("public apply reports an authority/catalog hash mismatch")
            source["executed_rule_hash"] = receipt["executed_rule_hash"]
            source["executed_rule_text_sha256"] = receipt["rule_text_sha256"]
            results = receipt["results"]
            if len(results) != len(batch):
                raise RuntimeError("public apply returned the wrong number of results")
            for index, (case, result) in enumerate(zip(batch, results)):
                if result.get("error") or not result.get("valid_output"):
                    raise RuntimeError(f"Racket execution failed for {case['id']}: {result}")
                if result.get("input") != case["input"]:
                    raise RuntimeError(f"public apply input mismatch for {case['id']}")
                case["actual_racket_output"] = result["output"]
                case["racket_receipt"] = {"path": str(result_path), "result_index": index,
                                           "input_sha256": result["input_sha256"],
                                           "output_sha256": result["output_sha256"]}
            print(f"batch {batch_id + 1}: {len(batch)} real Racket results", flush=True)
        if sha_bytes(generator_path.read_bytes()) != source_hash:
            raise RuntimeError("selected generator changed during run; partial evidence retained")
        mismatches = [case for case in cases
                      if snapshot_oracle(case["input"]) != case["actual_racket_output"]]
        canonical_mismatches = [case["id"] for case in canonical
                                if snapshot_oracle(case["input"]) != case["canonical_output"]]
        actual_canonical_mismatches = [case["id"] for case in cases if case["kind"] == "canonical"
                                       and case["actual_racket_output"] != case["canonical_output"]]
        report["oracle_comparison"] = {"compared": len(cases), "mismatch_count": len(mismatches),
                                        "mismatches": mismatches,
                                        "oracle_vs_canonical_mismatches": canonical_mismatches,
                                        "racket_vs_canonical_mismatches": actual_canonical_mismatches}
        report["self_check"] = {}
        for kind in ("local_mask", "targeted", "canonical"):
            subset = [case for case in cases if case["kind"] == kind]
            report["self_check"][kind] = {
                "total": len(subset), "accepted": sum(not c["self_check_errors"] for c in subset),
                "rejected": sum(bool(c["self_check_errors"]) for c in subset),
                "error_counts": dict(Counter(error for c in subset for error in c["self_check_errors"]))}
        rival_report, witnesses = {}, []
        for name, rival in rivals.items():
            disagreements, errors, canonical_fits = [], [], []
            for case in cases:
                try:
                    predicted = rival(deepcopy(case["input"]))
                except Exception as exc:
                    errors.append({"case_id": case["id"], "error": repr(exc)})
                    continue
                if case["kind"] == "canonical":
                    canonical_fits.append({"case_id": case["id"],
                                           "fits": predicted == case["canonical_output"]})
                if predicted != case["actual_racket_output"]:
                    disagreements.append((case, predicted))
            by_kind = Counter(case["kind"] for case, _ in disagreements)
            all_fit = len(canonical_fits) == len(canonical) and all(r["fits"] for r in canonical_fits)
            row_result = {"canonical_fit_all_labelled_pairs": all_fit,
                          "canonical_pairs": canonical_fits, "errors": errors,
                          "racket_disagreements": {kind: by_kind[kind] for kind in
                                                   ("local_mask", "targeted", "canonical")},
                          "description": RIVAL_DESCRIPTIONS.get(name.split(":", 1)[1],
                                                                "Selected generator declaration")}
            noncanonical = [(case, predicted) for case, predicted in disagreements
                            if case["kind"] != "canonical"]
            if noncanonical:
                case, prediction = min(noncanonical, key=lambda item: minimal_key(item[0]))
                witness = {"rival": name, "canonical_fit_all_labelled_pairs": all_fit,
                           "minimality": "minimum nonzero cells, then area/height/width/id within this finite probe set",
                           **case, "rival_output": prediction,
                           "snapshot_oracle_output": snapshot_oracle(case["input"])}
                row_result["minimal_witness_id"] = case["id"]
                witnesses.append(witness)
            if name.startswith("CANONICAL_SHORTCUTS:") and not all_fit:
                report["failures"].append(f"Claimed canonical shortcut fails labelled pairs: {name}")
            if errors:
                report["failures"].append(f"Rival raised on finite probe domain: {name}")
            rival_report[name] = row_result
        report["rivals"] = rival_report
        if mismatches or canonical_mismatches or actual_canonical_mismatches:
            report["failures"].append("Independent oracle, actual Racket, or canonical outputs disagree")
        witness_bundle = {"schema": "task-local-window-witnesses-v1", "source": source,
                          "evidence_report": str(out / "report.json"), "witnesses": witnesses,
                          "contrastful_joint_witness": next(case for case in cases
                                                             if case["id"] == "contrastful_joint_witness")}
        save_json(out / "witnesses.json", witness_bundle)
        if args.counterexamples:
            save_json(Path(args.counterexamples).resolve(), witness_bundle)
        report["status"] = "failed" if report["failures"] else "complete"
        report["limitations"] = [
            "Only 512 binary local masks, the listed targeted inputs, and the three canonical labelled pairs were evaluated.",
            "Local 3x3 masks cannot contain two separate window-bearing red 4-components; unequal-component behavior requires a targeted input.",
            "No generator sample-frequency, full-lesson teaching, arbitrary-size, arbitrary-color-arrangement, or universal-equivalence claim is made.",
            "Self-check acceptance describes the selected sampler grammar and is not an operator-domain validity decision.",
            "Independent authoring rivals are distinguished from dynamically loaded generator declarations; canonical fits are measured against every labelled pair.",
        ]
    except Exception as exc:
        report["status"] = "error"
        report["failures"].append(repr(exc))
        report["traceback"] = traceback.format_exc()
    save_json(out / "report.json", report)
    print(json.dumps({"status": report["status"], "source": source,
                      "failures": report["failures"], "report": str(out / "report.json")}, indent=2))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
