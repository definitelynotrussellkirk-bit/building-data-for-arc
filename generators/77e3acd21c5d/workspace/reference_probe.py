"""Independent geometry oracle and audit helpers for 77e3acd21c5d.

This module is test/reviewer tooling.  It deliberately does not import helper
functions from the selected generator, so a shared implementation bug cannot
make the regression suite agree with itself.  Canonical Racket remains the
label authority; this oracle is checked against every labeled canonical pair.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "77e3acd21c5d"
# Task-test snapshots contain a mirrored library and a selected execution
# layout. Import dependencies from the manifest-selected layout consistently;
# mixing the mirrored package with its execution copy violates cache isolation.
RUNTIME_ROOT = ROOT if (ROOT / "RUNTIME_MANIFEST.json").is_file() else ROOT / "shared/runtime"
sys.path.insert(0, str(RUNTIME_ROOT))


def load_generator(path: str | Path | None = None):
    if path is None:
        from reviewer_support import load_selected_generator

        return load_selected_generator(TASK, root=ROOT)[0]
    selected = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_77e3acd21c5d", selected)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as load_pairs

    return load_pairs(TASK, root=ROOT, labeled_only=True)


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def components8(grid) -> list[dict]:
    """Return scan-ordered 8-connected foreground components and bbox facts."""
    height, width = _validate_grid(grid)
    background = grid[0][0]
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == background or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if not (0 <= rr < height and 0 <= cc < width):
                            continue
                        if grid[rr][cc] == background or (rr, cc) in seen:
                            continue
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            c1 = max(c for _, c in cells)
            colors = Counter(grid[r][c] for r, c in cells)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "r0": r0,
                    "c0": c0,
                    "r1": r1,
                    "c1": c1,
                    "h": r1 - r0 + 1,
                    "w": c1 - c0 + 1,
                    "colors": colors,
                }
            )
    return components


def scene(grid) -> dict:
    components = components8(grid)
    blanks = [component for component in components if len(component["colors"]) == 1]
    markers = [component for component in components if len(component["colors"]) > 1]
    if len(blanks) != 1:
        raise ValueError(f"expected exactly one monochrome object, found {len(blanks)}")
    if not markers:
        raise ValueError("expected at least one multicolor object")
    blank = blanks[0]
    widest = max(component["w"] for component in markers)
    source = next(component for component in markers if component["w"] == widest)
    return {
        "background": grid[0][0],
        "components": components,
        "blank": blank,
        "markers": markers,
        "source": source,
    }


def _body_and_marker(grid, component: dict) -> tuple[int, int]:
    colors: Counter = component["colors"]
    if len(colors) != 2:
        raise ValueError(f"expected a two-color marker rectangle, got {dict(colors)}")
    ordered = colors.most_common()
    if ordered[0][1] == ordered[1][1]:
        raise ValueError("body color is not uniquely most common")
    return ordered[0][0], ordered[1][0]


def marker_offsets(grid, component: dict) -> tuple[tuple[int, int], ...]:
    _, marker = _body_and_marker(grid, component)
    return tuple(
        sorted(
            (r - component["r0"], c - component["c0"])
            for r, c in component["cells"]
            if grid[r][c] == marker
        )
    )


def project_offsets(
    offsets: Iterable[tuple[int, int]],
    *,
    source_h: int,
    source_w: int,
    output_h: int,
    output_w: int,
    mirror_ties: bool = True,
) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for marker_r, marker_c in offsets:
        top = marker_r
        bottom = source_h - 1 - marker_r
        left = marker_c
        right = source_w - 1 - marker_c
        if top < bottom:
            rows = (top,)
        elif top > bottom:
            rows = (output_h - 1 - bottom,)
        elif mirror_ties:
            rows = (top, output_h - 1 - bottom)
        else:
            rows = (top,)
        if left < right:
            cols = (left,)
        elif left > right:
            cols = (output_w - 1 - right,)
        elif mirror_ties:
            cols = (left, output_w - 1 - right)
        else:
            cols = (left,)
        for row in rows:
            for col in cols:
                if 0 <= row < output_h and 0 <= col < output_w:
                    result.add((row, col))
    return result


def geometry_output(
    grid,
    *,
    selector: str = "widest",
    mirror_ties: bool = True,
):
    """Independent statement of the canonical component/geometry rule."""
    facts = scene(grid)
    blank = facts["blank"]
    candidates = facts["markers"]
    if selector == "widest":
        widest = max(component["w"] for component in candidates)
        source = next(component for component in candidates if component["w"] == widest)
    elif selector == "first":
        source = candidates[0]
    elif selector == "largest_area":
        source = max(candidates, key=lambda component: component["h"] * component["w"])
    else:
        raise ValueError(f"unknown selector {selector!r}")
    blank_color = next(iter(blank["colors"]))
    _, marker_color = _body_and_marker(grid, source)
    output = [[blank_color for _ in range(blank["w"])] for _ in range(blank["h"])]
    projected = project_offsets(
        marker_offsets(grid, source),
        source_h=source["h"],
        source_w=source["w"],
        output_h=blank["h"],
        output_w=blank["w"],
        mirror_ties=mirror_ties,
    )
    for row, col in projected:
        output[row][col] = marker_color
    return output


def observed(grid) -> dict:
    facts = scene(grid)
    source = facts["source"]
    offsets = marker_offsets(grid, source)
    row_ties = [offset for offset in offsets if offset[0] == source["h"] - 1 - offset[0]]
    col_ties = [offset for offset in offsets if offset[1] == source["w"] - 1 - offset[1]]
    both_ties = [offset for offset in offsets if offset in row_ties and offset in col_ties]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "object_count": len(facts["components"]),
        "blank_bbox": (
            facts["blank"]["r0"],
            facts["blank"]["c0"],
            facts["blank"]["h"],
            facts["blank"]["w"],
        ),
        "source_bbox": (
            source["r0"], source["c0"], source["h"], source["w"]
        ),
        "row_tie_markers": len(row_ties),
        "col_tie_markers": len(col_ties),
        "both_tie_markers": len(both_ties),
        "intended_differs_from_no_tie": (
            geometry_output(grid) != geometry_output(grid, mirror_ties=False)
        ),
        "intended_differs_from_first": (
            geometry_output(grid) != geometry_output(grid, selector="first")
        ),
    }


def profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def racket_outputs(grids):
    """Run the selected canonical Racket rule; never silently fall back."""
    import json
    import tempfile

    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical = next(
        pair
        for pair in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if f'"task_id": "{TASK}"' in pair
    )
    program = __import__("json").loads(canonical)["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
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
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])
