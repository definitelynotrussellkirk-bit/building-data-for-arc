#!/usr/bin/env python3
"""Reproduce the two finding-only audit contract failures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "WORK" / "repo"
if not REPO.is_dir():
    # Packaged return layout places checks and repo beside one another.
    PACKET_ROOT = Path(__file__).resolve().parents[2]
    REPO = PACKET_ROOT / "repo"
for path in (REPO / "shared" / "runtime", REPO / "src", REPO):
    sys.path.insert(0, str(path))
OUT = Path(__file__).resolve().parent


def load(task_id):
    source = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return source, module


def components(grid, start_row=0):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(start_row, height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    rr, cc = point
                    if (
                        start_row <= rr < height
                        and 0 <= cc < width
                        and point not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(cells)
    return result


def write(task_id, record):
    path = OUT / task_id / "contract_counterexample.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main():
    task_id = "2b83f40cf6d9"
    source, gen = load(task_id)
    impostor = [[0] * 8 for _ in range(7)]
    impostor[1][1] = impostor[5][6] = 4
    generated = gen.generate(11, 3, difficulty="easy", n_colors=4)
    write(task_id, {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "finding": "validator and override contract are weaker than documented ordinary domain",
        "minimal_impostor": {
            "input": impostor,
            "self_check": gen.self_check(impostor),
            "documented_requirement": "2-3 distinct non-background colors, each appearing twice",
        },
        "override_probe": {
            "seed": 11,
            "sample_index": 3,
            "difficulty": "easy",
            "overrides": {"n_colors": 4},
            "observed_distinct_nonzero_colors": len(set(sum(generated, [])) - {0}),
            "self_check": gen.self_check(generated),
            "input": generated,
        },
        "command": ["python3", "checks/audit/probe_contracts.py"],
        "cwd": "return_root",
    })

    task_id = "532f4a848b71"
    source, gen = load(task_id)
    impostor = [[0] * 9 for _ in range(8)]
    impostor[0][0] = 9
    impostor[3][4] = 4
    generated = gen.generate(7, 2, difficulty="easy", n_objects=6, n_nines=6)
    write(task_id, {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "finding": "validator admits a one-object impostor and exact object/count overrides are ignored",
        "minimal_impostor": {
            "input": impostor,
            "self_check": gen.self_check(impostor),
            "documented_requirement": "3-6 body objects of distinct sizes; row-0 nine count n in [1,K]",
        },
        "override_probe": {
            "seed": 7,
            "sample_index": 2,
            "difficulty": "easy",
            "overrides": {"n_objects": 6, "n_nines": 6},
            "observed_body_objects": len(components(generated, 1)),
            "observed_row0_nines": sum(value == 9 for value in generated[0]),
            "self_check": gen.self_check(generated),
            "input": generated,
        },
        "command": ["python3", "checks/audit/probe_contracts.py"],
        "cwd": "return_root",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
