#!/usr/bin/env python3
"""Bounded, portable, authoritative shortcut probe for task 33275a4aae3e.

Run from a review packet through its public wrapper, for example::

    python3 run_with_racket.py python3 \
      generators/33275a4aae3e/workspace/probe_shortcuts.py \
      --out ../checks/shortcut-probe

The selected generator supplies the rival functions. This probe does not copy
their implementations or assume their names. It checks every usable labeled
canonical pair, one input per declared profile and difficulty band, and an exact
handmade counterexample. All labels are executed through public ``arcpuzzles
apply`` in batches of at most 64. Reports bind source hashes, declarations,
inputs, predictions, authoritative outputs, legality, and replay commands.

The result is finite evidence for the declared alternatives. It neither proves
general rule identification nor changes review approval or training admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "33275a4aae3e"
RIVAL_DECLARATIONS = (
    "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS",
)


def grid_hash(grid):
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path, values):
    with path.open("x", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, separators=(",", ":")) + "\n")


def exact_witness():
    """One concave room, one rectangle, and a diagonally sealed 2x2 pocket."""
    grid = [[0] * 25 for _ in range(22)]
    horizontal = [
        (4, 3, 18), (7, 0, 8), (10, 9, 18), (13, 2, 13), (16, 2, 15),
    ]
    vertical = [(5, 1, 19), (14, 1, 12), (11, 8, 20)]
    for row, left, right in horizontal:
        for col in range(left, right + 1):
            grid[row][col] = 8
    for col, top, bottom in vertical:
        for row in range(top, bottom + 1):
            grid[row][col] = 8
    return grid


def declaration_functions(module, attribute):
    declaration = getattr(module, attribute, {})
    if not isinstance(declaration, dict):
        raise TypeError(f"{attribute} must be a dictionary")
    for name, function in declaration.items():
        if not isinstance(name, str) or not name or not callable(function):
            raise TypeError(f"{attribute} requires nonempty string names and callables")
    return declaration


def discover_rivals(module):
    """Share predictions only for the same local name and callable object."""
    rivals, by_identity, bindings = [], {}, {}
    for namespace in RIVAL_DECLARATIONS:
        for name, function in sorted(declaration_functions(module, namespace).items()):
            identity = (name, id(function))
            if identity not in by_identity:
                rival = {
                    "id": f"rival_{len(rivals):03d}", "name": name,
                    "callable": function, "bindings": [],
                    "callable_name": getattr(function, "__qualname__", type(function).__name__),
                }
                rivals.append(rival)
                by_identity[identity] = rival
            rival = by_identity[identity]
            binding = f"{namespace}:{name}"
            rival["bindings"].append(binding)
            bindings[binding] = rival["id"]
    if not rivals:
        raise ValueError("No declared canonical shortcuts, lesson competitors, or semantic rivals")
    return rivals, bindings


def check_domain(module, grid):
    checker = getattr(module, "self_check", None)
    if not callable(checker):
        return {"status": "not_declared", "errors": []}
    argument = copy.deepcopy(grid)
    try:
        reasons = checker(argument)
        if argument != grid:
            raise ValueError("self_check mutated its input")
        if not isinstance(reasons, (list, tuple)) or any(type(x) is not str for x in reasons):
            raise TypeError("self_check must return list[str] or tuple[str]")
        return {"status": "invalid" if reasons else "valid", "errors": list(reasons)}
    except Exception as exc:
        return {"status": "error", "errors": [f"{type(exc).__name__}: {exc}"]}


def materialize_cases(module, root, args):
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("No usable labeled canonical pairs")
    profiles = getattr(module, "SCENE_PROFILES", None)
    if not isinstance(profiles, (tuple, list)) or not profiles:
        raise ValueError("SCENE_PROFILES must enumerate the selected generator's profiles")
    if len(set(profiles)) != len(profiles) or any(type(x) is not str for x in profiles):
        raise ValueError("SCENE_PROFILES must contain distinct string names")
    cases = []
    for pair in pairs:
        cases.append({
            "kind": "canonical", "variant": pair["variant"],
            "split": pair["split"], "pair_index": pair["pair_index"],
            "input": pair["input"], "canonical_output": pair["output"],
        })
    for band in ("easy", "medium", "hard"):
        for profile in profiles:
            options = {"difficulty": band, "scene_profile": profile}
            grid = module.generate(args.seed, args.sample_index, **options)
            repeated = module.generate(args.seed, args.sample_index, **options)
            if grid != repeated:
                raise ValueError(f"Generation is not deterministic for {band}/{profile}")
            cases.append({
                "kind": "generated", "seed": args.seed,
                "sample_index": args.sample_index, "difficulty": band,
                "overrides": {"scene_profile": profile}, "input": normalize_grid(grid),
            })
    cases.append({"kind": "handmade", "name": "stepped_diagonal_seal", "input": exact_witness()})
    for index, case in enumerate(cases):
        case["id"] = f"case_{index:03d}"
        case["input_sha256"] = grid_hash(case["input"])
        case["generator_domain"] = check_domain(module, case["input"])
    return cases


def apply_batches(cases, root, source_hash, out, args, commands):
    authorities = []
    for batch_index, start in enumerate(range(0, len(cases), args.batch_size)):
        batch = cases[start:start + args.batch_size]
        input_path = out / f"apply-{batch_index:03d}.input.json"
        receipt_path = out / f"apply-{batch_index:03d}.json"
        write_json(input_path, {"inputs": [case["input"] for case in batch]})
        argv = [
            sys.executable, "-m", "arcpuzzles", "--library", str(root),
            "apply", TASK_ID, "--input", str(input_path),
            "--check-generator-domain", "--allow-unapproved",
            "--timeout", str(args.timeout), "--out", str(receipt_path),
        ]
        command = {
            "cwd": str(root), "argv": argv,
            "input_file": input_path.name, "output_file": receipt_path.name,
            "case_ids": [case["id"] for case in batch],
        }
        commands.append(command)
        started = time.monotonic()
        print(f"Reference batch {batch_index + 1}: {len(batch)} inputs", file=sys.stderr, flush=True)
        try:
            result = subprocess.run(
                argv, cwd=root, text=True, capture_output=True,
                timeout=args.timeout + 60, check=False,
            )
            command.update(exit_code=result.returncode, timed_out=False)
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            command.update(exit_code=None, timed_out=True)
            stdout, stderr = exc.stdout or "", exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
        command["elapsed_seconds"] = round(time.monotonic() - started, 3)
        (out / f"apply-{batch_index:03d}.stdout.log").write_text(stdout, encoding="utf-8")
        (out / f"apply-{batch_index:03d}.stderr.log").write_text(stderr, encoding="utf-8")
        if command["timed_out"] or command["exit_code"] != 0:
            raise RuntimeError(f"Public apply failed; inspect {out / f'apply-{batch_index:03d}.stderr.log'}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("generator_sha256") != source_hash:
            raise ValueError("Reference batch used different generator bytes")
        if receipt.get("task_id") != TASK_ID or receipt.get("reference") != "canonical":
            raise ValueError("Reference batch used the wrong task or authority")
        if not receipt.get("rule_hash_matches_catalog"):
            raise ValueError("Executed reference hash differs from catalog authority")
        rows = receipt.get("results", [])
        if len(rows) != len(batch):
            raise ValueError("Reference batch omitted or added results")
        authorities.append({
            key: receipt[key] for key in (
                "executed_rule_hash", "rule_text_sha256", "generator_sha256",
                "reference", "rule_task_id", "rule_hash_matches_catalog",
            )
        })
        for local_index, (case, result) in enumerate(zip(batch, rows, strict=True)):
            if result.get("index") != local_index:
                raise ValueError("Reference results are out of order")
            if result.get("input") != case["input"] or result.get("input_sha256") != case["input_sha256"]:
                raise ValueError("Reference result is not bound to the supplied input")
            if result.get("error") or not result.get("valid_output"):
                raise ValueError(f"Reference error for {case['id']}: {result.get('error')}")
            output = normalize_grid(result["output"])
            if grid_hash(output) != result.get("output_sha256"):
                raise ValueError("Reference output hash is inconsistent")
            case["output"] = output
            case["output_sha256"] = grid_hash(output)
            case["authority_receipt"] = receipt_path.name
            case["authority_result_index"] = local_index
            case["authoritative_generator_domain"] = result.get("generator_domain")
    if any(authority != authorities[0] for authority in authorities[1:]):
        raise ValueError("Authority or selected source changed between batches")
    return authorities[0]


def predict(rival, case):
    argument = copy.deepcopy(case["input"])
    prediction = {"case_id": case["id"], "rival_id": rival["id"], "rival_name": rival["name"]}
    try:
        raw_output = rival["callable"](argument)
        if argument != case["input"]:
            raise ValueError("rival mutated its input")
        output = normalize_grid(raw_output)
        expected = case["output"]
        mismatches = []
        for row in range(max(len(output), len(expected))):
            predicted_row = output[row] if row < len(output) else []
            expected_row = expected[row] if row < len(expected) else []
            for col in range(max(len(predicted_row), len(expected_row))):
                actual = predicted_row[col] if col < len(predicted_row) else None
                target = expected_row[col] if col < len(expected_row) else None
                if actual != target:
                    mismatches.append({"row": row, "col": col, "expected": target, "predicted": actual})
        prediction.update(
            status="match" if output == expected else "disagree", output=output,
            output_sha256=grid_hash(output), disagreeing_cells=len(mismatches),
            first_disagreements=mismatches[:12],
        )
    except Exception as exc:
        prediction.update(status="error", error=f"{type(exc).__name__}: {exc}")
    return prediction


def score_witnesses(module, cases, predictions, bindings):
    witnesses = declaration_functions(module, "SEMANTIC_WITNESSES")
    claims = getattr(module, "WITNESS_RIVALS", {})
    if not isinstance(claims, dict):
        raise TypeError("WITNESS_RIVALS must be a dictionary")
    by_case_rival = {(item["case_id"], item["rival_id"]): item for item in predictions}
    results = []
    for case in cases:
        for name, predicate in sorted(witnesses.items()):
            item = {"case_id": case["id"], "witness": name}
            argument = copy.deepcopy(case["input"])
            try:
                fired = predicate(argument)
                if type(fired) is not bool or argument != case["input"]:
                    raise ValueError("witness must return bool without mutating its input")
                named = claims.get(name, [])
                if isinstance(named, str):
                    named = [named]
                if not isinstance(named, (list, tuple)) or any(type(x) is not str for x in named):
                    raise TypeError("Witness rival claims must be strings or lists of strings")
                refuted = []
                for rival_name in named:
                    binding = f"SEMANTIC_RIVALS:{rival_name}"
                    if binding not in bindings:
                        raise ValueError(f"Missing claimed rival {binding}")
                    scored = by_case_rival[(case["id"], bindings[binding])]
                    if scored["status"] == "disagree":
                        refuted.append(rival_name)
                item.update(status="checked", fired=fired, claimed_rivals=list(named), refuted_rivals=refuted)
                if fired and named and not refuted:
                    item.update(status="error", error="Firing witness refuted none of its claimed rivals")
            except Exception as exc:
                item.update(status="error", error=f"{type(exc).__name__}: {exc}")
            results.append(item)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; never overwritten")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--sample-index", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--timeout", type=float, default=120, help="reference worker timeout per batch")
    args = parser.parse_args(argv)
    if not 1 <= args.batch_size <= 64:
        parser.error("--batch-size must be 1..64")
    if args.sample_index < 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--sample-index must be nonnegative and --timeout positive and finite")
    out = args.out.resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"output already exists: {out}")
    root = find_root(__file__)
    report = {
        "schema": "arcpuzzles-task-shortcut-probe-v1", "task_id": TASK_ID,
        "seed": args.seed, "sample_index": args.sample_index,
        "difficulty_bands": ["easy", "medium", "hard"], "batch_size": args.batch_size,
        "root": str(root), "probe_sha256": file_hash(Path(__file__)),
        "replay": {"cwd": str(Path.cwd()), "argv": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]]},
        "scope": "All labeled canonical pairs; one input per profile/band; one handmade witness; declared rivals only",
        "failures": [],
    }
    commands, cases, predictions, witness_results = [], [], [], []
    source = None
    try:
        module, source, source_hash = load_selected_generator(TASK_ID, root=root)
        report.update(generator_sha256=source_hash, generator_source=str(source), generator_version=module.VERSION)
        rivals, bindings = discover_rivals(module)
        report["rival_identities"] = [{k: v for k, v in rival.items() if k != "callable"} for rival in rivals]
        report["declaration_bindings"] = bindings
        cases = materialize_cases(module, root, args)
        report["case_counts"] = dict(Counter(case["kind"] for case in cases))
        report["authority"] = apply_batches(cases, root, source_hash, out, args, commands)
        if report["authority"]["executed_rule_hash"] != getattr(module, "RULE_HASH", None):
            report["failures"].append("Generator RULE_HASH does not name the executed authority")
        canonical_hashes = {case["input_sha256"] for case in cases if case["kind"] == "canonical"}
        for case in cases:
            if case["generator_domain"]["status"] != "valid":
                report["failures"].append(f"Invalid or unchecked generator domain: {case['id']}")
            if case.get("authoritative_generator_domain") != case["generator_domain"]:
                report["failures"].append(f"Local and public domain checks differ: {case['id']}")
            if case["kind"] == "canonical" and case["output"] != case["canonical_output"]:
                report["failures"].append(f"Canonical label differs from executed authority: {case['id']}")
            if case["kind"] == "generated" and case["input_sha256"] in canonical_hashes:
                report["failures"].append(f"Generated input literally replays a canonical input: {case['id']}")
            for rival in rivals:
                predictions.append(predict(rival, case))
        case_kind = {case["id"]: case["kind"] for case in cases}
        summaries = []
        for rival in rivals:
            scores = [item for item in predictions if item["rival_id"] == rival["id"]]
            by_kind = {
                kind: dict(Counter(item["status"] for item in scores if case_kind[item["case_id"]] == kind))
                for kind in ("canonical", "generated", "handmade")
            }
            canonical_fit = by_kind["canonical"].get("match", 0) == report["case_counts"]["canonical"]
            generated_witnesses = [item["case_id"] for item in scores
                                   if case_kind[item["case_id"]] == "generated" and item["status"] == "disagree"]
            summaries.append({
                "rival_id": rival["id"], "name": rival["name"], "bindings": rival["bindings"],
                "scores": by_kind, "fits_all_canonical": canonical_fit,
                "generated_counterexample_case_ids": generated_witnesses,
                "handmade_counterexample_case_ids": [item["case_id"] for item in scores
                    if case_kind[item["case_id"]] == "handmade" and item["status"] == "disagree"],
            })
            if any(item["status"] == "error" for item in scores):
                report["failures"].append(f"Rival execution error: {rival['id']}")
            if any(binding.startswith("CANONICAL_SHORTCUTS:") for binding in rival["bindings"]):
                if not canonical_fit:
                    report["failures"].append(f"False canonical shortcut declaration: {rival['name']}")
                if not generated_witnesses:
                    report["failures"].append(f"No generated counterexample for canonical shortcut: {rival['name']}")
        report["rivals"] = summaries
        witness_results = score_witnesses(module, cases, predictions, bindings)
        for item in witness_results:
            if item["status"] == "error":
                report["failures"].append(f"Witness check error: {item['case_id']}/{item['witness']}")
        report["witness_firings"] = {
            name: dict(Counter(case_kind[item["case_id"]] for item in witness_results
                               if item["witness"] == name and item.get("fired")))
            for name in declaration_functions(module, "SEMANTIC_WITNESSES")
        }
        report["unique_inputs_by_kind"] = {
            kind: len({case["input_sha256"] for case in cases if case["kind"] == kind})
            for kind in report["case_counts"]
        }
        report["unique_outputs_by_kind"] = {
            kind: len({case["output_sha256"] for case in cases if case["kind"] == kind})
            for kind in report["case_counts"]
        }
        report["case_results"] = [{key: value for key, value in case.items()
                                   if key not in {"input", "output", "canonical_output"}} for case in cases]
    except Exception as exc:
        report["failures"].append(f"{type(exc).__name__}: {exc}")
    if source is not None:
        report["generator_sha256_after"] = file_hash(source)
        if report["generator_sha256_after"] != report["generator_sha256"]:
            report["failures"].append("Generator source changed while this probe was running")
    report["status"] = "FAIL" if report["failures"] else "PASS"
    write_jsonl(out / "cases.jsonl", cases)
    write_jsonl(out / "predictions.jsonl", predictions)
    write_jsonl(out / "witnesses.jsonl", witness_results)
    write_json(out / "commands.json", commands)
    write_json(out / "report.json", report)
    write_json(out / "manifest.json", {
        "schema": "arcpuzzles-task-probe-files-v1",
        "files": [{"path": path.name, "sha256": file_hash(path), "bytes": path.stat().st_size}
                  for path in sorted(out.iterdir()) if path.is_file()],
    })
    print(json.dumps({key: report.get(key) for key in (
        "status", "generator_sha256", "case_counts", "unique_inputs_by_kind", "failures",
    )}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
