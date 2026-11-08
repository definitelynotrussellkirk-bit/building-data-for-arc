#!/usr/bin/env python3
"""Reproduce the two assigned audit findings with the selected canonical rules."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
from puzzle_generators.rule_wrap import wrap_rule

REPO = Path.cwd()
CHECKS = REPO.parent / "checks"
TASKS = ("56c98fd9e674", "68b4181d35e1")
COMMAND = [
    "python3", "run_with_racket.py", "env", "PYTHONPATH=.:shared/runtime:src",
    "python3", "../checks/audit_reproducer.py",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_row(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def rule_hashes(rule: str) -> dict[str, str]:
    return {
        "raw_sha256": sha256_bytes(rule.encode()),
        "normalized_sha256": sha256_bytes(" ".join(rule.split()).encode()),
        "normalized_sha12": sha256_bytes(" ".join(rule.split()).encode())[:12],
    }


def install_comment_solutions_alias() -> None:
    """Mirror the review runtime's scripts.comment_solutions overlay."""
    if "scripts.comment_solutions" in sys.modules:
        return
    path = REPO / "shared" / "tools" / "comment_solutions.py"
    spec = importlib.util.spec_from_file_location("scripts.comment_solutions", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    package = types.ModuleType("scripts")
    package.__path__ = [str(path.parent)]
    module = importlib.util.module_from_spec(spec)
    sys.modules["scripts"] = package
    sys.modules["scripts.comment_solutions"] = module
    spec.loader.exec_module(module)


def apply_many(rule: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    install_comment_solutions_alias()
    bridge, name = _open_bridge_with_rule(wrap_rule(rule))
    try:
        return [_apply_rule(bridge, name, grid) for grid in grids]
    finally:
        bridge.shutdown()


def capture_generate(module, *args, **kwargs):
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = module.generate(*args, **kwargs)
    finally:
        set_ctx_observer(None)
    if len(contexts) != 1:
        raise RuntimeError(f"expected one generation context, saw {len(contexts)}")
    ctx = contexts[0]
    return grid, {
        "recorded_draws": ctx.recorded_draws(),
        "overrides_used": ctx.overrides_used(),
    }


def plus_interior_only_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: expand only markers with all four arms in bounds."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if value:
                for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    out[r + dr][c + dc] = value
    return out


def header_all_markers_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: any header clears and recolors every row marker."""
    out = deepcopy(grid)
    for row in out:
        header = row[0]
        if header != 0:
            row[0] = 0
            for c in range(1, len(row)):
                if row[c] == 1:
                    row[c] = header
    return out


def header_features(grid: list[list[int]]) -> dict[str, int]:
    counts = {"active": 0, "header_only": 0, "header_multi": 0, "marker_only": 0}
    for row in grid:
        has_header = row[0] not in (0, 1)
        markers = sum(value == 1 for value in row[1:])
        if has_header and markers == 1:
            counts["active"] += 1
        elif has_header and markers == 0:
            counts["header_only"] += 1
        elif has_header and markers >= 2:
            counts["header_multi"] += 1
        elif not has_header and markers >= 1:
            counts["marker_only"] += 1
    return counts


def audit_56() -> dict[str, Any]:
    task_id = TASKS[0]
    module, generator_path = load_generator(task_id)
    canon = canonical_row(task_id)
    rule = canon["program_solution"]

    census = {}
    all_default_interior = True
    for difficulty in ("easy", "medium", "hard"):
        total = 0
        edge = 0
        count_histogram: dict[str, int] = {}
        for seed in range(100):
            for sample_index in range(20):
                grid = module.generate(seed, sample_index, difficulty=difficulty)
                nonzero = [
                    (r, c, value)
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if value != 0
                ]
                has_edge = any(
                    r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1)
                    for r, c, _ in nonzero
                )
                edge += int(has_edge)
                all_default_interior &= not has_edge
                total += 1
                count_histogram[str(len(nonzero))] = count_histogram.get(str(len(nonzero)), 0) + 1
        census[difficulty] = {
            "seed_range": [0, 99],
            "sample_index_range": [0, 19],
            "denominator": total,
            "edge_marker_inputs": edge,
            "marker_count_histogram": count_histogram,
        }

    edge_grid, edge_ctx = capture_generate(
        module, 0, 0, difficulty="medium", texture="cells_at_corner"
    )
    edge_actual = apply_many(rule, [edge_grid])[0]
    edge_rival = plus_interior_only_rival(edge_grid)

    axis_grid, axis_ctx = capture_generate(
        module, 17, 0, difficulty="hard", n_cells=5, n_distinct_colors=1
    )
    axis_actual = apply_many(rule, [axis_grid])[0]
    observed_colors = sorted({value for row in axis_grid for value in row if value != 0})

    return {
        "schema": "review-audit-counterexample-v1",
        "task_id": task_id,
        "finding_kinds": ["semantic_support_hole", "ignored_declared_axis"],
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": sha256_bytes(generator_path.read_bytes()),
        "rule_source": "shared/data/canonical/puzzles.jsonl",
        "rule_hashes": rule_hashes(rule),
        "command": COMMAND,
        "cwd": "packet_root",
        "normal_default_census": census,
        "normal_default_all_markers_interior": all_default_interior,
        "shortcut": {
            "name": "expand_only_interior_markers",
            "claim": "Matches every normal generated input because every marker is interior; disagrees when clipping at a boundary is required.",
            "generated_witness": {
                "seed": 0,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"texture": "cells_at_corner"},
                "input": edge_grid,
                "actual_racket_output": edge_actual,
                "rival_output": edge_rival,
                "outputs_disagree": edge_actual != edge_rival,
                "self_check": module.self_check(edge_grid, difficulty="medium"),
                "belongs_to_documented_generator_domain": True,
                "accepted_by_target_validator": not module.self_check(edge_grid, difficulty="medium"),
                "generation_context": edge_ctx,
                "note": "The documented boundary override emits the needed witness, but self_check rejects it, so the accepted normal distribution never teaches clipping.",
            },
        },
        "ignored_axis": {
            "seed": 17,
            "sample_index": 0,
            "difficulty": "hard",
            "overrides": {"n_cells": 5, "n_distinct_colors": 1},
            "input": axis_grid,
            "actual_racket_output": axis_actual,
            "requested_n_distinct_colors": 1,
            "observed_marker_colors": observed_colors,
            "observed_n_distinct_colors": len(observed_colors),
            "self_check": module.self_check(axis_grid, difficulty="hard"),
            "accepted_by_target_validator": not module.self_check(axis_grid, difficulty="hard"),
            "belongs_to_documented_generator_domain": True,
            "generation_context": axis_ctx,
            "contract_violated": len(observed_colors) != 1,
        },
    }


def audit_68() -> dict[str, Any]:
    task_id = TASKS[1]
    module, generator_path = load_generator(task_id)
    canon = canonical_row(task_id)
    rule = canon["program_solution"]

    rates = {}
    first_surviving_seed = {}
    for difficulty in ("easy", "medium", "hard"):
        no_multi = 0
        no_header_only = 0
        no_either = 0
        first = None
        for seed in range(10_000):
            features = [
                header_features(module.generate(seed, i, difficulty=difficulty))
                for i in range(4)
            ]
            has_multi = any(item["header_multi"] for item in features)
            has_header_only = any(item["header_only"] for item in features)
            no_multi += int(not has_multi)
            no_header_only += int(not has_header_only)
            no_either += int(not has_multi and not has_header_only)
            if first is None and not has_multi and not has_header_only:
                first = seed
        rates[difficulty] = {
            "seed_range": [0, 9999],
            "sample_index_range_per_window": [0, 3],
            "window_denominator": 10_000,
            "windows_without_header_multi": no_multi,
            "windows_without_header_only": no_header_only,
            "windows_where_rival_survives": no_either,
            "rival_survival_rate": no_either / 10_000,
        }
        first_surviving_seed[difficulty] = first

    seed = 200
    lesson_grids = [module.generate(seed, i, difficulty="easy") for i in range(4)]
    lesson_actual = apply_many(rule, lesson_grids)
    lesson_rival = [header_all_markers_rival(grid) for grid in lesson_grids]
    lesson_records = []
    for i, (grid, actual, rival) in enumerate(zip(lesson_grids, lesson_actual, lesson_rival)):
        lesson_records.append({
            "seed": seed,
            "sample_index": i,
            "difficulty": "easy",
            "overrides": {},
            "input": grid,
            "actual_racket_output": actual,
            "rival_output": rival,
            "outputs_equal": actual == rival,
            "features": header_features(grid),
            "self_check": module.self_check(grid, difficulty="easy"),
            "accepted_by_target_validator": not module.self_check(grid, difficulty="easy"),
            "belongs_to_documented_generator_domain": True,
        })

    witness_grid = module.generate(seed, 4, difficulty="easy")
    witness_actual = apply_many(rule, [witness_grid])[0]
    witness_rival = header_all_markers_rival(witness_grid)

    marker_grid, marker_ctx = capture_generate(
        module, 0, 0, difficulty="medium", marker_position="right_edge"
    )
    right_edge = len(marker_grid[0]) - 1
    active_marker_columns = [
        row.index(1)
        for row in marker_grid
        if row[0] not in (0, 1) and sum(value == 1 for value in row[1:]) == 1
    ]

    color_grid, color_ctx = capture_generate(
        module, 3, 0, difficulty="hard", active_rows=8, n_distinct_colors=1
    )
    observed_headers = [row[0] for row in color_grid if row[0] not in (0, 1)]

    return {
        "schema": "review-audit-counterexample-v1",
        "task_id": task_id,
        "finding_kinds": ["lesson_window_shortcut", "ignored_declared_axes"],
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": sha256_bytes(generator_path.read_bytes()),
        "rule_source": "shared/data/canonical/puzzles.jsonl",
        "rule_hashes": rule_hashes(rule),
        "command": COMMAND,
        "cwd": "packet_root",
        "shortcut": {
            "name": "clear_any_header_and_recolor_all_row_markers",
            "claim": "Fits the canonical demonstrations and survives a measurable fraction of nominal four-example windows when no header-only or header-plus-multiple-marker row is drawn.",
            "window_census": rates,
            "first_surviving_seed_by_difficulty": first_surviving_seed,
            "exact_surviving_lesson_window": lesson_records,
            "all_four_outputs_equal": all(a == b for a, b in zip(lesson_actual, lesson_rival)),
            "generated_disagreement_witness": {
                "seed": seed,
                "sample_index": 4,
                "difficulty": "easy",
                "overrides": {},
                "input": witness_grid,
                "actual_racket_output": witness_actual,
                "rival_output": witness_rival,
                "outputs_disagree": witness_actual != witness_rival,
                "features": header_features(witness_grid),
                "self_check": module.self_check(witness_grid, difficulty="easy"),
                "accepted_by_target_validator": not module.self_check(witness_grid, difficulty="easy"),
                "belongs_to_documented_generator_domain": True,
            },
        },
        "ignored_axes": {
            "marker_position": {
                "seed": 0,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"marker_position": "right_edge"},
                "input": marker_grid,
                "right_edge_column": right_edge,
                "active_marker_columns": active_marker_columns,
                "all_active_markers_at_right_edge": all(c == right_edge for c in active_marker_columns),
                "self_check": module.self_check(marker_grid, difficulty="medium"),
                "accepted_by_target_validator": not module.self_check(marker_grid, difficulty="medium"),
                "generation_context": marker_ctx,
                "contract_violated": any(c != right_edge for c in active_marker_columns),
            },
            "n_distinct_colors": {
                "seed": 3,
                "sample_index": 0,
                "difficulty": "hard",
                "overrides": {"active_rows": 8, "n_distinct_colors": 1},
                "input": color_grid,
                "requested_n_distinct_colors": 1,
                "observed_header_colors": observed_headers,
                "observed_n_distinct_header_colors": len(set(observed_headers)),
                "self_check": module.self_check(color_grid, difficulty="hard"),
                "accepted_by_target_validator": not module.self_check(color_grid, difficulty="hard"),
                "generation_context": color_ctx,
                "contract_violated": len(set(observed_headers)) != 1,
            },
        },
    }


def main() -> None:
    outputs = {
        "56c98fd9e674": audit_56(),
        "68b4181d35e1": audit_68(),
    }
    for task_id, payload in outputs.items():
        path = CHECKS / f"audit-{task_id}-counterexample.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(path.relative_to(REPO.parent))


if __name__ == "__main__":
    main()
