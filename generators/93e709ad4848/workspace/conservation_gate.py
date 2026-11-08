#!/usr/bin/env python3
"""Check a declared one-object translation contract on public apply receipts.

This task-local gate does not execute an oracle or generate labels. It audits
Racket's echoed input/output pairs. Do not apply it indiscriminately to tasks
that legitimately delete, recolor, replicate, rotate, or reshape objects.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def digest_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def properties(grid):
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0])
                                 for row in grid)):
        raise ValueError("invalid rectangular grid")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("invalid colors")
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    todo = {(r, c) for r, c, v in cells}
    components = 0
    while todo:
        components += 1
        point = todo.pop()
        stack = [point]
        color = grid[point[0]][point[1]]
        while stack:
            r, c = stack.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in todo and grid[p[0]][p[1]] == color:
                    todo.remove(p)
                    stack.append(p)
    r0 = min((r for r, c, v in cells), default=0)
    c0 = min((c for r, c, v in cells), default=0)
    return {"canvas": (len(grid), len(grid[0])), "foreground": len(cells),
            "colors": sorted({v for r, c, v in cells}), "components": components,
            "normalized_pixels": sorted((r-r0, c-c0, v) for r, c, v in cells)}


def check_receipts(paths, task_id):
    failures, receipts, hashes, counts = [], [], set(), Counter()
    total = 0
    for path in paths:
        raw = path.read_bytes()
        receipt = json.loads(raw)
        if receipt.get("task_id") != task_id:
            raise ValueError(f"wrong task in {path}")
        receipts.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                         "generator_sha256": receipt.get("generator_sha256"),
                         "executed_rule_hash": receipt.get("executed_rule_hash"),
                         "rule_text_sha256": receipt.get("rule_text_sha256")})
        for result in receipt["results"]:
            total += 1
            reasons = []
            gi, go = result.get("input"), result.get("output")
            key = digest_grid(gi)
            hashes.add(key)
            if result.get("input_sha256") != key:
                reasons.append("input receipt hash mismatch")
            if result.get("error") or result.get("valid_output") is not True:
                reasons.append("reference execution or output validity failed")
            try:
                before, after = properties(gi), properties(go)
                if before["components"] != 1 or len(before["colors"]) != 1:
                    reasons.append("input violates unique monochrome object domain")
                if after["components"] != 1 or len(after["colors"]) != 1:
                    reasons.append("output violates unique monochrome object domain")
                if before["canvas"] != after["canvas"]:
                    reasons.append("canvas dimensions changed")
                if before["foreground"] != after["foreground"]:
                    reasons.append("foreground pixel count changed")
                if before["normalized_pixels"] != after["normalized_pixels"]:
                    reasons.append("object shape, holes, orientation or color changed")
                if result.get("output_sha256") != digest_grid(go):
                    reasons.append("output receipt hash mismatch")
            except (ValueError, TypeError) as exc:
                reasons.append(str(exc))
            counts.update(reasons)
            if reasons:
                failures.append({"receipt": str(path), "index": result.get("index"),
                                 "input_sha256": key, "reasons": reasons})
    if total == 0:
        raise ValueError("no reference pairs to audit")
    return {"schema": "one-object-conservation-gate-v1", "task_id": task_id,
            "contract": "one monochrome object, fixed canvas, rigid translation preserving colors and holes",
            "status": "FAIL" if failures else "PASS", "pair_count": total,
            "unique_inputs": len(hashes), "passed_pairs": total-len(failures),
            "failed_pairs": len(failures), "failure_categories": dict(counts),
            "source_receipts": receipts, "failures": failures,
            "limits": "Conservation alone does not establish the correct destination corner or lesson identifiability."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts", type=Path, nargs="+", required=True)
    parser.add_argument("--task-id", default="93e709ad4848")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be new")
    report = check_receipts(args.receipts, args.task_id)
    report["tool_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: report[k] for k in ("status", "pair_count", "unique_inputs", "failed_pairs")}))
    return 1 if report["failed_pairs"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
