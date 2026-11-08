"""Independent oracle and repeatable probes for d8ce64d73f8a.

This module deliberately does not import the generator's region helpers.  It is
used by the focused regression suite and can also compare a batch against the
real canonical Racket program when the packaged runtime is available.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "d8ce64d73f8a"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL = CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_d8ce64d73f8a", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)


def canonical_row():
    root = find_root(__file__)
    candidates = (
        root / "shared/data/canonical/puzzles.jsonl",
        root / "data/canonical/puzzles.jsonl",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError("canonical ledger not found")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    return row
    raise KeyError(TASK)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _validate_rectangular(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty list-of-lists grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    return len(grid), width


def region_from(grid, start, *, diagonal=False):
    """Return one non-wall region using an implementation independent of production."""
    h, w = _validate_rectangular(grid)
    sr, sc = start
    if not (0 <= sr < h and 0 <= sc < w) or grid[sr][sc] == 5:
        return frozenset()
    steps = DIAGONAL if diagonal else CARDINAL
    seen = {(sr, sc)}
    queue = deque([(sr, sc)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in steps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5 and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return frozenset(seen)


def components(grid, *, diagonal=False):
    h, w = _validate_rectangular(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    result = []
    while unseen:
        start = min(unseen)
        part = region_from(grid, start, diagonal=diagonal)
        result.append(part)
        unseen.difference_update(part)
    return sorted(result, key=lambda cells: min(cells))


def seed_cell(grid):
    hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one seed, found {len(hits)}")
    return hits[0]


def paint(grid, cells):
    out = deepcopy(grid)
    for r, c in cells:
        out[r][c] = 8
    return out


def flood_output(grid, *, diagonal=False):
    return paint(grid, region_from(grid, seed_cell(grid), diagonal=diagonal))


def top_left_output(grid):
    parts = components(grid)
    return paint(grid, parts[0] if parts else ())


def observed(grid):
    parts = components(grid)
    start = seed_cell(grid)
    seed_part = next(part for part in parts if start in part)
    sizes = [len(part) for part in parts]
    return {
        "room_count": len(parts),
        "seed_role": "largest" if len(seed_part) == max(sizes) else "nonlargest",
        "seed_not_top_left": seed_part != parts[0],
        "diagonal_leak": flood_output(grid, diagonal=True) != flood_output(grid),
        "component_sizes": sorted(sizes),
    }


def selected_base_path():
    root = find_root(__file__)
    # Staged task-test runtimes may expose the same corpus under both
    # shared/data and data. Prefer the repository layout instead of treating
    # that relocation mirror as two selected authorities.
    for pattern in (
        f"shared/data/base/solutions/banks/*/*__{TASK}.json",
        f"data/base/solutions/banks/*/*__{TASK}.json",
    ):
        candidates = list(root.glob(pattern))
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            raise RuntimeError(f"expected one selected base record, found {candidates}")
    return None


def racket_outputs(grids):
    """Apply the real selected canonical Racket rule to every grid; never fall back."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = r'''\
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: stdout={result['stdout']!r} stderr={result['stderr']!r}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
