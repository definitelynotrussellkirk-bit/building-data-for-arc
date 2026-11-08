#!/usr/bin/env python3
"""Reproduce the two immutable findings-only audit targets with real Racket labels."""
from __future__ import annotations

from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
# The portable packet stores shared tools in repo/shared/tools; runtime rule
# normalization imports them under their production package name, scripts.*.
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(ROOT / "repo/shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)
from puzzle_generators import runner

CANONICAL = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
OUT = ROOT / "checks/audit-probe/report.json"


def canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                test = row["test"]
                return list(row["train"]) + (test if isinstance(test, list) else [test])
    raise KeyError(task_id)


def load_generator(task_id: str) -> Any:
    path = ROOT / f"repo/generators/{task_id}/generator.py"
    spec = spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rule(task_id: str) -> str:
    matches = sorted((ROOT / "repo/shared/data/base/solutions").rglob(f"*{task_id}*.json"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one base solution for {task_id}, found {matches}")
    row = json.loads(matches[0].read_text(encoding="utf-8"))
    target = row["racket_target"]
    return target.get("target_code") or target["raw_code"]


def apply_all(task_id: str, grids: list[list[list[int]]]) -> tuple[Any, list[list[list[int]]]]:
    module = load_generator(task_id)
    bridge, fn_name = runner._open_bridge_with_rule(runner.wrap_rule(load_rule(task_id)))
    try:
        return module, [runner._apply_rule(bridge, fn_name, grid) for grid in grids]
    finally:
        bridge.shutdown()


def preserve_occupied_transpose(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: copy only into originally empty transposed cells."""
    out = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value and grid[col][row] == 0:
                out[col][row] = value
    return out


def bbox_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def bbox_frequency_rival(mod: Any, grid: Any) -> list[list[int]]:
    """Canonical-fitting rival: border the object with unique bbox dimensions."""
    values = mod._coerce_grid(grid)
    components = mod._components(values)
    keys = [bbox_dims(cells) for cells in components]
    counts = Counter(keys)
    unique = [index for index, key in enumerate(keys) if counts[key] == 1]
    if len(unique) != 1:
        return [list(row) for row in values]
    return mod._paint_border_for(values, components[unique[0]])


def audit_transpose_collision() -> dict[str, Any]:
    task_id = "aa378df15340"
    pairs = canonical_pairs(task_id)
    canonical_inputs = [pair["input"] for pair in pairs]
    mod, canonical_authority = apply_all(task_id, canonical_inputs)
    generated = mod.generate(0, 2, difficulty=None)
    _, [authority] = apply_all(task_id, [generated])
    rival = preserve_occupied_transpose(generated)
    n = len(generated)
    collisions = [
        {
            "a": [row, col, generated[row][col]],
            "b": [col, row, generated[col][row]],
        }
        for row in range(n)
        for col in range(row + 1, n)
        if generated[row][col] and generated[col][row]
    ]
    return {
        "task_id": task_id,
        "finding": "ordinary generation emits opposite-side occupied transpose collisions not present canonically",
        "canonical_authority_matches_stored": [
            actual == mod_output["output"] for actual, mod_output in zip(canonical_authority, pairs)
        ],
        "rival_fits_all_canonical": [
            preserve_occupied_transpose(pair["input"]) == pair["output"] for pair in pairs
        ],
        "canonical_collision_counts": [
            sum(
                1
                for row in range(len(pair["input"]))
                for col in range(row + 1, len(pair["input"]))
                if pair["input"][row][col] and pair["input"][col][row]
            )
            for pair in pairs
        ],
        "replay": {"seed": 0, "sample_index": 2, "difficulty": None},
        "symmetric_occupied_pairs": collisions,
        "input": generated,
        "racket_output": authority,
        "preserve_occupied_rival_output": rival,
        "disagrees": authority != rival,
    }


def audit_bbox_lesson() -> dict[str, Any]:
    task_id = "6ae9b48be0a8"
    pairs = canonical_pairs(task_id)
    canonical_inputs = [pair["input"] for pair in pairs]
    mod, canonical_authority = apply_all(task_id, canonical_inputs)

    seed, start, difficulty = 0, 12, None
    grids = [mod.generate(seed, start + offset, difficulty=difficulty) for offset in range(5)]
    _, outputs = apply_all(task_id, grids)
    demos = [{"input": grid, "output": output} for grid, output in zip(grids[:4], outputs[:4])]
    query = {"input": grids[4], "output": outputs[4]}
    rival_outputs = [bbox_frequency_rival(mod, grid) for grid in grids]

    def dims(grid: Any) -> list[list[int]]:
        values = mod._coerce_grid(grid)
        return [list(bbox_dims(cells)) for cells in mod._components(values)]

    return {
        "task_id": task_id,
        "finding": "unique-bounding-box-dimensions rival survives a declared-identifiable four-demo lesson",
        "canonical_authority_matches_stored": [
            actual == mod._coerce_grid(pair["output"])
            for actual, pair in zip(canonical_authority, pairs)
        ],
        "rival_fits_all_canonical": [
            bbox_frequency_rival(mod, pair["input"]) == mod._coerce_grid(pair["output"])
            for pair in pairs
        ],
        "replay": {"seed": seed, "sample_index": start, "difficulty": difficulty, "n_demos": 4},
        "demo_relations": [mod._analyze(grid)["unique_relation"] for grid in grids[:4]],
        "demo_target_ranks": [mod._analyze(grid)["target_rank"] for grid in grids[:4]],
        "demo_bbox_dimensions": [dims(grid) for grid in grids[:4]],
        "rival_fits_every_demo": [rival == output for rival, output in zip(rival_outputs[:4], outputs[:4])],
        "lesson_identifiable_result": mod.lesson_identifiable(demos, query),
        "query_bbox_dimensions": dims(grids[4]),
        "query_input": grids[4],
        "query_racket_output": outputs[4],
        "query_rival_output": rival_outputs[4],
        "query_disagrees": rival_outputs[4] != outputs[4],
    }


def main() -> None:
    report = {
        "schema": "arc-review-audit-probe-v1",
        "audits": [audit_transpose_collision(), audit_bbox_lesson()],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        row["task_id"]: {
            "finding": row["finding"],
            "disagrees": row.get("disagrees", row.get("query_disagrees")),
        }
        for row in report["audits"]
    }, indent=2))


if __name__ == "__main__":
    main()
