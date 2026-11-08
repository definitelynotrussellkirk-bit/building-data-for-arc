#!/usr/bin/env python3
"""Passive, finite projection-collision evidence for task fc814cec3976.

No generation, rule execution, dynamic imports, or input-provided code. A
collision refutes a projection-only predictor on supplied labels; absence is
unknown. Receipt binding checks provenance consistency, not a Racket rerun.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

TASK_ID = "fc814cec3976"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
RULE_HASH = re.compile(r"[0-9a-f]{12}\Z")


def json_sha256(value):
    """Hash JSON arrays compatibly with public arcpuzzles apply receipts."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _grid(value, name):
    if not isinstance(value, list) or not 1 <= len(value) <= 30:
        raise ValueError(f"{name}: grid must have 1..30 rows")
    width = None
    for row in value:
        if not isinstance(row, list) or not 1 <= len(row) <= 30:
            raise ValueError(f"{name}: grid rows must contain 1..30 cells")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError(f"{name}: grid colors must be literal integers 0..9")
        if width is not None and len(row) != width:
            raise ValueError(f"{name}: ragged grid")
        width = len(row)
    return value


def _domain(value):
    if isinstance(value, dict) and value.get("status") in ("valid", "invalid", "error"):
        return value["status"]
    return "unknown"


def _bind_receipt(envelope, cases, base_dir):
    source, rule = envelope.get("source"), envelope.get("rule")
    authority = envelope.get("label_authority")
    if (not isinstance(source, dict) or not isinstance(rule, dict)
            or not isinstance(authority, dict) or not envelope.get("task_id")
            or not isinstance(envelope.get("scope"), str) or not envelope["scope"].strip()
            or not SHA256.fullmatch(str(source.get("generator_sha256", "")))
            or not SHA256.fullmatch(str(rule.get("callable_sha256", "")))
            or not RULE_HASH.fullmatch(str(rule.get("normalized_hash", "")))):
        raise ValueError("certifying mode requires task, source, rule, scope and label-authority provenance")
    if envelope["task_id"] != TASK_ID:
        raise ValueError(f"certifying built-in projections are scoped to {TASK_ID}")
    if authority.get("kind") != "selected_racket":
        raise ValueError("certifying labels must declare selected_racket, not Python mirror or unknown authority")
    if (not isinstance(authority.get("receipt_path"), str)
            or not authority["receipt_path"].strip()
            or not SHA256.fullmatch(str(authority.get("receipt_sha256", "")))):
        raise ValueError("certifying label provenance needs a receipt_path and receipt_sha256")
    path = (Path(base_dir) / authority["receipt_path"]).resolve()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != authority["receipt_sha256"]:
        raise ValueError("receipt file hash does not match declared provenance")
    receipt = json.loads(raw)
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be a JSON object")
    if (receipt.get("schema") != "arcpuzzles-apply-v1"
            or receipt.get("task_id") != envelope["task_id"]
            or receipt.get("generator_sha256") != source["generator_sha256"]
            or receipt.get("rule_text_sha256") != rule["callable_sha256"]
            or receipt.get("executed_rule_hash") != rule["normalized_hash"]
            or receipt.get("catalog_rule_hash") != rule["normalized_hash"]
            or receipt.get("rule_hash_matches_catalog") is not True
            or receipt.get("reference") != "canonical"):
        raise ValueError("receipt task/source/rule authority does not match envelope provenance")
    rows = receipt.get("results")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("receipt results must be objects")
    by_index = {}
    for row in rows:
        index = row.get("index")
        if type(index) is not int or index < 0 or index in by_index:
            raise ValueError("receipt result indices must be unique nonnegative integers")
        by_index[index] = row
    for case in cases:
        index = case["original"].get("receipt_result_index")
        if type(index) is not int or index not in by_index:
            raise ValueError(f"{case['id']}: missing valid receipt_result_index")
        row = by_index[index]
        if (row.get("input") != case["input"] or row.get("output") != case["output"]
                or row.get("input_sha256") != case["input_sha256"]
                or row.get("output_sha256") != case["output_sha256"]
                or row.get("valid_output") is not True or row.get("error") is not None):
            raise ValueError(f"{case['id']}: input/output labels do not match the successful receipt row")
        case["domain_status"] = _domain(row.get("generator_domain"))
    return {"verification": "receipt_hash_and_cases_verified", "receipt_sha256": authority["receipt_sha256"],
            "receipt_path": authority["receipt_path"], "matched_cases": len(cases),
            "racket_executed_by_this_tool": False,
            "limit": "Checks consistency with the retained receipt; does not independently authenticate or rerun it."}


