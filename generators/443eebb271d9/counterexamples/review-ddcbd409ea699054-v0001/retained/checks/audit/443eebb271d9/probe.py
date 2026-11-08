"""Reproduce a demo-fit/query-diverge shortcut for audit target 443eebb271d9."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "443eebb271d9"
FINDING_ID = "A-443-1"
HERE = Path(__file__).resolve().parent
PACKET_ROOT = HERE.parents[2]
SOURCE = PACKET_ROOT / "repo" / "generators" / TASK_ID / "generator.py"
LESSON = HERE / "lesson.jsonl"
RACKET = HERE / "racket.json"
OUTPUT = HERE / "counterexample.json"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def color_components(grid: list[list[int]], color: int = 7) -> list[tuple[tuple[int, int], ...]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    found: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        found.append(tuple(sorted(cells)))
    return found


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def largest_component_rival(grid: list[list[int]]) -> list[list[int]]:
    """Treat only the largest 4-connected color-7 component as the source glyph.

    Ties are resolved by the first row-major component.  Once that component is
    chosen, repetition/recoloring follows the documented lattice operation.
    """
    components = color_components(grid)
    if not components:
        raise ValueError("no color-7 component")
    chosen = max(components, key=len)  # stable: row-major first wins equal-size ties
    row0, col0, row1, col1 = bbox(chosen)
    glyph_h = row1 - row0 + 1
    glyph_w = col1 - col0 + 1
    normalized = {(row - row0, col - col0) for row, col in chosen}
    hstep = glyph_w + 1
    vstep = glyph_h + 1
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(row0, height):
        for col in range(col0, width):
            rel_row, rel_col = row - row0, col - col0
            local = (rel_row % vstep, rel_col % hstep)
            instance = rel_col // hstep
            row_repeat = rel_row // vstep
            if local in normalized and (row_repeat == 0 or instance % 3 == 2):
                output[row][col] = 6 if instance % 3 == 2 else 7
    return output


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("shape mismatch")
    return [
        [row, col]
        for row, (lrow, rrow) in enumerate(zip(left, right))
        for col, (lval, rval) in enumerate(zip(lrow, rrow))
        if lval != rval
    ]


def main() -> None:
    generator = load_generator()
    lesson = json.loads(LESSON.read_text(encoding="utf-8").splitlines()[0])
    racket = json.loads(RACKET.read_text(encoding="utf-8"))
    pairs = lesson["train"] + lesson["test"]
    authoritative = [entry["output"] for entry in racket["results"]]
    if [pair["output"] for pair in pairs] != authoritative:
        raise AssertionError("materialized lesson labels differ from independent apply receipt")

    validation = [generator.self_check(pair["input"]) for pair in pairs]
    profiles = [generator.observe_overrides(pair["input"]).get("scene_profile") for pair in pairs]
    component_sizes = [sorted((len(c) for c in color_components(pair["input"])), reverse=True) for pair in pairs]
    rivals = [largest_component_rival(pair["input"]) for pair in pairs]
    matches = [rival == actual for rival, actual in zip(rivals, authoritative)]
    query_diff = differing_cells(authoritative[-1], rivals[-1])

    root = find_root(SOURCE)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_rows = []
    for pair in canonical:
        rival = largest_component_rival(pair["input"])
        canonical_rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "component_sizes": sorted((len(c) for c in color_components(pair["input"])), reverse=True),
                "rival_matches": rival == pair["output"],
            }
        )

    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "finding_id": FINDING_ID,
        "classification": "reproduced lesson ambiguity",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": racket["executed_rule_hash"],
        "rule_source_sha256": racket["rule_text_sha256"],
        "seed": lesson["seed"],
        "sample_index": lesson["sample_index"],
        "sample_indices": lesson["sample_indices"],
        "difficulty": lesson["provenance"]["difficulty"],
        "overrides": lesson["provenance"]["overrides"],
        "validator_errors": validation,
        "documented_domain": all(not errors for errors in validation),
        "profiles": {"train": profiles[:3], "query": profiles[3]},
        "component_sizes": {"train": component_sizes[:3], "query": component_sizes[3]},
        "rival": {
            "name": "largest_4_connected_component_only",
            "description": (
                "Use only the largest row-major 4-connected color-7 component as the glyph, "
                "then apply the same bbox-periodic repeat, every-third recolor, and vertical extension."
            ),
            "train_matches": matches[:3],
            "train_fit_count": sum(matches[:3]),
            "train_count": 3,
            "query_matches": matches[3],
            "query_difference_count": len(query_diff),
            "query_differing_cells": query_diff,
        },
        "canonical_check": {
            "rows": canonical_rows,
            "visible_train_fit_count": sum(row["rival_matches"] for row in canonical_rows if row["split"] == "train"),
            "visible_train_count": sum(row["split"] == "train" for row in canonical_rows),
            "all_labeled_fit_count": sum(row["rival_matches"] for row in canonical_rows),
            "all_labeled_count": len(canonical_rows),
            "interpretation": (
                "This is an undeclared lesson/solver rival, not a canonical shortcut: it fits the two "
                "visible canonical train pairs and is refuted by the labeled canonical query."
            ),
        },
        "query_input": pairs[-1]["input"],
        "actual_racket_output": authoritative[-1],
        "rival_output": rivals[-1],
        "commands": [
            {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "generate",
                    TASK_ID, "--count", "1", "--seed", "2", "--sample-index", "0",
                    "--difficulty", "medium", "--train", "3", "--test", "1", "--allow-unapproved",
                    "--timeout", "300", "--out", "../checks/audit/443eebb271d9/lesson.jsonl",
                ],
                "exit_code": 0,
            },
            {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
                    TASK_ID, "--input", "../checks/audit/443eebb271d9/input.json",
                    "--out", "../checks/audit/443eebb271d9/racket.json",
                ],
                "exit_code": 0,
            },
            {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3",
                    "../checks/audit/443eebb271d9/probe.py",
                ],
                "exit_code": 0,
            },
        ],
    }
    if not result["documented_domain"]:
        raise AssertionError("counterexample is outside the target validator domain")
    if matches[:3] != [True, True, True] or matches[3]:
        raise AssertionError(f"expected 3 demo fits and query divergence, got {matches}")
    if result["canonical_check"]["visible_train_fit_count"] != result["canonical_check"]["visible_train_count"]:
        raise AssertionError("rival does not fit every visible canonical demonstration")
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "finding_id": FINDING_ID,
        "profiles": result["profiles"],
        "train_fit": f"{result['rival']['train_fit_count']}/{result['rival']['train_count']}",
        "query_difference_count": len(query_diff),
        "canonical_visible_train_fit": (
            f"{result['canonical_check']['visible_train_fit_count']}/"
            f"{result['canonical_check']['visible_train_count']}"
        ),
        "out": str(OUTPUT),
    }, indent=2))


if __name__ == "__main__":
    main()
