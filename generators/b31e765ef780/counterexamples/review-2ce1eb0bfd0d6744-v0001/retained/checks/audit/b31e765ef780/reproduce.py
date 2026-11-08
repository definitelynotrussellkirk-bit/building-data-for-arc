"""Reproduce a finite area-versus-hole shortcut gap using public Racket labels.

Exit 0 means the reported defect reproduced, not that this generator passed.
No generator, rule, notes, or shared source is modified.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "b31e765ef780"
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid):
    visited, result = set(), []
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            pending, cells = [(row, col)], set()
            visited.add((row, col))
            while pending:
                r, c = pending.pop()
                cells.add((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width and (rr, cc) not in visited
                            and grid[rr][cc] == color):
                        visited.add((rr, cc))
                        pending.append((rr, cc))
            result.append((color, cells))
    return result


def hole_count(cells):
    """Count enclosed cells with only this monochrome component as a barrier."""
    top, bottom = min(r for r, _ in cells) - 1, max(r for r, _ in cells) + 1
    left, right = min(c for _, c in cells) - 1, max(c for _, c in cells) + 1
    pending, outside = [(top, left)], {(top, left)}
    while pending:
        r, c = pending.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            rr, cc = point
            if (top <= rr <= bottom and left <= cc <= right
                    and point not in cells and point not in outside):
                outside.add(point)
                pending.append(point)
    return sum((r, c) not in cells and (r, c) not in outside
               for r in range(top, bottom + 1) for c in range(left, right + 1))


def area_at_least_eight(grid):
    output = copy.deepcopy(grid)
    for _, cells in components(grid):
        if len(cells) >= 8:
            for row, col in cells:
                output[row][col] = 8
    return output


def counterexample():
    grid = [[0] * 14 for _ in range(12)]
    for row in range(1, 4):
        for col in range(1, 4):
            if row in (1, 3) or col in (1, 3):
                grid[row][col] = 2
    for row in range(1, 4):
        for col in range(8, 11):
            grid[row][col] = 3
    for row, col in ((7, 3), (8, 3), (9, 3), (9, 4)):
        grid[row][col] = 4
    return grid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE.parents[2] / "repo")
    parser.add_argument("--out-dir", type=Path, default=HERE)
    args = parser.parse_args()
    names = ("input.json", "reference.json", "rival.json", "probe.json")
    if any((args.out_dir / name).exists() for name in names):
        parser.error("Refusing to overwrite retained evidence; select a new --out-dir")
    root = find_root(args.root)
    gen, source, digest = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    requests = [{"id": f"canonical/{i}", "kind": "canonical", "input": pair["input"],
                 **{key: pair[key] for key in ("variant", "split", "pair_index")}}
                for i, pair in enumerate(canonical)]
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            requests.append({"id": f"{band}/{index}", "kind": "generated", "seed": 0,
                             "sample_index": index, "difficulty": band, "overrides": {},
                             "input": gen.generate(0, index, difficulty=band)})
    requests.append({"id": "solid-nine-cell-block", "kind": "handmade", "seed": None,
                     "sample_index": None, "difficulty": None, "overrides": {},
                     "recipe": "12x14 zero grid; color-2 3x3 perimeter at (1,1); color-3 solid 3x3 at (1,8); color-4 L at [(7,3),(8,3),(9,3),(9,4)]",
                     "input": counterexample()})
    args.out_dir.mkdir(parents=True, exist_ok=True)

    def save(name, value):
        with (args.out_dir / name).open("x", encoding="utf-8") as handle:
            json.dump(value, handle, separators=(",", ":"))
            handle.write("\n")

    save("input.json", {"inputs": [row["input"] for row in requests]})
    report = {"schema": "arcpuzzles-size-shortcut-audit-v1", "task_id": TASK,
              "generator_sha256": digest, "script_sha256": sha(Path(__file__)),
              "command": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                          "environment": {"TMPDIR": os.environ.get("TMPDIR")}},
              "reference_api": "Catalog(root).apply(TASK, inputs, timeout=120)",
              "classification": "finite canonical-compatible size shortcut / missing discriminating generation support",
              "population": {"canonical_pairs": len(canonical), "generated_pairs": 36,
                             "seed": 0, "indices": list(range(12)),
                             "bands": ["easy", "medium", "hard"], "overrides": {}},
              "limits": "Finite audit; handmade query is validator-accepted and follows the stated hole/solid grammar, but is not emitted by the current solid-shape inventory. No incorrect Racket label or all-seed claim.",
              "errors": [], "rows": []}
    try:
        reference = Catalog(root).apply(TASK, [row["input"] for row in requests], timeout=120)
        save("reference.json", reference)
        if len(reference["results"]) != len(requests):
            raise ValueError("Reference batch is incomplete")
        if reference["generator_sha256"] != digest or not reference["rule_hash_matches_catalog"]:
            raise ValueError("Reference source/rule identity mismatch")
        report["reference_identity"] = {key: reference[key] for key in
            ("generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")}
        for index, (request, result) in enumerate(zip(requests, reference["results"], strict=True)):
            if result["error"] is not None or not result["valid_output"] or result["input"] != request["input"]:
                raise ValueError(f"Invalid reference result for {request['id']}: {result['error']}")
            rival = area_at_least_eight(request["input"])
            row = {key: value for key, value in request.items() if key != "input"}
            row.update(reference_index=index, self_check=gen.self_check(request["input"]),
                       rival_matches_reference=rival == result["output"],
                       components=[{"color": color, "area": len(cells), "enclosed_cells": hole_count(cells)}
                                   for color, cells in components(request["input"])])
            if request["kind"] == "canonical":
                row["reference_matches_canonical_label"] = result["output"] == canonical[index]["output"]
            if request["kind"] == "handmade":
                row["different_cells"] = sum(a != b for left, right in zip(rival, result["output"], strict=True)
                                              for a, b in zip(left, right, strict=True))
                save("rival.json", {"name": "area_at_least_eight", "input": request["input"],
                                    "rival_output": rival, "reference_index": index})
            report["rows"].append(row)
        canonical_rows = [row for row in report["rows"] if row["kind"] == "canonical"]
        generated = [row for row in report["rows"] if row["kind"] == "generated"]
        query = report["rows"][-1]
        report["summary"] = {"canonical_fit_count": sum(row["rival_matches_reference"] for row in canonical_rows),
                             "generated_fit_count": sum(row["rival_matches_reference"] for row in generated),
                             "query_self_check": query["self_check"], "query_different_cells": query["different_cells"],
                             "query_components": query["components"]}
        report["reproduced"] = (len(canonical_rows) == 3
            and all(row["rival_matches_reference"] and row["reference_matches_canonical_label"] for row in canonical_rows)
            and len(generated) == 36 and all(row["rival_matches_reference"] for row in generated)
            and all(not row["self_check"] for row in report["rows"])
            and query["different_cells"] == 9)
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["generator_sha256_after"] = sha(source)
    report["source_stable"] = digest == report["generator_sha256_after"]
    report["reproduced"] = bool(report.get("reproduced") and not report["errors"] and report["source_stable"])
    report["exit_code"] = 0 if report["reproduced"] else 1
    report["evidence"] = {name: {"path": str(args.out_dir / name), "sha256": sha(args.out_dir / name)}
                          for name in names[:-1] if (args.out_dir / name).is_file()}
    save("probe.json", report)
    print(json.dumps({key: report.get(key) for key in
                      ("generator_sha256", "reference_identity", "summary", "source_stable", "reproduced", "exit_code", "errors")}, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
