"""Focused findings-only audit. Run via the packet's `review.py run` wrapper."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "bb1b1e111e1a"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK
SOURCE = ROOT / "generators" / TASK / "generator.py"
SEED = "audit-bb1-20261023"


def digest(value):
    data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()


def panels(grid):
    width = (len(grid[0]) - 2) // 3
    return ([row[:width] for row in grid],
            [row[width + 1:2 * width + 1] for row in grid],
            [row[2 * width + 2:] for row in grid])


def select(grid):
    mask, a, b = panels(grid)
    return [[x if m else y for m, x, y in zip(mrow, arow, brow)]
            for mrow, arow, brow in zip(mask, a, b)]


def main():
    spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    cases, inputs = [], []

    def add(name, index, difficulty=None, **overrides):
        grid = module.generate(SEED, index, difficulty=difficulty, **overrides)
        mask, a, b = panels(grid)
        cases.append({
            "name": name, "input_index": len(inputs), "seed": SEED,
            "sample_index": index, "difficulty": difficulty,
            "overrides": overrides, "input_sha256": digest(grid),
            "self_check": module.self_check(grid, difficulty=difficulty),
            "a_equals_b": a == b,
            "independent_cellwise_output": select(grid),
        })
        inputs.append(grid)

    add("identical_panels", 0, texture="identical_panels")
    for index in range(3):
        add(f"density_low_{index}", index, grid_h=4, panel_w=4, mask_density=0.1)
        add(f"density_high_{index}", index, grid_h=4, panel_w=4, mask_density=0.9)
    for index, difficulty in enumerate(("easy", "medium", "hard")):
        add(f"ordinary_{difficulty}", index, difficulty)

    endpoints = []
    for overrides in ({"grid_h": 3}, {"grid_h": 10},
                      {"panel_w": 3}, {"panel_w": 9},
                      {"grid_h": 4, "panel_w": 4}):
        row = {"seed": SEED, "sample_index": 0, "difficulty": None,
               "overrides": overrides}
        try:
            grid = module.generate(SEED, 0, difficulty=None, **overrides)
            row.update(status="generated", shape=[len(grid), len(grid[0])],
                       input_sha256=digest(grid), self_check=module.self_check(grid))
        except Exception as error:
            row.update(status="error", exception_type=type(error).__name__,
                       error=str(error))
        endpoints.append(row)

    density_pairs = [{"sample_index": index,
                      "low_input_index": 1 + 2 * index,
                      "high_input_index": 2 + 2 * index,
                      "identical_complete_input": inputs[1 + 2 * index] == inputs[2 + 2 * index]}
                     for index in range(3)]
    manifest = {"task_id": TASK, "generator_sha256": source_hash,
                "input_hash_encoding": "UTF-8 JSON, sorted keys, compact separators",
                "cases": cases, "density_pairs": density_pairs,
                "declared_axis_domains": module.AXES,
                "dimension_endpoint_probes": endpoints}
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, data in (("input.json", {"inputs": inputs}),
                           ("probe.json", manifest)):
        path = OUT / filename
        with path.open("x") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
    print(json.dumps({"generator_sha256": source_hash,
                      "reference_input_count": len(inputs),
                      "density_pairs": density_pairs,
                      "identical_panels_a_equals_b": cases[0]["a_equals_b"],
                      "identical_panels_self_check": cases[0]["self_check"],
                      "dimension_endpoint_probes": endpoints}, indent=2))


if __name__ == "__main__":
    main()
