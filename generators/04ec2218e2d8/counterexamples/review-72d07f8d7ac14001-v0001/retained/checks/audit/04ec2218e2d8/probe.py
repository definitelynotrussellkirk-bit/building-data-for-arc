from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET_WORK = HERE.parents[2]
SOURCE = PACKET_WORK / "repo/generators/04ec2218e2d8/generator.py"

def load_module():
    spec = importlib.util.spec_from_file_location("audit_04ec2218e2d8", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

module = load_module()

def bbox_fill_rival(grid):
    output = [row[:] for row in grid]
    for cells in module._components4_of_color(grid, 8):
        top, left, bottom, right = module._bbox(cells)
        height = bottom - top + 1
        width = right - left + 1
        inset = max(2, min(height, width) // 4)
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                rr, cc = row - top, col - left
                if inset <= rr < height - inset and inset <= cc < width - inset:
                    color = 4
                elif 2 * rr < height and 2 * cc < width:
                    color = 6
                elif 2 * rr < height:
                    color = 1
                elif 2 * cc < width:
                    color = 2
                else:
                    color = 3
                output[row][col] = color
    return output

matched = 0
generated = 0
all_solid = True
for band in ("easy", "medium", "hard"):
    for profile in module.SCENE_PROFILES:
        for seed in range(100):
            grid = module.generate(
                10000 + seed,
                seed * 43,
                difficulty=band,
                scene_profile=profile,
            )
            analysis = module._analyze_scene(grid)
            assert analysis is not None
            generated += 1
            all_solid &= all(
                len(rect["cells"]) == rect["height"] * rect["width"]
                for rect in analysis["rectangles"]
            )
            matched += bbox_fill_rival(grid) == module.rule_mirror(grid)

hole_grid = json.loads((HERE / "input.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
authority = racket["results"][0]["output"]
rival = bbox_fill_rival(hole_grid)
record = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": "04ec2218e2d8",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": racket["executed_rule_hash"],
    "sample_policy": "100 seeds x 5 profiles x 3 difficulty bands",
    "generated_cases": generated,
    "all_generated_components_solid_rectangles": all_solid,
    "bbox_fill_rival_matches_generated": matched,
    "counterexample": {
        "description": (
            "23x23 scene with an 8x8 cyan bbox at (2,2), a 6x6 bbox at "
            "(14,14), and one black interior hole at (5,5)"
        ),
        "self_check_errors": module.self_check(hole_grid),
        "authority_hole_output": authority[5][5],
        "bbox_fill_rival_hole_output": rival[5][5],
        "outputs_differ": authority != rival,
        "input": hole_grid,
        "actual_racket_output": authority,
        "rival_output": rival,
        "supported_apply_evidence": "checks/audit/04ec2218e2d8/racket.json",
    },
}
(HERE / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "generated": generated,
    "matches": matched,
    "all_solid": all_solid,
    "self_check_rejects_counterexample": bool(record["counterexample"]["self_check_errors"]),
    "counterexample_differs": authority != rival,
}, sort_keys=True))
assert generated == 1500
assert all_solid
assert matched == generated
assert module.self_check(hole_grid)
assert authority[5][5] == 0
assert rival[5][5] == 4
assert authority != rival
