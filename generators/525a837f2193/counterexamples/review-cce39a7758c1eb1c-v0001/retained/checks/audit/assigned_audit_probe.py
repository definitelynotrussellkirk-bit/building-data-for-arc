#!/usr/bin/env python3
"""Reproduce the two immutable adversarial audit assignments without editing them."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

HERE = Path(__file__).resolve()
PACKET_ROOT = HERE.parents[2]
REPO_ROOT = PACKET_ROOT / "repo"
Grid = list[list[int]]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid: Grid) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_generator(task_id: str):
    path = REPO_ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def pixel_line_rival_525(grid: Grid) -> Grid:
    """Treat the anomaly as raw pixels and extend only its occupied pixel rows/columns."""
    out = deepcopy(grid)
    anomalous = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value not in (0, 1)]
    if not anomalous:
        return out
    color = anomalous[0][2]
    rows = {r for r, _c, value in anomalous if value == color}
    cols = {c for _r, c, value in anomalous if value == color}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1 and (r in rows or c in cols):
                out[r][c] = color
    return out


def color_one_components(grid: Grid) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            for x, y in todo:
                component.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    a, b = x + dx, y + dy
                    if (0 <= a < h and 0 <= b < w and grid[a][b] == 1
                            and (a, b) not in seen):
                        seen.add((a, b))
                        todo.append((a, b))
            result.append(component)
    return result


def bbox_frame_rival_342(grid: Grid) -> Grid:
    """Assume every blue component is exactly its rectangular-frame bounding box."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for component in color_one_components(grid):
        r0 = min(r for r, _c in component)
        r1 = max(r for r, _c in component)
        c0 = min(c for _r, c in component)
        c1 = max(c for _r, c in component)
        outer_r0, outer_r1 = max(0, r0 - 1), min(h - 1, r1 + 1)
        outer_c0, outer_c1 = max(0, c0 - 1), min(w - 1, c1 + 1)
        for r in range(outer_r0, outer_r1 + 1):
            for c in range(outer_c0, outer_c1 + 1):
                if (out[r][c] == 0
                        and (r in (outer_r0, outer_r1) or c in (outer_c0, outer_c1))):
                    out[r][c] = 2
        if r1 - r0 >= 2 and c1 - c0 >= 2:
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    if (out[r][c] == 0
                            and (r in (r0 + 1, r1 - 1) or c in (c0 + 1, c1 - 1))):
                        out[r][c] = 3
    return out


def make_three_by_three_lattice() -> Grid:
    cell_size, rows, cols = 3, 4, 4
    anomaly_row, anomaly_col, anomaly_color = 1, 2, 8
    h = rows * cell_size + rows - 1
    w = cols * cell_size + cols - 1
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for rr in range(rows):
        for cc in range(cols):
            value = anomaly_color if (rr, cc) == (anomaly_row, anomaly_col) else 1
            for dr in range(cell_size):
                for dc in range(cell_size):
                    grid[rr * (cell_size + 1) + dr][cc * (cell_size + 1) + dc] = value
    return grid


def make_protruded_frame() -> Grid:
    grid = [[0 for _ in range(10)] for _ in range(10)]
    for c in range(2, 7):
        grid[2][c] = 1
        grid[6][c] = 1
    for r in range(2, 7):
        grid[r][2] = 1
        grid[r][6] = 1
    grid[4][7] = 1
    return grid


def canonical_probe(task_id: str, rival: Callable[[Grid], Grid]) -> dict[str, Any]:
    rows = canonical_pairs(task_id, root=REPO_ROOT)
    records = []
    for pair in rows:
        predicted = rival(pair["input"])
        records.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input_sha256": grid_sha(pair["input"]),
            "expected_output_sha256": grid_sha(pair["output"]),
            "rival_matches": predicted == pair["output"],
        })
    return {
        "pair_count": len(records),
        "rival_match_count": sum(row["rival_matches"] for row in records),
        "records": records,
    }


def generated_probe(catalog: Catalog, task_id: str, module: Any,
                    rival: Callable[[Grid], Grid]) -> dict[str, Any]:
    grids = [module.generate("assigned-audit-generated", index,
                             difficulty=("easy", "medium", "hard")[index % 3])
             for index in range(12)]
    applied = catalog.apply(task_id, grids, timeout=120)
    records = []
    for index, (grid, receipt) in enumerate(zip(grids, applied["results"])):
        records.append({
            "sample_index": index,
            "difficulty": ("easy", "medium", "hard")[index % 3],
            "input_sha256": receipt["input_sha256"],
            "output_sha256": receipt["output_sha256"],
            "self_check_errors": module.self_check(grid),
            "rival_matches_reference": rival(grid) == receipt["output"],
        })
    return {
        "seed": "assigned-audit-generated",
        "draw_count": len(records),
        "unique_input_count": len({row["input_sha256"] for row in records}),
        "self_check_pass_count": sum(not row["self_check_errors"] for row in records),
        "rival_match_count": sum(row["rival_matches_reference"] for row in records),
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "executed_rule_hash": applied["executed_rule_hash"],
        "records": records,
    }


