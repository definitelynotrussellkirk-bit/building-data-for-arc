"""Independent oracle and distribution probe for 1407f5e6f3e5.

The Python code here is supplementary review/test tooling.  The selected Racket
program remains the label authority; ``--racket`` executes it and fails closed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "1407f5e6f3e5"
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))

try:
    from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:
    for _parent in Path(__file__).resolve().parents:
        _runtime = _parent / "shared/runtime"
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root

ROOT = Path(find_root(__file__)).resolve()


def _generator_path(path=None):
    if path is not None:
        candidate = Path(path).resolve()
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        return candidate
    for candidate in (
        ROOT / f"generators/{TASK}/generator.py",
        ROOT / f"puzzle_generators/per_puzzle/{TASK}/generator.py",
    ):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"selected generator {TASK} is absent under {ROOT}")


def load_generator(path=None):
    selected = path or os.environ.get("GENERATOR_UNDER_TEST")
    generator_path = _generator_path(selected)
    spec = importlib.util.spec_from_file_location("reviewed_generator", generator_path)
    if spec is None or spec.loader is None:
        raise ImportError(generator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def components(grid):
    """Return same-color 4-connected components in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            todo = [(r, c)]
            cells = []
            for cr, cc in todo:
                cells.append((cr, cc))
                for dr, dc in STEPS:
                    point = cr + dr, cc + dc
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        todo.append(point)
            r0 = min(x for x, _ in cells)
            c0 = min(y for _, y in cells)
            r1 = max(x for x, _ in cells)
            c1 = max(y for _, y in cells)
            result.append({"color": color, "cells": tuple(cells), "bbox": (r0, c0, r1, c1)})
    return result


def oracle_output(grid):
    """Independent component-wise bounding-box fill on a fresh zero canvas."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for obj in components(grid):
        r0, c0, r1, c1 = obj["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = obj["color"]
    return out


def global_color_bbox(grid):
    """Plausible wrong rule: merge disconnected objects that share a color."""
    h, w = len(grid), len(grid[0])
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                points[value].append((r, c))
    out = [[0 for _ in range(w)] for _ in range(h)]
    for color in sorted(points):
        cells = points[color]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def observed(grid):
    objs = components(grid)
    colors = {obj["color"] for obj in objs}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "components": len(objs),
        "repeat_color": len(objs) - len(colors),
    }


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])


def audit(module, count=240):
    report = {
        "task": TASK,
        "count_per_band": count,
        "bands": {},
        "canonical_oracle_matches": 0,
        "canonical_shortcut_matches": 0,
    }
    pairs = canonical_pairs()
    report["canonical_oracle_matches"] = sum(oracle_output(p["input"]) == p["output"] for p in pairs)
    report["canonical_shortcut_matches"] = sum(global_color_bbox(p["input"]) == p["output"] for p in pairs)
    for band in (None, "easy", "medium", "hard"):
        stats = Counter()
        shapes = set()
        colors = set()
        grids = set()
        invalid = []
        for index in range(count):
            grid = module.generate(71000 + index, index, difficulty=band)
            messages = module.self_check(deepcopy(grid), difficulty=band)
            if messages:
                invalid.append({"index": index, "messages": list(messages)})
            obs = observed(grid)
            stats[("components", obs["components"])] += 1
            stats[("repeat_color", obs["repeat_color"])] += 1
            stats[("height", obs["grid_h"])] += 1
            stats[("width", obs["grid_w"])] += 1
            stats["rival_witnesses"] += global_color_bbox(grid) != oracle_output(grid)
            stats["teaching_profile"] += module.schedule_profile(71000 + index, index, band) == "teaching"
            shapes.update(tuple(sorted((r - obj["bbox"][0], c - obj["bbox"][1]) for r, c in obj["cells"])) for obj in components(grid))
            colors.update(v for row in grid for v in row if v)
            grids.add(repr(grid))
        report["bands"][str(band)] = {
            "invalid": invalid,
            "unique_grids": len(grids),
            "unique_local_shapes": len(shapes),
            "colors": sorted(colors),
            "rival_witnesses": stats["rival_witnesses"],
            "teaching_profiles": stats["teaching_profile"],
            "component_counts": {str(k[1]): v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "components"},
            "repeat_color_counts": {str(k[1]): v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "repeat_color"},
            "heights": sorted(k[1] for k in stats if isinstance(k, tuple) and k[0] == "height"),
            "widths": sorted(k[1] for k in stats if isinstance(k, tuple) and k[0] == "width"),
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator")
    parser.add_argument("--count", type=int, default=240)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args(argv)
    module = load_generator(args.generator)
    report = audit(module, args.count)
    if args.racket:
        grids = [p["input"] for p in canonical_pairs()]
        grids += [module.generate(991, i, difficulty="hard") for i in range(24)]
        report["racket_parity"] = sum(
            a == b for a, b in zip(racket_outputs(grids), [oracle_output(g) for g in grids])
        )
        report["racket_parity_total"] = len(grids)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not any(v["invalid"] for v in report["bands"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
