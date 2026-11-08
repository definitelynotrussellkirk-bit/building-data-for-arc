"""Independent oracle and audit helpers for generator 807c284a7e79.

This module is reviewer/test tooling, not a replacement label authority.  The
Python mirror is deliberately independent of ``generator.py``.  ``racket_outputs``
requires and executes the repository's selected canonical Racket program; it
never silently falls back to Python.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "807c284a7e79"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_807c284a7e79", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(tests)


def _seed(grid: list[list[int]]) -> tuple[int, int]:
    hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(hits) != 1:
        raise ValueError(f"expected one seed-2, found {len(hits)}")
    return hits[0]


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Enumerate 4-connected non-wall components without generator helpers."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8 or (r, c) in seen:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(cells)
    return out


def bfs_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent implementation of the public BFS-distance parity rule."""
    h, w = len(grid), len(grid[0])
    start = _seed(grid)
    distance = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            point = (nr, nc)
            if (
                0 <= nr < h
                and 0 <= nc < w
                and grid[nr][nc] != 8
                and point not in distance
            ):
                distance[point] = distance[(r, c)] + 1
                queue.append(point)
    result = deepcopy(grid)
    for (r, c), d in distance.items():
        result[r][c] = 3 if d % 2 == 0 else 4
    return result


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover the four public generator axes from returned pixels."""
    h, w = len(grid), len(grid[0])
    walls = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 8]
    rows = {r for r, _ in walls}
    cols = {c for _, c in walls}
    if walls and len(cols) == 1:
        orientation = "vertical"
    elif walls and len(rows) == 1:
        orientation = "horizontal"
    else:
        orientation = "mixed"

    comps = components(grid)
    seed = _seed(grid)
    seed_comp = next(cells for cells in comps if seed in cells)
    if len(comps) == 1:
        profile = "connected"
    else:
        max_size = max(map(len, comps))
        profile = "split_seed_large" if len(seed_comp) == max_size else "split_seed_small"
    return {
        "grid_h": h,
        "grid_w": w,
        "scene_profile": profile,
        "wall_orientation": orientation,
    }


def shortcut_all_non_walls(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: checkerboard every non-wall cell, reachable or not."""
    sr, sc = _seed(grid)
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                result[r][c] = 3 if (abs(r - sr) + abs(c - sc)) % 2 == 0 else 4
    return result


def shortcut_largest_component(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: always fill the largest chamber rather than seed chamber."""
    sr, sc = _seed(grid)
    result = deepcopy(grid)
    largest = max(components(grid), key=len)
    for r, c in largest:
        result[r][c] = 3 if (abs(r - sr) + abs(c - sc)) % 2 == 0 else 4
    return result


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Run the selected canonical Racket program over a batch, with no fallback."""
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
            json.dumps({"program": program, "grids": grids})
        )
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict, list[list[list[int]]]]:
    counters = Counter()
    by_band: dict[str, dict] = {}
    parity_grids: list[list[list[int]]] = [pair["input"] for pair in canonical_pairs()]
    canonical_errors = [module.self_check(pair["input"]) for pair in canonical_pairs()]
    canonical_rule_matches = sum(
        bfs_output(pair["input"]) == pair["output"] for pair in canonical_pairs()
    )
    for band in ("easy", "medium", "hard"):
        row = Counter()
        shapes: set[tuple[int, int]] = set()
        inputs: set[str] = set()
        profiles = Counter()
        orientations = Counter()
        for i in range(count):
            grid = module.generate(1009 + i, i, difficulty=band)
            row["draws"] += 1
            row["self_check_errors"] += bool(module.self_check(grid))
            row["nondeterministic"] += grid != module.generate(1009 + i, i, difficulty=band)
            stats = observed(grid)
            profiles[str(stats["scene_profile"])] += 1
            orientations[str(stats["wall_orientation"])] += 1
            shapes.add((len(grid), len(grid[0])))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = bfs_output(grid)
            row["changed"] += intended != grid
            row["all_non_walls_disagreements"] += intended != shortcut_all_non_walls(grid)
            row["largest_component_disagreements"] += intended != shortcut_largest_component(grid)
            if i < 12:
                parity_grids.append(grid)
        row["distinct_shapes"] = len(shapes)
        row["distinct_inputs"] = len(inputs)
        by_band[band] = dict(row, profiles=dict(profiles), orientations=dict(orientations))
        counters.update(row)
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "canonical_rule_matches": canonical_rule_matches,
        "canonical_self_check_errors": canonical_errors,
        "counts": dict(counters),
        "by_band": by_band,
        "warning": "Python BFS is supplementary evidence; selected Racket remains label authority.",
    }, parity_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=200, help="samples per difficulty band")
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
    exit_code = int(
        report["canonical_rule_matches"] != len(canonical_pairs())
        or any(report["canonical_self_check_errors"])
        or report["counts"].get("self_check_errors", 0)
        or report["counts"].get("nondeterministic", 0)
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                i for i, (grid, output) in enumerate(zip(grids, outputs))
                if bfs_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # surfaced in the JSON and exit status
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("version", "counts", "racket")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
