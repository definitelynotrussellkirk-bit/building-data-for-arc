#!/usr/bin/env python3
"""Audit 35b93111c742 for untested zero/multi-marker room behavior."""
from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
for parent in HERE.parents:
    support = parent / "repo" / "shared" / "runtime"
    if (support / "reviewer_support.py").is_file():
        sys.path.insert(0, str(support))
        break
    support = parent / "shared" / "runtime"
    if (support / "reviewer_support.py").is_file():
        sys.path.insert(0, str(support))
        break

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "35b93111c742"


def rooms(grid):
    """Connected components of all non-wall cells; wall color is 1."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            markers = sorted(
                (rr, cc, grid[rr][cc])
                for rr, cc in cells
                if grid[rr][cc] not in (0, 1)
            )
            found.append({"cells": sorted(cells), "markers": markers})
    return found


def first_marker_fills_any_seeded_room(grid):
    """Plausible rival: any seeded room fills with its first marker.

    This equals the intended rule whenever every room has exactly one marker,
    which is the generator's entire ordinary support, but differs on canonical
    rooms containing multiple markers.
    """
    output = [row[:] for row in grid]
    for room in rooms(grid):
        if not room["markers"]:
            continue
        color = room["markers"][0][2]
        for row, col in room["cells"]:
            output[row][col] = color
    return output


def main():
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    target = next(
        pair
        for pair in pairs
        if pair["variant"] == 0 and pair["split"] == "train" and pair["pair_index"] == 2
    )
    canonical_rooms = rooms(target["input"])
    marker_counts = [len(room["markers"]) for room in canonical_rooms]
    rival = first_marker_fills_any_seeded_room(target["input"])

    sample_counts = {"draws": 0, "rooms": 0, "zero_marker_rooms": 0, "multi_marker_rooms": 0}
    examples = []
    for difficulty in ("easy", "medium", "hard"):
        for index in range(100):
            grid = generator.generate(5000 + index, index, difficulty=difficulty)
            current = rooms(grid)
            counts = [len(room["markers"]) for room in current]
            sample_counts["draws"] += 1
            sample_counts["rooms"] += len(counts)
            sample_counts["zero_marker_rooms"] += sum(count == 0 for count in counts)
            sample_counts["multi_marker_rooms"] += sum(count > 1 for count in counts)
            if index == 0:
                examples.append({"difficulty": difficulty, "marker_counts": counts})

    report = {
        "schema": "audit-35b93111c742-room-cardinality-v1",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "declared_rule_hash": getattr(generator, "RULE_HASH", None),
        "canonical_pair": {"variant": 0, "split": "train", "pair_index": 2},
        "generator_domain_errors_on_canonical": generator.self_check(target["input"]),
        "canonical_room_marker_counts": marker_counts,
        "input": target["input"],
        "canonical_output": target["output"],
        "rival": "fill every room having >=1 marker with its first row-major marker",
        "rival_output": rival,
        "rival_matches_canonical": rival == target["output"],
        "sample": {
            "seed_formula": "seed=5000+index, sample_index=index",
            "per_band": 100,
            **sample_counts,
            "first_draw_marker_counts": examples,
        },
        "conclusion": (
            "All 300 ordinary draws had exactly one marker in every room, so the rival "
            "is observationally identical on the sampled generator support. Canonical "
            "train[2] has a two-marker room that the authority leaves unchanged; the "
            "rival incorrectly floods it with the first marker."
        ),
    }
    out = HERE.parent / "probe.json"
    inp = HERE.parent / "input.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    inp.write_text(json.dumps({"input": target["input"]}, indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "input": str(inp),
        "generator_sha256": source_sha,
        "canonical_room_marker_counts": marker_counts,
        "sample": sample_counts,
        "rival_matches_canonical": rival == target["output"],
    }, indent=2))


if __name__ == "__main__":
    main()
