"""Independent semantic probes for task f361853c0fcd.

This module is review/test tooling, not production label authority.  The Python
oracle is an independent direct reading of the selected rule.  ``racket_outputs``
executes that selected canonical Racket program when the pinned runtime exists.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root

TASK_ID = "f361853c0fcd"
ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=ROOT, variant=0, labeled_only=True)


def _shape(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangle")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer colors 0..9")
    return len(grid), width


def frame_bounds(grid):
    _shape(grid)
    fives = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not fives:
        raise ValueError("missing color-5 frame")
    return (
        min(row for row, _ in fives),
        min(col for _, col in fives),
        max(row for row, _ in fives),
        max(col for _, col in fives),
    )


def intended_output(grid):
    """Independent direct translation of the selected Racket rule."""
    r1, c1, r2, c2 = frame_bounds(grid)
    output = deepcopy(grid)
    colors = sorted(
        {
            grid[row][col]
            for row, col in (
                [(row, c1) for row in range(r1, r2 + 1)]
                + [(row, c2) for row in range(r1, r2 + 1)]
                + [(r1, col) for col in range(c1, c2 + 1)]
                + [(r2, col) for col in range(c1, c2 + 1)]
            )
            if grid[row][col] not in (0, 5)
        }
    )
    for color in colors:
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color and grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color and grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def any_border_marker_rival(grid):
    """Wrong: every border marker launches a line without an opposite mate."""
    r1, c1, r2, c2 = frame_bounds(grid)
    output = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    for color in colors:
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color or grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color or grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def opposite_anywhere_rival(grid):
    """Wrong: opposite-side occurrence is enough; alignment is ignored."""
    r1, c1, r2, c2 = frame_bounds(grid)
    output = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    for color in colors:
        top = [col for col in range(c1 + 1, c2) if grid[r1][col] == color]
        bottom = [col for col in range(c1 + 1, c2) if grid[r2][col] == color]
        if top and bottom:
            for col in sorted(set(top + bottom)):
                for row in range(r1 + 1, r2):
                    output[row][col] = color
        left = [row for row in range(r1 + 1, r2) if grid[row][c1] == color]
        right = [row for row in range(r1 + 1, r2) if grid[row][c2] == color]
        if left and right:
            for row in sorted(set(left + right)):
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def rows_always_win_rival(grid):
    """Wrong: paint all valid columns first, then all valid rows."""
    r1, c1, r2, c2 = frame_bounds(grid)
    output = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    for color in colors:
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color and grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
    for color in colors:
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color and grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def columns_always_win_rival(grid):
    """Wrong: paint all valid rows first, then all valid columns."""
    r1, c1, r2, c2 = frame_bounds(grid)
    output = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    for color in colors:
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color and grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    for color in colors:
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color and grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
    return output


def observed(grid):
    """Independent observable summary of a valid input."""
    h, w = _shape(grid)
    r1, c1, r2, c2 = frame_bounds(grid)
    vertical = {}
    horizontal = {}
    paired_cells = set()
    for col in range(c1 + 1, c2):
        color = grid[r1][col]
        if color not in (0, 5) and grid[r2][col] == color:
            vertical.setdefault(color, []).append(col)
            paired_cells.update(((r1, col), (r2, col)))
    for row in range(r1 + 1, r2):
        color = grid[row][c1]
        if color not in (0, 5) and grid[row][c2] == color:
            horizontal.setdefault(color, []).append(row)
            paired_cells.update(((row, c1), (row, c2)))
    marker_cells = {
        (row, col)
        for row, col in (
            [(r1, col) for col in range(c1 + 1, c2)]
            + [(r2, col) for col in range(c1 + 1, c2)]
            + [(row, c1) for row in range(r1 + 1, r2)]
            + [(row, c2) for row in range(r1 + 1, r2)]
        )
        if grid[row][col] not in (0, 5)
    }
    v_colors = set(vertical)
    h_colors = set(horizontal)
    return {
        "grid_h": h,
        "grid_w": w,
        "frame_h": r2 - r1 + 1,
        "frame_w": c2 - c1 + 1,
        "frame_bounds": [r1, c1, r2, c2],
        "n_v_only": len(v_colors - h_colors),
        "n_h_only": len(h_colors - v_colors),
        "n_cross": len(v_colors & h_colors),
        "n_decoys": len(marker_cells - paired_cells),
        "vertical_pairs": {str(color): cols for color, cols in sorted(vertical.items())},
        "horizontal_pairs": {str(color): rows for color, rows in sorted(horizontal.items())},
        "decoy_cells": [list(cell) for cell in sorted(marker_cells - paired_cells)],
        "palette": sorted({value for row in grid for value in row}),
    }


def racket_outputs(grids):
    """Execute the selected canonical Racket program in a staged runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = None
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
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


def grid_differences(left, right):
    return [
        {"row": row, "col": col, "intended": a, "rival": b}
        for row, (left_row, right_row) in enumerate(zip(left, right))
        for col, (a, b) in enumerate(zip(left_row, right_row))
        if a != b
    ]


def _first_rival_witness(module, rival, *, seeds, sample_indices, difficulties):
    for difficulty in difficulties:
        for seed in seeds:
            for sample_index in sample_indices:
                grid = module.generate(seed, sample_index, difficulty=difficulty)
                if module.self_check(grid):
                    continue
                truth = intended_output(grid)
                other = rival(grid)
                if other != truth:
                    return {
                        "difficulty": difficulty,
                        "seed": seed,
                        "sample_index": sample_index,
                        "input": grid,
                        "observed": observed(grid),
                        "intended_output": truth,
                        "rival_output": other,
                        "different_cells": grid_differences(truth, other),
                    }
    return None


def build_contract_report(
    module=None,
    *,
    seeds=range(12),
    sample_indices=range(12),
    difficulties=("easy", "medium", "hard"),
):
    module = load_generator() if module is None else module
    pairs = canonical_pairs()

    def entry(name, rival, *, require_canonical_fit):
        checks = [rival(pair["input"]) == pair["output"] for pair in pairs]
        return {
            "name": name,
            "fits_all_canonical": all(checks),
            "canonical_pair_checks": checks,
            "canonical_fit_required": require_canonical_fit,
            "witness": _first_rival_witness(
                module,
                rival,
                seeds=tuple(seeds),
                sample_indices=tuple(sample_indices),
                difficulties=tuple(difficulties),
            ),
        }

    source = Path(module.__file__).resolve()
    return {
        "schema": "arc-task-rival-probe-v1",
        "task_id": getattr(module, "TASK_ID", TASK_ID),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "authority": "independent_python_oracle_not_racket",
        "canonical_pair_count": len(pairs),
        "canonical_shortcuts": {
            name: entry(name, rival, require_canonical_fit=True)
            for name, rival in getattr(module, "CANONICAL_SHORTCUTS", {}).items()
        },
        "lesson_competitors": {
            name: entry(name, rival, require_canonical_fit=False)
            for name, rival in getattr(module, "LESSON_COMPETITORS", {}).items()
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator")
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--sample-indices", type=int, default=12)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = build_contract_report(
        module,
        seeds=range(args.seeds),
        sample_indices=range(args.sample_indices),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
