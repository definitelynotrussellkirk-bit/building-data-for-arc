"""Independent visible-geometry oracle and probes for task 195dfcc5b541.

This is reviewer tooling, not label authority.  The optional Racket parity path
executes the canonical program and never silently falls back to this oracle.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

TASK = "195dfcc5b541"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_HINT = Path(__file__).resolve().parents[3]
for candidate in (REPO_HINT / "shared/runtime", REPO_HINT):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import (  # noqa: E402
    canonical_pairs as _canonical_pairs,
    canonical_path,
    find_root,
)

ROOT = find_root(__file__)
NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def load_generator(path=None):
    source = Path(path or TASK_HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs(*, training_only=False):
    pairs = _canonical_pairs(TASK, root=ROOT, labeled_only=True)
    if training_only:
        return [pair for pair in pairs if pair["split"] == "train"]
    return pairs


def norm(cells):
    cells = list(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def rotate(cells):
    return norm((col, -row) for row, col in cells)


def reflect(cells):
    return norm((row, -col) for row, col in cells)


def components_8(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current = stack.pop()
                cells.append(current)
                for row_delta, col_delta in NEIGHBORS_8:
                    nxt = current[0] + row_delta, current[1] + col_delta
                    if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
                        continue
                    if nxt in seen or grid[nxt[0]][nxt[1]] != color:
                        continue
                    seen.add(nxt)
                    stack.append(nxt)
            result.append(cells)
    return result


def geometry_output(grid, *, include_reflections=True):
    """Reproduce the selected rule's shape matching and greedy non-overlap order."""
    height, width = len(grid), len(grid[0])
    matches = []
    for obj in components_8(grid, 8):
        base = norm(obj)
        rotations = []
        shape = base
        for _ in range(4):
            rotations.append(shape)
            shape = rotate(shape)
        variants = [(0, shape) for shape in rotations]
        if include_reflections:
            variants.extend((1, reflect(shape)) for shape in rotations)
        # The Racket source conses candidates, then stably sorts by only
        # (flip-rank,row,column). Prepending reproduces that tie order.
        for flip_rank, shape in variants:
            shape_height = max(row for row, _ in shape) + 1
            shape_width = max(col for _, col in shape) + 1
            for row0 in range(height - shape_height + 1):
                for col0 in range(width - shape_width + 1):
                    cells = tuple((row0 + row, col0 + col) for row, col in shape)
                    if all(grid[row][col] == 3 for row, col in cells):
                        matches.insert(0, (flip_rank, row0, col0, cells))
    matches.sort(key=lambda match: match[:3])
    output = deepcopy(grid)
    used = set()
    for _, _, _, cells in matches:
        if used.intersection(cells):
            continue
        used.update(cells)
        for row, col in cells:
            output[row][col] = 8
    return output


def rotation_only_output(grid):
    return geometry_output(grid, include_reflections=False)


def changed_cells(before, after):
    return [
        (row, col)
        for row in range(len(before))
        for col in range(len(before[0]))
        if before[row][col] != after[row][col]
    ]


def stencil_cells(grid):
    objects = components_8(grid, 8)
    if len(objects) != 1:
        raise ValueError(f"expected one color-8 stencil, found {len(objects)}")
    return objects[0]


def no_copy_mutant(grid):
    """Keep density/palette but replace semantic copies with isolated 3 noise."""
    changed = deepcopy(grid)
    for row in range(len(changed)):
        for col in range(len(changed[0])):
            if changed[row][col] == 3:
                changed[row][col] = 2
    protected = {
        (rr, cc)
        for row, col in stencil_cells(changed)
        for rr in range(max(0, row - 1), min(len(changed), row + 2))
        for cc in range(max(0, col - 1), min(len(changed[0]), col + 2))
    }
    for row in range(0, len(changed), 2):
        for col in range(0, len(changed[0]), 2):
            if (row, col) not in protected and changed[row][col] != 8:
                changed[row][col] = 3
    return changed


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical()["program_solution"], "grids": grids}
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
            raise RuntimeError(f"Racket parity worker failed: {result}")
        return json.loads(result["stdout"])
