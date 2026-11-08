"""Reproduce the proposed fixed examples, obtaining every label from Racket.

Run in a prepared checkout; --out must be a new ignored scratch directory:
  PYTHONPATH=src .venv/bin/python generators/generic_waypoint_route_gen2/workspace/materialize_canonical.py --out var/typed-waypoint-canonical
This authoring utility exposes private reference answers. It neither selects a
catalog authority nor changes approval or training-admission metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog, runtime


TASK_ID = "generic_waypoint_route_gen2"
ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "catalog/puzzles.jsonl").is_file())
PLAN = [
    ("train", "medium", 0, "train", 0),
    ("train", "medium", 0, "train", 1),
    ("train", "medium", 0, "train", 2),
    ("test", "easy", 1, "test", 0),
    ("test", "medium", 17, "test", 0),
    ("test", "hard", 31, "test", 0),
    ("test", "hard", 207, "train", 0),
]


def sha(body):
    return hashlib.sha256(body).hexdigest()


def grid_sha(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    stage = out / "runtime"
    runtime.prepare_runtime(Catalog(ROOT), stage, task_ids=[
        "generic_waypoint_route_gen1", TASK_ID])
    sys.path.insert(0, str(stage))
    module = importlib.import_module("puzzle_generators.generic.concepts.waypoint_route.gen2")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    row = {
        "task_id": TASK_ID,
        "source": "custom",
        "title": "Typed cursor follows the remaining final-panel waypoint route",
        "difficulty": "mixed",
        "skills": ["objects", "color_roles", "sequential_state", "relative_direction"],
        "written_solution": (
            "Take the panel after the last full-height separator. Identify its two-cell "
            "cursor: the head shares its color with the singleton waypoints, while the "
            "other color is the tail. Repeatedly move the head to the uniquely aligned "
            "unconsumed waypoint. After the last hop, return a clean panel containing "
            "the head at that waypoint and the tail one cell opposite the final travel "
            "direction. Earlier panels are unused context in this semantic variant."
        ),
        "train": [], "test": [],
        "program_solution": module.PROGRAM,
        "solution_language": "racket",
        "needs_conversion": False,
        "content_hash": module.RULE_HASH,
        "slug": "typed_cursor_final_panel_waypoint_route",
        "parent_hash": "5545f144",
        "parent_reason": "semantic inspiration only; not an original-task solution",
        "source_task_id": "5545f144",
        "relationship": "semantic_variant",
        "rule_scope": "final_panel_only",
        "label_origin": "executed_protected_racket",
    }
    executions = []
    with RacketBridge() as bridge:
        bridge.eval_text("(define typed-waypoint-rule " + wrap_rule(module.PROGRAM) + ")")
        for split, difficulty, seed, source_split, source_index in PLAN:
            pair = module.generate_task(seed, difficulty=difficulty)[source_split][source_index]
            bridge.define_grid("typed-waypoint-input", pair["input"])
            output = bridge.eval_text("(typed-waypoint-rule typed-waypoint-input)")
            if output != pair["output"]:
                raise AssertionError("Racket and independently computed generator output disagree")
            row[split].append({"input": pair["input"], "output": output})
            state = module._parse_last_state(pair["input"])
            executions.append({
                "split": split, "index": len(row[split]) - 1,
                "seed": seed, "difficulty": difficulty,
                "source_split": source_split, "source_index": source_index,
                "input_sha256": grid_sha(pair["input"]),
                "racket_output_sha256": grid_sha(output),
                "python_expected_sha256": grid_sha(pair["output"]),
                "parity": True,
                "input_shape": [len(pair["input"]), len(pair["input"][0])],
                "head_color": state["head_color"], "tail_color": state["tail_color"],
                "remaining_hops": len(state["dots"]),
            })
        identity = bridge.runtime_identity
    (out / "reference.rkt").write_bytes(module.PROGRAM.encode())
    (out / "canonical-candidate.json").write_text(json.dumps(row, indent=2) + "\n")
    manifest = {
        "schema": "arcpuzzles-task-reference-materialization-v1",
        "task_id": TASK_ID,
        "generator_sha256": sha((ROOT / "generators" / TASK_ID / "generator.py").read_bytes()),
        "sampler_generator_sha256": sha((ROOT / "generators/generic_waypoint_route_gen1/generator.py").read_bytes()),
        "program_text_sha256": sha(module.PROGRAM.encode()),
        "normalized_rule_hash": module.RULE_HASH,
        "canonical_candidate_sha256": sha((out / "canonical-candidate.json").read_bytes()),
        "callable_text_sha256": sha(wrap_rule(module.PROGRAM).encode()),
        "runtime_identity": identity,
        "executions": executions,
        "status": "locally_executed",
        "approved": False,
        "training_admission": False,
        "scope": "Seven fixed semantic-variant examples; earlier panels are unused context.",
    }
    (out / "execution.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"out": str(out), "pairs": len(executions),
                      "rule_hash": module.RULE_HASH, "status": "locally_executed"}))


if __name__ == "__main__":
    main()
