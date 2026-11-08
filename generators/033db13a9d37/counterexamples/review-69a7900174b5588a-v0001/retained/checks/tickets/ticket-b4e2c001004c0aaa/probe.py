#!/usr/bin/env python3
"""One bounded, source-bound witness probe for 033db13a9d37.

The only tested shortcut is column-major seed selection (leftmost, then topmost)
versus the selected row-major first-nonzero rule. The search uses one fixed
seed, one difficulty band, at most 32 consecutive four-pair windows, and stops
at the first three-demo/one-query ambiguity. The retained candidate is then
replayed with the exact canonical Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body
from reviewer_support import canonical_path, load_selected_generator

TASK_ID = "033db13a9d37"
TICKET_ID = "ticket-b4e2c001004c0aaa"
TICKET_SEED = "028915a8477e555e64bbaff5b1616a8a2f114e63404c0599a61f90bdcec20576"
EXPECTED_SOURCE_SHA256 = "9a6756b67c901b2e0b973c4c2dd30524d20f364f6af1a556b6cfb33f4fbcdda4"
EXPECTED_PROGRAM_SHA256 = "afd73fcc3dc1f7b8d34a9d7b00f5d45afbdea107cae524b65867416f69ca1d01"
EXPECTED_RULE_HASH = "3773168d1737"
GENERATOR_SEED = int(TICKET_SEED[:16], 16) & 0xFFFFFFFF
DIFFICULTY = "medium"
MAX_STARTS = 32


def sha_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def nonzero_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def render_from_cell(
    grid: list[list[int]], cell: tuple[int, int, int]
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    row, col, color = cell
    output = [[0 for _ in range(width)] for _ in range(height)]
    for out_row in range(row + 1):
        for out_col in range(col % 2, width, 2):
            output[out_row][out_col] = 4
    if row + 1 < height:
        output[row + 1][col] = color
    return output


def row_major_output(grid: list[list[int]]) -> list[list[int]]:
    cells = nonzero_cells(grid)
    if not cells:
        raise ValueError("grid has no nonzero seed")
    return render_from_cell(grid, cells[0])


def column_major_output(grid: list[list[int]]) -> list[list[int]]:
    cells = nonzero_cells(grid)
    if not cells:
        raise ValueError("grid has no nonzero seed")
    return render_from_cell(grid, min(cells, key=lambda cell: (cell[1], cell[0])))


def canonical_program(root: Path) -> str:
    matches = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one canonical row, found {len(matches)}")
    program = matches[0].get("program_solution")
    if not isinstance(program, str):
        raise AssertionError("canonical row has no string program_solution")
    digest = hashlib.sha256(program.encode("utf-8")).hexdigest()
    if digest != EXPECTED_PROGRAM_SHA256:
        raise AssertionError(f"canonical program hash changed: {digest}")
    return program


def racket_outputs(
    bridge: RacketBridge, program: str, grids: list[list[list[int]]]
) -> list[list[list[int]]]:
    body = _program_body(program)
    outputs = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def select_candidate(generator) -> dict[str, Any] | None:
    for start in range(MAX_STARTS):
        grids = [
            generator.generate(
                GENERATOR_SEED,
                start + offset,
                difficulty=DIFFICULTY,
            )
            for offset in range(4)
        ]
        for grid in grids:
            errors = generator.self_check(grid, difficulty=DIFFICULTY)
            if errors:
                raise AssertionError(f"generated grid failed self_check: {errors}")
        selected = [row_major_output(grid) for grid in grids]
        rival = [column_major_output(grid) for grid in grids]
        for query_index in range(4):
            train_indices = [index for index in range(4) if index != query_index]
            if (
                all(rival[index] == selected[index] for index in train_indices)
                and rival[query_index] != selected[query_index]
            ):
                return {
                    "start": start,
                    "query_index": query_index,
                    "train_indices": train_indices,
                    "grids": grids,
                    "selected_outputs": selected,
                    "rival_outputs": rival,
                }
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    generator, source_path, source_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"peer source hash changed: {source_sha256}")
    if generator.RULE_HASH != EXPECTED_RULE_HASH:
        raise AssertionError(f"peer rule hash changed: {generator.RULE_HASH}")

    program = canonical_program(root)
    candidate = select_candidate(generator)
    report: dict[str, Any] = {
        "schema": "arc-review-targeted-column-major-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "canonical_program_sha256": EXPECTED_PROGRAM_SHA256,
        "rival": {
            "name": "column_major_seed",
            "definition": "choose the nonzero cell with minimum (column,row), then apply the same canopy/echo rendering",
            "canonical_fit_reason": "all four canonical inputs contain exactly one nonzero cell",
        },
        "search": {
            "generator_seed": GENERATOR_SEED,
            "ticket_seed": TICKET_SEED,
            "difficulty": DIFFICULTY,
            "max_starts": MAX_STARTS,
            "window_size": 4,
            "query_rotations_per_window": 4,
            "stopped_at_first_witness": True,
            "universal_claim": False,
        },
        "limits": [
            "One fixed seed and one difficulty band only.",
            "At most 32 starts; the search stops at the first witness.",
            "Only the column-major/leftmost-then-top shortcut is tested.",
            "A retained finding is source-bound and requires maintainer assessment.",
        ],
    }

    if candidate is None:
        report.update(
            {
                "status": "bounded_no_witness",
                "finding": False,
                "starts_examined": MAX_STARTS,
            }
        )
    else:
        grids = candidate["grids"]
        with RacketBridge(max_calls_before_restart=64) as bridge:
            actual = racket_outputs(bridge, program, grids)
            runtime_identity = bridge.runtime_identity

        selected = candidate["selected_outputs"]
        rival = candidate["rival_outputs"]
        if actual != selected:
            raise AssertionError("independent row-major oracle disagrees with Racket")
        train_indices = candidate["train_indices"]
        query_index = candidate["query_index"]
        if not all(rival[index] == actual[index] for index in train_indices):
            raise AssertionError("rival does not fit all retained demonstrations")
        if rival[query_index] == actual[query_index]:
            raise AssertionError("rival does not disagree on retained query")

        pairs = []
        for index, (grid, output, rival_output) in enumerate(
            zip(grids, actual, rival, strict=True)
        ):
            cells = nonzero_cells(grid)
            row_major_cell = cells[0]
            column_major_cell = min(cells, key=lambda cell: (cell[1], cell[0]))
            pairs.append(
                {
                    "window_index": index,
                    "sample_index": candidate["start"] + index,
                    "role": "query" if index == query_index else "demonstration",
                    "schedule_profile": generator.schedule_profile(
                        GENERATOR_SEED,
                        candidate["start"] + index,
                        difficulty=DIFFICULTY,
                    ),
                    "input": deepcopy(grid),
                    "racket_output": output,
                    "column_major_rival_output": rival_output,
                    "rival_matches_racket": rival_output == output,
                    "row_major_cell": list(row_major_cell),
                    "column_major_cell": list(column_major_cell),
                    "input_sha256": sha_json(grid),
                    "racket_output_sha256": sha_json(output),
                    "rival_output_sha256": sha_json(rival_output),
                    "self_check": generator.self_check(
                        grid, difficulty=DIFFICULTY
                    ),
                }
            )

        report.update(
            {
                "status": "finding",
                "finding": True,
                "starts_examined": candidate["start"] + 1,
                "witness": {
                    "start": candidate["start"],
                    "sample_indices": [
                        candidate["start"] + index for index in range(4)
                    ],
                    "query_index": query_index,
                    "train_indices": train_indices,
                    "all_three_demonstrations_fit_rival": all(
                        pairs[index]["rival_matches_racket"]
                        for index in train_indices
                    ),
                    "query_refutes_rival": not pairs[query_index][
                        "rival_matches_racket"
                    ],
                    "pairs": pairs,
                },
                "racket_runtime": runtime_identity,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "finding": report["finding"],
                "starts_examined": report["starts_examined"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
