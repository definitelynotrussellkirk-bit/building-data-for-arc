"""Independent geometry probe for task 76b818438a96.

This module is reviewer tooling, not label authority.  It parses the two
L-path/two-marker scene without importing production helpers, offers a small
Python mirror for diagnostics, and can require real canonical Racket parity.
The CLI writes replayable geometry/distribution evidence for future reviewers.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK = "76b818438a96"
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict[str, Any]:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical()
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return [*row.get("train", []), *test]


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while stack:
                point = stack.pop()
                cells.add(point)
                for dr, dc in DIRS4:
                    nxt = point[0] + dr, point[1] + dc
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append({"color": color, "cells": cells})
    return result


def _simple_path(component: dict[str, Any]) -> dict[str, Any] | None:
    """Analyze a one-cell-wide, non-branching orthogonal path.

    Canonical paths may turn several times; the invariant is graph topology,
    not an L-shaped bounding box.  Nonconsecutive side-touching cells create
    extra graph edges and are therefore rejected here.
    """
    cells: set[tuple[int, int]] = component["cells"]
    if len(cells) < 3:
        return None
    degrees = {
        point: sum((point[0] + dr, point[1] + dc) in cells for dr, dc in DIRS4)
        for point in cells
    }
    if any(degree not in (1, 2) for degree in degrees.values()):
        return None
    endpoints = tuple(sorted(point for point, degree in degrees.items() if degree == 1))
    if len(endpoints) != 2:
        return None
    order = []
    previous = None
    current = endpoints[0]
    while current is not None:
        order.append(current)
        choices = [
            (current[0] + dr, current[1] + dc)
            for dr, dc in DIRS4
            if (current[0] + dr, current[1] + dc) in cells
            and (current[0] + dr, current[1] + dc) != previous
        ]
        if len(choices) > 1:
            return None
        nxt = choices[0] if choices else None
        previous, current = current, nxt
    if len(order) != len(cells) or order[-1] != endpoints[1]:
        return None
    directions = [
        (b[0] - a[0], b[1] - a[1]) for a, b in zip(order, order[1:])
    ]
    turns = sum(left != right for left, right in zip(directions, directions[1:]))
    if turns < 1:
        return None
    segment_lengths = []
    run = 1
    for left, right in zip(directions, directions[1:]):
        if left == right:
            run += 1
        else:
            segment_lengths.append(run)
            run = 1
    segment_lengths.append(run)
    return {
        "color": component["color"],
        "cells": cells,
        "endpoints": endpoints,
        "order": tuple(order),
        "turn_count": turns,
        "segment_lengths": tuple(segment_lengths),
    }


def _outward(path: dict[str, Any], endpoint: tuple[int, int]) -> tuple[int, int]:
    cells = path["cells"]
    neighbor = next(
        (point for point in cells if abs(point[0] - endpoint[0]) + abs(point[1] - endpoint[1]) == 1),
        None,
    )
    if neighbor is None:
        raise ValueError("endpoint has no path neighbor")
    return endpoint[0] - neighbor[0], endpoint[1] - neighbor[1]


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    """Return exact object/link geometry or raise ValueError on a malformed scene."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors")
    components = _components([list(row) for row in grid])
    paths = []
    markers = []
    for component in components:
        if len(component["cells"]) == 1:
            markers.append({"color": component["color"], "point": next(iter(component["cells"]))})
        else:
            path = _simple_path(component)
            if path is None:
                raise ValueError(f"non-path component of size {len(component['cells'])}")
            paths.append(path)
    if len(paths) != 2 or len(markers) != 2:
        raise ValueError(f"expected two L paths and two markers, found {len(paths)} and {len(markers)}")
    if len({component["color"] for component in components}) != 4:
        raise ValueError("the four objects must use four distinct colors")

    h = len(grid)
    links = []
    used_markers: set[tuple[int, int]] = set()
    for path in paths:
        candidates = []
        for endpoint in path["endpoints"]:
            dr, dc = _outward(path, endpoint)
            for marker in markers:
                mr, mc = marker["point"]
                delta_r, delta_c = mr - endpoint[0], mc - endpoint[1]
                if dr and (delta_c != 0 or delta_r * dr <= 0):
                    continue
                if dc and (delta_r != 0 or delta_c * dc <= 0):
                    continue
                distance = abs(delta_r) + abs(delta_c)
                corridor = [
                    (endpoint[0] + dr * step, endpoint[1] + dc * step)
                    for step in range(1, distance)
                ]
                if all(0 <= r < h and 0 <= c < w and grid[r][c] == 0 for r, c in corridor):
                    candidates.append((endpoint, (dr, dc), marker, distance))
        if len(candidates) != 1:
            raise ValueError(f"path color {path['color']} has {len(candidates)} clear aligned markers")
        endpoint, direction, marker, distance = candidates[0]
        if distance < 2:
            raise ValueError(f"path color {path['color']} has an adjacent marker")
        if marker["point"] in used_markers:
            raise ValueError("one marker is aligned to both paths")
        used_markers.add(marker["point"])
        other_endpoint = next(point for point in path["endpoints"] if point != endpoint)
        links.append(
            {
                "path": path,
                "marker": marker,
                "aligned_endpoint": endpoint,
                "other_endpoint": other_endpoint,
                "direction": direction,
                "distance": distance,
                "extension_count": distance - 1,
            }
        )
    if len(used_markers) != 2:
        raise ValueError("not every marker is used exactly once")
    return {
        "height": len(grid),
        "width": w,
        "paths": paths,
        "markers": markers,
        "links": links,
        "colors": tuple(sorted({value for row in grid for value in row if value})),
    }


