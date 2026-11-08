#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "f0f2806877da"
REPO = Path.cwd().resolve()
TASK_HOME = REPO / "generators" / TASK_ID
GENERATOR_PATH = TASK_HOME / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program missing")


def parse_rival_types(grid):
    gaps = [grid[0][col] == grid[1][col] == 0 for col in range(len(grid[0]))]
    types = []
    col = 0
    while col < len(gaps):
        while col < len(gaps) and gaps[col]:
            col += 1
        if col == len(gaps):
            break
        start = col
        while col + 1 < len(gaps) and not gaps[col + 1]:
            col += 1
        end = col
        if start == end:
            types.append("straight")
        else:
            types.append("left" if grid[0][end] == 2 else "right")
        col += 1
    return types


def parse_true_types(grid):
    gaps = [grid[0][col] == grid[1][col] == 0 for col in range(len(grid[0]))]
    types = []
    col = 0
    while col < len(gaps):
        while col < len(gaps) and gaps[col]:
            col += 1
        if col == len(gaps):
            break
        start = col
        while col + 1 < len(gaps) and not gaps[col + 1]:
            col += 1
        end = col
        if start == end:
            types.append("straight")
        else:
            types.append("left" if grid[0][start] == 0 else "right")
        col += 1
    return types


def trace(types):
    row, col = 1, 3
    out = [[0] * 7 for _ in range(8)]
    out[0][3] = 3
    for kind in types:
        if kind == "straight":
            cells = ((row, col), (row + 1, col))
            row += 2
        elif kind == "left":
            cells = ((row, col - 1), (row, col))
            row += 1
            col -= 1
        else:
            cells = ((row, col), (row, col + 1))
            row += 1
            col += 1
        for rr, cc in cells:
            out[rr][cc] = 2
    return out


def racket_outputs(program, grids):
    sys.path.insert(0, str(REPO / "shared/runtime"))
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix="f0-audit-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO), stage, TASK_ID)
        (stage / "request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(result)
        return json.loads(result["stdout"])


def main():
    gen = load_generator()
    seed = 167
    sample_indices = [4, 5, 6, 7]
    grids = [gen.generate(seed, index, difficulty=None) for index in sample_indices]
    program = canonical_program()
    intended = racket_outputs(program, grids)
    rows = []
    for index, grid, label in zip(sample_indices, grids, intended):
        true_types = parse_true_types(grid)
        rival_types = parse_rival_types(grid)
        rival = trace(rival_types)
        rows.append({
            "sample_index": index,
            "input": grid,
            "racket_output": label,
            "true_types": true_types,
            "rival_types": rival_types,
            "rival_output": rival,
            "rival_matches": rival == label,
        })
    report = {
        "schema": "arcpuzzles-audit-top-right-rival-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "seed": seed,
        "demos": sample_indices[:3],
        "query": sample_indices[3],
        "rows": rows,
        "all_demos_fit": all(row["rival_matches"] for row in rows[:3]),
        "query_disagrees": not rows[3]["rival_matches"],
    }
    if not report["all_demos_fit"] or not report["query_disagrees"]:
        raise AssertionError("expected teaching shortcut was not reproduced")
    out = Path(__file__).with_name("counterexample.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "reproduced",
        "output": str(out),
        "generator_sha256": report["generator_sha256"],
        "demo_fit": [r["rival_matches"] for r in rows[:3]],
        "query_fit": rows[3]["rival_matches"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
