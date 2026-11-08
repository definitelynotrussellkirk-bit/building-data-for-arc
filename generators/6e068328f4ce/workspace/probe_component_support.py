"""Independent component-center support probe for a library or copied runtime.

Run with the local runtime on PYTHONPATH and an explicit fresh --out JSON path.
Only public generator behavior is inspected; no reference labels are loaded.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

from reviewer_support import find_root
from puzzle_generators.base import set_ctx_observer

TASK_ID = "6e068328f4ce"
BOUNDARIES = ((7, 7), (7, 16), (16, 7), (8, 8), (16, 16))
SUPPORTED_RIVALS = frozenset(("per_color", "eight_connected", "ceil_midpoint",
                            "floor_centroid", "rounded_centroid", "existing_cells_only"))


def components(grid, diagonal=False):
    """Independent same-color BFS, without generator or grid helper calls."""
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diagonal:
        steps += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                x, y = queue.popleft()
                cells.append((x, y))
                for dx, dy in steps:
                    point = x + dx, y + dy
                    if (0 <= point[0] < len(grid) and 0 <= point[1] < len(row)
                            and point not in seen and grid[point[0]][point[1]] == color):
                        queue.append(point)
                        seen.add(point)
            result.append((color, cells))
    return result


def render(grid, mode="bbox"):
    if mode != "bbox" and mode not in SUPPORTED_RIVALS:
        raise ValueError(f"unsupported independent rival: {mode!r}")
    groups = components(grid, diagonal=mode == "eight_connected")
    if mode == "per_color":
        merged = defaultdict(list)
        for color, cells in groups:
            merged[color].extend(cells)
        groups = list(merged.items())
    output = [[0] * len(grid[0]) for _ in grid]
    for color, cells in groups:
        rs, cs = zip(*cells)
        r, c = (min(rs) + max(rs)) // 2, (min(cs) + max(cs)) // 2
        if mode == "ceil_midpoint":
            r, c = (min(rs) + max(rs) + 1) // 2, (min(cs) + max(cs) + 1) // 2
        elif mode == "floor_centroid":
            r, c = sum(rs) // len(rs), sum(cs) // len(cs)
        elif mode == "rounded_centroid":
            r, c = round(sum(rs) / len(rs)), round(sum(cs) / len(cs))
        if mode != "existing_cells_only" or (r, c) in cells:
            output[r][c] = color
    return output


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def inspect_grid(generator, grid, controls=None):
    require(bool(grid) and bool(grid[0]), "empty grid")
    require(all(len(row) == len(grid[0]) for row in grid), "ragged grid")
    require(all(type(v) is int and 0 <= v <= 9 for row in grid for v in row), "invalid cells")
    groups = components(grid)
    observed = dict(grid_h=len(grid), grid_w=len(grid[0]), n_blobs=len(groups),
                    n_distinct_colors=len({color for color, _ in groups}))
    require(2 <= len(groups) <= 5, f"component count: {observed}")
    require(all(len(cells) >= 2 for _, cells in groups), "singleton component")
    if controls is not None:
        require(observed == controls, f"controls mismatch: {observed} != {controls}")
    boxes = []
    for _, cells in groups:
        rs, cs = zip(*cells)
        boxes.append((min(rs), min(cs), max(rs), max(cs)))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            overlap = (max(a[0], b[0]) <= min(a[2], b[2])
                       and max(a[1], b[1]) <= min(a[3], b[3]))
            require(not overlap, f"overlapping bboxes: {a}, {b}")
    before = copy.deepcopy(grid)
    require(generator.observe_overrides(grid) == observed, "incorrect observation hook")
    require(generator.self_check(grid) == [], "self_check rejected generated grid")
    require(generator.strict_canonical_like(grid) == [], "strict hook rejected generated grid")
    require(grid == before, "input mutated by validation/observation hooks")
    for name, rival in generator.SEMANTIC_RIVALS.items():
        require(rival(grid) == render(grid, name), f"independent rival mismatch: {name}")
        require(grid == before, f"input mutated by rival: {name}")
    for name, witness in generator.SEMANTIC_WITNESSES.items():
        witness(grid)
        require(grid == before, f"input mutated by witness: {name}")
    require(grid == before, "input mutated by validation/observation hooks")


def run(report):
    root = find_root(__file__)
    library_source = root / "generators" / TASK_ID / "generator.py"
    source = (library_source if library_source.is_file()
              else root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    report.update(generator_source=str(source),
                  generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    spec = importlib.util.spec_from_file_location("component_support_under_review", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    report["generator_version"] = generator.VERSION
    report["declared_rivals"] = sorted(generator.SEMANTIC_RIVALS)
    unknown = set(generator.SEMANTIC_RIVALS) - SUPPORTED_RIVALS
    require(not unknown, f"unimplemented declared rivals: {sorted(unknown)}")
    missing = SUPPORTED_RIVALS - set(generator.SEMANTIC_RIVALS)
    require(not missing, f"missing required component-center rivals: {sorted(missing)}")
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for height, width in BOUNDARIES:
            for count in range(2, 6):
                for colors in range(1, count + 1):
                    controls = dict(grid_h=height, grid_w=width,
                                    n_blobs=count, n_distinct_colors=colors)
                    for seed in range(16):
                        for index in (0, 1):
                            report["active_case"] = dict(seed=seed, sample_index=index, overrides=controls)
                            contexts.clear()
                            grid = generator.generate(seed, index, **controls)
                            inspect_grid(generator, grid, controls)
                            require(len(contexts) == 1, "expected one generator context")
                            context = contexts[0]
                            require(context.overrides_used() == controls, "override consumption mismatch")
                            require(all(context.axis_value(k) == v for k, v in controls.items()),
                                    "keyed provenance values mismatch")
                            report["control_cases"] += 1
                            report["input_mutation_cases"] += 1
        for difficulty in (None, "easy", "medium", "hard"):
            for seed in range(16):
                report["active_case"] = dict(seed=seed, sample_index=1, difficulty=difficulty)
                contexts.clear()
                grid = generator.generate(seed, 1, difficulty=difficulty)
                inspect_grid(generator, grid)
                expected = render(grid)
                for name in generator.SEMANTIC_RIVALS:
                    require(expected != render(grid, name), f"default rich rival survived: {name}")
                report["default_rich_cases"] += 1
        report.pop("active_case", None)
    finally:
        set_ctx_observer(None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="fresh JSON report path")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Reserve output before running: never overwrite an earlier source-bound result.
    with args.out.open("x", encoding="utf-8") as handle:
        report = dict(status="running", command=[sys.executable, *sys.argv],
                      boundaries=BOUNDARIES, seeds=16, parities=[0, 1], control_cases=0,
                      input_mutation_cases=0, default_rich_cases=0, failures=[],
                      scope="independent geometry, controls, provenance, rivals and mutation; no labels or Racket")
        try:
            run(report)
            report["status"] = "PASS"
        except Exception as exc:
            report["status"] = "FAIL"
            report["failures"].append(dict(exception=type(exc).__name__, message=str(exc),
                                           case=report.get("active_case"), traceback=traceback.format_exc()))
        handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
