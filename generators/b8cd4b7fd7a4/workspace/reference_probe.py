"""Independent geometry oracle and repeatable audit for b8cd4b7fd7a4.

This module is review/test tooling, not label authority.  The optional Racket
path executes the selected canonical program and never silently falls back to
Python.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "b8cd4b7fd7a4"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_b8cd4b7fd7a4", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK_ID, root=find_root(__file__))


def analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    points = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError(f"expected two nonzero cells, found {len(points)}")
    (r1, c1, color1), (r2, c2, color2) = points
    if color1 != color2:
        raise ValueError("endpoint colors differ")
    dr, dc = r2 - r1, c2 - c1
    if dr == 0 and dc != 0:
        orientation = "horizontal"
    elif dc == 0 and dr != 0:
        orientation = "vertical"
    elif abs(dr) == abs(dc) and dr != 0:
        orientation = "diagonal"
    else:
        raise ValueError("endpoints are not horizontal, vertical, or 45-degree aligned")
    distance = max(abs(dr), abs(dc))
    if distance < 2:
        raise ValueError("endpoints have no strict interior cell")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "orientation": orientation,
        "endpoint_color": color1,
        "points": ((r1, c1), (r2, c2)),
        "distance": distance,
    }


def _sign(value):
    return (value > 0) - (value < 0)


def intended_output(grid):
    info = analyze(grid)
    (r1, c1), (r2, c2) = info["points"]
    step_r, step_c = _sign(r2 - r1), _sign(c2 - c1)
    out = [[0 for _ in row] for row in grid]
    for offset in range(1, info["distance"]):
        out[r1 + offset * step_r][c1 + offset * step_c] = 8
    return out


def include_endpoints_rival(grid):
    info = analyze(grid)
    (r1, c1), (r2, c2) = info["points"]
    step_r, step_c = _sign(r2 - r1), _sign(c2 - c1)
    out = [[0 for _ in row] for row in grid]
    for offset in range(info["distance"] + 1):
        out[r1 + offset * step_r][c1 + offset * step_c] = 8
    return out


def axis_only_rival(grid):
    info = analyze(grid)
    if info["orientation"] == "diagonal":
        return [[0 for _ in row] for row in grid]
    return intended_output(grid)


def endpoint_color_rival(grid):
    out = intended_output(grid)
    color = analyze(grid)["endpoint_color"]
    return [[color if value == 8 else value for value in row] for row in out]


def color_three_only_rival(grid):
    if analyze(grid)["endpoint_color"] != 3:
        return [[0 for _ in row] for row in grid]
    return intended_output(grid)


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog

    catalog = Catalog(ROOT)
    receipt = catalog.apply(TASK_ID, grids, reference="canonical")
    results = receipt.get("results")
    if not isinstance(results, list) or len(results) != len(grids):
        raise RuntimeError("canonical apply returned an incomplete result set")
    outputs = []
    for index, result in enumerate(results):
        if not isinstance(result, dict) or result.get("output") is None:
            detail = result.get("error") if isinstance(result, dict) else repr(result)
            raise RuntimeError(f"canonical apply failed for input {index}: {detail}")
        outputs.append(result["output"])
    return outputs


def audit(module, count):
    bands = (None, "easy", "medium", "hard")
    report = {
        "schema": "b8cd4b7fd7a4-independent-audit-v1",
        "task_id": TASK_ID,
        "version": module.VERSION,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical": {"pairs": 0, "mismatches": []},
        "bands": {},
    }
    for index, pair in enumerate(canonical_pairs()):
        report["canonical"]["pairs"] += 1
        if intended_output(pair["input"]) != pair["output"]:
            report["canonical"]["mismatches"].append(index)
    for band in bands:
        shapes, orientations, colors, inputs = set(), set(), set(), set()
        counts = {
            "samples": 0,
            "self_check_errors": 0,
            "nondeterministic": 0,
            "strict_errors": 0,
            "include_endpoints_disagreements": 0,
            "axis_only_disagreements": 0,
            "endpoint_color_disagreements": 0,
            "color_three_only_disagreements": 0,
        }
        for index in range(count):
            seed = 1009 + index
            sample_index = index * 7 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["strict_errors"] += bool(module.strict_canonical_like(grid))
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            info = analyze(grid)
            truth = intended_output(grid)
            shapes.add((info["grid_h"], info["grid_w"]))
            orientations.add(info["orientation"])
            colors.add(info["endpoint_color"])
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            counts["include_endpoints_disagreements"] += include_endpoints_rival(grid) != truth
            counts["axis_only_disagreements"] += axis_only_rival(grid) != truth
            counts["endpoint_color_disagreements"] += endpoint_color_rival(grid) != truth
            counts["color_three_only_disagreements"] += color_three_only_rival(grid) != truth
        report["bands"][str(band)] = {
            **counts,
            "distinct_shapes": len(shapes),
            "orientations": sorted(orientations),
            "endpoint_colors": sorted(colors),
            "distinct_inputs": len(inputs),
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=256)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    report["racket"] = {"status": "not_requested", "checked": 0, "mismatches": []}
    exit_code = int(bool(report["canonical"]["mismatches"]))
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids.extend(module.generate(300 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(24))
        try:
            outputs = racket_outputs(grids)
            mismatches = [i for i, (grid, output) in enumerate(zip(grids, outputs)) if intended_output(grid) != output]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "mismatches": [],
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"canonical": report["canonical"], "bands": report["bands"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
