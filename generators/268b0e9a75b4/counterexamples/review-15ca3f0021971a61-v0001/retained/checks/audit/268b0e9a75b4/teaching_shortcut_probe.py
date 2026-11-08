from __future__ import annotations
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "268b0e9a75b4"
ROOT = find_root(__file__)
generator, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def execute_rule(bridge, program, grid):
    bridge.define_grid("g", grid)
    body = program[len("(rule!") : -1].strip()
    # This canonical rule is an implicit-g expression rather than a lambda.
    return bridge.eval_text(body)


def global_largest_fallback_rival(grid):
    """Use the intended unique branch; otherwise crop the global largest object."""
    components = generator._components(grid)
    order = generator._color_order(grid)
    counts = {
        color: sum(obj["color"] == color for obj in components)
        for color in order
    }
    unique_colors = [color for color in order if counts[color] == 1]
    if unique_colors:
        chosen = next(
            obj for obj in components if obj["color"] == unique_colors[0]
        )
    else:
        # Row-major first object resolves equal-size ties, but the retained
        # witness has a strict global maximum.
        chosen = max(components, key=lambda obj: obj["size"])
    return generator._crop(grid, chosen)


def differing_cells(left, right):
    height = max(len(left), len(right))
    width = max(
        max((len(row) for row in left), default=0),
        max((len(row) for row in right), default=0),
    )
    result = []
    for row in range(height):
        for col in range(width):
            lv = left[row][col] if row < len(left) and col < len(left[row]) else None
            rv = right[row][col] if row < len(right) and col < len(right[row]) else None
            if lv != rv:
                result.append([row, col, lv, rv])
    return result


rows = []
with canonical_path(ROOT).open() as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
if len(rows) != 1:
    raise RuntimeError(f"expected one canonical row, found {len(rows)}")
canonical = rows[0]
program = canonical["program_solution"]
program_sha256 = hashlib.sha256(program.encode()).hexdigest()

seed = 119
band = "easy"
with RacketBridge() as bridge:
    canonical_checks = []
    public_pairs = [*canonical["train"]]
    test = canonical["test"]
    public_pairs.extend(test if isinstance(test, list) else [test])
    for index, pair in enumerate(public_pairs):
        grid = [
            [int(cell) for cell in row] if isinstance(row, str) else list(row)
            for row in pair["input"]
        ]
        intended = execute_rule(bridge, program, grid)
        rival = global_largest_fallback_rival(grid)
        canonical_checks.append({
            "pair_index": index,
            "rival_matches": rival == intended,
            "branch": generator._analysis(grid)["branch"],
        })

    lesson = []
    for sample_index in range(4):
        grid = generator.generate(seed, sample_index, difficulty=band)
        findings = generator.self_check(grid)
        if findings:
            raise RuntimeError(f"generated pair {sample_index} failed: {findings}")
        intended = execute_rule(bridge, program, grid)
        mirror = generator.rule_mirror(grid)
        if intended != mirror:
            raise RuntimeError("Python mirror disagrees with canonical Racket")
        rival = global_largest_fallback_rival(grid)
        info = generator._analysis(grid)
        lesson.append({
            "sample_index": sample_index,
            "role": "demo" if sample_index < 3 else "query",
            "scene_profile": info["scene_profile"],
            "branch": info["branch"],
            "object_counts": list(info["object_counts"]),
            "chosen_color": info["chosen_color"],
            "input": grid,
            "intended_output": intended,
            "rival_output": rival,
            "rival_matches": rival == intended,
            "differing_cells": differing_cells(intended, rival),
        })

if not all(row["rival_matches"] for row in canonical_checks):
    raise RuntimeError("rival should fit every canonical pair")
if not all(row["rival_matches"] for row in lesson[:3]):
    raise RuntimeError("rival should fit all three generated demonstrations")
if lesson[3]["rival_matches"]:
    raise RuntimeError("query should distinguish the fallback rules")

payload = {
    "schema": "268b0e9a75b4-teaching-shortcut-probe-v1",
    "task_id": TASK_ID,
    "source_path": str(source.relative_to(ROOT)),
    "source_sha256": source_sha256,
    "canonical_program_sha256": program_sha256,
    "seed": seed,
    "difficulty": band,
    "rival": (
        "use the intended first-unique-color branch; if no color is unique, "
        "crop the globally largest object instead of the largest object of "
        "the numerically highest color"
    ),
    "canonical_pair_count": len(canonical_checks),
    "canonical_all_fit_rival": all(row["rival_matches"] for row in canonical_checks),
    "canonical_checks": canonical_checks,
    "generated_profiles": [row["scene_profile"] for row in lesson],
    "all_three_demos_fit_rival": all(row["rival_matches"] for row in lesson[:3]),
    "query_distinguishes_rival": not lesson[3]["rival_matches"],
    "query_difference_count": len(lesson[3]["differing_cells"]),
    "lesson": lesson,
    "conclusion": (
        "Three consecutive default demonstrations do not teach the fallback "
        "priority, while the fourth default draw queries it. A global-largest "
        "fallback solver fits every canonical pair and every demonstration but "
        "predicts a different query crop."
    ),
}
out = Path(__file__).with_name("teaching_shortcut_probe.json")
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    key: payload[key]
    for key in (
        "task_id", "source_sha256", "seed", "difficulty",
        "canonical_all_fit_rival", "generated_profiles",
        "all_three_demos_fit_rival", "query_distinguishes_rival",
        "query_difference_count", "conclusion",
    )
}, indent=2, sort_keys=True))
