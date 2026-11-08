#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "fc814cec3976"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def key(grid):
    return tuple(tuple(row) for row in grid)


def red_key(grid):
    return tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )


def build_masks():
    masks = {}
    for template in GEN._TEMPLATES.values():
        grid = [list(row) for row in template["grid"]]
        output = GEN.rule_mirror(grid)
        rkey = red_key(grid)
        changes = {
            f"{r},{c}": output[r][c]
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if output[r][c] != grid[r][c]
        }
        masks[rkey] = changes
    assert len(masks) == 32
    return masks


MASKS = build_masks()


def template_lookup_rival(grid):
    output = deepcopy(grid)
    changes = MASKS[red_key(grid)]
    for encoded, value in changes.items():
        row, column = map(int, encoded.split(","))
        output[row][column] = value
    return output


def exhaustive_generated_check():
    mismatches = []
    output_pairs = set()
    red_layouts = set()
    for scene_code in range(GEN.SCENE_COUNT):
        grid = GEN.generate(0, 0, scene_code=scene_code)
        actual = GEN.rule_mirror(grid)
        rival = template_lookup_rival(grid)
        if rival != actual and len(mismatches) < 5:
            mismatches.append(scene_code)
        red_layouts.add(red_key(grid))
        output_pairs.add((key(grid), key(actual)))
    return {
        "scene_codes_checked": GEN.SCENE_COUNT,
        "matches": GEN.SCENE_COUNT - len(mismatches),
        "mismatch_examples": mismatches,
        "distinct_red_layouts": len(red_layouts),
        "distinct_input_output_pairs": len(output_pairs),
    }


def find_nearby_counterexample():
    # Keep the red layout fixed while changing one candidate-relevant gray cell.
    # This stays meaningful to the broad canonical rule but falls outside the
    # generator's exact closed scene-code validator.
    for scene_code in range(0, GEN.SCENE_COUNT, 5):
        grid = GEN.generate(0, 0, scene_code=scene_code)
        template = GEN._RED_LAYOUT_TO_TEMPLATE[GEN._red_key(grid)]
        for row, column in sorted(template["protected"]):
            if grid[row][column] != 5:
                continue
            mutated = deepcopy(grid)
            mutated[row][column] = 0
            actual = GEN.rule_mirror(mutated)
            rival = template_lookup_rival(mutated)
            if actual != rival:
                differing = [
                    [r, c, actual[r][c], rival[r][c]]
                    for r in range(19)
                    for c in range(19)
                    if actual[r][c] != rival[r][c]
                ]
                return {
                    "source_scene_code": scene_code,
                    "mutation": {"row": row, "column": column, "from": 5, "to": 0},
                    "input": mutated,
                    "python_rule_output": actual,
                    "template_lookup_output": rival,
                    "differing_cells": differing,
                    "self_check_errors": GEN.self_check(mutated),
                    "passes_generator_self_check": not GEN.self_check(mutated),
                    "documented_generator_domain": False,
                    "canonical_rule_domain_note": (
                        "The public Racket rule scans arbitrary rectangular grids; "
                        "the selected self_check intentionally admits only exact encoded scenes."
                    ),
                }
    raise RuntimeError("no nearby counterexample found")


report = {
    "schema": "arcpuzzles-audit-template-lookup-v1",
    "task_id": TASK_ID,
    "generator_source": str(SOURCE),
    "generator_sha256": SOURCE_SHA256,
    "rule_hash": getattr(GEN, "RULE_HASH", None),
    "finding": (
        "A 32-entry red-coordinate lookup plus fixed recolor masks matches every "
        "generated scene without scanning 3x3 windows, ranking candidates, or "
        "performing greedy red-overlap selection."
    ),
    "exhaustive_generated_check": exhaustive_generated_check(),
    "nearby_counterexample": find_nearby_counterexample(),
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "template-lookup-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
(OUT / "mutation-input.json").write_text(
    json.dumps(report["nearby_counterexample"]["input"], indent=2) + "\n"
)
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "exhaustive_generated_check": report["exhaustive_generated_check"],
    "mutation": report["nearby_counterexample"]["mutation"],
    "differing_cells": len(report["nearby_counterexample"]["differing_cells"]),
}, sort_keys=True))
