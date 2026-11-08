#!/usr/bin/env python3
"""Opt-in authoring obligation: foreground per-color cell-count conservation.

Use only when a reviewed rule is expected to preserve each color 1..9:
    python check_color_conservation.py --receipt RACKET_APPLY.json --out NEW.json
This is not a universal ARC law. Shape and background-cell counts may change.
The tool analyzes retained arcpuzzles-apply-v1 evidence, without executing a rule.
Recorded source identities bind provenance; they do not certify label semantics
or claim that the retained source matches a subsequently edited live generator.
Exit 0: preserved; 1: count mismatch; 2: malformed/stale/error evidence or I/O.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


IDENTITIES = ("task_id", "rule_task_id", "generator_sha256", "rule_text_sha256",
              "executed_rule_hash", "catalog_rule_hash")


def grid_digest(grid):
    # Same compact JSON convention as arcpuzzles.runtime._grid_sha256.
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def validate_grid(grid, label):
    require(isinstance(grid, list) and 1 <= len(grid) <= 30,
            f"{label}: expected 1..30 rows")
    width = None
    for row in grid:
        require(isinstance(row, list) and 1 <= len(row) <= 30,
                f"{label}: expected 1..30 cells per row")
        require(all(type(cell) is int and 0 <= cell <= 9 for cell in row),
                f"{label}: cells must be integer colors 0..9")
        require(width is None or len(row) == width, f"{label}: ragged grid")
        width = len(row)


def analyze(receipt):
    require(isinstance(receipt, dict), "receipt must be an object")
    require(receipt.get("schema") == "arcpuzzles-apply-v1", "wrong receipt schema")
    for name in IDENTITIES:
        value = receipt.get(name)
        require(isinstance(value, str) and bool(value.strip()), f"missing identity: {name}")
        if name.endswith("sha256"):
            require(re.fullmatch(r"[0-9a-f]{64}", value) is not None,
                    f"invalid SHA-256 identity: {name}")
        elif name.endswith("rule_hash"):
            require(re.fullmatch(r"[0-9a-f]+", value) is not None,
                    f"invalid rule hash: {name}")
    require(receipt["executed_rule_hash"] == receipt["catalog_rule_hash"]
            and receipt.get("rule_hash_matches_catalog") is True,
            "executed/catalog rule hash disagreement or missing match flag")
    rows = receipt.get("results")
    require(isinstance(rows, list) and bool(rows), "results must be a nonempty list")
    checked = []
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"result {index}: expected object")
        require(type(row.get("index")) is int and row["index"] == index,
                f"result {index}: missing or out-of-order index")
        require(row.get("valid_output") is True and "error" in row and row["error"] is None,
                f"result {index}: invalid/error evidence")
        counts = []
        for side in ("input", "output"):
            grid = row.get(side)
            validate_grid(grid, f"result {index} {side}")
            require(row.get(f"{side}_sha256") == grid_digest(grid),
                    f"result {index}: stale {side}_sha256")
            cells = Counter(cell for line in grid for cell in line)
            counts.append({str(color): cells[color] for color in range(1, 10)})
        before, after = counts
        delta = {color: after[color] - before[color] for color in before}
        checked.append({"index": index, "preserved": not any(delta.values()),
                        "input_counts": before, "output_counts": after,
                        "delta_by_color": delta,
                        "lost_cells": sum(-n for n in delta.values() if n < 0),
                        "gained_cells": sum(n for n in delta.values() if n > 0)})
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="new JSON report; never overwritten")
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        print(f"ERROR: output already exists: {args.out}", file=sys.stderr)
        return 2
    report = {"schema": "arcpuzzles-color-conservation-v1",
              "obligation": "opt-in foreground per-color cell-count conservation (colors 1..9)",
              "receipt_path": str(args.receipt), "receipt_sha256": None,
              "status": "ERROR", "checked_rows": 0, "results": []}
    code = 2
    try:
        raw = args.receipt.read_bytes()
        report["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
        receipt = json.loads(raw, parse_constant=reject_constant)
        if isinstance(receipt, dict):
            report.update({name: receipt.get(name) for name in IDENTITIES})
        results = analyze(receipt)
        code = 0 if all(row["preserved"] for row in results) else 1
        report.update(status="PASS" if code == 0 else "FAIL",
                      checked_rows=len(results), results=results)
    except (OSError, ValueError, TypeError) as error:
        report["error"] = str(error)
    try:
        with args.out.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2, allow_nan=False)
            output.write("\n")
    except (OSError, ValueError) as error:
        print(f"ERROR: cannot write report: {error}", file=sys.stderr)
        return 2
    print(f"{report['status']}: {report['checked_rows']} rows; {args.out}")
    return code


if __name__ == "__main__":
    sys.exit(main())
