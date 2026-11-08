#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
# The staged runtime expects shared/tools to be importable as scripts.*.
scripts_package = types.ModuleType("scripts")
scripts_package.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_package)

from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
from puzzle_generators.rule_wrap import wrap_rule



def load_bundle(task_id: str):
    generator_path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    canonical_path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    rule_source = None
    for line in canonical_path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == task_id:
            rule_source = row.get("program_solution")
            break
    if not rule_source:
        raise RuntimeError(f"missing canonical program_solution for {task_id}")
    rule_file = "shared/data/canonical/puzzles.jsonl"
    class Bundle:
        pass
    bundle = Bundle()
    bundle.generator_module = module
    bundle.rule_source = rule_source
    bundle.rule_file = rule_file
    bundle.rule_callable_text = wrap_rule(rule_source)
    return bundle

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_hash12(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def source_identity(task_id: str, bundle) -> dict:
    path = REPO / "generators" / task_id / "generator.py"
    return {
        "generator_path": str(path.relative_to(ROOT)),
        "generator_sha256": sha256_bytes(path.read_bytes()),
        "rule_source_file": bundle.rule_file,
        "rule_source_sha256": sha256_bytes(bundle.rule_source.encode()),
        "rule_normalized_sha12": normalized_hash12(bundle.rule_source),
        "declared_rule_hash": getattr(bundle.generator_module, "RULE_HASH", None),
    }


def canonical_row(task_id: str) -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def force_origin_rival(grid):
    masks = []
    for cells in nonzero_components(grid):
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        mask = {(r - r0, c - c0) for r, c in cells}
        mask.add((0, 0))
        masks.append(mask)
    height = max(max(r for r, _ in mask) + 1 for mask in masks)
    width = max(max(c for _, c in mask) + 1 for mask in masks)
    counts = [[0] * width for _ in range(height)]
    for mask in masks:
        for r, c in mask:
            counts[r][c] += 1
    mapping = {0: 0, 1: 2, 2: 3, 3: 4}
    return [[mapping.get(value, 6) for value in row] for row in counts]


def manhattan_rival(grid):
    start = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    goal = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    direct = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            via = abs(start[0] - r) + abs(start[1] - c) + abs(goal[0] - r) + abs(goal[1] - c)
            if via == direct:
                output[r][c] = 8
    return output


def racket_outputs(task_id: str, inputs: list[list[list[int]]]):
    bundle = load_bundle(task_id)
    bridge, name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        outputs = [_apply_rule(bridge, name, grid) for grid in inputs]
    finally:
        bridge.shutdown()
    return bundle, outputs


def build_ea3():
    task_id = "ea3fc2d64936"
    row = canonical_row(task_id)
    pair = row["train"][0]
    grid = pair["input"]
    bundle, outputs = racket_outputs(task_id, [grid])
    actual = outputs[0]
    rival = force_origin_rival(grid)
    validator_errors = bundle.generator_module.self_check(grid)
    result = {
        "schema": "generator_audit_counterexample/1",
        "finding_id": "A-EA3-ORIGIN",
        "target_task_id": task_id,
        **source_identity(task_id, bundle),
        "source": {"kind": "canonical_public_pair", "split": "train", "index": 0},
        "seed": None,
        "sample_index": None,
        "difficulty": None,
        "overrides": {},
        "input": grid,
        "actual_racket_output": actual,
        "stored_canonical_output_matches": actual == pair["output"],
        "rival_name": "force_every_normalized_component_to_include_origin",
        "rival_output": rival,
        "rival_matches_actual": rival == actual,
        "differing_cells": [
            [r, c, actual[r][c], rival[r][c]]
            for r in range(len(actual))
            for c in range(len(actual[0]))
            if actual[r][c] != rival[r][c]
        ],
        "target_validator_errors": validator_errors,
        "passes_target_validator": not validator_errors,
        "belongs_to_documented_generator_domain": False,
        "canonical_public_input": True,
        "reproduction": {
            "cwd": "packet_root",
            "argv": ["python3", "run_with_racket.py", "python3", "../checks/build_audit_counterexamples.py"],
        },
    }
    assert actual == pair["output"]
    assert rival != actual
    assert validator_errors
    (ROOT / "checks" / "audit-ea3-origin-counterexample.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build_50e():
    task_id = "50e0af791608"
    seed, start, difficulty = 33, 0, "medium"
    bundle = load_bundle(task_id)
    module = bundle.generator_module
    grids = [module.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
    bridge, name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        actuals = [_apply_rule(bridge, name, grid) for grid in grids]
    finally:
        bridge.shutdown()
    records = []
    for offset, (grid, actual) in enumerate(zip(grids, actuals)):
        rival = manhattan_rival(grid)
        errors = module.self_check(grid)
        records.append(
            {
                "sample_index": start + offset,
                "scene_profile": module.observe_overrides(grid).get("scene_profile"),
                "input": grid,
                "actual_racket_output": actual,
                "python_rule_mirror_matches": module.rule_mirror(grid) == actual,
                "rival_output": rival,
                "rival_matches_actual": rival == actual,
                "target_validator_errors": errors,
                "passes_target_validator": not errors,
            }
        )
    result = {
        "schema": "generator_audit_counterexample/1",
        "finding_id": "A-50E-MANHATTAN-WINDOW",
        "target_task_id": task_id,
        **source_identity(task_id, bundle),
        "seed": seed,
        "sample_index": start,
        "difficulty": difficulty,
        "overrides": {},
        "lesson_policy": "same seed, sequential sample indices, first 3 demos then query",
        "rival_name": "wall_ignorant_manhattan_between_start_and_goal",
        "demos": records[:3],
        "query": records[3],
        "all_demo_rival_matches": all(record["rival_matches_actual"] for record in records[:3]),
        "query_rival_matches": records[3]["rival_matches_actual"],
        "all_inputs_pass_target_validator": all(record["passes_target_validator"] for record in records),
        "belongs_to_documented_generator_domain": True,
        "reproduction": {
            "cwd": "packet_root",
            "argv": ["python3", "run_with_racket.py", "python3", "../checks/build_audit_counterexamples.py"],
        },
    }
    assert result["all_demo_rival_matches"]
    assert not result["query_rival_matches"]
    assert result["all_inputs_pass_target_validator"]
    (ROOT / "checks" / "audit-50e-manhattan-window.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build_ea3()
    build_50e()
    print("wrote audit counterexamples")
