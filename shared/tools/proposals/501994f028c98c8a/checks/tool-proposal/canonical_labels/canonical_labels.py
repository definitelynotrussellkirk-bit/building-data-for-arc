#!/usr/bin/env python3
"""Optional authoring-only canonical-label gate; no staging or source changes.

Exit 0: every labeled pair matches. Exit 1: at least one label mismatch.
Exit 2: data, binding, execution, output-format, or report-writing error.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


SCHEMA = "canonical-label-consistency-proposal-v1"


def sha256(value) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def value_hash(value) -> str:
    return sha256(json.dumps(value, separators=(",", ":"), sort_keys=True))


def _local_file(path: Path, root: Path) -> Path:
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError(f"Source must remain inside the selected root: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.resolve()


def _selected_generator_identity(root: Path, task_id: str):
    """Hash selected bytes without importing or running a generator."""
    library_path = f"generators/{task_id}/generator.py"
    source = root / library_path
    manifest = root / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        _local_file(manifest, root)
        entries = json.loads(manifest.read_text()).get("files", [])
        matches = [entry for entry in entries if entry.get("library_path") == library_path]
        selected = [entry for entry in matches if entry.get("runtime_path") != library_path]
        matches = selected or matches
        if len(matches) != 1:
            raise ValueError("Runtime manifest must select exactly one generator source")
        relative = Path(matches[0]["runtime_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe selected-generator runtime path")
        source = root / relative
    if not source.exists():
        return {"present": False, "required_for_label_execution": False}
    source = _local_file(source, root)
    return {"present": True, "path": source.relative_to(root).as_posix(),
            "sha256": sha256(source.read_bytes()), "executed": False}


def load_canonical_binding(root: Path, task_id: str, expected_program_sha256: str | None = None):
    root = Path(root).resolve()
    if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]*", task_id):
        raise ValueError("Use an exact task ID, not a path or alias")
    ledger = _local_file(canonical_path(root), root)
    raw = ledger.read_bytes()
    variants = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"Canonical ledger line {line_number} is not an object")
        if row.get("task_id") == task_id:
            variants.append({"row": row, "line_number": line_number, "row_sha256": sha256(line)})
    if not variants:
        raise ValueError(f"No canonical record for exact task {task_id}")
    programs = []
    for variant in variants:
        row = variant["row"]
        program = row.get("program_solution")
        if row.get("solution_language") != "racket" or row.get("needs_conversion", False):
            raise ValueError("Every variant must declare an executable Racket reference")
        if not isinstance(program, str) or not program.strip():
            raise ValueError("Every variant needs a nonempty canonical program")
        programs.append(program)
    if len(set(programs)) != 1:
        raise ValueError("Conflicting exact canonical program strings across variants")
    program = programs[0]
    if expected_program_sha256 is not None and expected_program_sha256 != sha256(program):
        raise ValueError("Selected canonical program does not match expected SHA-256")

    skipped, expected_count = [], 0
    for index, variant in enumerate(variants):
        row = variant["row"]
        for split in ("train", "test"):
            collection = row.get(split, [])
            if isinstance(collection, dict):
                collection = [collection]
            if not isinstance(collection, list):
                raise ValueError(f"variant {index} {split}: pair collection is not a list/object")
            for pair_index, pair in enumerate(collection):
                location = f"variant {index} {split}[{pair_index}]"
                if not isinstance(pair, dict):
                    raise ValueError(f"{location}: pair is not an object")
                try:
                    inp = normalize_grid(pair.get("input"))
                    if split == "test" and "output" not in pair:
                        skipped.append({"variant": index, "split": split, "pair_index": pair_index,
                                        "reason": "unlabeled test input", "input_sha256": value_hash(inp)})
                    else:
                        normalize_grid(pair.get("output"))
                        expected_count += 1
                except ValueError as exc:
                    raise ValueError(f"{location}: {exc}") from exc
    pairs = canonical_pairs(task_id, root=root, labeled_only=True)
    if not pairs or len(pairs) != expected_count:
        raise ValueError("No labeled pairs, or helper coverage differs from raw ledger accounting")
    seen_inputs = {}
    for pair in pairs:
        key = json.dumps(pair["input"], separators=(",", ":"))
        identity = {field: pair[field] for field in ("variant", "split", "pair_index")}
        if key in seen_inputs and seen_inputs[key]["output"] != pair["output"]:
            raise ValueError(f"Conflicting labels for an identical input: {seen_inputs[key]['identity']} and {identity}")
        seen_inputs[key] = {"output": pair["output"], "identity": identity}
    if sha256(ledger.read_bytes()) != sha256(raw):
        raise ValueError("Canonical ledger changed while binding the audit")
    return {"root": str(root), "task_id": task_id,
            "canonical_file": {"path": ledger.relative_to(root).as_posix(), "sha256": sha256(raw)},
            "program": program, "program_sha256": sha256(program),
            "variant_count": len(variants),
            "variants": [{"variant": i, "ledger_line": row["line_number"],
                          "row_sha256": row["row_sha256"], "program_sha256": sha256(programs[i])}
                         for i, row in enumerate(variants)],
            "skipped_unlabeled_test": skipped,
            "selected_generator": _selected_generator_identity(root, task_id),
            "pairs": pairs}


def execute_racket_batch(program: str, inputs: list, *, root: Path, timeout: float = 10.0) -> dict:
    """Return actual outputs with no trusted labels, Python mirror, or staging.

    Public ArcExecutor.step loads the exact source. Raw output application uses
    the same internal _apply_rule/Grid/_unwrap path as isolated_verifier._worker.
    This optional proposal documents that narrow internal coupling explicitly.
    """
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite positive number")
    root = Path(root).resolve()
    from arc_repl import executor as executor_module
    from arc_repl import racket_bridge as bridge_module
    from arc_repl import parser as parser_module
    from arc_repl.builtins import helpers as grid_module
    from arc_repl.builtins import Grid, _unwrap
    from arc_repl.executor import ArcExecutor
    from arc_repl.parser import Symbol, parse_all

    runtime_sources = {}
    for module in (executor_module, bridge_module, parser_module, grid_module):
        source = _local_file(Path(module.__file__), root)
        runtime_sources[source.relative_to(root).as_posix()] = sha256(source.read_bytes())
    forms = parse_all(program)
    if (len(forms) != 1 or not isinstance(forms[0], list) or len(forms[0]) != 2
            or forms[0][0] != Symbol("rule!")):
        raise ValueError("Exactly one (rule! expression) is required")
    results, identities, executor, session_index = [], [], None, -1
    try:
        for index, value in enumerate(inputs):
            original = normalize_grid(value)
            try:
                if executor is None:
                    session_index += 1
                    executor = ArcExecutor({"train": [], "test": []}, auto_scan_on_load=False, use_racket=True)
                    if not executor.use_racket or executor._bridge is None:
                        raise RuntimeError("Racket backend was not activated")
                    executor._bridge.timeout = float(timeout)
                    observation = executor.step(program)
                    if observation.startswith("ERROR") or not executor.state_summary["rule"]:
                        raise RuntimeError(f"Rule load failed: {observation}")
                    identity = executor.runtime_identity
                    if identity.get("backend") != "racket":
                        raise RuntimeError("Unexpected backend identity")
                    identities.append({"session_index": session_index, **identity})
                wrapped = Grid(deepcopy(original))
                raw_output = _unwrap(executor._apply_rule(wrapped))
                if _unwrap(wrapped) != original:
                    raise RuntimeError("Racket application mutated the input")
                try:
                    output = normalize_grid(raw_output)
                except ValueError as exc:
                    results.append({"index": index, "session_index": session_index, "status": "error", "error_kind": "invalid_output",
                                    "message": str(exc), "raw_output": raw_output})
                    continue
                results.append({"index": index, "session_index": session_index, "status": "ok", "output": output,
                                "input_purity": True})
            except Exception as exc:
                results.append({"index": index, "session_index": session_index, "status": "error", "error_kind": type(exc).__name__,
                                "message": str(exc)})
                # Do not retry a failed input. A later pair gets a new child and
                # reloads the program so timeout recovery cannot lose bindings.
                if executor is not None:
                    executor.close()
                    executor = None
    finally:
        if executor is not None:
            executor.close()
    return {"backend": "racket", "program_sha256": sha256(program),
            "application_path": "ArcExecutor.step -> ArcExecutor._apply_rule -> RacketBridge",
            "runtime_source_sha256": runtime_sources, "runtime_identities": identities,
            "results": results}


def compare_grids(expected, actual) -> dict:
    """Shape-safe exact diff, retaining extra/missing rows and columns."""
    expected, actual = normalize_grid(expected), normalize_grid(actual)
    eh, ew, ah, aw = len(expected), len(expected[0]), len(actual), len(actual[0])
    differences = []
    for row in range(max(eh, ah)):
        for column in range(max(ew, aw)):
            before = expected[row][column] if row < eh and column < ew else None
            after = actual[row][column] if row < ah and column < aw else None
            if before != after:
                differences.append({"cell": [row, column], "expected": before, "actual": after,
                                    "kind": "extra_actual_cell" if before is None else
                                            "missing_actual_cell" if after is None else "value_mismatch"})
    return {"matches": expected == actual, "expected_shape": [eh, ew], "actual_shape": [ah, aw],
            "shape_mismatch": [eh, ew] != [ah, aw], "differing_cells": len(differences),
            "differences": differences}


def compare_labeled_pairs(pairs: list, execution: dict) -> dict:
    """Comparison/report kernel, injectable in unit tests without a rule mirror."""
    records = execution.get("results")
    if execution.get("backend") != "racket" or not isinstance(records, list) or len(records) != len(pairs):
        raise ValueError("Incomplete or non-Racket execution receipt")
    if not pairs:
        raise ValueError("An empty labeled set cannot pass")
    if [record.get("index") for record in records] != list(range(len(pairs))):
        raise ValueError("Execution records must have unique ordered input indices")
    outcomes = []
    for pair, record in zip(pairs, records):
        result = {"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                  "execution_session_index": record.get("session_index"),
                  "input": pair["input"], "input_sha256": value_hash(pair["input"]),
                  "expected": pair["output"], "expected_sha256": value_hash(pair["output"])}
        if record.get("status") == "error":
            result.update(status="error", execution_error={key: value for key, value in record.items()
                                                           if key not in {"index", "status"}})
        elif record.get("status") == "ok":
            try:
                actual = normalize_grid(record.get("output"))
                diff = compare_grids(pair["output"], actual)
                result.update(actual=actual, actual_sha256=value_hash(actual), comparison=diff,
                              status="match" if diff["matches"] else "mismatch")
            except ValueError as exc:
                result.update(status="error", execution_error={"error_kind": "invalid_output", "message": str(exc),
                                                               "raw_output": record.get("output")})
        else:
            raise ValueError("Unknown execution-record status")
        outcomes.append(result)
    counts = {status: sum(row["status"] == status for row in outcomes) for status in ("match", "mismatch", "error")}
    exit_code = 2 if counts["error"] else 1 if counts["mismatch"] else 0
    return {"status": "error" if exit_code == 2 else "mismatch" if exit_code == 1 else "match",
            "exit_code": exit_code, "counts": {"labeled_pairs": len(pairs), **counts}, "pairs": outcomes}


def audit_task(root: Path, task_id: str, *, expected_program_sha256=None, timeout=10.0,
               runner=execute_racket_batch) -> dict:
    source = Path(__file__).resolve()
    report = {"schema": SCHEMA, "proposal_status": "proposed", "visibility": "private-authoring-only",
              "task_id": task_id, "tool_source": {"path": str(source), "sha256": sha256(source.read_bytes())},
              "source_files_modified": False, "runtime_staged": False}
    stage = "data_binding"
    try:
        binding = load_canonical_binding(root, task_id, expected_program_sha256)
        pairs = binding.pop("pairs")
        report.update(binding)
        stage = "racket_execution"
        execution = runner(binding["program"], [deepcopy(pair["input"]) for pair in pairs],
                           root=Path(binding["root"]), timeout=timeout)
        report["execution"] = {key: value for key, value in execution.items() if key != "results"}
        if execution.get("program_sha256") != binding["program_sha256"]:
            raise ValueError("Executed program hash differs from selected canonical source")
        ledger = _local_file(Path(binding["root"]) / binding["canonical_file"]["path"], Path(binding["root"]))
        if sha256(ledger.read_bytes()) != binding["canonical_file"]["sha256"]:
            raise ValueError("Canonical ledger changed during execution")
        stage = "comparison"
        report.update(compare_labeled_pairs(pairs, execution))
        report["coverage"] = {"all_variants": True, "variant_count": binding["variant_count"],
                              "labeled_pairs": len(pairs), "attempted_pairs": len(execution["results"]),
                              "skipped_only_unlabeled_test": len(binding["skipped_unlabeled_test"])}
    except Exception as exc:
        report.update(status="error", exit_code=2,
                      error={"stage": stage, "kind": type(exc).__name__, "message": str(exc)})
    report["admission_implication"] = ("Eligible for other checks; consistency alone does not approve data or a generator."
                                      if report["exit_code"] == 0 else
                                      "Hold these labels for inspection; this tool does not rewrite the source.")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="exact canonical task ID")
    parser.add_argument("--root", type=Path, help="explicit repository/staged root; default binds to this tool's own tree")
    parser.add_argument("--out", type=Path, required=True, help="new private authoring JSON report")
    parser.add_argument("--expected-program-sha256", help="optional exact source pin")
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds per Racket evaluation")
    args = parser.parse_args(argv)
    try:
        root = args.root if args.root is not None else find_root(__file__)
        report = audit_task(root, args.task_id, expected_program_sha256=args.expected_program_sha256, timeout=args.timeout)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    except Exception as exc:
        print(json.dumps({"status": "error", "exit_code": 2,
                          "error": {"stage": "report_write_or_root", "kind": type(exc).__name__, "message": str(exc)}}))
        return 2
    print(json.dumps({"task_id": args.task_id, "status": report["status"], "exit_code": report["exit_code"],
                      "counts": report.get("counts"), "error": report.get("error"), "report": str(args.out)}, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
