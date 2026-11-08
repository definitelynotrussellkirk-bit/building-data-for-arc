"""Reproduce an undeclared row-tie ordering rival; never execute private runners.

Run preparation from the packet root, then the supported arcpuzzles apply
command retained in commands.json, and finally run this script with --verify.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "611cc0f4e0fe"
SEED = 72
BAND = "easy"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def top_row_then_color(grid):
    """Paint first/last diagonal endpoints; numeric color breaks top-row ties.

    A natural implementation can group colors numerically, then sort groups by
    their top endpoint's row. It loses the reference's column tie-break when
    two colors first occur on the same row. This is deliberately wrong.
    """
    output = [list(row) for row in grid]
    groups = {}
    for row, cells in enumerate(grid):
        for col, color in enumerate(cells):
            if color:
                groups.setdefault(color, []).append((row, col))
    for color, points in sorted(
        groups.items(), key=lambda item: (item[1][0][0], item[0])
    ):
        if len(points) < 2:
            continue
        (row, col), (last_row, last_col) = points[0], points[-1]
        dr, dc = last_row - row, last_col - col
        if dr == 0 or abs(dr) != abs(dc):
            continue
        sr, sc = (1 if dr > 0 else -1), (1 if dc > 0 else -1)
        for offset in range(abs(dr) + 1):
            output[row + sr * offset][col + sc * offset] = color
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("repo"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    repo_argument = args.repo.resolve()
    sys.path.insert(0, str(repo_argument / "shared/runtime"))
    from reviewer_support import canonical_pairs, canonical_path, find_root

    repo = find_root(repo_argument / "generators" / TASK_ID / "generator.py")
    output_dir = Path(__file__).resolve().parent
    source = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_target_" + TASK_ID, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    canonical = canonical_pairs(TASK_ID, root=repo, labeled_only=True)
    rows = []
    with canonical_path(repo).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    assert len(rows) == 1
    rule = rows[0]["program_solution"]
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    rule_sha = hashlib.sha256(rule.encode("utf-8")).hexdigest()
    assert source_sha == "d4ec1012858b37a8c0c2de83844cb4731062f979246cdb53b379fbdf8c099af1"
    assert rule_sha == "51d7c63afd4ff52bbbc05f701e5c47e8c8e8df273123e21fc9dffcf2881e7de1"

    lesson = []
    for index in range(5):
        grid = module.generate(SEED, index, difficulty=BAND)
        lesson.append({
            "input": grid,
            "output": module.rule_mirror(grid),
            "seed": SEED,
            "sample_index": index,
            "difficulty": BAND,
            "overrides": {},
            "self_check_errors": module.self_check(grid, difficulty=BAND),
            "observed_profile": module.observe_overrides(grid)["scene_profile"],
            "analysis": module.analyze_grid(grid),
        })
    inputs = [pair["input"] for pair in canonical + lesson]
    rivals = [top_row_then_color(grid) for grid in inputs]
    declared_canonical_fit = {
        name: [rival(pair["input"]) == pair["output"] for pair in canonical]
        for name, rival in module.CANONICAL_SHORTCUTS.items()
    }
    declared_refuting_demos = {
        name: [
            index for index, pair in enumerate(lesson[:4])
            if rival(pair["input"]) != pair["output"]
        ]
        for name, rival in module.LESSON_COMPETITORS.items()
    }
    report = {
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_sha256": rule_sha,
        "rule_sha256_basis": "UTF-8 bytes of the selected canonical program_solution expression, without rewriting",
        "rule_hash": module.RULE_HASH,
        "phase": "final unchanged audit target",
        "finding_type": "suspected shortcut with reproduced in-domain witness",
        "rival_name": "top_row_then_numeric_color",
        "rival_definition": "Paint diagonal color groups in top-endpoint-row order, breaking equal-row ties by numeric color instead of first-appearance column.",
        "canonical_pairs": [
            {key: pair[key] for key in ("variant", "split", "pair_index")}
            for pair in canonical
        ],
        "canonical_pair_count": len(canonical),
        "lesson": lesson,
        "lesson_assembly": "Direct generate(72, sample_index, difficulty='easy') at indices 0..4, no overrides; first four are demonstrations, index 4 is query.",
        "generator_calls": 5,
        "unique_generated_inputs": len({json.dumps(pair["input"]) for pair in lesson}),
        "apply_input_mapping": {
            "0..4": "canonical pairs in portable canonical_pairs order",
            "5..8": "demonstration sample indices 0..3",
            "9": "query sample index 4",
        },
        "canonical_rival_fit": [
            top_row_then_color(pair["input"]) == pair["output"] for pair in canonical
        ],
        "demo_rival_fit": [
            top_row_then_color(pair["input"]) == pair["output"] for pair in lesson[:4]
        ],
        "query_rival_fit": top_row_then_color(lesson[4]["input"]) == lesson[4]["output"],
        "lesson_identifiable_errors": module.lesson_identifiable(lesson[:4], lesson[4]),
        "declared_canonical_shortcut_fit": declared_canonical_fit,
        "declared_lesson_rival_refuting_demo_indices": declared_refuting_demos,
        "source_domain": "All five inputs are generated directly with no overrides, and all pass self_check. Query is canonical_opposite_slopes with exactly one endpoint crossing; no hand-authored out-of-domain mutation is used.",
        "exploration": {
            "first_search": "Query index 4, no overrides, seeds 0..63 in easy, medium, hard: 192 probes; no rival disagreement.",
            "second_search": "Easy query index 4, no overrides, seeds 0..72 inclusive: 73 probes, stopped on first rival disagreement at seed 72. Sixty-four inputs overlap first search.",
            "distinct_query_parameter_cases": 201,
            "exploratory_deduplication_basis": "Distinct (seed, difficulty, sample_index) triples; no claim about distinct grid content across the exploratory population.",
            "formal_reproducer_counts": "This script regenerates only the selected five-pair lesson and reads five canonical pairs; exploratory search counts are explicitly separate from final Racket-labelled counts.",
        },
        "limits": "One source-bound lesson and one undeclared rival; no claim of population frequency, completeness of rival coverage, or an incorrect Racket reference/generator label. Existing finite-rival policy can intentionally accept this limitation.",
    }

    assert all(report["canonical_rival_fit"])
    assert all(report["demo_rival_fit"])
    assert not report["query_rival_fit"]
    assert all(not pair["self_check_errors"] for pair in lesson)
    assert report["lesson_identifiable_errors"] == []
    assert all(all(fit) for fit in declared_canonical_fit.values())
    assert all(declared_refuting_demos.values())

    if not args.verify:
        dump(output_dir / "input.json", inputs)
        dump(output_dir / "rival.json", {
            "rival_name": report["rival_name"],
            "description": report["rival_definition"],
            "outputs_in_input_order": rivals,
            "query_output": rivals[-1],
        })
        dump(output_dir / "probe_pre_racket.json", report)
        print(json.dumps({
            "stage": "prepared",
            "generator_sha256": source_sha,
            "rule_sha256": rule_sha,
            "apply_input_count": len(inputs),
            "canonical_rival_fit": report["canonical_rival_fit"],
            "demo_rival_fit": report["demo_rival_fit"],
            "query_rival_fit": report["query_rival_fit"],
        }))
        return

    payload = json.loads((output_dir / "racket.json").read_text())
    outputs = [row["output"] for row in payload["results"]]
    assert len(outputs) == len(inputs)
    assert all(row["input"] == grid for row, grid in zip(payload["results"], inputs))
    assert all(row["valid_output"] and row["error"] is None for row in payload["results"])
    assert payload["generator_sha256"] == source_sha
    assert payload["executed_rule_hash"] == rule_sha[:12]
    assert payload["catalog_rule_hash"] == rule_sha[:12]
    assert payload["rule_hash_matches_catalog"]
    assert outputs[:len(canonical)] == [pair["output"] for pair in canonical]
    assert outputs[len(canonical):] == [pair["output"] for pair in lesson]
    assert all(rivals[i] == outputs[i] for i in range(len(inputs) - 1))
    assert rivals[-1] != outputs[-1]
    differences = [
        {"row": r, "column": c, "racket": value, "rival": rivals[-1][r][c]}
        for r, row in enumerate(outputs[-1])
        for c, value in enumerate(row) if rivals[-1][r][c] != value
    ]
    report["racket_verified"] = {
        "executed_rule_hash": payload["executed_rule_hash"],
        "rule_text_sha256": payload["rule_text_sha256"],
        "rule_text_sha256_basis": "Public apply receipt's executable Racket rule text (distinct from the canonical expression hash above)",
        "command": payload["command"],
        "cwd": payload["cwd"],
        "input_count": len(inputs),
        "canonical_labels_match": len(canonical),
        "generated_mirror_matches": len(lesson),
        "rival_canonical_match_count": len(canonical),
        "rival_demo_match_count": 4,
        "rival_query_match_count": 0,
        "different_query_cells": differences,
        "query_input": inputs[-1],
        "query_racket_output": outputs[-1],
        "query_rival_output": rivals[-1],
        "query_self_check_errors": lesson[-1]["self_check_errors"],
        "query_seed": SEED,
        "query_sample_index": 4,
        "query_overrides": {},
        "query_difficulty": BAND,
    }
    dump(output_dir / "finding.json", report)
    print(json.dumps({
        "stage": "Racket verified",
        "input_count": len(inputs),
        "canonical_fit": f"{len(canonical)}/{len(canonical)}",
        "demo_fit": "4/4",
        "query_fit": "0/1",
        "different_query_cells": differences,
        "lesson_identifiable_errors": report["lesson_identifiable_errors"],
    }))


if __name__ == "__main__":
    main()
