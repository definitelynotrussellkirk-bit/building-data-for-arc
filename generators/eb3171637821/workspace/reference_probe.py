"""Independent lattice oracle and review helpers for eb3171637821.

This module is test tooling, not label authority.  The Python oracle derives the
cell-band count directly from input pixels.  ``racket_outputs`` executes the
selected canonical Racket source and never silently falls back to Python.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TASK = "eb3171637821"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK, root=find_root(__file__))


def _runs(indexes):
    groups = []
    for index in indexes:
        if not groups or index != groups[-1][-1] + 1:
            groups.append([index])
        else:
            groups[-1].append(index)
    return [tuple(group) for group in groups]


def _nondivider_runs(length, divider_indexes):
    blocked = set(divider_indexes)
    return _runs([index for index in range(length) if index not in blocked])


def analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0]) if isinstance(grid[0], (list, tuple)) else 0
    if not width or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    height = len(grid)
    palette = {value for row in grid for value in row}
    if len(palette) != 2:
        raise ValueError("expected exactly two colors")

    candidates = []
    for color in palette:
        rows = [r for r in range(height) if all(grid[r][c] == color for c in range(width))]
        cols = [c for c in range(width) if all(grid[r][c] == color for r in range(height))]
        if rows and cols:
            candidates.append((color, rows, cols))
    if len(candidates) != 1:
        raise ValueError(f"expected one divider color, found {len(candidates)}")
    divider_color, divider_rows, divider_cols = candidates[0]
    cell_color = next(color for color in palette if color != divider_color)

    expected = [
        [divider_color if r in divider_rows or c in divider_cols else cell_color
         for c in range(width)]
        for r in range(height)
    ]
    if [list(row) for row in grid] != expected:
        raise ValueError("grid is not an exact Cartesian divider lattice")

    row_runs = _runs(divider_rows)
    col_runs = _runs(divider_cols)
    row_bands = _nondivider_runs(height, divider_rows)
    col_bands = _nondivider_runs(width, divider_cols)
    if not row_bands or not col_bands:
        raise ValueError("lattice has no cell band on an axis")

    def boundary_mode(dividers, length):
        start = 0 in dividers
        end = length - 1 in dividers
        return "both" if start and end else "start" if start else "end" if end else "none"

    row_thicknesses = {len(run) for run in row_runs}
    col_thicknesses = {len(run) for run in col_runs}
    return {
        "height": height,
        "width": width,
        "palette": palette,
        "divider_color": divider_color,
        "cell_color": cell_color,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_divider_runs": row_runs,
        "col_divider_runs": col_runs,
        "row_bands": len(row_bands),
        "col_bands": len(col_bands),
        "row_band_sizes": tuple(len(run) for run in row_bands),
        "col_band_sizes": tuple(len(run) for run in col_bands),
        "row_divider_thickness": next(iter(row_thicknesses)) if len(row_thicknesses) == 1 else None,
        "col_divider_thickness": next(iter(col_thicknesses)) if len(col_thicknesses) == 1 else None,
        "row_boundary_mode": boundary_mode(divider_rows, height),
        "col_boundary_mode": boundary_mode(divider_cols, width),
    }


def geometry_output(grid):
    info = analyze(grid)
    return [[info["cell_color"]] * info["col_bands"] for _ in range(info["row_bands"])]


def line_count_rival(grid):
    """Plausible wrong rule: count individual full lines, correcting only edges."""
    info = analyze(grid)
    row_edges = int(0 in info["divider_rows"]) + int(info["height"] - 1 in info["divider_rows"])
    col_edges = int(0 in info["divider_cols"]) + int(info["width"] - 1 in info["divider_cols"])
    rows = len(info["divider_rows"]) + 1 - row_edges
    cols = len(info["divider_cols"]) + 1 - col_edges
    return [[info["cell_color"]] * cols for _ in range(rows)]


def build_lattice(*, row_band_sizes, col_band_sizes, row_divider_thickness=1,
                  col_divider_thickness=1, row_boundary_mode="none",
                  col_boundary_mode="none", cell_color=5, divider_color=8):
    if cell_color == divider_color:
        raise ValueError("colors must differ")
    if row_boundary_mode not in {"none", "start", "end", "both"}:
        raise ValueError("bad row boundary mode")
    if col_boundary_mode not in {"none", "start", "end", "both"}:
        raise ValueError("bad column boundary mode")

    def axis(lengths, thickness, mode):
        values = []
        if mode in {"start", "both"}:
            values.extend([True] * thickness)
        for index, size in enumerate(lengths):
            values.extend([False] * size)
            if index + 1 < len(lengths):
                values.extend([True] * thickness)
        if mode in {"end", "both"}:
            values.extend([True] * thickness)
        return values

    row_divider = axis(tuple(row_band_sizes), row_divider_thickness, row_boundary_mode)
    col_divider = axis(tuple(col_band_sizes), col_divider_thickness, col_boundary_mode)
    return [
        [divider_color if is_div_row or is_div_col else cell_color
         for is_div_col in col_divider]
        for is_div_row in row_divider
    ]


def witness_input():
    return build_lattice(
        row_band_sizes=(2, 2),
        col_band_sizes=(2, 2),
        row_divider_thickness=2,
        col_divider_thickness=2,
        row_boundary_mode="none",
        col_boundary_mode="start",
    )


def canonical_rule_source():
    from reviewer_support import canonical_path, find_root

    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK and row.get("program_solution"):
                    return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK}: no canonical program_solution")


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical_rule_source(), "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
