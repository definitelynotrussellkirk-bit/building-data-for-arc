"""Compact authoring probe for c1ae510562f9; never use in a visible-only solve.

This compares candidate shortcuts with every labelled canonical example and
writes three small inputs for the public ``arcpuzzles apply`` command. It does
not execute or replace the Racket authority. Saved reference outputs are read
only when --racket is explicitly supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "c1ae510562f9"
SPIRAL = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
          (2, 1), (2, 0), (1, 0), (1, 1))
SNAKE = ((0, 0), (0, 1), (0, 2), (1, 2), (1, 1),
         (1, 0), (2, 0), (2, 1), (2, 2))


def paint(count, order=SPIRAL):
    result = [[0] * 3 for _ in range(3)]
    for r, c in order[:max(0, min(count, 9))]:
        result[r][c] = 8
    return result


def interior(grid):
    gray = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 5]
    top = min(r for r, _ in gray)
    floor = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)
    return [row[left + 1:right] for row in grid[top:floor]]


def empty_row_count(grid):
    """Independent interpretation, not a source of reference labels."""
    return sum(all(value == 0 for value in row) for row in interior(grid))


def top_prefix(grid):
    count = 0
    for row in interior(grid):
        if any(row):
            break
        count += 1
    return paint(count)


def empty_area(grid):
    rows = interior(grid)
    return paint(sum(value == 0 for row in rows for value in row) // len(rows[0]))


def column_empty(grid, which):
    rows = interior(grid)
    index = {"left": 0, "middle": len(rows[0]) // 2,
             "right": len(rows[0]) - 1}[which]
    return paint(sum(row[index] == 0 for row in rows))


# These are explicitly authored proposals, not a copied declaration list from
# the production generator. The report names them accordingly.
CANDIDATE_RIVALS = {
    "alternating_rows": lambda grid: paint(empty_row_count(grid), SNAKE),
    "top_empty_prefix": top_prefix,
    "empty_area_divided_by_width": empty_area,
    "left_column_only": lambda grid: column_empty(grid, "left"),
    "middle_column_only": lambda grid: column_empty(grid, "middle"),
    "right_column_only": lambda grid: column_empty(grid, "right"),
    "any_zero_in_row": lambda grid: paint(sum(0 in row for row in interior(grid))),
    "cap_at_four": lambda grid: paint(min(4, empty_row_count(grid))),
    "span_only": lambda grid: paint(len(interior(grid))),
    "plain_row_major": lambda grid: paint(empty_row_count(grid),
                                          tuple((r, c) for r in range(3) for c in range(3))),
}


def cup(rows):
    """Gray U around explicit interiors, one blank top row and side margins."""
    width = len(rows[0]) + 4
    return ([[0] * width]
            + [[0, 5, *row, 5, 0] for row in rows]
            + [[0, *([5] * (width - 2)), 0]])


def witnesses():
    return [
        ("spiral_count_five", cup([[0, 0]] * 5 + [[8, 8]])),
        ("empty_row_after_occupied", cup([[0, 0], [8, 8], [0, 0], [8, 8]])),
        ("partial_rows_all_columns", cup([[0, 0, 0], [8, 0, 0],
                                          [0, 8, 0], [0, 0, 8]])),
        ("combined_lesson_witness", cup([[8, 0], [0, 0], [0, 0],
                                        [0, 8], [0, 0], [0, 0], [0, 0]])),
    ]


def load_selected(root):
    path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("selected_semantic_review", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    root = find_root(__file__)
    module, source = load_selected(root)
    task = Catalog(root).get(TASK_ID)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    cases = witnesses()
    canonical = []
    for pair in pairs:
        count = empty_row_count(pair["input"])
        canonical.append({
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"], "empty_rows": count,
            "independent_semantics_equal_canonical": paint(count) == pair["output"],
            "selected_self_check": module.self_check(pair["input"]),
            "candidate_rivals": {name: rival(pair["input"]) == pair["output"]
                                 for name, rival in CANDIDATE_RIVALS.items()},
        })
    report = {
        "schema": "c1ae510562f9-semantic-review-v1",
        "task_id": TASK_ID,
        "generator_sha256": file_hash(source),
        "rule_hash": task["rule_hash"],
        "rule_source_sha256": hashlib.sha256(
            task["variants"][0]["program_solution"].encode()).hexdigest(),
        "probe_sha256": file_hash(Path(__file__)),
        "canonical_labeled_pair_count": len(pairs),
        "canonical": canonical,
        "canonical_candidate_fit": {
            name: {"matched": sum(row["candidate_rivals"][name] for row in canonical),
                   "total": len(pairs),
                   "fits_all": all(row["candidate_rivals"][name] for row in canonical)}
            for name in CANDIDATE_RIVALS
        },
        "witnesses": [
            {"name": name, "input": grid,
             "independent_empty_rows": empty_row_count(grid),
             "independent_interpretation": paint(empty_row_count(grid)),
             "selected_self_check": module.self_check(grid),
             "candidate_rival_outputs": {key: rival(grid)
                                         for key, rival in CANDIDATE_RIVALS.items()}}
            for name, grid in cases
        ],
        "limits": [
            "Independent Python interpretation is diagnostic; Racket apply supplies labels.",
            "Candidate rivals are authored proposals and do not establish universal identifiability.",
            "Canonical inputs/labels are referenced in place through reviewer_support, not copied.",
        ],
    }
    if args.inputs:
        if args.inputs.exists():
            parser.error(f"refusing to overwrite {args.inputs}")
        args.inputs.parent.mkdir(parents=True, exist_ok=True)
        args.inputs.write_text(json.dumps({"inputs": [grid for _, grid in cases]}) + "\n")
    if args.racket:
        receipt = json.loads(args.racket.read_text())
        report["racket_receipt"] = {"path": str(args.racket), "sha256": file_hash(args.racket)}
        report["racket_receipt_keys"] = list(receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("generator_sha256", "rule_hash", "canonical_labeled_pair_count",
                       "canonical_candidate_fit")}, indent=2))


if __name__ == "__main__":
    main()
