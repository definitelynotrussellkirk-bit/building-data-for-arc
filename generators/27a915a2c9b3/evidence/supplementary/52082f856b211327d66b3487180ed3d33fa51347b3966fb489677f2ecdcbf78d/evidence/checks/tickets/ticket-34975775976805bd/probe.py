#!/usr/bin/env python3
"""One bounded adversarial witness probe for ticket-34975775976805bd."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "27a915a2c9b3"
PINNED_SOURCE_SHA256 = "9993d1beffeb7ec2f4ac71f7f1c05b9256e2cf47130b4529ad1d83c306e5a765"
PINNED_RULE_HASH = "043982b4cb5e"
PROBE_SEED_HEX = "61da0fe447293041b0e1121989584428e6f3e3c999df913796d086ffa862f1d3"
OUTPUT = Path(__file__).with_name("witness.json")


def all_red_halo_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: every red cell is an interior marker."""
    height = len(grid)
    width = len(grid[0])
    red = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    output = deepcopy(grid)
    for marker_row, marker_col in red:
        for row in range(max(0, marker_row - 1), min(height, marker_row + 2)):
            for col in range(max(0, marker_col - 1), min(width, marker_col + 2)):
                if (row, col) not in red:
                    output[row][col] = 1
    return output


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != PINNED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha256} != {PINNED_SOURCE_SHA256}")
    if generator.RULE_HASH != PINNED_RULE_HASH:
        raise RuntimeError(f"rule drift: {generator.RULE_HASH} != {PINNED_RULE_HASH}")

    probe_seed = int(PROBE_SEED_HEX, 16)
    for sample_index in range(64):
        grid = generator.generate(probe_seed, sample_index, difficulty="medium")
        errors = generator.self_check(grid, difficulty="medium")
        if errors:
            raise RuntimeError("generated witness failed self_check: " + "; ".join(errors))
        analysis = generator._inspect_scene(grid)
        if analysis is None:
            raise RuntimeError("generated witness was not analyzable")
        canonical = generator.rule_mirror(grid)
        shortcut = all_red_halo_shortcut(grid)
        differences = [
            {
                "row": row,
                "col": col,
                "canonical": canonical[row][col],
                "shortcut": shortcut[row][col],
            }
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if canonical[row][col] != shortcut[row][col]
        ]
        if not differences:
            continue
        interior = {tuple(cell) for cell in analysis["interior_markers"]}
        external = sorted(
            (row, col)
            for row, line in enumerate(grid)
            for col, value in enumerate(line)
            if value == 2 and (row, col) not in interior
        )
        linked = []
        for item in differences:
            point = (item["row"], item["col"])
            triggers = [
                [row, col]
                for row, col in external
                if abs(row - point[0]) <= 1 and abs(col - point[1]) <= 1
            ]
            if triggers:
                linked.append({**item, "outside_red_triggers": triggers})
        if not linked:
            raise RuntimeError("shortcut differed without an outside-red attribution")

        payload = {
            "schema": "arcpuzzles-ticket-adversarial-witness-v1",
            "ticket_id": "ticket-34975775976805bd",
            "status": "completed",
            "task_id": TASK_ID,
            "source_path": str(Path(source_path).relative_to(root)),
            "source_sha256": source_sha256,
            "rule_hash": generator.RULE_HASH,
            "probe_seed": PROBE_SEED_HEX,
            "probe_seed_as_integer": probe_seed,
            "sample_index": sample_index,
            "difficulty": "medium",
            "scene_profile": analysis["scene_profile"],
            "lawfulness": {
                "self_check_errors": errors,
                "rectangle_count": analysis["rectangle_count"],
                "inside_marker_count": analysis["interior_count"],
                "outside_distractor_count": analysis["external_count"],
            },
            "shortcut": {
                "name": "all_red_cells_trigger_halos",
                "description": (
                    "Treat every red input cell as a marker, paint its clipped 3x3 "
                    "blue halo, and preserve every red cell. This ignores the "
                    "green-rectangle membership condition."
                ),
            },
            "difference_count": len(differences),
            "outside_red_cells": [list(cell) for cell in external],
            "attributed_differences": linked,
            "input_sha256": hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest(),
            "input": grid,
            "canonical_output": canonical,
            "shortcut_output": shortcut,
        }
        OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "status": "completed",
                    "sample_index": sample_index,
                    "scene_profile": analysis["scene_profile"],
                    "outside_distractors": analysis["external_count"],
                    "difference_count": len(differences),
                    "witness": str(OUTPUT),
                },
                sort_keys=True,
            )
        )
        return 0
    raise RuntimeError("bounded probe found no shortcut-separating witness in 64 samples")


if __name__ == "__main__":
    raise SystemExit(main())