def _walk_path(path: dict[str, Any], start: tuple[int, int]) -> list[tuple[int, int]]:
    order = list(path["order"])
    if start == order[0]:
        return order
    if start == order[-1]:
        return list(reversed(order))
    raise ValueError("path traversal must start at an endpoint")


def reference_output(
    grid: list[list[int]],
    *,
    minimum_marker_distance: int = 1,
    recolor_origin: str = "opposite",
) -> list[list[int]]:
    """Diagnostic Python mirror; use real Racket for retained authority evidence."""
    if recolor_origin not in {"opposite", "aligned"}:
        raise ValueError("recolor_origin must be 'opposite' or 'aligned'")
    scene = analyze_scene(grid)
    out = deepcopy(grid)
    for link in scene["links"]:
        if link["distance"] < minimum_marker_distance:
            continue
        dr, dc = link["direction"]
        er, ec = link["aligned_endpoint"]
        for step in range(1, link["distance"]):
            out[er + dr * step][ec + dc * step] = link["path"]["color"]
        start = link["other_endpoint"] if recolor_origin == "opposite" else link["aligned_endpoint"]
        for r, c in _walk_path(link["path"], start)[: link["extension_count"]]:
            out[r][c] = link["marker"]["color"]
    return out


def observed(grid: list[list[int]]) -> dict[str, Any]:
    scene = analyze_scene(grid)
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "path_sizes": tuple(sorted(len(path["cells"]) for path in scene["paths"])),
        "marker_distances": tuple(sorted(link["distance"] for link in scene["links"])),
        "extension_counts": tuple(sorted(link["extension_count"] for link in scene["links"])),
        "turn_counts": tuple(sorted(path["turn_count"] for path in scene["paths"])),
        "colors": scene["colors"],
    }


def racket_outputs(grids: list[list[list[int]]], programs: list[str] | None = None):
    """Execute real Racket programs; never fall back to the Python mirror."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    if programs is None:
        programs = [canonical()["program_solution"]]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"programs": programs, "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
all_outputs=[]
for program in request["programs"]:
    bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(program))
    try:
        all_outputs.append([runner._apply_rule(bridge,name,g) for g in request["grids"]])
    finally:
        bridge.close()
print(json.dumps(all_outputs))
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(programs) or any(len(row) != len(grids) for row in outputs):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict[str, Any], list[list[list[int]]]]:
    pairs = [pair for pair in canonical_pairs() if pair.get("output") is not None]
    canonical_errors = [module.self_check(pair["input"]) for pair in pairs]
    python_mismatches = [
        index for index, pair in enumerate(pairs)
        if reference_output(pair["input"]) != pair["output"]
    ]
    by_band = {}
    retained = [pair["input"] for pair in pairs]
    all_path_sizes: set[int] = set()
    all_distances: set[int] = set()
    all_turn_counts: set[int] = set()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes: set[tuple[int, int]] = set()
        palettes: set[tuple[int, ...]] = set()
        hashes: set[str] = set()
        for index in range(count):
            seed, sample_index = 1201 + index, index * 7 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            again = module.generate(seed, sample_index, difficulty=band)
            counts["samples"] += 1
            counts["nondeterministic"] += grid != again
            counts["self_check_errors"] += bool(module.self_check(grid))
            stats = observed(grid)
            production_stats = module.observe_overrides(grid)
            counts["observer_mismatches"] += any(
                production_stats.get(key) != value
                for key, value in stats.items()
                if key in production_stats
            )
            counts["near_witness"] += min(stats["marker_distances"]) <= 3
            counts["far_witness"] += max(stats["marker_distances"]) >= 4
            counts["far_only_rival_disagrees"] += (
                reference_output(grid, minimum_marker_distance=4) != reference_output(grid)
            )
            shapes.add((stats["grid_h"], stats["grid_w"]))
            palettes.add(stats["colors"])
            all_path_sizes.update(stats["path_sizes"])
            all_distances.update(stats["marker_distances"])
            all_turn_counts.update(stats["turn_counts"])
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 8:
                retained.append(grid)
        counts["distinct_shapes"] = len(shapes)
        counts["distinct_palettes"] = len(palettes)
        counts["distinct_inputs"] = len(hashes)
        by_band[str(band)] = dict(counts)
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_self_check_errors": canonical_errors,
        "canonical_python_mismatches": python_mismatches,
        "by_band": by_band,
        "support": {
            "path_sizes": sorted(all_path_sizes),
            "marker_distances": sorted(all_distances),
            "turn_counts": sorted(all_turn_counts),
        },
        "warning": "Python geometry is supplementary; retained Racket parity is separate.",
    }
    return report, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    generator_path = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or bool(report["canonical_python_mismatches"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["by_band"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)[0]
            mismatches = [
                index for index, (grid, output) in enumerate(zip(grids, outputs))
                if reference_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # evidence should retain the exact runtime failure
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"version": report["version"], "support": report["support"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
