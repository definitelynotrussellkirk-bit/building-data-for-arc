"""Independent semantic oracle and rival probes for 59a9a5c505fb.

This module deliberately does not import analysis/rendering helpers from the
reviewed generator.  The canonical Racket program remains the label authority;
these Python functions are a separately implemented mirror used for focused
regressions and retained evidence.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "59a9a5c505fb"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if not RUNTIME.exists():
    # Portable task-test runtime: workspace/ and tests/ sit beside copied data.
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "puzzle_generators").is_dir() and (candidate / "reviewer_support.py").is_file():
            RUNTIME = candidate
            break
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

Grid = list[list[int]]
Box = tuple[int, int, int, int]
CANONICAL_PROFILES = {
    (9, 9, 3),
    (10, 12, 3),
    (11, 11, 4),
    (12, 14, 4),
    (11, 13, 4),
}


class GeometryError(ValueError):
    """Raised when a grid is outside the independent probe's lawful domain."""


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_59a9a5c505fb", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise GeometryError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise GeometryError("expected nonempty rows")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise GeometryError("ragged grid")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise GeometryError("cells must be integer ARC colors 0..9")
    return len(grid), width


def _components(grid) -> list[dict]:
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    parts: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for point in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    pr, pc = point
                    if (0 <= pr < h and 0 <= pc < w and point not in seen
                            and grid[pr][pc] == color):
                        seen.add(point)
                        todo.append(point)
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            box: Box = (min(rs), min(cs), max(rs), max(cs))
            r1, c1, r2, c2 = box
            perimeter = {
                (rr, cc)
                for rr in range(r1, r2 + 1)
                for cc in range(c1, c2 + 1)
                if rr in (r1, r2) or cc in (c1, c2)
            }
            parts.append({
                "color": color,
                "cells": frozenset(cells),
                "box": box,
                "is_frame": cells == perimeter and r1 < r2 and c1 < c2,
            })
    return parts


def _contains(outer: Box, inner: Box, *, strict: bool = False) -> bool:
    okay = (outer[0] <= inner[0] and outer[1] <= inner[1]
            and outer[2] >= inner[2] and outer[3] >= inner[3])
    return okay and (not strict or outer != inner)


def _overlap(a: Box, b: Box) -> bool:
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])


def _boxes_form_strict_chain(boxes: Iterable[Box]) -> bool:
    seq = list(boxes)
    return all(_contains(a, b, strict=True) or _contains(b, a, strict=True)
               for index, a in enumerate(seq) for b in seq[index + 1 :])


def analyze(grid) -> dict:
    h, w = _validate_grid(grid)
    parts = _components(grid)
    boxes = [part["box"] for part in parts]
    palette = tuple(sorted({value for row in grid for value in row}))
    depth = [[0] * w for _ in range(h)]
    for r1, c1, r2, c2 in boxes:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                depth[r][c] += 1
    return {
        "height": h,
        "width": w,
        "palette": palette,
        "components": parts,
        "boxes": boxes,
        "all_frames": bool(parts) and all(part["is_frame"] for part in parts),
        "any_frames": any(part["is_frame"] for part in parts),
        "any_non_frame": any(not part["is_frame"] for part in parts),
        "strict_chain": _boxes_form_strict_chain(boxes),
        "has_crossing_pair": any(
            _overlap(a, b) and not _contains(a, b) and not _contains(b, a)
            for index, a in enumerate(boxes) for b in boxes[index + 1 :]
        ),
        "max_depth": max((value for row in depth for value in row), default=0),
    }


def intended_output(grid) -> Grid:
    info = analyze(grid)
    out = [[0] * info["width"] for _ in range(info["height"])]
    for r1, c1, r2, c2 in info["boxes"]:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] += 1
    return out


def rival_frame_fill_only(grid) -> Grid:
    """Canonical-fitting shortcut: only true rectangle frames imply bbox fill."""
    info = analyze(grid)
    out = [[0] * info["width"] for _ in range(info["height"])]
    for part in info["components"]:
        cells = None
        if part["is_frame"]:
            r1, c1, r2, c2 = part["box"]
            cells = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        else:
            cells = set(part["cells"])
        for r, c in cells:
            out[r][c] += 1
    return out


def rival_nested_chain_only(grid) -> Grid:
    """Canonical-fitting shortcut: non-nested objects count only where visible."""
    info = analyze(grid)
    out = [[0] * info["width"] for _ in range(info["height"])]
    boxes = info["boxes"]
    for index, part in enumerate(info["components"]):
        comparable = all(
            index == other or _contains(part["box"], boxes[other])
            or _contains(boxes[other], part["box"])
            for other in range(len(boxes))
        )
        if comparable:
            r1, c1, r2, c2 = part["box"]
            cells = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        else:
            cells = set(part["cells"])
        for r, c in cells:
            out[r][c] += 1
    return out


def rival_visible_cells_only(grid) -> Grid:
    info = analyze(grid)
    out = [[0] * info["width"] for _ in range(info["height"])]
    for part in info["components"]:
        for r, c in part["cells"]:
            out[r][c] += 1
    return out


def profile_of(grid) -> str:
    info = analyze(grid)
    if info["strict_chain"] and info["all_frames"]:
        return "nested_frames"
    if info["strict_chain"] and info["any_non_frame"] and not info["any_frames"]:
        return "nested_sparse"
    if info["has_crossing_pair"] and not info["any_frames"]:
        return "crossing_sparse"
    if info["has_crossing_pair"] and info["any_frames"] and info["any_non_frame"]:
        return "crossing_mixed"
    raise GeometryError("grid does not match any reviewed scene profile")


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Execute the selected canonical Racket source; never use a fallback."""
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

    canonical = root / "data" / "canonical" / "puzzles.jsonl"
    if not canonical.exists():
        canonical = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    program = None
    with canonical.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                program = row["program_solution"]
                break
    if not program:
        raise RuntimeError("selected canonical Racket source not found")

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(root), stage, TASK_ID)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": grids}))
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
