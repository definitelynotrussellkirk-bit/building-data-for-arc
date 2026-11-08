"""Replay this task's current Python mirror against saved public Racket receipts.

The anchor must bind the live generator and selected canonical rule. Older
receipts may bind older generators, but must name the same full executed rule.
This command does not execute Racket, relabel inputs, or change old evidence.
Exit 0: replay passed; exit 1: mirror/validator failure; exit 2: invalid evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

TASK_ID = "d3575d4206d7"
RECEIPT_SCHEMA = "arcpuzzles-apply-v1"
REPORT_SCHEMA = "d3575d4206d7-reference-replay-v1"


class EvidenceError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise EvidenceError(code, message)


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def grid_sha256(grid):
    # Public arcpuzzles-apply-v1 contract: src/arcpuzzles/runtime.py::_grid_sha256.
    # There is no whitespace, trailing newline or wrapper object in this digest.
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def portable_context():
    """Use the public reviewer helper and paths in this script's own tree."""
    script = Path(__file__).resolve()
    for ancestor in script.parents:
        for directory in (ancestor / "shared/runtime", ancestor):
            if (directory / "reviewer_support.py").is_file():
                sys.path.insert(0, str(directory))
                from reviewer_support import canonical_path, find_root
                root = find_root(script)
                source_candidates = [
                    root / "generators" / TASK_ID / "generator.py",
                    root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py",
                ]
                source = next((p for p in source_candidates if p.is_file()), None)
                require(source is not None, "missing_generator", f"No task generator under {root}")
                source_bytes = source.read_bytes()
                # Compile exactly the bytes we hash, without accepting stale bytecode.
                spec = importlib.util.spec_from_file_location("current_receipt_replay_generator", source)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                exec(compile(source_bytes, str(source), "exec"), module.__dict__)
                require(getattr(module, "TASK_ID", None) == TASK_ID, "wrong_generator_task", "Generator TASK_ID differs")
                require(getattr(module, "GENERATOR_ID", None) == TASK_ID, "wrong_generator_task", "Generator GENERATOR_ID differs")
                for name in ("rule_mirror", "self_check", "strict_canonical_like"):
                    require(callable(getattr(module, name, None)), "missing_replay_hook", f"Missing {name}")
                ledger = canonical_path(root)
                rules = []
                with ledger.open(encoding="utf-8") as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        row = json.loads(line)
                        if row.get("task_id") == TASK_ID:
                            rule = row.get("program_solution")
                            require(isinstance(rule, str) and rule.strip(), "missing_selected_rule", "Matching canonical row has no rule")
                            rules.append(rule)
                require(bool(rules), "missing_selected_rule", f"No canonical rule for {TASK_ID}")
                normalized = {sha256_bytes(" ".join(rule.split()).encode()) for rule in rules}
                require(len(normalized) == 1, "ambiguous_selected_rule", "Canonical task rows select different rules")
                selected_hash = next(iter(normalized))[:12]
                require(getattr(module, "RULE_HASH", None) == selected_hash, "generator_rule_pin_mismatch", "Generator rule pin differs from selected canonical rule")
                return module, source, {
                    "root": str(root), "source_path": str(source),
                    "source_sha256": sha256_bytes(source_bytes), "version": getattr(module, "VERSION", None),
                    "selected_rule_hash": selected_hash, "canonical_path": str(ledger),
                    "canonical_rule_rows": len(rules),
                    "canonical_raw_program_sha256": sorted({sha256_bytes(rule.encode()) for rule in rules}),
                    "mode_helper": "_mode_first",
                    "mode_helper_docstring": getattr(getattr(module, "_mode_first", None), "__doc__", None),
                }
    raise EvidenceError("missing_reviewer_support", "No public reviewer_support helper in this script's tree")


def hash_field(value, label, length=64):
    require(isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{length}}}", value),
            "malformed_hash", f"{label} must be a lowercase {length}-digit SHA-256 string")


def literal_grid(value, label):
    require(isinstance(value, list) and bool(value), "invalid_grid", f"{label}: expected a nonempty grid")
    require(all(isinstance(row, list) and bool(row) for row in value), "invalid_grid", f"{label}: rows must be nonempty lists")
    width = len(value[0])
    require(all(len(row) == width for row in value), "invalid_grid", f"{label}: ragged rows")
    require(all(type(cell) is int and 0 <= cell <= 9 for row in value for cell in row),
            "invalid_grid", f"{label}: cells must be literal integers 0..9")


