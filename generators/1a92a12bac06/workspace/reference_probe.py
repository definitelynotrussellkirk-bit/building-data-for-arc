"""Independent oracle and retained probes for task 1a92a12bac06.

This file is test/review tooling, not label authority.  The Python oracle is
implemented independently of generator helpers; ``racket_outputs`` executes the
selected canonical program when the pinned runtime is available.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK_ID = "1a92a12bac06"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as _canonical_pairs

    return _canonical_pairs(TASK_ID, root=ROOT, variant=0, labeled_only=True)


def components(grid, color=2):
    height = len(grid)
    width = len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for nxt in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if nxt in pending:
                    pending.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append(cells)
    return sorted(result, key=lambda part: (min(col for _, col in part), min(part)))


def intended_output(grid):
    """Independent direct translation of the selected Racket semantics."""
    output = deepcopy(grid)
    for part in components(grid, 2):
        rows = [row for row, _ in part]
        bottom = max(rows)
        height = bottom - min(rows) + 1
        cyan_start = bottom - (height // 2) + 1
        for row, col in part:
            if row >= cyan_start:
                output[row][col] = 8
    return output


def grid_bottom_anchor_rival(grid):
    """Wrong shortcut: measure each half-fill upward from the canvas floor."""
    output = deepcopy(grid)
    canvas_height = len(grid)
    for part in components(grid, 2):
        rows = [row for row, _ in part]
        height = max(rows) - min(rows) + 1
        cyan_start = canvas_height - (height // 2)
        for row, col in part:
            if row >= cyan_start:
                output[row][col] = 8
    return output


def ceil_half_rival(grid):
    """Wrong shortcut: recolor ceil(height/2), not floor(height/2)."""
    output = deepcopy(grid)
    for part in components(grid, 2):
        rows = [row for row, _ in part]
        bottom = max(rows)
        height = bottom - min(rows) + 1
        cyan_start = bottom - ((height + 1) // 2) + 1
        for row, col in part:
            if row >= cyan_start:
                output[row][col] = 8
    return output


def observed(grid):
    parts = components(grid, 2)
    height = len(grid)
    tops = [min(row for row, _ in part) for part in parts]
    bottoms = [max(row for row, _ in part) for part in parts]
    bar_heights = [bottom - top + 1 for top, bottom in zip(tops, bottoms)]
    if parts and all(bottom == height - 1 for bottom in bottoms):
        texture = "bottom_aligned"
    elif parts and all(top == 0 for top in tops):
        texture = "top_aligned"
    elif parts and all(top > 0 and bottom < height - 1 for top, bottom in zip(tops, bottoms)):
        texture = "floating"
    elif (
        parts
        and any(top == 0 for top in tops)
        and any(bottom == height - 1 for bottom in bottoms)
        and any(top > 0 and bottom < height - 1 for top, bottom in zip(tops, bottoms))
    ):
        texture = "mixed_anchors"
    else:
        texture = "unclassified"
    return {
        "grid_h": height,
        "grid_w": len(grid[0]),
        "n_bars": len(parts),
        "texture": texture,
        "heights": bar_heights,
        "columns": [next(iter({col for _, col in part})) for part in parts],
    }


def racket_outputs(grids):
    """Execute the canonical Racket program in a disposable staged runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = None
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row["program_solution"]
                break
    if program is None:
        raise ValueError("canonical task is absent")

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])


def _grid_differences(left, right):
    """Return JSON-safe differing coordinates and values for equal-shape grids."""
    differences = []
    for row, (left_row, right_row) in enumerate(zip(left, right)):
        for col, (left_value, right_value) in enumerate(zip(left_row, right_row)):
            if left_value != right_value:
                differences.append(
                    {
                        "row": row,
                        "col": col,
                        "intended": left_value,
                        "rival": right_value,
                    }
                )
    return differences


def _first_rival_witness(module, rival, *, seeds, sample_indices, difficulties):
    for difficulty in difficulties:
        for seed in seeds:
            for sample_index in sample_indices:
                grid = module.generate(seed, sample_index, difficulty=difficulty)
                if module.self_check(grid):
                    continue
                intended = intended_output(grid)
                rival_output = rival(grid)
                if rival_output == intended:
                    continue
                return {
                    "difficulty": difficulty,
                    "seed": seed,
                    "sample_index": sample_index,
                    "input": grid,
                    "observed": observed(grid),
                    "intended_output": intended,
                    "rival_output": rival_output,
                    "different_cells": _grid_differences(intended, rival_output),
                }
    return None


def build_contract_report(
    module=None,
    *,
    seeds=range(12),
    sample_indices=range(12),
    difficulties=("easy", "medium", "hard"),
):
    """Audit declared rivals and retain first production-sampler witnesses.

    This is an independent Python probe, not label authority.  Pair it with
    ``arcpuzzles apply`` when an official Racket output is needed as evidence.
    """
    module = load_generator() if module is None else module
    seeds = tuple(int(value) for value in seeds)
    sample_indices = tuple(int(value) for value in sample_indices)
    difficulties = tuple(difficulties)
    pairs = canonical_pairs()

    def entry(name, rival, *, require_canonical_fit):
        canonical_checks = [
            rival(pair["input"]) == pair["output"]
            for pair in pairs
        ]
        return {
            "name": name,
            "fits_all_canonical": all(canonical_checks),
            "canonical_pair_checks": canonical_checks,
            "canonical_fit_required": require_canonical_fit,
            "witness": _first_rival_witness(
                module,
                rival,
                seeds=seeds,
                sample_indices=sample_indices,
                difficulties=difficulties,
            ),
        }

    shortcuts = {
        name: entry(name, rival, require_canonical_fit=True)
        for name, rival in getattr(module, "CANONICAL_SHORTCUTS", {}).items()
    }
    competitors = {
        name: entry(name, rival, require_canonical_fit=False)
        for name, rival in getattr(module, "LESSON_COMPETITORS", {}).items()
    }
    source = Path(module.__file__).resolve()
    import hashlib

    return {
        "schema": "arc-task-rival-probe-v1",
        "task_id": getattr(module, "TASK_ID", TASK_ID),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "authority": "independent_python_oracle_not_racket",
        "search": {
            "difficulties": list(difficulties),
            "seeds": list(seeds),
            "sample_indices": list(sample_indices),
        },
        "canonical_pair_count": len(pairs),
        "canonical_shortcuts": shortcuts,
        "lesson_competitors": competitors,
    }


def _main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Find replayable production-sampler witnesses for declared rivals."
    )
    parser.add_argument("--generator", help="alternate generator.py path")
    parser.add_argument("--seeds", type=int, default=12, help="search seeds 0..N-1")
    parser.add_argument(
        "--sample-indices", type=int, default=12, help="search sample indices 0..N-1"
    )
    parser.add_argument(
        "--difficulty",
        action="append",
        choices=("easy", "medium", "hard"),
        help="repeat to restrict bands; default searches all three",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = build_contract_report(
        module,
        seeds=range(args.seeds),
        sample_indices=range(args.sample_indices),
        difficulties=args.difficulty or ("easy", "medium", "hard"),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)


if __name__ == "__main__":
    _main()