def counterexample(catalog: Catalog, task_id: str, module: Any, grid: Grid,
                   rival: Callable[[Grid], Grid], domain_note: str) -> dict[str, Any]:
    receipt = catalog.apply(task_id, [grid], timeout=120)
    item = receipt["results"][0]
    predicted = rival(grid)
    if item["output"] == predicted:
        raise AssertionError(f"{task_id}: proposed counterexample does not distinguish the rival")
    return {
        "input": grid,
        "actual_racket_output": item["output"],
        "rival_output": predicted,
        "outputs_differ": True,
        "self_check_errors": module.self_check(grid),
        "input_sha256": item["input_sha256"],
        "actual_output_sha256": item["output_sha256"],
        "rival_output_sha256": grid_sha(predicted),
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "domain_note": domain_note,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    catalog = Catalog(REPO_ROOT)
    output: dict[str, Any] = {
        "schema": "arcpuzzles-assigned-adversarial-audits-v1",
        "status": "completed_with_findings",
        "passed": True,
        "passed_means": "The immutable audit targets were reproduced; this is not generator approval.",
        "probe_sha256": sha256_bytes(HERE.read_bytes()),
        "targets": {},
    }

    task_id = "525a837f2193"
    module, source = load_generator(task_id)
    description = catalog.describe(task_id)
    anomaly_9 = module.generate("assigned-audit-override", 0, difficulty="medium", anomaly=9)
    anomaly_2 = module.generate("assigned-audit-override", 0, difficulty="medium", anomaly=2)
    output["targets"][task_id] = {
        "classification": "reproduced ignored override plus canonical-perfect raw-pixel shortcut",
        "generator_sha256": sha256_bytes(source.read_bytes()),
        "assigned_generator_sha256": "e5ff9a4894638da756d18d8b394fe1e1eb8cdee8e92f089b2c332465ed03182a",
        "catalog_rule_hash": description["rule_hash"],
        "rival": "Extend the anomaly color along its occupied raw pixel rows and columns, without inferring blocks.",
        "canonical": canonical_probe(task_id, pixel_line_rival_525),
        "generated": generated_probe(catalog, task_id, module, pixel_line_rival_525),
        "override_probe": {
            "seed": "assigned-audit-override",
            "sample_index": 0,
            "difficulty": "medium",
            "request_a": {"anomaly": 9},
            "request_b": {"anomaly": 2},
            "outputs_identical": anomaly_9 == anomaly_2,
            "output_sha256": grid_sha(anomaly_9),
            "observed_colors": sorted({value for row in anomaly_9 for value in row}),
            "self_check_errors": module.self_check(anomaly_9),
            "note": "generate() advertises anomaly but draws anomaly_color, so both exact requests are ignored.",
        },
        "counterexample": counterexample(
            catalog, task_id, module, make_three_by_three_lattice(), pixel_line_rival_525,
            "The canonical Racket rule executes this 3x3-block lattice and disagrees with the raw-pixel rival. "
            "The current self_check rejects it because the generator hard-codes 2x2 blocks; the witness therefore "
            "shows a support restriction/abstraction ambiguity rather than a wrong label inside current support.",
        ),
    }

    task_id = "34200461c67f"
    module, source = load_generator(task_id)
    description = catalog.describe(task_id)
    frame_5x5 = module.generate("assigned-audit-override", 0, difficulty="medium", frame_size="5x5")
    frame_6x5 = module.generate("assigned-audit-override", 0, difficulty="medium", frame_size="6x5")
    output["targets"][task_id] = {
        "classification": "reproduced ignored override and validator false acceptance for a generator-perfect bbox shortcut",
        "generator_sha256": sha256_bytes(source.read_bytes()),
        "assigned_generator_sha256": "8b48afdb3f8ee097eb8fbf59c7261d5658d318415775bbf1573d98cdb6d393b0",
        "catalog_rule_hash": description["rule_hash"],
        "rival": "Treat each blue component as a rectangular frame equal to its bounding box; paint fixed inner/outer bbox rings.",
        "canonical": canonical_probe(task_id, bbox_frame_rival_342),
        "generated": generated_probe(catalog, task_id, module, bbox_frame_rival_342),
        "override_probe": {
            "seed": "assigned-audit-override",
            "sample_index": 0,
            "difficulty": "medium",
            "request_a": {"frame_size": "5x5"},
            "request_b": {"frame_size": "6x5"},
            "outputs_identical": frame_5x5 == frame_6x5,
            "output_sha256": grid_sha(frame_5x5),
            "self_check_errors": module.self_check(frame_5x5),
            "note": "generate() advertises frame_size but only reads the texture alias, so exact frame_size requests are ignored.",
        },
        "counterexample": counterexample(
            catalog, task_id, module, make_protruded_frame(), bbox_frame_rival_342,
            "The current self_check accepts this hollow frame with a one-cell protrusion, and the canonical rule "
            "handles its actual geometry. The documented sampler emits rectangles only, so this is both a validator "
            "false acceptance and a generated-distribution shortcut; all five canonical pairs already refute the rival.",
        ),
    }

    for task_id, row in output["targets"].items():
        if row["generator_sha256"] != row["assigned_generator_sha256"]:
            raise AssertionError(f"{task_id}: source changed since audit assignment")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        task_id: {
            "classification": row["classification"],
            "canonical_rival_matches": f"{row['canonical']['rival_match_count']}/{row['canonical']['pair_count']}",
            "generated_rival_matches": f"{row['generated']['rival_match_count']}/{row['generated']['draw_count']}",
            "override_outputs_identical": row["override_probe"]["outputs_identical"],
            "counterexample_outputs_differ": row["counterexample"]["outputs_differ"],
            "counterexample_self_check_errors": row["counterexample"]["self_check_errors"],
        } for task_id, row in output["targets"].items()
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