def read_receipt(path, selected_rule, *, anchor_rule_text=None, current_source=None):
    raw = path.read_bytes()
    receipt = json.loads(raw)
    require(isinstance(receipt, dict), "invalid_receipt", f"{path}: expected an object")
    require(receipt.get("schema") == RECEIPT_SCHEMA, "wrong_schema", f"{path}: wrong receipt schema")
    for name in ("task_id", "rule_task_id"):
        require(receipt.get(name) == TASK_ID, "wrong_task", f"{path}: {name} differs from {TASK_ID}")
    require(receipt.get("reference") == "canonical", "wrong_reference", f"{path}: canonical reference required")
    hash_field(receipt.get("executed_rule_hash"), f"{path}: executed_rule_hash", 12)
    hash_field(receipt.get("catalog_rule_hash"), f"{path}: catalog_rule_hash", 12)
    hash_field(receipt.get("rule_text_sha256"), f"{path}: rule_text_sha256")
    hash_field(receipt.get("generator_sha256"), f"{path}: generator_sha256")
    require(receipt["executed_rule_hash"] == selected_rule == receipt["catalog_rule_hash"],
            "selected_rule_mismatch", f"{path}: executed/catalog rule differs from live selected rule")
    require(receipt.get("rule_hash_matches_catalog") is True, "rule_match_flag_false", f"{path}: rule match flag must be true")
    if current_source is not None:
        require(receipt["generator_sha256"] == current_source, "stale_anchor_source",
                f"{path}: anchor generator {receipt['generator_sha256']} differs from current source {current_source}")
    if anchor_rule_text is not None:
        require(receipt["rule_text_sha256"] == anchor_rule_text, "full_rule_text_mismatch",
                f"{path}: full executed rule text differs from anchor")
    rows = receipt.get("results")
    require(isinstance(rows, list) and 1 <= len(rows) <= 64, "invalid_results", f"{path}: expected 1..64 results")
    for index, row in enumerate(rows):
        label = f"{path}: result {index}"
        require(isinstance(row, dict), "invalid_result", f"{label}: expected an object")
        require(type(row.get("index")) is int and row["index"] == index, "invalid_result_index", f"{label}: wrong index")
        require(row.get("valid_output") is True and "error" in row and row["error"] is None,
                "reference_result_failure", f"{label}: successful reference output required")
        for name in ("input", "output"):
            literal_grid(row.get(name), f"{label} {name}")
            hash_field(row.get(name + "_sha256"), f"{label} {name}_sha256")
            actual_hash = grid_sha256(row[name])
            require(row[name + "_sha256"] == actual_hash, "grid_hash_mismatch",
                    f"{label} {name}: stored {row[name + '_sha256']} differs from computed {actual_hash}")
    identity = {
        "path": str(path), "receipt_sha256": sha256_bytes(raw), "schema": RECEIPT_SCHEMA,
        "input_generator_sha256": receipt["generator_sha256"],
        "executed_rule_hash": receipt["executed_rule_hash"], "rule_text_sha256": receipt["rule_text_sha256"],
        "validated_result_count": len(rows), "original_command": receipt.get("command"),
        "original_cwd": receipt.get("cwd"),
    }
    return receipt, identity


def differing_coordinates(expected, actual):
    coordinates = []
    for r in range(max(len(expected), len(actual))):
        expected_row = expected[r] if r < len(expected) else []
        actual_row = actual[r] if r < len(actual) else []
        for c in range(max(len(expected_row), len(actual_row))):
            if c >= len(expected_row) or c >= len(actual_row) or expected_row[c] != actual_row[c]:
                coordinates.append([r, c])
    return coordinates


