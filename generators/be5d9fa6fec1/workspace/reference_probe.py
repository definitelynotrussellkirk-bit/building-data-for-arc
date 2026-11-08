"""Independent probe/oracle for the be5d9fa6fec1 row-group curriculum.

This module deliberately does not import implementation helpers from generator.py.
The selected Racket program remains label authority; ``intended_output`` is a
small separately implemented mirror for regression tests and diagnostics.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "be5d9fa6fec1"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if not RUNTIME.exists():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "puzzle_generators").is_dir() and (candidate / "reviewer_support.py").is_file():
            RUNTIME = candidate
            break
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

Grid = list[list[int]]
PROFILE_SPECS = {
    0: (20, 4, 14),
    1: (19, 5, 12),
    2: (14, 5, 11),
    3: (15, 3, 8),
    4: (22, 4, 16),
}
SHAPE_TO_PROFILE = {(h, w): profile for profile, (h, w, _) in PROFILE_SPECS.items()}


class RowGrammarError(ValueError):
    """Raised when a grid is malformed or outside the row-block grammar."""


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_be5d9fa6fec1", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise RowGrammarError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise RowGrammarError("expected nonempty rows")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise RowGrammarError("ragged grid")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise RowGrammarError("cells must be integer ARC colors 0..9")
    return len(grid), width


def row_groups(grid) -> list[dict]:
    """Return maximal consecutive runs of identical rows."""
    _validate_grid(grid)
    groups: list[dict] = []
    start = 0
    for stop in range(1, len(grid) + 1):
        if stop == len(grid) or list(grid[stop]) != list(grid[stop - 1]):
            row = tuple(grid[start])
            values = set(row)
            if values <= {0, 1} and 1 in values:
                kind = "mix"
            elif values <= {0, 8} and 8 in values:
                kind = "eight"
            elif values == {0}:
                kind = "zero"
            elif 1 in values and 8 in values:
                kind = "mixed_foregrounds"
            else:
                kind = "other"
            groups.append({
                "start": start,
                "stop": stop,
                "height": stop - start,
                "row": row,
                "kind": kind,
            })
            start = stop
    return groups


def analyze(grid) -> dict:
    height, width = _validate_grid(grid)
    groups = row_groups(grid)
    profile_id = SHAPE_TO_PROFILE.get((height, width))
    palette = tuple(sorted({value for row in grid for value in row}))
    return {
        "height": height,
        "width": width,
        "palette": palette,
        "profile_id": profile_id,
        "groups": groups,
        "group_count": len(groups),
        "heights": tuple(group["height"] for group in groups),
        "kinds": tuple(group["kind"] for group in groups),
        "start_kind": groups[0]["kind"] if groups else None,
        "two_step_repeats": tuple(
            index for index in range(2, len(groups))
            if groups[index]["row"] == groups[index - 2]["row"]
        ),
    }


def group_indices(grid) -> list[int]:
    _validate_grid(grid)
    result: list[int] = []
    group = -1
    previous = None
    for index, row in enumerate(grid):
        current = tuple(row)
        if index == 0 or current != previous:
            group += 1
        result.append(group)
        previous = current
    return result


def _render(grid, selector, cell_selector=lambda value: value != 0) -> Grid:
    _validate_grid(grid)
    indices = group_indices(grid)
    output = deepcopy([list(row) for row in grid])
    seen: set[int] = set()
    for r, row in enumerate(grid):
        group = indices[r]
        first = group not in seen
        seen.add(group)
        if selector(r, group, first):
            for c, value in enumerate(row):
                if cell_selector(value):
                    output[r][c] = 2
    return output


def intended_output(grid) -> Grid:
    return _render(grid, lambda _row, group, _first: group % 3 == 0)


def rival_row_index_mod3(grid) -> Grid:
    return _render(grid, lambda row, _group, _first: row % 3 == 0)


def rival_one_based_groups(grid) -> Grid:
    return _render(grid, lambda _row, group, _first: (group + 1) % 3 == 0)


def rival_first_row_only(grid) -> Grid:
    return _render(grid, lambda _row, group, first: group % 3 == 0 and first)


def rival_color8_only(grid) -> Grid:
    return _render(
        grid,
        lambda _row, group, _first: group % 3 == 0,
        lambda value: value == 8,
    )


def rival_color1_only(grid) -> Grid:
    return _render(
        grid,
        lambda _row, group, _first: group % 3 == 0,
        lambda value: value == 1,
    )


def rival_all_nonzero(grid) -> Grid:
    return _render(grid, lambda _row, _group, _first: True)


RIVALS = {
    "row_index_mod3": rival_row_index_mod3,
    "one_based_groups": rival_one_based_groups,
    "first_row_only": rival_first_row_only,
    "color8_only": rival_color8_only,
    "color1_only": rival_color1_only,
    "all_nonzero": rival_all_nonzero,
}


def canonical_program() -> str:
    root = find_root(__file__)
    for relative in ("data/canonical/puzzles.jsonl", "shared/data/canonical/puzzles.jsonl"):
        path = root / relative
        if path.is_file():
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    if row.get("task_id") == TASK_ID:
                        program = row.get("program_solution")
                        if not program:
                            raise RuntimeError("canonical row has no program_solution")
                        return program
    raise FileNotFoundError("canonical puzzles ledger not found")


def canonical_rule_hash() -> str:
    return hashlib.sha256(" ".join(canonical_program().split()).encode()).hexdigest()[:12]


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Execute canonical Racket source; never substitute the Python mirror."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    root = find_root(__file__)
    src = root / "src"
    if not src.exists():
        src = root / "shared" / "runtime" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(root), stage, TASK_ID)
        request = {"program": canonical_program(), "grids": grids}
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
