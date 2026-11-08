"""Independent probes for bc932ac8117a.

This module is test/review tooling, not label authority.  ``true_output`` is an
independent Python transcription of the written topology rule; ``racket_outputs``
executes the selected canonical Racket program when parity evidence is required.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

from reviewer_support import canonical_pairs, find_root

TASK = "bc932ac8117a"
ROOT = find_root(__file__)
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
PALETTE_PAIRS = {
    "default": frozenset((2, 3)),
    "warm": frozenset((4, 6)),
    "cool": frozenset((1, 8)),
    "varied": frozenset((5, 9)),
}
PAIR_TO_PALETTE = {pair: name for name, pair in PALETTE_PAIRS.items()}


def load_generator(path: str | os.PathLike[str] | None = None):
    """Load the exact candidate path or the selected repository source."""
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or
                     ROOT / f"generators/{TASK}/generator.py").resolve()
    name = "reviewed_bc932ac8117a_" + str(abs(hash(str(candidate))))
    spec = importlib.util.spec_from_file_location(name, candidate)
    if spec is None or spec.loader is None:
        raise ImportError(candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pairs() -> list[dict[str, Any]]:
    return canonical_pairs(TASK, root=ROOT)


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Monochromatic 4-connected nonzero components, in raster order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while pending:
                current = pending.popleft()
                cells.add(current)
                cr, cc = current
                for dr, dc in DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return result


def enclosed_regions(component: dict[str, Any]) -> list[set[tuple[int, int]]]:
    """Zero regions enclosed by one component, returned in local coordinates."""
    r0, c0, r1, c1 = component["bbox"]
    height, width = r1 - r0 + 1, c1 - c0 + 1
    occupied = {(r - r0, c - c0) for r, c in component["cells"]}
    seen: set[tuple[int, int]] = set()
    regions: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in occupied or (row, col) in seen:
                continue
            pending = deque([(row, col)])
            seen.add((row, col))
            region: set[tuple[int, int]] = set()
            touches_edge = False
            while pending:
                cr, cc = pending.popleft()
                region.add((cr, cc))
                touches_edge |= cr in (0, height - 1) or cc in (0, width - 1)
                for dr, dc in DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr, nc) not in occupied and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            if not touches_edge:
                regions.append(region)
    return regions


def analyze(grid: list[list[int]]) -> tuple[dict[str, Any], dict[str, Any], list[set[tuple[int, int]]]]:
    records = components(grid)
    hollow_records = [(record, enclosed_regions(record)) for record in records]
    hollows = [(record, holes) for record, holes in hollow_records if holes]
    solids = [record for record, holes in hollow_records if not holes]
    if len(hollows) != 1:
        raise ValueError(f"expected one hollow object, found {len(hollows)}")
    hollow, holes = hollows[0]
    hr0, hc0, hr1, hc1 = hollow["bbox"]
    hshape = (hr1 - hr0 + 1, hc1 - hc0 + 1)
    matches = []
    for solid in solids:
        sr0, sc0, sr1, sc1 = solid["bbox"]
        if (sr1 - sr0 + 1, sc1 - sc0 + 1) == hshape:
            matches.append(solid)
    if len(matches) != 1:
        raise ValueError(f"expected one same-size solid twin, found {len(matches)}")
    return hollow, matches[0], holes


def true_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent intended rule: transfer every enclosed local zero region."""
    hollow, solid, holes = analyze(grid)
    sr0, sc0, _, _ = solid["bbox"]
    output = deepcopy(grid)
    for region in holes:
        for row, col in region:
            output[sr0 + row][sc0 + col] = 0
    return output


def expected_pattern(size: int, diagonal: str) -> set[tuple[int, int]]:
    if size == 4:
        base = {(1, 1), (2, 2)}
    elif size == 5:
        base = {(1, 1), (2, 1), (2, 2), (3, 2)}
    else:
        raise ValueError(size)
    if diagonal == "anti":
        return {(row, size - 1 - col) for row, col in base}
    if diagonal != "main":
        raise ValueError(diagonal)
    return base


def observed(grid: list[list[int]]) -> dict[str, Any]:
    hollow, solid, _ = analyze(grid)
    r0, c0, r1, c1 = hollow["bbox"]
    size = r1 - r0 + 1
    interior = {(r - r0, c - c0) for r, c in hollow["cells"]
                if r0 < r < r1 and c0 < c < c1}
    diagonal = next((name for name in ("main", "anti")
                     if interior == expected_pattern(size, name)), None)
    if diagonal is None:
        raise ValueError(f"unrecognized divider pattern: {sorted(interior)}")
    colors = frozenset((hollow["color"], solid["color"]))
    if colors not in PAIR_TO_PALETTE:
        raise ValueError(f"unrecognized generated palette: {sorted(colors)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "box_size": size,
        "palette_kind": PAIR_TO_PALETTE[colors],
        "hollow_side": "left" if c0 < solid["bbox"][1] else "right",
        "hole_diagonal": diagonal,
    }


def witness_input() -> list[list[int]]:
    """A 5x11 exact counterexample to both canonical-fitting shortcuts."""
    return [
        [2, 2, 2, 2, 0, 3, 3, 3, 3, 0, 0],
        [2, 2, 0, 2, 0, 3, 3, 3, 3, 0, 0],
        [2, 0, 2, 2, 0, 3, 3, 3, 3, 0, 0],
        [2, 2, 2, 2, 0, 3, 3, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Run the selected canonical Racket program; never fall back to Python."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical = next(row for row in _canonical_rows() if row["task_id"] == TASK)
    materialized = list(grids)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({
            "program": canonical["program_solution"], "grids": materialized,
        }))
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
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(materialized):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def _canonical_rows():
    from reviewer_support import canonical_path
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)
