#!/usr/bin/env python3
"""Findings-only audit: independent vertical normalization versus row alignment.

Capture uses the selected generator. Canonical labels are obtained separately
through the public `arcpuzzles apply` command, then assessed by summarize.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "afa7a3af9331"
HERE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())


def write_new(name, value):
    with (HERE / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def objects(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color != 0}
    found = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        stack, cells = [start], {start}
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            for pos in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if pos in remaining and grid[pos[0]][pos[1]] == color:
                    remaining.remove(pos)
                    cells.add(pos)
                    stack.append(pos)
        found.append((color, cells))
    if len(found) != 2:
        raise ValueError("Rival requires exactly two monochrome objects")
    return found


def preserve_relative_rows(grid):
    """Overlay horizontally; normalize rows only once for the entire scene.

    This plausible rival omits independently normalizing each object's top row.
    It has no seeds, shape-size constants, stored labels, or canonical exceptions.
    """
    found = objects(grid)
    top = min(r for _, cells in found for r, _ in cells)
    normalized = []
    for color, cells in found:
        left = min(c for _, c in cells)
        normalized.append((color, {(r - top, c - left) for r, c in cells}))
    (ca, a), (cb, b) = normalized
    height = max(r for r, _ in a | b) + 1
    width = max(c for _, c in a | b) + 1
    return [[8 if (r, c) in a & b else ca if (r, c) in a else cb if (r, c) in b else 0
             for c in range(width)] for r in range(height)]


def capture():
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK, root=root)
    canonical = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
                 if json.loads(line).get("task_id") == TASK]
    assert len(canonical) == 1
    program = canonical[0]["program_solution"]
    cases = []
    for pair in canonical_pairs(TASK, root=root):
        cases.append({"id": f"canonical_{pair['split']}_{pair['pair_index']}",
                      "kind": "canonical", "input": pair["input"],
                      "recorded_output": pair["output"], "variant": pair["variant"],
                      "split": pair["split"], "pair_index": pair["pair_index"]})
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(4):
            seed = 1700 + band_index
            grid = generator.generate(seed, index, difficulty=band)
            cases.append({"id": f"generated_{band}_{index}", "kind": "generated",
                          "seed": seed, "sample_index": index, "difficulty": band,
                          "overrides": {}, "input": grid})
    original = next(case for case in cases if case["id"] == "generated_easy_3")
    shifted = deepcopy(original["input"])
    right_color, right_cells = max(objects(shifted), key=lambda item: min(c for _, c in item[1]))
    assert max(r for r, _ in right_cells) + 1 < len(shifted)
    for r, c in right_cells:
        shifted[r][c] = 0
    for r, c in right_cells:
        assert shifted[r + 1][c] == 0
        shifted[r + 1][c] = right_color
    cases.append({"id": "shifted_right_operand", "kind": "handmade_from_generated",
                  "source_case": original["id"], "seed": original["seed"],
                  "sample_index": original["sample_index"], "difficulty": original["difficulty"],
                  "overrides": {}, "transformation": "Translate only the right object down by one row; preserve canvas and all cells/colors.",
                  "input": shifted})
    for case in cases:
        case["input_sha256"] = grid_hash(case["input"])
        case["domain_errors"] = generator.self_check(case["input"])
        case["mirror_output"] = generator.rule_mirror(case["input"])
        case["rival_output"] = preserve_relative_rows(case["input"])
        case["object_top_rows"] = [min(r for r, _ in cells) for _, cells in objects(case["input"])]
    sources = {str(source.relative_to(root)): source_hash}
    for relative in (f"generators/{TASK}/tests/test_audit_{TASK}.py", f"generators/{TASK}/notes.md",
                     "shared/runtime/reviewer_support.py"):
        sources[relative] = digest((root / relative).read_bytes())
    report = {"schema": "afa7a3af9331-row-normalization-audit-v1", "task_id": TASK,
              "classification": "shortcut/domain-support question; labels pending public Racket execution",
              "source_hashes": sources, "program_text_sha256": digest(program.encode()),
              "normalized_rule_hash": digest(" ".join(program.split()).encode())[:12],
              "program": program, "generator_version": generator.VERSION,
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "invocation": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())},
              "cases": cases,
              "lesson": {"demonstrations": [f"generated_easy_{i}" for i in range(3)],
                         "generated_query": "generated_easy_3", "counterfactual_query": "shifted_right_operand"}}
    write_new("cases.json", report)
    write_new("inputs.json", {"inputs": [case["input"] for case in cases]})
    write_new("shifted_input.json", {"input": shifted})
    print(json.dumps({"cases": len(cases), "generator_sha256": source_hash,
                      "domain_errors": sum(bool(case["domain_errors"]) for case in cases),
                      "rival_matches_mirror_generated": sum(case["rival_output"] == case["mirror_output"]
                                                           for case in cases if case["kind"] == "generated")}))


def summarize():
    captured = json.loads((HERE / "cases.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    results = applied["results"]
    assert len(results) == len(captured["cases"])
    assessed = []
    for case, result in zip(captured["cases"], results):
        assert result["input"] == case["input"]
        row = deepcopy(case)
        row["racket_result"] = result
        row["rival_matches_racket"] = row["rival_output"] == result.get("output")
        row["mirror_matches_racket"] = row["mirror_output"] == result.get("output")
        if "recorded_output" in case:
            row["canonical_matches_racket"] = case["recorded_output"] == result.get("output")
        assessed.append(row)
    groups = {}
    for kind in ("canonical", "generated", "handmade_from_generated"):
        rows = [row for row in assessed if row["kind"] == kind]
        groups[kind] = {"count": len(rows),
                        "racket_success": sum(row["racket_result"].get("valid_output") is True and not row["racket_result"].get("error") for row in rows),
                        "domain_valid": sum(not row["domain_errors"] for row in rows),
                        "rival_matches": sum(row["rival_matches_racket"] for row in rows),
                        "mirror_matches": sum(row["mirror_matches_racket"] for row in rows)}
    by_id = {row["id"]: row for row in assessed}
    lesson = captured["lesson"]
    query = by_id[lesson["counterfactual_query"]]
    summary = {"schema": "afa7a3af9331-row-normalization-assessment-v1", "task_id": TASK,
               "classification": "reproduced shortcut/domain-support gap; no generated-label mismatch found",
               "generator_sha256": next(value for path, value in captured["source_hashes"].items() if path.endswith("generator.py")),
               "program_text_sha256": captured["program_text_sha256"],
               "normalized_rule_hash": captured["normalized_rule_hash"],
               "cases_sha256": digest((HERE / "cases.json").read_bytes()),
               "racket_receipt_sha256": digest((HERE / "racket.json").read_bytes()),
               "groups": groups,
               "lesson": {**lesson, "rival_fits_all_demonstrations": all(by_id[name]["rival_matches_racket"] for name in lesson["demonstrations"]),
                          "rival_fits_original_generated_query": by_id[lesson["generated_query"]]["rival_matches_racket"],
                          "rival_fits_counterfactual_query": query["rival_matches_racket"],
                          "canonical_translation_invariance": query["racket_result"]["output"] == by_id[lesson["generated_query"]]["racket_result"]["output"]},
               "counterexample": query,
               "limitations": ["Only 12 ordinary draws, four canonical pairs and one handcrafted translation were executed here.",
                               "The translated input passes the selected self_check and the canonical rule, but is outside this sampler's fixed aligned-row support.",
                               "This finding does not show incorrect Racket labels for generated inputs or prove solver learning.",
                               "The canonical demonstration layouts refute this rival; newly sampled lessons alone do not."]}
    write_new("assessment.json", summary)
    print(json.dumps({key: summary[key] for key in ("classification", "groups", "lesson")}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("capture", "summarize"))
    arguments = parser.parse_args()
    capture() if arguments.command == "capture" else summarize()
