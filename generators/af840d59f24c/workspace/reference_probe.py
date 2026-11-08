"""Independent oracle and diagnostics for af840d59f24c.

This module is test/review tooling.  It does not provide production labels and
uses the canonical Racket runtime only when ``racket_outputs`` is requested.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "af840d59f24c"


def _bootstrap_runtime(start: Path) -> Path:
    """Locate reviewer_support without assuming this helper's nesting depth."""
    start = start.resolve()
    for candidate in (start, *start.parents):
        if ((candidate / "RUNTIME_MANIFEST.json").is_file()
                and (candidate / "reviewer_support.py").is_file()):
            return candidate
        if (candidate / "shared/runtime/reviewer_support.py").is_file():
            return candidate
    raise FileNotFoundError(f"No shared/runtime/reviewer_support.py above {start}")


_BOOTSTRAP_ROOT = _bootstrap_runtime(Path(__file__).parent)
_DEPENDENCY_ROOT = (_BOOTSTRAP_ROOT if (_BOOTSTRAP_ROOT / "RUNTIME_MANIFEST.json").is_file()
                    else _BOOTSTRAP_ROOT / "shared/runtime")
sys.path.insert(0, str(_DEPENDENCY_ROOT))
from reviewer_support import (  # noqa: E402
    canonical_pairs as read_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
TASK_DIR = Path(__file__).resolve().parents[1]


def load_generator(path=None):
    if path is None:
        return load_selected_generator(TASK_ID, root=ROOT)[0]
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def intended_output(grid):
    """Independent direct implementation of the canonical column-rank rule."""
    zero_columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
    rank = {column: index + 1 for index, column in enumerate(zero_columns)}
    return [
        [rank[c] if value == 0 else value for c, value in enumerate(row)]
        for row in grid
    ]


def zero_stats(grid):
    by_column = Counter()
    first_row = {}
    by_row = Counter()
    nonzero = Counter()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                by_column[c] += 1
                by_row[r] += 1
                first_row.setdefault(c, r)
            else:
                nonzero[value] += 1
    return {
        "columns": tuple(sorted(by_column)),
        "counts": dict(by_column),
        "first_rows": first_row,
        "row_counts": dict(by_row),
        "nonzero_counts": dict(nonzero),
    }


def row_local_rank(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        columns = [c for c, value in enumerate(row) if value == 0]
        ranks = {column: index + 1 for index, column in enumerate(columns)}
        for c in columns:
            out[r][c] = ranks[c]
    return out


def first_seen_rank(grid):
    first = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                first.setdefault(c, (r, c))
    columns = sorted(first, key=lambda c: first[c])
    ranks = {column: index + 1 for index, column in enumerate(columns)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)] for row in grid]


def frequency_rank(grid):
    stats = zero_stats(grid)
    columns = sorted(stats["columns"], key=lambda c: (-stats["counts"][c], c))
    ranks = {column: index + 1 for index, column in enumerate(columns)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)] for row in grid]


def modal_nonzero(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("grid has no nonzero color")
    return min(counts, key=lambda color: (-counts[color], color))


def canonical_record():
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task {TASK_ID} is absent")


def canonical_pairs():
    return list(read_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))


def racket_outputs(grids):
    """Run the actual canonical Racket program in a relocated runtime."""
    sys.path.insert(0, str(_DEPENDENCY_ROOT))
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_record()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
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
