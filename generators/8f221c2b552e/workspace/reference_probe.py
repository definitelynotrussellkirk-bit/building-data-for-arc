"""Independent oracle and distribution probes for generator 8f221c2b552e.

This module intentionally does not import production geometry helpers.  It is
review/test tooling; the canonical Racket program remains the label authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK_ID = "8f221c2b552e"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(
        path
        or os.environ.get("GENERATOR_UNDER_TEST")
        or ROOT / f"generators/{TASK_ID}/generator.py"
    ).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_8f221c2b552e", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def bridge_rows(grid):
    """Independent direct implementation of the written row-pair rule."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        by_color: dict[int, list[int]] = {}
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append(c)
        for color, columns in by_color.items():
            if len(columns) >= 2:
                for c in range(min(columns), max(columns) + 1):
                    out[r][c] = color
    return out


def analyze(grid):
    """Recover the proposed public axes from pixels alone.

    Raises ValueError for a grid outside the proposed generated manifold.  This
    is intentionally independent of production ``observe_overrides``.
    """
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("empty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("empty row")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")

    pair_colors: list[int] = []
    gaps: list[int] = []
    distractors: list[int] = []
    for row in grid:
        positions: dict[int, list[int]] = {}
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("invalid cell")
            if value:
                positions.setdefault(value, []).append(c)
        repeated = [(color, cols) for color, cols in positions.items() if len(cols) >= 2]
        if repeated:
            if len(repeated) != 1 or len(positions) != 1:
                raise ValueError("pair rows must contain one repeated color only")
            color, cols = repeated[0]
            if len(cols) != 2 or cols[1] - cols[0] < 2:
                raise ValueError("pair row must have two separated endpoints")
            if any(row[c] != 0 for c in range(cols[0] + 1, cols[1])):
                raise ValueError("pair interior must start empty")
            pair_colors.append(color)
            gaps.append(cols[1] - cols[0] - 1)
        else:
            if any(len(cols) != 1 for cols in positions.values()):
                raise ValueError("non-pair rows may contain only singletons")
            distractors.extend(positions)

    if len(pair_colors) < 2:
        raise ValueError("need at least two pair rows")
    if len(set(pair_colors)) == 1:
        color_mode = "shared"
    elif len(set(pair_colors)) == len(pair_colors):
        color_mode = "distinct"
    else:
        raise ValueError("pair colors must be all shared or all distinct")

    short = any(gap <= 2 for gap in gaps)
    long = any(gap >= 3 for gap in gaps)
    span_style = "mixed" if short and long else ("short" if short else "long")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_pairs": len(pair_colors),
        "color_mode": color_mode,
        "distractor_count": len(distractors),
        "span_style": span_style,
    }


def profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def cyclic_lessons(module, *, seed: int, band: str, starts: int = 30, n_demos: int = 3):
    """Yield every short sliding lesson from a deterministic generated stream."""
    for start in range(starts):
        pairs = []
        for offset in range(n_demos + 1):
            grid = module.generate(seed + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": bridge_rows(grid)})
        yield pairs[:n_demos], pairs[-1]


def cyclic_lesson_rotations(
    module, *, seed: int, band: str, starts: int = 30, window_size: int = 4
):
    """Yield every query rotation of short cyclic windows.

    Each returned case has ``window_size - 1`` demonstrations and one query.
    This catches schedules whose sole semantic witness accidentally lands in the
    query rather than in the demonstrations.
    """
    if starts < 1:
        raise ValueError("starts must be positive")
    if window_size < 2:
        raise ValueError("window_size must be at least 2")
    for start in range(starts):
        pairs = []
        for offset in range(window_size):
            grid = module.generate(seed + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": bridge_rows(grid)})
        for query_index in range(window_size):
            yield {
                "start": start,
                "query_index": query_index,
                "demos": [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ],
                "query": pairs[query_index],
            }


def racket_outputs(grids):
    """Apply the real selected Racket authority to a batch; never fall back."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = next(
        json.loads(line)
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    with tempfile.TemporaryDirectory(prefix="8f221c2b552e-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": row["program_solution"], "grids": grids})
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
