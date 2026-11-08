#!/usr/bin/env python3
"""Focused, source-bound audit probes for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT_ROOT = Path(__file__).resolve().parent


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_hash(grid):
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def outcome(module, seed, sample_index, *, difficulty=None, **overrides):
    try:
        grid = module.generate(
            seed, sample_index, difficulty=difficulty, **overrides
        )
    except Exception as exc:
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {
        "status": "ok",
        "dims": [len(grid), len(grid[0])],
        "grid_sha256": grid_hash(grid),
        "self_check": module.self_check(grid),
        "colors": sorted({value for row in grid for value in row}),
        "grid": grid,
    }


def eight_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        p = (rr + dr, cc + dc)
                        if (
                            0 <= p[0] < h
                            and 0 <= p[1] < w
                            and p not in seen
                            and grid[p[0]][p[1]] == color
                        ):
                            seen.add(p)
                            stack.append(p)
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            result.append(
                {
                    "color": color,
                    "size": len(cells),
                    "bbox": [max(rows) - min(rows) + 1, max(cols) - min(cols) + 1],
                }
            )
    return sorted(result, key=lambda row: row["size"])


def catalog_row(task_id):
    with (ROOT / "catalog" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("id") == task_id:
                return row
    raise KeyError(task_id)


def write(task_id, payload):
    module, path = load(task_id)
    row = catalog_row(task_id)
    result = {
        "schema": "arcpuzzles-review-audit-contract-probe-v1",
        "task_id": task_id,
        "generator_path": str(path.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "catalog_reviewed_generator_sha256": row.get("reviewed_generator_sha256"),
        "catalog_reviewed_rule_hash": row.get("reviewed_rule_hash"),
        "command": [
            "PYTHONPATH=shared/runtime:src",
            "python3",
            "../checks/audit/contract_probe.py",
        ],
        "cwd": "WORK/repo",
    }
    result.update(payload(module))
    out = OUT_ROOT / task_id / "contract_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(out)


def probe_08(module):
    base = outcome(module, 0, 0)
    unknown = outcome(module, 0, 0, unknown_axis=1)
    hard_width = outcome(module, 0, 0, difficulty="hard", grid_w=1)
    target = outcome(module, 0, 0, grid_w=14, xor_target=56)
    bogus_pattern = outcome(module, 2, 0, panel_pattern="bogus")
    bad_density = outcome(
        module,
        2,
        0,
        panel_pattern="random",
        top_density=-1.0,
        bot_density=2.0,
    )
    impostor = [[0] * 3 for _ in range(9)]
    impostor[0][0] = 1
    return {
        "declared_axes": module.AXES,
        "cases": {
            "baseline": base,
            "unknown_axis": unknown,
            "hard_grid_w_1_declared_valid": hard_width,
            "xor_target_56_declared_valid": target,
            "invalid_panel_pattern": bogus_pattern,
            "out_of_range_densities": bad_density,
            "minimal_impostor": {
                "grid": impostor,
                "self_check": module.self_check(impostor),
            },
        },
        "comparisons": {
            "unknown_axis_same_as_baseline": (
                base.get("grid_sha256") == unknown.get("grid_sha256")
            ),
        },
    }


def probe_c4(module):
    base = outcome(module, 0, 0)
    dims = outcome(module, 0, 0, grid_h=9, grid_w=22)
    anchor = outcome(module, 0, 0, anchor_corner=True)
    unknown = outcome(module, 0, 0, unknown_axis=1)
    invalid_big = outcome(module, 2, 0, big_h=99, big_w=4)
    if invalid_big.get("status") == "ok":
        invalid_big["objects_8"] = eight_components(invalid_big["grid"])
    impostor = [[0] * 9 for _ in range(9)]
    impostor[1][1] = 1
    impostor[1][2] = 2
    return {
        "declared_axes": module.AXES,
        "cases": {
            "baseline": base,
            "grid_dimensions_override": dims,
            "anchor_corner_true": anchor,
            "unknown_axis": unknown,
            "invalid_big_h_99": invalid_big,
            "minimal_impostor": {
                "grid": impostor,
                "self_check": module.self_check(impostor),
            },
        },
        "comparisons": {
            "grid_dimensions_same_as_baseline": (
                base.get("grid_sha256") == dims.get("grid_sha256")
            ),
            "anchor_corner_same_as_baseline": (
                base.get("grid_sha256") == anchor.get("grid_sha256")
            ),
            "unknown_axis_same_as_baseline": (
                base.get("grid_sha256") == unknown.get("grid_sha256")
            ),
        },
    }


write("08eaba8254b2", probe_08)
write("c4ab07496ad4", probe_c4)