def replay(args, report):
    report["phase"] = "load_current_source"
    module, source, context = portable_context()
    report["current_generator"] = context
    report["phase"] = "validate_anchor"
    anchor, anchor_identity = read_receipt(args.anchor, context["selected_rule_hash"], current_source=context["source_sha256"])
    report["anchor"] = anchor_identity
    report["phase"] = "validate_reference_receipts"
    paths = [path.resolve() for path in args.receipts]
    require(len(set(paths)) == len(paths), "duplicate_receipt", "The same receipt path was supplied twice")
    validated = []
    for path in paths:
        receipt, identity = read_receipt(path, context["selected_rule_hash"], anchor_rule_text=anchor["rule_text_sha256"])
        report["reference_receipts"].append(identity)
        validated.append(receipt)
    result_count = sum(len(receipt["results"]) for receipt in validated)
    if args.expect_count is not None:
        require(result_count == args.expect_count, "unexpected_input_count",
                f"Expected {args.expect_count} retained inputs, found {result_count}")
    report["phase"] = "replay_current_mirror_and_validators"
    report["reference_input_count"] = result_count
    report["unique_input_count"] = len({row["input_sha256"] for receipt in validated for row in receipt["results"]})
    counts = report["counts"]
    for receipt_index, receipt in enumerate(validated):
        for row in receipt["results"]:
            record = {"receipt_index": receipt_index, "result_index": row["index"],
                      "input_sha256": row["input_sha256"], "reference_output_sha256": row["output_sha256"]}
            for name in ("self_check", "strict_canonical_like"):
                try:
                    source_grid = copy.deepcopy(row["input"])
                    errors = getattr(module, name)(source_grid)
                    require(isinstance(errors, list) and all(isinstance(error, str) for error in errors),
                            "invalid_validator_result", f"{name} must return a list of strings")
                    require(source_grid == row["input"], "input_mutation", f"{name} changed its input")
                    record[name] = errors
                    counts[name]["rejected" if errors else "accepted"] += 1
                except Exception as exc:
                    record[name + "_exception"] = f"{type(exc).__name__}: {exc}"
                    counts[name]["exceptions"] += 1
            try:
                source_grid = copy.deepcopy(row["input"])
                output = module.rule_mirror(source_grid)
                literal_grid(output, "current mirror output")
                require(source_grid == row["input"], "input_mutation", "rule_mirror changed its input")
                record["mirror_output_sha256"] = grid_sha256(output)
                record["mirror_matches_reference"] = output == row["output"]
                counts["mirror"]["matched" if output == row["output"] else "mismatched"] += 1
                if output != row["output"]:
                    record["differing_coordinates"] = differing_coordinates(row["output"], output)
            except Exception as exc:
                record["mirror_exception"] = f"{type(exc).__name__}: {exc}"
                counts["mirror"]["exceptions"] += 1
            report["results"].append(record)
    require(sha256_bytes(source.read_bytes()) == context["source_sha256"], "source_changed_during_replay",
            "Generator bytes changed while replaying")
    report["phase"] = "complete"
    failures = counts["mirror"]["mismatched"] + counts["mirror"]["exceptions"]
    failures += sum(counts[name]["rejected"] + counts[name]["exceptions"] for name in ("self_check", "strict_canonical_like"))
    report["status"] = "failed" if failures else "passed"
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, nargs="+", required=True)
    parser.add_argument("--expect-count", type=int)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        print(f"Refusing to overwrite {args.out}", file=sys.stderr)
        return 2
    args.anchor = args.anchor.resolve()
    report = {
        "schema": REPORT_SCHEMA, "task_id": TASK_ID, "status": "error", "phase": "initialize",
        "label_basis": "Replay of saved public Racket outputs; no new Racket execution or labels.",
        "grid_hash_contract": {"receipt_schema": RECEIPT_SCHEMA, "algorithm": "SHA-256",
                               "serialization": "json.dumps(grid, separators=(',', ':')).encode()",
                               "public_implementation": "src/arcpuzzles/runtime.py::_grid_sha256"},
        "mirror_limit": "The current source calibrates fallback ties for at most three distinct noncyan uniform-row colors; wider tied palettes require Racket.",
        "tool_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "reference_receipts": [],
        "counts": {"self_check": {"accepted": 0, "rejected": 0, "exceptions": 0},
                   "strict_canonical_like": {"accepted": 0, "rejected": 0, "exceptions": 0},
                   "mirror": {"matched": 0, "mismatched": 0, "exceptions": 0}}, "results": [],
    }
    try:
        code = replay(args, report)
    except EvidenceError as exc:
        report["error"] = {"code": exc.code, "message": str(exc)}
        code = 2
    except (OSError, ValueError, TypeError, KeyError, ImportError) as exc:
        report["error"] = {"code": "invalid_evidence_or_environment", "message": f"{type(exc).__name__}: {exc}"}
        code = 2
    report["exit_code"] = code
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key in ("status", "phase", "error", "reference_input_count", "unique_input_count", "counts", "exit_code")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
