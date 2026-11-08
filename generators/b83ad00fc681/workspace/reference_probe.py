"""Independent oracle and reproducible probes for b83ad00fc681.

This file deliberately does not import parser or solver helpers from the
production generator.  It is test/reviewer tooling, not label authority.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK = "b83ad00fc681"

# Make the portable canonical helper available both in the source checkout and
# in the staged task-test runtime.
_HERE = Path(__file__).resolve()
_SOURCE_ROOT = _HERE.parents[3] if len(_HERE.parents) > 3 else _HERE.parent
if (_SOURCE_ROOT / "shared/runtime").is_dir():
    sys.path.insert(0, str(_SOURCE_ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root

ROOT = Path(find_root(__file__)).resolve()

# The exact dictionary repeated in all three public canonical inputs.  This is
# intentionally a WRONG memorization rule outside those inputs.
FIXED_CANONICAL_PATTERNS = {
    1: ((0, 0, 1), (0, 1, 5), (1, 0, 5), (1, 1, 5)),
    2: ((-1, 0, 6), (0, 0, 2), (0, 1, 6), (1, 0, 6)),
    3: ((0, 0, 3), (0, 1, 7), (0, 2, 7), (1, 1, 7)),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = path or os.environ.get("GENERATOR_UNDER_TEST")
    if candidate is None:
        for p in (
            ROOT / f"generators/{TASK}/generator.py",
            ROOT / f"puzzle_generators/per_puzzle/{TASK}/generator.py",
        ):
            if p.is_file():
                candidate = p
                break
    if candidate is None:
        raise FileNotFoundError("could not locate generator under test")
    path = Path(candidate).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def _rectangular(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("empty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("empty first row")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    return len(grid), width


def split_board(grid: list[list[int]]):
    """Split at the unique full color-9 row and full color-9 top columns."""
    height, width = _rectangular(grid)
    divider_rows = [r for r, row in enumerate(grid) if all(v == 9 for v in row)]
    if len(divider_rows) != 1:
        raise ValueError(f"expected one divider row, found {divider_rows}")
    divider = divider_rows[0]
    if divider == 0 or divider == height - 1:
        raise ValueError("divider leaves an empty top or body")
    top = [list(row) for row in grid[:divider]]
    body = [list(row) for row in grid[divider + 1 :]]
    sep_cols = [c for c in range(width) if all(top[r][c] == 9 for r in range(len(top)))]
    spans = []
    start = 0
    for cut in sep_cols + [width]:
        if cut > start:
            spans.append((start, cut))
        start = cut + 1
    return divider, top, body, spans


def dictionary(grid: list[list[int]]):
    _, top, _, spans = split_board(grid)
    result: dict[int, tuple[tuple[int, int, int], ...]] = {}
    for left, right in spans:
        cells = [
            (r, c - left, top[r][c])
            for r in range(len(top))
            for c in range(left, right)
            if top[r][c] not in (0, 9)
        ]
        if not cells:
            raise ValueError("empty prototype panel")
        key = min(v for _, _, v in cells)
        anchors = [(r, c) for r, c, v in cells if v == key]
        if len(anchors) != 1:
            raise ValueError("prototype key must be a unique minimum")
        ar, ac = anchors[0]
        if key in result:
            raise ValueError("duplicate prototype key")
        result[key] = tuple((r - ar, c - ac, v) for r, c, v in cells)
    return result


def stamp_output(grid: list[list[int]], patterns=None):
    """Independent direct implementation of the documented stamping law."""
    _, _, body, _ = split_board(grid)
    patterns = dictionary(grid) if patterns is None else patterns
    height, width = len(body), len(body[0])
    out = [[0] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            pattern = patterns.get(body[r][c])
            if pattern is None:
                continue
            for dr, dc, color in pattern:
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width:
                    out[rr][cc] = color
    return out


def fixed_dictionary_output(grid: list[list[int]]):
    """Wrong but canonical-fitting rival: ignore the visible top dictionary."""
    return stamp_output(grid, FIXED_CANONICAL_PATTERNS)


def observed(grid: list[list[int]]):
    _, _, body, spans = split_board(grid)
    motifs = dictionary(grid)
    sizes = {len(pattern) for pattern in motifs.values()}
    if len(sizes) != 1:
        raise ValueError(f"prototype sizes differ: {sorted(sizes)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_panels": len(spans),
        "marker_count": sum(v != 0 for row in body for v in row),
        "motif_size": next(iter(sizes)),
        "color_count": len({v for row in grid for v in row}),
    }


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def pinned_profile_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _canonical_path() -> Path:
    for path in (
        ROOT / "shared/data/canonical/puzzles.jsonl",
        ROOT / "data/canonical/puzzles.jsonl",
    ):
        if path.is_file():
            return path
    raise FileNotFoundError("canonical ledger unavailable")


def _canonical_program() -> str:
    with _canonical_path().open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                return row["program_solution"]
    raise FileNotFoundError("canonical Racket program unavailable")


def racket_outputs(grids: Iterable[list[list[int]]]):
    """Require the real selected Racket authority; never fall back to Python."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    source_src = ROOT / "src"
    if source_src.is_dir():
        sys.path.insert(0, str(source_src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    grids = list(grids)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": _canonical_program(), "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(
                f"Racket parity worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket returned an incomplete batch")
        return outputs
