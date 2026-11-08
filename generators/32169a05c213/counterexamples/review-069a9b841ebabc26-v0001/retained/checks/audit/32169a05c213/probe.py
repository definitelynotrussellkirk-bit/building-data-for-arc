#!/usr/bin/env python3
"""Source-bound audit of the cap-at-four size-sorting shortcut.

Run prepare, label input.json through public arcpuzzles apply, then run verify.
The selected generator and every Racket authority remain unchanged.
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "32169a05c213"
HERE = Path(__file__).resolve().parent


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def components(grid):
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            result.append({
                "color": color, "size": len(cells), "top": top, "left": left,
                "height": max(rr for rr, _ in cells) - top + 1,
                "width": max(cc for _, cc in cells) - left + 1,
                "cells": cells,
            })
    return result


def capped_count_rival(grid):
    """Count 1, 2, 3, or 'at least 4'; break all remaining ties by color."""
    objects = sorted(components(grid), key=lambda x: (
        min(x["size"], 4), x["color"], x["top"], x["left"]))
    h = max(x["height"] for x in objects)
    w = sum(x["width"] for x in objects) + len(objects) - 1
    output = [[0] * w for _ in range(h)]
    offset = 0
    for obj in objects:
        for r, c in obj["cells"]:
            output[r - obj["top"]][offset + c - obj["left"]] = obj["color"]
        offset += obj["width"] + 1
    return output


def object_summary(grid):
    return [{k: obj[k] for k in ("size", "color", "top", "left", "height", "width")}
            for obj in sorted(components(grid), key=lambda x: (x["size"], x["color"]))]


def prepare(gen, root, digest):
    inputs, cases = [], []

    def add(grid, **metadata):
        errors = gen.self_check(grid)
        assert errors == [], errors
        inputs.append(grid)
        cases.append({
            "index": len(cases), **metadata, "self_check_errors": errors,
            "observed_axes": gen.observe_overrides(grid),
            "objects_by_true_size": object_summary(grid),
            "rival_output": capped_count_rival(grid),
        })

    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    for pair in pairs:
        add(pair["input"], kind="canonical", variant=pair["variant"],
            split=pair["split"], pair_index=pair["pair_index"])
    originals = {}
    for band in ("easy", "medium", "hard"):
        for seed in range(2):
            for sample_index in range(4):
                grid = gen.generate(seed, sample_index, difficulty=band)
                add(grid, kind="generated", seed=seed, sample_index=sample_index,
                    difficulty=band, overrides={})
                originals[(band, seed, sample_index)] = (len(cases) - 1, grid)
    for sample_index in (2, 3):
        source_index, base = originals[("medium", 0, sample_index)]
        largest = sorted(components(base), key=lambda x: x["size"])[-2:]
        a, b = [x["color"] for x in largest]
        swap = {a: b, b: a}
        mutated = [[swap.get(value, value) for value in row] for row in base]
        add(mutated, kind="counterfactual", seed=0, sample_index=sample_index,
            difficulty="medium", overrides={}, source_case_index=source_index,
            transformation={"kind": "swap_unequal_large_object_colors", "map": swap},
            generated_support=False,
            documented_domain=True,
            domain_basis="Only colors of the two largest unequal objects are swapped; "
                         "dimensions, size profile, shapes, component separation, and "
                         "three distinct nonzero colors are preserved.")
    rule_programs = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rule_programs.append(hashlib.sha256(row["program_solution"].encode()).hexdigest())
    dump("input.json", {"inputs": inputs})
    dump("cases.json", {
        "task_id": TASK_ID, "generator_sha256": digest,
        "generator_rule_hash": gen.RULE_HASH,
        "canonical_program_solution_sha256": rule_programs,
        "cases": cases,
    })
    print(json.dumps({"prepared": len(cases), "canonical": len(pairs),
                      "generated": 24, "counterfactual": 2,
                      "generator_sha256": digest}))


def verify(gen, root, digest):
    metadata = json.loads((HERE / "cases.json").read_text())
    inputs = json.loads((HERE / "input.json").read_text())["inputs"]
    receipt = json.loads((HERE / "racket.json").read_text())
    assert metadata["generator_sha256"] == digest == receipt["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    results = receipt["results"]
    assert len(results) == len(inputs) == len(metadata["cases"])
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    expected_canonical = {(p["variant"], p["split"], p["pair_index"]): p["output"]
                          for p in canonical}
    counts = {kind: {"inputs": 0, "rival_matches_racket": 0, "self_check_passed": 0}
              for kind in ("canonical", "generated", "counterfactual")}
    unique_inputs = {kind: set() for kind in counts}
    rows = []
    declared_canonical = {name: 0 for name in gen.CANONICAL_SHORTCUTS}
    declared_generated = {name: 0 for name in gen.LESSON_COMPETITORS}
    for grid, case, result in zip(inputs, metadata["cases"], results):
        assert result["error"] is None, result
        assert gen.self_check(grid) == []
        kind = case["kind"]
        assert result["input"] == grid
        unique_inputs[kind].add(result["input_sha256"])
        counts[kind]["inputs"] += 1
        counts[kind]["self_check_passed"] += 1
        equal = case["rival_output"] == result["output"]
        counts[kind]["rival_matches_racket"] += int(equal)
        assert equal == (kind != "counterfactual"), (case["index"], kind, equal)
        if kind == "canonical":
            assert expected_canonical[(case["variant"], case["split"], case["pair_index"])] == result["output"]
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                declared_canonical[name] += int(rival(grid) == result["output"])
        if kind == "generated":
            for name, rival in gen.LESSON_COMPETITORS.items():
                declared_generated[name] += int(rival(grid) == result["output"])
        rows.append({"case_index": case["index"], "kind": kind,
                     "rival_matches_racket": equal,
                     "racket_output": result["output"],
                     "input_sha256": result["input_sha256"],
                     "output_sha256": result["output_sha256"]})
    for kind, hashes in unique_inputs.items():
        counts[kind]["unique_inputs"] = len(hashes)
    report = {
        "task_id": TASK_ID, "finding": "reproduced_capped_count_shortcut",
        "generator_sha256": digest,
        "rule_identity": {key: receipt[key] for key in (
            "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256",
            "rule_hash_matches_catalog")},
        "counts": counts,
        "unique_input_total": len(set().union(*unique_inputs.values())),
        "generated_settings": {"seeds": [0, 1], "sample_indices": [0, 1, 2, 3],
                               "bands": ["easy", "medium", "hard"], "overrides": {}},
        "declared_canonical_shortcut_match_counts": declared_canonical,
        "declared_lesson_competitor_generated_match_counts": declared_generated,
        "production_lesson_verdict": "not_run",
        "query_rotation_verdict": "not_run",
        "rows": rows,
    }
    dump("report.json", report)
    case = metadata["cases"][-1]
    result = results[-1]
    dump("counterexample.json", {
        "task_id": TASK_ID,
        "generator_sha256": digest,
        "canonical_program_solution_sha256": metadata["canonical_program_solution_sha256"],
        "rule_identity": report["rule_identity"],
        "batch_case_index": case["index"],
        "seed": case["seed"], "sample_index": case["sample_index"],
        "difficulty": case["difficulty"], "overrides": case["overrides"],
        "transformation": case["transformation"],
        "self_check_errors": case["self_check_errors"],
        "documented_domain": case["documented_domain"],
        "generated_support": case["generated_support"],
        "domain_basis": case["domain_basis"],
        "observed_axes": case["observed_axes"],
        "input": result["input"],
        "actual_racket_output": result["output"],
        "rival_output": case["rival_output"],
        "input_sha256": result["input_sha256"],
        "output_sha256": result["output_sha256"],
        "cwd_relative_to_WORK": ".", "payload_cwd_relative_to_WORK": "repo",
        "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                 TASK_ID, "--input", "../checks/audit/32169a05c213/input.json",
                 "--out", "../checks/audit/32169a05c213/racket.json"],
    })
    print(json.dumps({"finding": report["finding"], "counts": counts,
                      "generator_sha256": digest}))


def main():
    root = find_root(__file__)
    gen, _source, digest = load_selected_generator(TASK_ID, root=root)
    if sys.argv[1:] == ["prepare"]:
        prepare(gen, root, digest)
    elif sys.argv[1:] == ["verify"]:
        verify(gen, root, digest)
    else:
        raise SystemExit("usage: probe.py prepare|verify")


if __name__ == "__main__":
    main()