def analyze(envelope, *, target="yellow-centers", certify=False, base_dir=None):
    """Return finite evidence. No collision means unknown, never a universal pass."""
    if not isinstance(envelope, dict) or envelope.get("schema") != "projection-cases-v1":
        raise ValueError("expected a projection-cases-v1 envelope")
    if target not in ("yellow-centers", "edit-mask"):
        raise ValueError("target must be yellow-centers or edit-mask")
    examples = envelope.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError("examples must be a nonempty list")
    cases, ids, input_labels = [], set(), {}
    for example in examples:
        if not isinstance(example, dict) or not isinstance(example.get("id"), str) or not example["id"].strip():
            raise ValueError("every example needs a nonempty string id")
        cid = example["id"]
        if cid in ids:
            raise ValueError("example IDs must be unique")
        ids.add(cid)
        inp, out = _grid(example.get("input"), f"{cid} input"), _grid(example.get("output"), f"{cid} output")
        if (len(inp), len(inp[0])) != (len(out), len(out[0])):
            raise ValueError(f"{cid}: built-in projections require matching input/output shape")
        ih, oh = json_sha256(inp), json_sha256(out)
        for field, actual in (("input_sha256", ih), ("output_sha256", oh)):
            if field in example and example[field] != actual:
                raise ValueError(f"{cid}: declared {field} hash mismatch")
        if ih in input_labels and input_labels[ih] != oh:
            raise ValueError(f"{cid}: conflicting labels for identical input; not a projection collision")
        input_labels[ih] = oh
        red = [[r, c] for r, row in enumerate(inp) for c, value in enumerate(row) if value == 2]
        key = {"shape": [len(inp), len(inp[0])], "red_cells": red}
        context = [[0 if value == 2 else value for value in row] for row in inp]
        if target == "yellow-centers":
            selected = [[r, c] for r, row in enumerate(out) for c, value in enumerate(row)
                        if value == 4 and inp[r][c] != 4]
        else:
            selected = [[r, c] for r, row in enumerate(out) for c, value in enumerate(row)
                        if value != inp[r][c]]
        cases.append({"id": cid, "input": inp, "output": out, "original": example,
                      "input_sha256": ih, "output_sha256": oh,
                      "projection": key, "projection_sha256": json_sha256(key),
                      "context_sha256": json_sha256(context), "target": selected,
                      "target_sha256": json_sha256(selected),
                      "domain_status": _domain(example.get("generator_domain")),
                      "case_scope": example.get("scope", envelope.get("scope", "unknown"))})
    label_check = (_bind_receipt(envelope, cases, base_dir or Path.cwd()) if certify else
                   {"verification": "declared_only", "racket_executed_by_this_tool": False})
    grouped = defaultdict(list)
    for case in cases:
        grouped[case["projection_sha256"]].append(case)
    groups = []
    for key_hash, rows in sorted(grouped.items()):
        first = rows[0]
        other = next((row for row in rows[1:]
                      if row["target"] != first["target"] and row["context_sha256"] != first["context_sha256"]), None)
        witness = None
        if other is not None:
            witness = {"case_ids": [first["id"], other["id"]],
                       "input_sha256": [first["input_sha256"], other["input_sha256"]],
                       "output_sha256": [first["output_sha256"], other["output_sha256"]],
                       "targets": [first["target"], other["target"]],
                       "has_domain_rejection": "invalid" in (first["domain_status"], other["domain_status"])}
        unique_inputs = len({row["input_sha256"] for row in rows})
        groups.append({"projection_sha256": key_hash, "projection": first["projection"],
                       "case_count": len(rows), "case_ids": [row["id"] for row in rows],
                       "unique_inputs": unique_inputs, "duplicate_inputs": len(rows) - unique_inputs,
                       "distinct_contexts": len({row["context_sha256"] for row in rows}),
                       "distinct_targets": len({row["target_sha256"] for row in rows}),
                       "witness": witness})
    collisions = sum(group["witness"] is not None for group in groups)
    warnings = []
    if not certify:
        warnings.append("Labels and source authority are declared only; diagnostic results are not reference-certified.")
    if any(case["domain_status"] == "invalid" for case in cases):
        warnings.append("A retained validator rejects at least one case. The collision is not evidence of final generated support.")
    if any(case["domain_status"] in ("unknown", "error") for case in cases):
        warnings.append("Generator-domain validity is unknown or errored for at least one supplied case.")
    return {
        "schema": "projection-collision-report-v1",
        "status": "witnessed_collision" if collisions else "unknown_no_witnessed_collision",
        "mode": "certifying_receipt_binding" if certify else "diagnostic",
        "task_id": envelope.get("task_id", "unknown"), "source": envelope.get("source", {}),
        "rule": envelope.get("rule", {}), "scope": envelope.get("scope", "unknown"),
        "label_authority": {"declared": envelope.get("label_authority", {}), **label_check},
        "input_projection": "shape_and_red_color_2_coordinates",
        "target_projection": target,
        "context_projection": "input_with_red_cells_replaced_by_zero",
        "projection_scope": f"Task {TASK_ID}: red=2; newly selected yellow=4; coordinates are zero-based and absolute.",
        "interpretation": ("The target is not a function of the red-layout key on at least one supplied group."
                           if collisions else "No collision was witnessed; projection sufficiency remains unknown."),
        "general_learnability_certified": False, "generated_support_certified": False,
        "summary": {"cases": len(cases), "unique_inputs": len(input_labels),
                    "duplicate_inputs": len(cases) - len(input_labels),
                    "duplicate_labeled_cases": len(cases) - len({(case['input_sha256'], case['output_sha256']) for case in cases}),
                    "projection_keys": len(groups), "collision_keys": collisions,
                    "keys_with_multiple_contexts": sum(group["distinct_contexts"] > 1 for group in groups),
                    "witnesses_with_domain_rejection": sum(bool(group["witness"] and group["witness"]["has_domain_rejection"]) for group in groups),
                    "domain_status_counts": dict(Counter(case["domain_status"] for case in cases))},
        "groups": groups,
        "cases": [{key: value for key, value in case.items() if key not in ("input", "output", "original", "projection")}
                  for case in cases],
        "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path, help="projection-cases-v1 JSON envelope")
    parser.add_argument("--target", choices=("yellow-centers", "edit-mask"), default="yellow-centers")
    parser.add_argument("--certify", action="store_true", help="require source/rule provenance and hash-bound selected-Racket receipt labels")
    parser.add_argument("--out", type=Path, help="new JSON report; refuses overwrite; omitted prints full report")
    args = parser.parse_args(argv)
    try:
        raw = args.cases.read_bytes()
        report = analyze(json.loads(raw), target=args.target, certify=args.certify, base_dir=args.cases.resolve().parent)
        report["envelope_sha256"] = hashlib.sha256(raw).hexdigest()
        report["tool_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        serialized = json.dumps(report, indent=2) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8") as handle:
                handle.write(serialized)
            print(json.dumps({"status": report["status"], "summary": report["summary"], "report": str(args.out)}))
        else:
            print(serialized, end="")
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f"projection_gate: {error}\n")
    return 0  # Both witnessed collisions and unknown are completed evidence, not universal pass/fail.


if __name__ == "__main__":
    raise SystemExit(main())
