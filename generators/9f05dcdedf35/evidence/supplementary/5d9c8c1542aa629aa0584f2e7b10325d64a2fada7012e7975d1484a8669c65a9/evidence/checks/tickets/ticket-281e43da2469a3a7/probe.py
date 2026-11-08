#!/usr/bin/env python3
"""Bounded source-bound witness for the distinct-neighbor-color shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "9f05dcdedf35"
TICKET_ID = "ticket-281e43da2469a3a7"
TICKET_SEED = "9f5f289336b1c57b777297887a014ff1c0df7334249e35d2397bcf6a931ead3e"
EXPECTED_SOURCE_SHA256 = "32eae1598eb032fa4de9d4af7c65aa2113405e9c392b5a8398b2071d5a135ecc"
EXPECTED_RULE_HASH = "85fa63b64c3c"
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def canonical_row(root: Path) -> dict:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task missing: {TASK_ID}")


def objects(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            color = grid[row0][col0]
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for drow, dcol in CARDINAL:
                    nxt = row + drow, col + dcol
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, cells))
    return result


def graph(grid: list[list[int]]):
    objs = objects(grid)
    neighbors = [set() for _ in objs]
    for left, (_, cells) in enumerate(objs):
        for right in range(left + 1, len(objs)):
            other = objs[right][1]
            if any((row + drow, col + dcol) in other
                   for row, col in cells for drow, dcol in CARDINAL):
                neighbors[left].add(right)
                neighbors[right].add(left)
    return objs, neighbors


def paint(grid, objs, selected):
    output = [list(row) for row in grid]
    for index in selected:
        for row, col in objs[index][1]:
            output[row][col] = 8
    return output


def degree_one_rule(grid):
    objs, neighbors = graph(grid)
    return paint(grid, objs, [i for i, linked in enumerate(neighbors) if len(linked) == 1])


def distinct_neighbor_color_rival(grid):
    objs, neighbors = graph(grid)
    selected = [
        i for i, linked in enumerate(neighbors)
        if len({objs[j][0] for j in linked}) == 1
    ]
    return paint(grid, objs, selected)


def racket_output(program: str, grid):
    callable_rule = wrap_rule(program)
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        bridge.eval_text(f"(define __ticket_rule {callable_rule})")
        bridge.define_grid("__ticket_input", grid)
        return bridge.eval_text("(__ticket_rule __ticket_input)")


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    row = canonical_row(root)
    normalized_rule = " ".join(row["program_solution"].split())
    rule_hash = hashlib.sha256(normalized_rule.encode()).hexdigest()[:12]

    generation_seed = int(TICKET_SEED[:16], 16)
    sample_index = 0  # fixed teaching branch in the current period-4 schedule
    difficulty = "medium"
    grid = generator.generate(generation_seed, sample_index, difficulty=difficulty)
    actual = racket_output(row["program_solution"], grid)
    intended = degree_one_rule(grid)
    rival = distinct_neighbor_color_rival(grid)
    objs, neighbors = graph(grid)
    witness_nodes = [
        {
            "object_index": i,
            "color": objs[i][0],
            "degree": len(linked),
            "neighbor_colors": sorted({objs[j][0] for j in linked}),
            "cells": [list(point) for point in sorted(objs[i][1])],
        }
        for i, linked in enumerate(neighbors)
        if len(linked) > 1 and objs[i][0] != 8
        and len({objs[j][0] for j in linked}) == 1
    ]
    differences = [
        [row_index, col_index]
        for row_index, output_row in enumerate(actual)
        for col_index, value in enumerate(output_row)
        if value != rival[row_index][col_index]
    ]
    checks = {
        "source_identity_matches_ticket": source_sha256 == EXPECTED_SOURCE_SHA256,
        "rule_identity_matches_ticket": rule_hash == EXPECTED_RULE_HASH == generator.RULE_HASH,
        "validator_accepts": generator.self_check(grid) == [],
        "lawful_same_color_neighbor_witness_present": bool(witness_nodes),
        "independent_degree_one_mirror_matches_racket": intended == actual,
        "distinct_neighbor_color_rival_is_refuted": rival != actual and bool(differences),
    }
    result = {
        "schema": "arcpuzzles-bounded-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "generation": {
            "seed_formula": "int(ticket_seed[:16], 16)",
            "seed": generation_seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {},
        },
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha256,
            "expected_sha256": EXPECTED_SOURCE_SHA256,
        },
        "rule_hash_12": rule_hash,
        "shortcut": "recolor any component having exactly one distinct neighboring color",
        "witness_nodes": witness_nodes,
        "input": grid,
        "actual_racket_output": actual,
        "independent_degree_one_output": intended,
        "shortcut_output": rival,
        "differing_coordinates": differences,
        "checks": checks,
        "all_passed": all(checks.values()),
        "interpretation": (
            "A lawful teaching draw contains a degree-2 component whose two neighboring "
            "objects share one color. The canonical object-degree rule preserves it, while "
            "the distinct-neighbor-color shortcut recolors it."
        ),
    }
    output_path = Path(__file__).with_name("witness.json")
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_passed": result["all_passed"],
        "witness_nodes": len(witness_nodes),
        "differing_coordinates": len(differences),
        "output": str(output_path),
    }, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
