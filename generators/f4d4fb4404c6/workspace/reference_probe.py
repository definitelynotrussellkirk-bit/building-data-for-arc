"""Independent oracle, rivals, and schedule probe for f4d4fb4404c6.

This module intentionally does not import geometry helpers from generator.py.
The canonical Racket program remains the label authority; the Python renderer is
an independently testable mirror used to localize generator and teaching defects.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "f4d4fb4404c6"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

Grid = list[list[int]]
DIRECTIONS = ("up", "down", "left", "right")
CANONICAL_PROFILES = {(18, 17, 3), (22, 19, 3), (22, 22, 3), (24, 24, 3)}


class GeometryError(ValueError):
    """Raised when a grid is outside the independent probe's lawful domain."""


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_f4d4fb4404c6", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_rows() -> list[dict]:
    path = find_root(__file__) / "shared" / "data" / "canonical" / "puzzles.jsonl"
    if not path.exists():
        path = find_root(__file__) / "data" / "canonical" / "puzzles.jsonl"
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if not rows:
        raise KeyError(TASK_ID)
    return rows


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


def frame_ring(top: int, left: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(top, top + 4)
        for c in range(left, left + 4)
        if r in (top, top + 3) or c in (left, left + 3)
    }


def _components(grid, color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    parts: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    todo.append(point)
        parts.append(cells)
    return parts


def _marker_info(cells: set[tuple[int, int]], h: int, w: int) -> dict:
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if len(rows) == 1 and rows[0] == 0 and cols == list(range(cols[0], cols[-1] + 1)):
        direction = "up"
    elif len(rows) == 1 and rows[0] == h - 1 and cols == list(range(cols[0], cols[-1] + 1)):
        direction = "down"
    elif len(cols) == 1 and cols[0] == 0 and rows == list(range(rows[0], rows[-1] + 1)):
        direction = "left"
    elif len(cols) == 1 and cols[0] == w - 1 and rows == list(range(rows[0], rows[-1] + 1)):
        direction = "right"
    else:
        raise GeometryError("color-1 component is not a straight contiguous edge marker")
    return {
        "direction": direction,
        "r1": rows[0], "r2": rows[-1],
        "c1": cols[0], "c2": cols[-1],
        "cells": frozenset(cells),
        "length": len(cells),
    }


def analyze(grid) -> dict:
    """Parse frames and markers without using generator implementation code."""
    h, w = _validate_grid(grid)
    frames = []
    occupied: set[tuple[int, int]] = set()
    for top in range(h - 3):
        for left in range(w - 3):
            ring = frame_ring(top, left)
            values = {grid[r][c] for r, c in ring}
            if len(values) != 1:
                continue
            color = next(iter(values))
            if color in (0, 1):
                continue
            if any(grid[r][c] != 0 for r in (top + 1, top + 2) for c in (left + 1, left + 2)):
                continue
            if occupied & ring:
                raise GeometryError("overlapping 4x4 frame candidates")
            index = len(frames)
            frame = {
                "index": index,
                "color": color,
                "r1": top, "r2": top + 3,
                "c1": left, "c2": left + 3,
                "cells": frozenset(ring),
            }
            frames.append(frame)
            occupied.update(ring)
    if not frames:
        raise GeometryError("no 4x4 hollow frame")

    markers = [_marker_info(cells, h, w) for cells in _components(grid, 1)]
    if not markers:
        raise GeometryError("no color-1 edge marker")

    marker_cells = set().union(*(set(marker["cells"]) for marker in markers))
    foreground = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    stray = foreground - occupied - marker_cells
    if stray:
        raise GeometryError(f"{len(stray)} foreground cells are outside frames and markers")

    frame_marker_counts = [0] * len(frames)
    for marker in markers:
        direction = marker["direction"]
        matches = []
        for frame in frames:
            if direction in ("up", "down"):
                aligned = not (frame["c2"] < marker["c1"] or marker["c2"] < frame["c1"])
                room = frame["r1"] if direction == "up" else h - 1 - frame["r2"]
            else:
                aligned = not (frame["r2"] < marker["r1"] or marker["r2"] < frame["r1"])
                room = frame["c1"] if direction == "left" else w - 1 - frame["c2"]
            if aligned and room >= 4:
                matches.append(frame)
        if len(matches) != 1:
            raise GeometryError(f"{direction} marker matches {len(matches)} frames, expected 1")
        marker["frame_index"] = matches[0]["index"]
        marker["room"] = (
            matches[0]["r1"] if direction == "up"
            else h - 1 - matches[0]["r2"] if direction == "down"
            else matches[0]["c1"] if direction == "left"
            else w - 1 - matches[0]["c2"]
        )
        frame_marker_counts[matches[0]["index"]] += 1
    if any(count == 0 for count in frame_marker_counts):
        raise GeometryError("every frame must be selected by at least one marker")

    return {
        "height": h,
        "width": w,
        "frames": frames,
        "markers": markers,
        "frame_marker_counts": frame_marker_counts,
    }


def marker_exactly_spans_frame(marker: dict, frame: dict) -> bool:
    if marker["direction"] in ("up", "down"):
        return marker["c1"] == frame["c1"] and marker["c2"] == frame["c2"]
    return marker["r1"] == frame["r1"] and marker["r2"] == frame["r2"]


def _draw_ring(out: Grid, color: int, r1: int, c1: int, r2: int, c2: int) -> None:
    h, w = len(out), len(out[0])
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if (r in (r1, r2) or c in (c1, c2)) and 0 <= r < h and 0 <= c < w:
                out[r][c] = color


def _render(
    grid,
    *,
    exact_span_only: bool = False,
    global_color: bool = False,
    one_copy_only: bool = False,
    first_marker_only: bool = False,
) -> Grid:
    parsed = analyze(grid)
    h, w = parsed["height"], parsed["width"]
    out = [[0] * w for _ in range(h)]
    first_color = parsed["frames"][0]["color"]
    for frame in parsed["frames"]:
        color = first_color if global_color else frame["color"]
        _draw_ring(out, color, frame["r1"], frame["c1"], frame["r2"], frame["c2"])

    seen_frames: set[int] = set()
    for marker in parsed["markers"]:
        frame = parsed["frames"][marker["frame_index"]]
        if exact_span_only and not marker_exactly_spans_frame(marker, frame):
            continue
        if first_marker_only and frame["index"] in seen_frames:
            continue
        seen_frames.add(frame["index"])
        color = first_color if global_color else frame["color"]
        direction = marker["direction"]
        if direction == "up":
            positions = ((frame["r1"] - 4 * step, frame["c1"]) for step in range(1, h + 1))
        elif direction == "down":
            positions = ((frame["r2"] + 1 + 4 * (step - 1), frame["c1"]) for step in range(1, h + 1))
        elif direction == "left":
            positions = ((frame["r1"], frame["c1"] - 4 * step) for step in range(1, w + 1))
        else:
            positions = ((frame["r1"], frame["c2"] + 1 + 4 * (step - 1)) for step in range(1, w + 1))
        for copy_index, (top, left) in enumerate(positions):
            if direction == "up" and top + 3 < 0:
                break
            if direction == "down" and top >= h:
                break
            if direction == "left" and left + 3 < 0:
                break
            if direction == "right" and left >= w:
                break
            _draw_ring(out, color, top, left, top + 3, left + 3)
            if one_copy_only and copy_index == 0:
                break
    return out


def intended_output(grid) -> Grid:
    return _render(grid)


def rival_exact_span_only(grid) -> Grid:
    return _render(grid, exact_span_only=True)


def rival_global_frame_color(grid) -> Grid:
    return _render(grid, global_color=True)


def rival_one_copy_only(grid) -> Grid:
    return _render(grid, one_copy_only=True)


def rival_first_marker_only(grid) -> Grid:
    return _render(grid, first_marker_only=True)


def facts(grid) -> dict:
    parsed = analyze(grid)
    colors = {frame["color"] for frame in parsed["frames"]}
    exact = [
        marker_exactly_spans_frame(marker, parsed["frames"][marker["frame_index"]])
        for marker in parsed["markers"]
    ]
    return {
        "height": parsed["height"],
        "width": parsed["width"],
        "palette": tuple(sorted({value for row in grid for value in row})),
        "frame_count": len(parsed["frames"]),
        "frame_colors": tuple(sorted(colors)),
        "marker_count": len(parsed["markers"]),
        "marker_lengths": tuple(sorted(marker["length"] for marker in parsed["markers"])),
        "directions": tuple(sorted({marker["direction"] for marker in parsed["markers"]})),
        "all_exact_span": all(exact),
        "has_partial_overlap": not all(exact),
        "has_long_chain": any(marker["room"] >= 8 for marker in parsed["markers"]),
        "has_multi_marker_frame": any(count >= 2 for count in parsed["frame_marker_counts"]),
    }


def profile_of(grid) -> str:
    info = facts(grid)
    multiple_colors = len(info["frame_colors"]) > 1
    partial_overlap = info["has_partial_overlap"]
    if multiple_colors and partial_overlap:
        return "combined_witness"
    if multiple_colors:
        return "multicolor_frames"
    if partial_overlap:
        return "overlap_marker"
    return "canonical_core"


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Require and execute the canonical Racket authority; never fall back."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_rows()[0]["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        request = {"program": program, "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> dict:
    canonical = canonical_pairs()
    reports = {}
    for band in ("easy", "medium", "hard"):
        counter = Counter(samples=count)
        profiles = Counter()
        dimensions = Counter()
        inputs = set()
        for index in range(count):
            grid = module.generate(17000 + index, index, difficulty=band)
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            counter["self_check_failures"] += bool(module.self_check(grid))
            counter["nondeterministic"] += grid != module.generate(17000 + index, index, difficulty=band)
            info = facts(grid)
            profiles[profile_of(grid)] += 1
            dimensions[(info["height"], info["width"], len(info["palette"]))] += 1
            intended = intended_output(grid)
            counter["exact_span_disagreements"] += rival_exact_span_only(grid) != intended
            counter["global_color_disagreements"] += rival_global_frame_color(grid) != intended
            counter["one_copy_disagreements"] += rival_one_copy_only(grid) != intended
            counter["first_marker_disagreements"] += rival_first_marker_only(grid) != intended
        reports[band] = {
            "counts": dict(counter),
            "profiles": dict(profiles),
            "dimensions": {str(k): v for k, v in dimensions.items()},
            "distinct_inputs": len(inputs),
        }
    canonical_matches = sum(intended_output(pair["input"]) == pair["output"] for pair in canonical)
    shortcut_fit = {
        "exact_span_only": all(rival_exact_span_only(pair["input"]) == pair["output"] for pair in canonical),
        "global_frame_color": all(rival_global_frame_color(pair["input"]) == pair["output"] for pair in canonical),
    }
    return {
        "schema": f"{TASK_ID}-independent-audit-v1",
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_pairs": len(canonical),
        "canonical_oracle_matches": canonical_matches,
        "canonical_shortcut_fit": shortcut_fit,
        "bands": reports,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK_ID}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids += [module.generate(700 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(18)]
        authoritative = racket_outputs(grids)
        mismatches = [i for i, (grid, out) in enumerate(zip(grids, authoritative)) if intended_output(grid) != out]
        report["racket"] = {"checked": len(grids), "mismatches": mismatches}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(
        report["canonical_oracle_matches"] != report["canonical_pairs"]
        or not all(report["canonical_shortcut_fit"].values())
        or any(
            item["counts"]["self_check_failures"] or item["counts"]["nondeterministic"]
            for item in report["bands"].values()
        )
        or bool(report.get("racket", {}).get("mismatches"))
    )


if __name__ == "__main__":
    raise SystemExit(main())
