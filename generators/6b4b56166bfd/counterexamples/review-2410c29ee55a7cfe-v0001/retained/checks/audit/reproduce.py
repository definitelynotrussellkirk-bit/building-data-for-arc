"""Reproduce the two assigned findings without modifying either audit target.

Run with the packet's review.py run wrapper from its outer root.
The prepare step records Python diagnostics; the verify step consumes separate
public arcpuzzles apply receipts for authoritative outputs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


def load(root, task):
    path = root / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_" + task, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def local_rule(grid, changed_code=None, alternative=None):
    """Independent coordinate implementation for the control-motif audit."""
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value and (r, c) != (0, 0)]
    top, left = min(r for r, _, _ in cells), min(c for _, c, _ in cells)
    height = max(r for r, _, _ in cells) - top + 1
    width = max(c for _, c, _ in cells) - left + 1
    code = grid[0][0]
    operation = {1: "cw90", 2: "half_turn", 3: "flip_lr", 4: "flip_ud"}[code]
    if code == changed_code:
        operation = alternative
    output = [[0] * len(grid[0]) for _ in grid]
    for rr, cc, value in cells:
        r, c = rr - top, cc - left
        if operation == "cw90":
            r, c = c, height - 1 - r
        elif operation == "ccw90":
            r, c = width - 1 - c, r
        elif operation == "half_turn":
            r, c = height - 1 - r, width - 1 - c
        elif operation == "flip_lr":
            c = width - 1 - c
        elif operation == "flip_ud":
            r = height - 1 - r
        elif operation != "identity":
            raise ValueError(operation)
        if not (0 <= top + r < len(output) and 0 <= left + c < len(output[0])):
            raise ValueError("rival would clip; this audit excludes that case")
        output[top + r][left + c] = value
    return output


def orbit_rule(grid):
    pivot = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5)
    pr, pc = pivot
    output = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                dr, dc = r - pr, c - pc
                for a, b in ((dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)):
                    output[pr + a][pc + b] = value
    return output


def prepare(root, destination):
    task = "6b4b56166bfd"
    module, digest = load(root, task)
    out = destination / task
    cases = []
    for kwargs in ({"grid_h": 14}, {"grid_w": 14}, {"grid_h": 5},
                   {"n_cells": 2.75}, {"unknown_axis": 1}):
        try:
            grid = module.generate(0, 0, difficulty="easy", **kwargs)
            cases.append({"overrides": kwargs, "returned": True,
                          "shape": [len(grid), len(grid[0])],
                          "seed_cells": sum(v not in (0, 5) for row in grid for v in row),
                          "self_check": module.self_check(grid), "input": grid})
        except Exception as exc:
            cases.append({"overrides": kwargs, "returned": False,
                          "exception": type(exc).__name__, "message": str(exc)})
    base = module.generate(0, 0, difficulty="easy", n_cells=1)
    r, c = next((r, c) for r, row in enumerate(base) for c, v in enumerate(row) if v not in (0, 5))
    invalid = []
    for value in (12, True, 2.75):
        grid = copy.deepcopy(base); grid[r][c] = value
        invalid.append({"replacement": value, "input": grid,
                        "self_check": module.self_check(grid)})
    ordinary = [module.generate(seed, 0, difficulty=band)
                for band in ("easy", "medium", "hard") for seed in range(4)]
    report = {"task_id": task, "generator_sha256": digest,
              "seed": 0, "sample_index": 0, "difficulty": "easy",
              "override_cases": cases, "invalid_color_cases": invalid,
              "ordinary_sample": {"bands": ["easy", "medium", "hard"],
                                  "seeds": [0, 1, 2, 3], "sample_index": 0,
                                  "count": len(ordinary),
                                  "validator_failures": sum(bool(module.self_check(g)) for g in ordinary)},
              "canonical_validator_findings": [module.self_check(pair["input"])
                                                for pair in canonical_pairs(task, root=root)]}
    write(out / "findings.json", report)
    write(out / "input.json", ordinary)

    task = "a7d4df2828a0"
    module, digest = load(root, task)
    first, total, covered, ambiguous = None, 0, 0, 0
    rivals = {1: "ccw90", 3: "flip_ud", 4: "flip_lr"}
    for seed in range(200):
        grids = [module.generate(seed, index, difficulty="medium") for index in range(14)]
        labels = [local_rule(g) for g in grids]
        for start in range(10):
            total += 1
            window = grids[start:start + 5]
            if {g[0][0] for g in window[:4]} != {1, 2, 3, 4}:
                continue
            covered += 1
            query_code = window[4][0][0]
            alternative = rivals.get(query_code)
            if alternative is None:
                continue
            predictions = [local_rule(g, query_code, alternative) for g in window]
            expected = labels[start:start + 5]
            if predictions[:4] == expected[:4] and predictions[4] != expected[4]:
                ambiguous += 1
                if first is None:
                    first = {"task_id": task, "generator_sha256": digest,
                             "seed": seed, "sample_indices": list(range(start, start + 5)),
                             "difficulty": "medium", "codes": [g[0][0] for g in window],
                             "changed_code": query_code, "alternative": alternative,
                             "rival_outputs": predictions, "python_expected": expected,
                             "validator_findings": [module.self_check(g) for g in window],
                             "label_basis": "Python diagnostic, pending Racket replay"}
                    write(destination / task / "input.json", window)
    if first is None:
        raise RuntimeError("No all-codes-present symmetry witness found")
    write(destination / task / "metadata.json", first)
    write(destination / task / "frequency.json", {
        "task_id": task, "generator_sha256": digest, "difficulty": "medium",
        "seeds": [0, 199], "starts": [0, 9], "demos": 4, "queries": 1,
        "total_overlapping_lessons": total, "all_codes_present": covered,
        "ambiguous_among_all_codes_present": ambiguous,
        "rivals": {str(k): v for k, v in rivals.items()},
        "label_basis": "Python diagnostic only; first witness is separately Racket-replayed"})
    print(json.dumps({"prepared": ["6b4b56166bfd", task], "all_codes_witness": {
        key: first[key] for key in ("seed", "sample_indices", "codes", "changed_code", "alternative")},
        "frequency": {"total": total, "covered": covered, "ambiguous": ambiguous}}))


def verify(root, destination):
    for task in ("6b4b56166bfd", "a7d4df2828a0"):
        module, digest = load(root, task)
        out = destination / task
        report = json.loads((out / "racket.json").read_text())
        grids = json.loads((out / "input.json").read_text())
        assert report["generator_sha256"] == digest
        assert report["rule_hash_matches_catalog"]
        assert len(report["results"]) == len(grids)
        for g, result in zip(grids, report["results"]):
            assert result["input"] == g and result["valid_output"] and result["error"] is None
            assert module.self_check(g) == []
            expected = orbit_rule(g) if task == "6b4b56166bfd" else local_rule(g)
            assert result["output"] == expected
        if task == "a7d4df2828a0":
            metadata = json.loads((out / "metadata.json").read_text())
            matches = [result["output"] == rival for result, rival in
                       zip(report["results"], metadata["rival_outputs"])]
            assert matches == [True, True, True, True, False]
            write(out / "verified_witness.json", {
                "task_id": task, "generator_sha256": digest,
                "rule_hash": report["executed_rule_hash"],
                "rule_text_sha256": report["rule_text_sha256"],
                "codes": metadata["codes"], "rival_matches": matches,
                "all_four_controls_demonstrated": True,
                "actual_query_output": report["results"][-1]["output"],
                "rival_query_output": metadata["rival_outputs"][-1],
                "status": "reproduced_teaching_ambiguity"})
        print(task, "Racket checked", len(grids), "inputs; source", digest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--out", type=Path, default=Path("../checks/audit"))
    args = parser.parse_args()
    root = find_root(Path.cwd())
    (prepare if args.mode == "prepare" else verify)(root, args.out)
