"""Independent oracle and repeatable audit for 564cab531f76.

This is reviewer tooling, not a label authority.  ``--racket`` executes the
repository's canonical Racket program and refuses to fall back to Python.
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

ROOT = Path(__file__).resolve().parents[3]
TASK = "564cab531f76"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs  # noqa: E402


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_564cab531f76", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["cells must be integer colors in 0..9"]
    return []


def _components(points):
    remaining = set(points)
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group, stack = {first}, [first]
        while stack:
            row, col = stack.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    group.add(point)
                    stack.append(point)
        groups.append(tuple(sorted(group)))
    return groups


def objects(grid):
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    by_color = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                by_color.setdefault(color, set()).add((row, col))
    result = []
    for color in sorted(by_color):
        for cells in _components(by_color[color]):
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            result.append({"color": color, "cells": cells,
                           "r1": min(rows), "r2": max(rows),
                           "c1": min(cols), "c2": max(cols)})
    return result


def split_objects(grid):
    height, width = len(grid), len(grid[0])
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    corner_set = set(corners)
    corner_objects, blobs = [], []
    for obj in objects(grid):
        if len(obj["cells"]) == 1 and obj["cells"][0] in corner_set:
            corner_objects.append(obj)
        else:
            blobs.append(obj)
    return corners, corner_objects, blobs


def _corner_index_from_flags(bottom, right):
    return 2 * int(bool(bottom)) + int(bool(right))


def _render_rule(grid, selector):
    height, width = len(grid), len(grid[0])
    corners, _, blobs = split_objects(grid)
    out = [[0] * width for _ in range(height)]
    for row, col in corners:
        out[row][col] = grid[row][col]
    for obj in blobs:
        index = selector(obj, height, width, corners)
        if type(index) is not int or not 0 <= index < 4:
            raise ValueError(f"selector returned invalid corner index {index!r}")
        color = grid[corners[index][0]][corners[index][1]]
        for row, col in obj["cells"]:
            out[row][col] = color
    return out


def bbox_center_output(grid):
    def selector(obj, height, width, _corners):
        return _corner_index_from_flags(obj["r1"] + obj["r2"] > height - 1,
                                        obj["c1"] + obj["c2"] > width - 1)
    return _render_rule(grid, selector)


def bbox_top_left_output(grid):
    return _render_rule(grid, lambda obj, h, w, _: _corner_index_from_flags(
        2 * obj["r1"] > h - 1, 2 * obj["c1"] > w - 1))


def bbox_bottom_right_output(grid):
    return _render_rule(grid, lambda obj, h, w, _: _corner_index_from_flags(
        2 * obj["r2"] > h - 1, 2 * obj["c2"] > w - 1))


def occupied_centroid_output(grid):
    def selector(obj, height, width, _):
        count = len(obj["cells"])
        return _corner_index_from_flags(
            2 * sum(row for row, _ in obj["cells"]) > count * (height - 1),
            2 * sum(col for _, col in obj["cells"]) > count * (width - 1),
        )
    return _render_rule(grid, selector)


def first_pixel_output(grid):
    def selector(obj, height, width, _):
        row, col = min(obj["cells"])
        return _corner_index_from_flags(2 * row > height - 1, 2 * col > width - 1)
    return _render_rule(grid, selector)


def nearest_pixel_manhattan_output(grid):
    def selector(obj, _height, _width, corners):
        return min(range(4), key=lambda index: min(
            abs(row - corners[index][0]) + abs(col - corners[index][1])
            for row, col in obj["cells"]))
    return _render_rule(grid, selector)


def nearest_pixel_euclidean_output(grid):
    def selector(obj, _height, _width, corners):
        return min(range(4), key=lambda index: min(
            (row - corners[index][0]) ** 2 + (col - corners[index][1]) ** 2
            for row, col in obj["cells"]))
    return _render_rule(grid, selector)


def ties_bottom_right_output(grid):
    return _render_rule(grid, lambda obj, h, w, _: _corner_index_from_flags(
        obj["r1"] + obj["r2"] >= h - 1,
        obj["c1"] + obj["c2"] >= w - 1))


def identity_output(grid):
    return deepcopy(grid)


def always_top_left_output(grid):
    return _render_rule(grid, lambda _obj, _h, _w, _corners: 0)


CANONICAL_GEOMETRY_RIVALS = {
    "bbox_top_left": bbox_top_left_output,
    "bbox_bottom_right": bbox_bottom_right_output,
    "occupied_centroid": occupied_centroid_output,
    "first_pixel": first_pixel_output,
    "nearest_foreground_pixel_manhattan": nearest_pixel_manhattan_output,
    "nearest_foreground_pixel_euclidean": nearest_pixel_euclidean_output,
    "ties_bottom_right": ties_bottom_right_output,
}
CANONICAL_FITTING_RIVALS = {
    name: rule for name, rule in CANONICAL_GEOMETRY_RIVALS.items()
    if name not in {"bbox_bottom_right", "ties_bottom_right"}
}


def observed(grid):
    corners, corner_objects, blobs = split_objects(grid)
    if len(corner_objects) != 4:
        raise ValueError(f"expected four corner objects, got {len(corner_objects)}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(blobs)}


def target_corner_indices(grid):
    height, width = len(grid), len(grid[0])
    return [
        _corner_index_from_flags(obj["r1"] + obj["r2"] > height - 1,
                                 obj["c1"] + obj["c2"] > width - 1)
        for obj in split_objects(grid)[2]
    ]


def max_blob_size(grid):
    return max(len(obj["cells"]) for obj in split_objects(grid)[2])


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    program = None
    for line in canonical_path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK:
            program = row["program_solution"]
            break
    if not program:
        raise ValueError("canonical program is absent")
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
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
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    counts = Counter()
    bands = {}
    sample_grids = []
    canonical = canonical_pairs()
    canonical_self_check = [module.self_check(pair["input"]) for pair in canonical]
    canonical_matches = sum(bbox_center_output(pair["input"]) == pair["output"] for pair in canonical)
    shortcut_fit = {
        name: sum(rule(pair["input"]) == pair["output"] for pair in canonical)
        for name, rule in CANONICAL_GEOMETRY_RIVALS.items()
    }
    for band in (None, "easy", "medium", "hard"):
        local = Counter()
        shapes, inputs, palettes, targets = set(), set(), set(), set()
        for index in range(count):
            seed, sample_index = 4001 + index, index * 13 + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            local["samples"] += 1
            local["self_check_errors"] += bool(module.self_check(grid))
            local["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            intended = bbox_center_output(grid)
            local["changed"] += intended != grid
            for name, rival in CANONICAL_GEOMETRY_RIVALS.items():
                local[f"refutes_{name}"] += rival(grid) != intended
            shapes.add((len(grid), len(grid[0])))
            palettes.add(len({cell for row in grid for cell in row}))
            targets.update(target_corner_indices(grid))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if len(sample_grids) < 24:
                sample_grids.append(grid)
        local.update(distinct_shapes=len(shapes), distinct_inputs=len(inputs),
                     distinct_palettes=len(palettes), target_corner_bins=len(targets))
        bands[str(band)] = dict(local)
        counts.update(local)
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "task_id": TASK,
        "version": module.VERSION,
        "canonical_matches": canonical_matches,
        "canonical_pair_count": len(canonical),
        "canonical_self_check": canonical_self_check,
        "canonical_shortcut_fit_counts": shortcut_fit,
        "counts": dict(counts),
        "by_band": bands,
        "warning": "Python geometry is supplementary evidence; --racket binds sampled labels to canonical Racket.",
    }, [pair["input"] for pair in canonical] + sample_grids


def main():
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
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    failed = (report["canonical_matches"] != report["canonical_pair_count"]
              or any(report["canonical_self_check"])
              or report["counts"].get("self_check_errors", 0)
              or report["counts"].get("nondeterministic", 0))
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [index for index, (grid, output) in enumerate(zip(grids, outputs))
                          if bbox_center_output(grid) != output]
            report["racket"] = {"status": "passed" if not mismatches else "failed",
                                "checked": len(outputs), "mismatches": mismatches}
            failed = failed or bool(mismatches)
        except Exception as exc:
            report["racket"] = {"status": "unavailable_or_failed", "checked": 0,
                                "error": f"{type(exc).__name__}: {exc}"}
            failed = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"version": report["version"], "canonical_matches": report["canonical_matches"],
                      "counts": report["counts"], "racket": report["racket"]}, indent=2))
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
