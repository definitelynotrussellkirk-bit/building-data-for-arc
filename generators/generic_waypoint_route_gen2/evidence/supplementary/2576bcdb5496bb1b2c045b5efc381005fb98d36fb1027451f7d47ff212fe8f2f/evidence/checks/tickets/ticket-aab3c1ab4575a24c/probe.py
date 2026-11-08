from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path.cwd().resolve()
CHECK = ROOT.parent / "checks" / "tickets" / "ticket-aab3c1ab4575a24c"
SOURCE = ROOT / "generators" / "generic_waypoint_route_gen2" / "generator.py"
EXPECTED_SOURCE_SHA256 = "a4317b9a443121b6c8342c79a651e94e0ffa741facdbb545f81d6a5ebf040b15"
EXPECTED_RULE_HASH = "46236b0fd524"
PROBE_SEED_HEX = "6f86017c8a49aa95df9189f3f3777a5ba4960425dc949e7686ce2c0e91c3ca18"

sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]
from arcpuzzles import Catalog, runtime  # noqa: E402
from arcpuzzles.parametric_worker import _real_evaluator  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_route(module, grid):
    state = module._parse_last_state(grid)
    position = state["head"]
    route = [position]
    remaining = list(state["dots"])
    while remaining:
        aligned = [
            point
            for point in remaining
            if point[0] == position[0] or point[1] == position[1]
        ]
        if len(aligned) != 1:
            raise AssertionError(f"expected one aligned successor, found {len(aligned)}")
        position = aligned[0]
        remaining.remove(position)
        route.append(position)
    return state, route


def previous_waypoint_tail_shortcut(module, grid):
    state, route = trace_route(module, grid)
    if len(route) < 2:
        raise AssertionError("route has no final leg")
    final_head, previous_waypoint = route[-1], route[-2]
    out = [[state["bg"]] * len(state["panel"][0]) for _ in state["panel"]]
    out[final_head[0]][final_head[1]] = state["head_color"]
    out[previous_waypoint[0]][previous_waypoint[1]] = state["tail_color"]
    return out, route


def differing_cells(left, right):
    return [
        {"row": r, "col": c, "canonical": left[r][c], "shortcut": right[r][c]}
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def main() -> None:
    source_sha = sha256(SOURCE)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"source identity drifted: {source_sha}")

    stage = CHECK / "runtime-stage"
    if stage.exists():
        shutil.rmtree(stage)
    runtime.prepare_runtime(
        Catalog(ROOT),
        stage,
        task_ids=["generic_waypoint_route_gen1", "generic_waypoint_route_gen2"],
    )
    sys.path.insert(0, str(stage))
    try:
        module = importlib.import_module(
            "puzzle_generators.generic.concepts.waypoint_route.gen2"
        )
        if module.RULE_HASH != EXPECTED_RULE_HASH:
            raise AssertionError(f"rule hash drifted: {module.RULE_HASH}")

        base_seed = int(PROBE_SEED_HEX[:16], 16)
        selected = None
        candidates_examined = 0
        for offset in range(32):
            task_seed = base_seed + offset
            task = module.generate_task(task_seed, difficulty="medium")
            for pair_index, pair in enumerate(task["train"] + task["test"]):
                candidates_examined += 1
                state, route = trace_route(module, pair["input"])
                if len(route) < 2:
                    continue
                final_leg = (
                    abs(route[-1][0] - route[-2][0])
                    + abs(route[-1][1] - route[-2][1])
                )
                if final_leg <= 1:
                    continue
                canonical_python = module._apply(pair["input"])
                shortcut, route = previous_waypoint_tail_shortcut(module, pair["input"])
                if canonical_python == shortcut:
                    continue
                selected = {
                    "task_seed": task_seed,
                    "pair_index": pair_index,
                    "pair": pair,
                    "state": state,
                    "route": route,
                    "final_leg_manhattan": final_leg,
                    "canonical_python": canonical_python,
                    "shortcut": shortcut,
                }
                break
            if selected is not None:
                break
        if selected is None:
            raise AssertionError("bounded candidate scan found no multi-cell final leg")

        grid = selected["pair"]["input"]
        expected = selected["pair"]["output"]
        legality = module.strict_canonical_like(grid)
        if legality:
            raise AssertionError(f"selected input is not lawful: {legality}")
        if selected["canonical_python"] != expected:
            raise AssertionError("generated label disagrees with Python authority")

        apply, runtime_identity, bridge = _real_evaluator(stage)
        try:
            canonical_racket = apply(module.PROGRAM, grid)
        finally:
            bridge.close()
        if canonical_racket != expected:
            raise AssertionError("real Racket authority disagrees with selected label")
        if canonical_racket == selected["shortcut"]:
            raise AssertionError("shortcut unexpectedly agrees with canonical Racket")

        diffs = differing_cells(canonical_racket, selected["shortcut"])
        result = {
            "schema": "arc-review-adversarial-witness-v1",
            "ticket_id": "ticket-aab3c1ab4575a24c",
            "task_id": module.TASK_ID,
            "status": "completed",
            "pinned_identity": {
                "generator_sha256": source_sha,
                "rule_hash": module.RULE_HASH,
                "probe_seed": PROBE_SEED_HEX,
            },
            "shortcut": {
                "name": "tail_at_previous_waypoint",
                "description": (
                    "Trace the correct aligned route, but render the tail on the exact "
                    "previous waypoint rather than one unit opposite the final direction."
                ),
                "registered_in_current_semantic_rivals": False,
                "current_semantic_rivals": sorted(module.SEMANTIC_RIVALS),
            },
            "bounded_probe": {
                "candidate_tasks_limit": 32,
                "candidates_examined": candidates_examined,
                "selected_task_seed": selected["task_seed"],
                "selected_pair_index": selected["pair_index"],
            },
            "witness": {
                "lawful_under_strict_canonical_like": legality == [],
                "input": grid,
                "canonical_output": canonical_racket,
                "shortcut_output": selected["shortcut"],
                "route": [list(point) for point in selected["route"]],
                "final_leg_manhattan": selected["final_leg_manhattan"],
                "differing_cells": diffs,
            },
            "verification": {
                "generated_label_matches_python_authority": expected
                == selected["canonical_python"],
                "generated_label_matches_real_racket": expected == canonical_racket,
                "shortcut_differs_from_real_racket": selected["shortcut"]
                != canonical_racket,
                "runtime": runtime_identity,
            },
            "scope_note": (
                "This is one lawful, source-bound adversarial witness for one plausible "
                "shortcut; it is not a full peer battery or safety census."
            ),
        }
        (CHECK / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "candidates_examined": candidates_examined,
                    "final_leg_manhattan": selected["final_leg_manhattan"],
                    "differing_cells": len(diffs),
                },
                sort_keys=True,
            )
        )
    finally:
        if str(stage) in sys.path:
            sys.path.remove(str(stage))


if __name__ == "__main__":
    main()
