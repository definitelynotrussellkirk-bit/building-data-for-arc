#!/usr/bin/env python3
"""Source-bound adversarial probes for the two randomly assigned audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_record(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == task_id:
                return record
    raise KeyError(task_id)


def canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    record = canonical_record(task_id)
    return [*record["train"], *record["test"]]


def rival_reflection_only(gen, grid):
    """Diagonal plus reflection-only pairs; deliberately excludes rotation pairs."""
    components = gen._components(grid)
    output = []
    for row_index, left in enumerate(components):
        row = []
        for col_index, right in enumerate(components):
            same_d8 = gen._canon(left["shape"]) == gen._canon(right["shape"])
            same_rotation = gen._norm(left["shape"]) in gen._all_rotations(
                right["shape"]
            )
            row.append(
                8
                if row_index == col_index or (same_d8 and not same_rotation)
                else 0
            )
        output.append(row)
    return output


def colored_components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def outline_rule(grid):
    out = [[0 for _ in row] for row in grid]
    for component in colored_components(grid):
        r0, c0, r1, c1 = component["bbox"]
        color = component["color"]
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if row in (r0, r1) or col in (c0, c1):
                    out[row][col] = color
    return out


def rival_force_a_hole(grid):
    """Correct on >=3x3 rectangles, but wrongly punches one cell in thin ones."""
    out = outline_rule(grid)
    for component in colored_components(grid):
        r0, c0, r1, c1 = component["bbox"]
        height = r1 - r0 + 1
        width = c1 - c0 + 1
        if min(height, width) <= 2:
            out[(r0 + r1) // 2][(c0 + c1) // 2] = 0
    return out


def probe_50() -> dict[str, Any]:
    task = "50b66a854306"
    gen, path = load_generator(task)
    pairs = canonical_pairs(task)
    bands = {}
    for difficulty in ("easy", "medium", "hard"):
        matches = 0
        self_check_failures = []
        for sample_index in range(300):
            grid = gen.generate(918273, sample_index, difficulty=difficulty)
            errors = gen.self_check(grid)
            if errors:
                self_check_failures.append(
                    {"sample_index": sample_index, "errors": errors}
                )
            matches += rival_reflection_only(gen, grid) == gen.rule_mirror(grid)
        bands[difficulty] = {
            "seed": 918273,
            "sample_indices": [0, 299],
            "draws": 300,
            "rival_matches": matches,
            "rival_disagreements": 300 - matches,
            "self_check_failures": self_check_failures,
        }
    canonical = []
    for index, pair in enumerate(pairs):
        canonical.append(
            {
                "pair_index": index,
                "self_check": gen.self_check(pair["input"]),
                "rival_matches": rival_reflection_only(gen, pair["input"])
                == pair["output"],
            }
        )
    return {
        "task_id": task,
        "generator_sha256": sha256(path),
        "declared_rule_hash": gen.RULE_HASH,
        "rival": "diagonal_or_reflection_only_but_not_rotation_equivalent",
        "bands": bands,
        "canonical": canonical,
        "finding": (
            "The rival matches every sampled easy draw but fails canonical pairs, "
            "so the easy curriculum does not positively demonstrate rotation-orbit matches."
        ),
    }


def probe_99() -> dict[str, Any]:
    task = "99a1cb372ca4"
    gen, path = load_generator(task)
    pairs = canonical_pairs(task)
    bands = {}
    all_dims: set[tuple[int, int]] = set()
    total_rival_matches = 0
    total_draws = 0
    for difficulty in ("easy", "medium", "hard"):
        dims: set[tuple[int, int]] = set()
        self_check_failures = []
        rival_matches = 0
        for sample_index in range(200):
            grid = gen.generate(12345, sample_index, difficulty=difficulty)
            errors = gen.self_check(grid, difficulty=difficulty)
            if errors:
                self_check_failures.append(
                    {"sample_index": sample_index, "errors": errors}
                )
            for component in colored_components(grid):
                r0, c0, r1, c1 = component["bbox"]
                dims.add((r1 - r0 + 1, c1 - c0 + 1))
            rival_matches += rival_force_a_hole(grid) == outline_rule(grid)
        all_dims.update(dims)
        total_rival_matches += rival_matches
        total_draws += 200
        bands[difficulty] = {
            "seed": 12345,
            "sample_indices": [0, 199],
            "draws": 200,
            "observed_rectangle_dims": [list(value) for value in sorted(dims)],
            "rival_matches": rival_matches,
            "rival_disagreements": 200 - rival_matches,
            "self_check_failures": self_check_failures,
        }

    canonical = []
    for index, pair in enumerate(pairs):
        dims = []
        for component in colored_components(pair["input"]):
            r0, c0, r1, c1 = component["bbox"]
            dims.append([r1 - r0 + 1, c1 - c0 + 1])
        canonical.append(
            {
                "pair_index": index,
                "rectangle_dims": dims,
                "self_check": gen.self_check(pair["input"]),
                "rival_matches": rival_force_a_hole(pair["input"])
                == pair["output"],
            }
        )

    dead_axis_checks = {}
    for axis, left, right in (
        ("palette_kind", "warm", "cool"),
        ("palette_size", 1, 9),
        ("n_distinct_colors", 1, 9),
    ):
        equal = 0
        for sample_index in range(50):
            a = gen.generate(77001, sample_index, **{axis: left})
            b = gen.generate(77001, sample_index, **{axis: right})
            equal += a == b
        dead_axis_checks[axis] = {
            "seed": 77001,
            "sample_indices": [0, 49],
            "comparisons": 50,
            "identical_outputs": equal,
            "values": [left, right],
        }

    return {
        "task_id": task,
        "generator_sha256": sha256(path),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "rival": "outline_normally_but_force_one_hole_in_every_thin_rectangle",
        "bands": bands,
        "aggregate": {
            "draws": total_draws,
            "observed_rectangle_dims": [list(value) for value in sorted(all_dims)],
            "rival_matches": total_rival_matches,
            "rival_disagreements": total_draws - total_rival_matches,
        },
        "canonical": canonical,
        "dead_axis_checks": dead_axis_checks,
        "finding": (
            "Default generation never emits a rectangle with a dimension <=2, while "
            "three of four canonical inputs contain one and are rejected by self_check; "
            "a forced-hole-on-thin-rectangles rival therefore survives all sampled draws."
        ),
    }


def main() -> None:
    results = {
        "schema": "arcpuzzles-audit-probe-v1",
        "source_policy": "final generator source; fixed seed/index ranges; no target edits",
        "targets": [probe_50(), probe_99()],
    }
    out = PACKET / "checks" / "audit" / "probe_results.json"
    out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")

    # Save one canonical authority input for each supported Racket apply command.
    for task in ("50b66a854306", "99a1cb372ca4"):
        pair = canonical_pairs(task)[0]
        target = PACKET / "checks" / "audit" / task / "input.json"
        target.write_text(json.dumps(pair["input"], separators=(",", ":")) + "\n")

    # Save deterministic rival outputs beside the future Racket receipts.
    gen50, _ = load_generator("50b66a854306")
    pair50 = canonical_pairs("50b66a854306")[0]
    (PACKET / "checks" / "audit" / "50b66a854306" / "rival.json").write_text(
        json.dumps(rival_reflection_only(gen50, pair50["input"]), separators=(",", ":"))
        + "\n"
    )
    pair99 = canonical_pairs("99a1cb372ca4")[0]
    (PACKET / "checks" / "audit" / "99a1cb372ca4" / "rival.json").write_text(
        json.dumps(rival_force_a_hole(pair99["input"]), separators=(",", ":"))
        + "\n"
    )
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
