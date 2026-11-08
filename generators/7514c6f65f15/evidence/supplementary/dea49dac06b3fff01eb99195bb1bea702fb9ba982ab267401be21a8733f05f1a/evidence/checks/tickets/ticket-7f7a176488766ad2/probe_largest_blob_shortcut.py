#!/usr/bin/env python3
"""One bounded witness search for 'largest blob' vs canonical 'tallest blob'."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "7514c6f65f15"
TICKET_SEED_HEX = "c51191ebe10df068e622ab83f633c97e2212da64ca1f8da33df27897d985968c"
MAX_SAMPLE_INDEX = 256
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            result.append(
                {
                    "color": color,
                    "cells": sorted([list(p) for p in cells]),
                    "size": len(cells),
                    "bbox_height": max(rows) - min(rows) + 1,
                    "bbox_width": max(cols) - min(cols) + 1,
                    "top": min(rows),
                    "left": min(cols),
                }
            )
    return result


def documented_lawful(grid, blobs):
    if GEN.self_check(grid):
        return False
    if len(blobs) != 3:
        return False
    if sorted(blob["size"] for blob in blobs) != [3, 4, 5]:
        return False
    if len({blob["color"] for blob in blobs}) != 3:
        return False
    if 8 in {blob["color"] for blob in blobs}:
        return False
    if len({blob["bbox_height"] for blob in blobs}) != 3:
        return False
    owners = {}
    for index, blob in enumerate(blobs):
        for r, c in blob["cells"]:
            owners[(r, c)] = index
    for (r, c), owner in owners.items():
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            other = owners.get((r + dr, c + dc))
            if other is not None and other != owner:
                return False
    return True


def recolor(grid, blob):
    out = [row[:] for row in grid]
    for r, c in blob["cells"]:
        out[r][c] = 8
    return out


def canonical_program():
    programs = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError("missing or ambiguous canonical program")
    return programs[0]


def main():
    seed = int(TICKET_SEED_HEX, 16) % (2**63)
    checked = 0
    lawful = 0
    witness = None
    for sample_index in range(MAX_SAMPLE_INDEX):
        checked += 1
        grid = GEN.generate(seed, sample_index)
        blobs = components(grid)
        if not documented_lawful(grid, blobs):
            continue
        lawful += 1
        tallest = max(blobs, key=lambda b: (b["bbox_height"], b["size"], -b["top"], -b["left"]))
        largest = max(blobs, key=lambda b: (b["size"], b["bbox_height"], -b["top"], -b["left"]))
        if tallest["cells"] != largest["cells"]:
            witness = {
                "seed": seed,
                "sample_index": sample_index,
                "input": grid,
                "components": blobs,
                "tallest_component": tallest,
                "largest_component": largest,
                "expected_tallest_output": recolor(grid, tallest),
                "largest_blob_shortcut_output": recolor(grid, largest),
            }
            break

    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": "ticket-7f7a176488766ad2",
        "task_id": TASK_ID,
        "probe_seed_hex": TICKET_SEED_HEX,
        "generator_source": str(SOURCE_PATH.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA256,
        "canonical_rule_hash": "5bd088e5acec",
        "shortcut": "recolor the largest component by cell count instead of the greatest bbox height",
        "sample_indices_checked": checked,
        "documented_lawful_inputs_checked": lawful,
        "max_sample_index_exclusive": MAX_SAMPLE_INDEX,
    }
    if witness is None:
        report.update(status="bounded_unknown", summary="No separating lawful witness found within the bounded probe.")
    else:
        source = canonical_program()
        body = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in witness["input"]) + ")"
        with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
            racket_output = bridge.eval_text(f"({body} {literal})")
        witness["canonical_racket_output"] = racket_output
        witness["input_sha256"] = digest(witness["input"])
        witness["canonical_output_sha256"] = digest(racket_output)
        witness["shortcut_output_sha256"] = digest(witness["largest_blob_shortcut_output"])
        witness["canonical_matches_tallest_oracle"] = racket_output == witness["expected_tallest_output"]
        witness["shortcut_is_separated"] = racket_output != witness["largest_blob_shortcut_output"]
        if not witness["canonical_matches_tallest_oracle"] or not witness["shortcut_is_separated"]:
            raise RuntimeError("candidate did not validate as a canonical separating witness")
        report.update(
            status="witness_retained",
            summary=(
                "A documented-lawful generated input separates bbox-height selection from the plausible largest-cell-count shortcut."
            ),
            witness={
                key: witness[key]
                for key in (
                    "seed",
                    "sample_index",
                    "input_sha256",
                    "canonical_output_sha256",
                    "shortcut_output_sha256",
                    "canonical_matches_tallest_oracle",
                    "shortcut_is_separated",
                )
            },
        )
        (OUT / "witness.json").write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
