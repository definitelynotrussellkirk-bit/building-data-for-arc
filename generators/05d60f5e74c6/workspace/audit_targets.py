#!/usr/bin/env python3
"""Reproduce the two immutable findings-only audit assignments; changes no target."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from review_probe import ReviewContext, components

MOVE = "24d677c76640"
TOP = "e99db35d533d"


def snap_first_cell_to_anchor(grid):
    anchor = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1)]
    first = min(cells)
    dr, dc = anchor[0]-first[0], anchor[1]-first[1]
    out = [[0]*len(grid[0]) for _ in grid]
    for r, c in cells:
        rr, cc = r+dr, c+dc
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            out[rr][cc] = grid[r][c]
    return out


def recolor_eight_connected(grid):
    out = [row[:] for row in grid]
    for obj in components(grid, diagonal=True):
        if obj["color"] == 1 and obj["bbox"][0] == 0:
            for r, c in obj["cells"]:
                out[r][c] = 4
    return out


def has_verified_findings(move, top):
    """A test being run is not itself a finding; inspect its measured outcome."""
    return bool(move.get("ambiguous_lessons") or move.get("generation_or_parity_failures")
                or move.get("boundary_failures") or top.get("count_mismatches")
                or any(item["total"] > 0 and item["same_input_count"] == item["total"]
                       for item in top.get("ignored_axes", [])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with ReviewContext([MOVE, TOP]) as ctx:
        reports = {
            "schema": "arcpuzzles-adversarial-audits-v1",
            "command": {"cwd": "repo", "argv": ["python3", "generators/05d60f5e74c6/workspace/audit_targets.py", *sys.argv[1:]]},
            "runtime_directory": str(ctx.runtime), "targets": {},
        }
        gen = ctx.modules[MOVE]
        canonical = ctx.normal_pairs(ctx.rows[MOVE])
        move = reports["targets"][MOVE] = {
            "source": ctx.identity[MOVE], "seed_range_inclusive": [0, 99],
            "sample_index_range_inclusive": [0, 3], "bands": ["easy", "medium", "hard"],
            "lesson_policy": "three consecutive demonstrations then query (no EXAMPLES_NEEDED declared)",
            "canonical_rival_matches": [snap_first_cell_to_anchor(p["input"]) == p["output"] for p in canonical],
            "canonical_reference_matches": sum(ctx.reference(MOVE, p["input"]) == p["output"] for p in canonical),
            "canonical_pair_count": len(canonical), "lessons": 0, "ambiguous_lessons": [],
            "generation_or_parity_failures": [], "boundary_count": 0, "boundary_failures": [],
        }
        input_keys = set()
        for band in move["bands"]:
            for seed in range(100):
                pairs = []
                for index in range(4):
                    grid = gen.generate(seed, index, difficulty=band)
                    output = ctx.reference(MOVE, grid)
                    input_keys.add(json.dumps(grid))
                    errors = gen.self_check(grid)
                    if errors or gen.rule_mirror(grid) != output:
                        move["generation_or_parity_failures"].append({"seed": seed, "sample_index": index,
                                                                     "difficulty": band, "input": grid,
                                                                     "racket_output": output, "validator_errors": errors})
                    pairs.append({"input": grid, "output": output})
                move["lessons"] += 1
                if (all(snap_first_cell_to_anchor(p["input"]) == p["output"] for p in pairs[:3])
                        and snap_first_cell_to_anchor(pairs[3]["input"]) != pairs[3]["output"]):
                    move["ambiguous_lessons"].append({"task_id": MOVE, **ctx.identity[MOVE],
                        "seed": seed, "sample_index": 3, "difficulty": band, "overrides": {},
                        "input": pairs[3]["input"], "racket_output": pairs[3]["output"],
                        "rival_output": snap_first_cell_to_anchor(pairs[3]["input"]),
                        "demos": pairs[:3], "validator_errors": gen.self_check(pairs[3]["input"]),
                        "in_documented_generator_domain": True})
        # All shape/direction combinations on all four dimension boundaries.
        for h in (7, 12):
            for w in (7, 12):
                for shape in range(12):
                    for relation in gen.RELATIONS:
                        kw = dict(grid_h=h, grid_w=w, shape_id=shape,
                                  shape_color=2+shape%8, anchor_relation=relation)
                        grid = gen.generate(17, 4, difficulty="medium", **kw)
                        output = ctx.reference(MOVE, grid)
                        move["boundary_count"] += 1
                        if gen.observe_overrides(grid) != kw or gen.self_check(grid) or gen.rule_mirror(grid) != output:
                            move["boundary_failures"].append({"seed": 17, "sample_index": 4,
                                                             "difficulty": "medium", "overrides": kw,
                                                             "input": grid, "racket_output": output})
        move["sample_draws"] = 1200
        move["unique_sample_inputs"] = len(input_keys)
        move["ambiguous_lesson_count"] = len(move["ambiguous_lessons"])
        print(MOVE, "ambiguous lessons", move["ambiguous_lesson_count"], "/", move["lessons"], flush=True)

        gen = ctx.modules[TOP]
        canonical = ctx.normal_pairs(ctx.rows[TOP])
        top = reports["targets"][TOP] = {
            "source": ctx.identity[TOP], "seed_range_inclusive": [0, 99], "sample_index": 0,
            "bands": ["easy", "medium", "hard"], "sample_draws": 0,
            "canonical_rival_matches": [recolor_eight_connected(p["input"]) == p["output"] for p in canonical],
            "canonical_reference_matches": sum(ctx.reference(TOP, p["input"]) == p["output"] for p in canonical),
            "canonical_pair_count": len(canonical),
            "validator_available": callable(getattr(gen, "self_check", None)),
            "rival_disagreements_on_generated": 0, "count_mismatches": [], "ignored_axes": [],
        }
        from puzzle_generators.base import set_ctx_observer
        input_keys = set()
        for band in top["bands"]:
            for seed in range(100):
                contexts = []
                set_ctx_observer(contexts.append)
                try:
                    grid = gen.generate(seed, 0, difficulty=band)
                finally:
                    set_ctx_observer(None)
                output = ctx.reference(TOP, grid)
                top["sample_draws"] += 1
                input_keys.add(json.dumps(grid))
                top["rival_disagreements_on_generated"] += recolor_eight_connected(grid) != output
                obs = components(grid)
                actual_top = sum(o["bbox"][0] == 0 for o in obs)
                actual_interior = len(obs)-actual_top
                drawn = contexts[-1].recorded_draws()
                if drawn["n_top"] != actual_top or drawn["n_interior"] != actual_interior:
                    top["count_mismatches"].append({"seed": seed, "sample_index": 0, "difficulty": band,
                        "overrides": {}, "drawn_counts": {"n_top": drawn["n_top"], "n_interior": drawn["n_interior"]},
                        "actual_counts": {"n_top": actual_top, "n_interior": actual_interior},
                        "input": grid, "racket_output": output})
        for axis, left, right in (("blob_size", 2, 6), ("palette_kind", "warm", "cool")):
            matches = []
            for seed in range(20):
                a = gen.generate(seed, 0, difficulty="medium", **{axis: left})
                b = gen.generate(seed, 0, difficulty="medium", **{axis: right})
                matches.append(a == b)
            top["ignored_axes"].append({"axis": axis, "values": [left, right],
                                        "seed_range_inclusive": [0, 19], "same_input_count": sum(matches),
                                        "total": len(matches), "sample_index": 0, "difficulty": "medium"})
        grid = [[0]*9 for _ in range(8)]
        for r, c in ((0, 0), (1, 0), (2, 1), (2, 2)):
            grid[r][c] = 1
        top["diagonal_counterexample"] = {
            "task_id": TOP, **ctx.identity[TOP], "seed": None, "sample_index": None, "overrides": None,
            "construction": "blue cells at (0,0),(1,0),(2,1),(2,2) on an 8x9 zero grid",
            "input": grid, "racket_output": ctx.reference(TOP, grid), "rival_output": recolor_eight_connected(grid),
            "validator_errors": None, "validator_available": False,
            "in_documented_generator_domain": False,
            "domain_reason": "Violates deliberate 8-halo separation, but satisfies the written top-touching 4-component rule.",
        }
        top["count_mismatch_count"] = len(top["count_mismatches"])
        top["unique_sample_inputs"] = len(input_keys)
        print(TOP, "count mismatches", top["count_mismatch_count"], "/", top["sample_draws"], flush=True)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(reports, indent=2) + "\n")
        # Findings-only: nonzero means a verified audit finding, not script failure.
        return int(has_verified_findings(move, top))


if __name__ == "__main__":
    raise SystemExit(main())
