"""Independent probes for ad9405621c3d.

This module deliberately does not import implementation helpers from the reviewed
module.  Its Python BFS mirrors the published neighbor order only as a test oracle;
``--racket`` additionally executes the selected repository authority and never
silently substitutes the Python result.
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
TASK = "ad9405621c3d"
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_ad9405621c3d", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical_row()
    test = row.get("test") or []
    if isinstance(test, dict):
        test = [test]
    return list(row.get("train") or []) + list(test)


def endpoints(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                by_color.setdefault(value, []).append((r, c))
    matches = [(color, cells) for color, cells in by_color.items() if len(cells) == 2]
    if len(matches) != 1 or len(by_color) != 1:
        raise ValueError("expected exactly one non-{0,5} color appearing twice")
    return matches[0][0], matches[0][1][0], matches[0][1][1]


def shortest_path(grid, start, goal, *, outer_ring_depth=None):
    """Independent U,D,L,R BFS through zeros or the goal."""
    h, w = len(grid), len(grid[0])
    parent = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for dr, dc in DIRS:
            nr, nc = current[0] + dr, current[1] + dc
            nxt = (nr, nc)
            if not (0 <= nr < h and 0 <= nc < w) or nxt in parent:
                continue
            if outer_ring_depth is not None and nxt not in (start, goal):
                depth = min(nr, h - 1 - nr, nc, w - 1 - nc)
                if depth > outer_ring_depth:
                    continue
            if nxt != goal and grid[nr][nc] != 0:
                continue
            parent[nxt] = current
            queue.append(nxt)
    if goal not in parent:
        return []
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return path[::-1]


def independent_output(grid):
    color, start, goal = endpoints(grid)
    path = shortest_path(grid, start, goal)
    if not path:
        raise ValueError("endpoints are disconnected")
    output = deepcopy(grid)
    for r, c in path:
        output[r][c] = color
    return output


def outer_two_ring_output(grid):
    """Plausible wrong rule: solve only in cells at boundary depth <= 1."""
    color, start, goal = endpoints(grid)
    path = shortest_path(grid, start, goal, outer_ring_depth=1)
    output = deepcopy(grid)
    for r, c in path:
        output[r][c] = color
    return output


def path_features(grid):
    _color, start, goal = endpoints(grid)
    path = shortest_path(grid, start, goal)
    h, w = len(grid), len(grid[0])
    return {
        "grid_h": h,
        "grid_w": w,
        "endpoint_color": grid[start[0]][start[1]],
        "path_length": len(path),
        "max_boundary_depth": max(
            min(r, h - 1 - r, c, w - 1 - c) for r, c in path
        ),
        "outer_two_ring_agrees": outer_two_ring_output(grid) == independent_output(grid),
    }


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
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
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])


def audit(module, per_band):
    report = {
        "schema": "ad9405621c3d-independent-audit-v1",
        "task_id": TASK,
        "version": module.VERSION,
        "sampling_design": (
            "Disjoint seeds by band; sample_index=17*i+band_offset. "
            "Counts describe this finite sampler, not universal induction."
        ),
        "canonical": {
            "pairs": len(canonical_pairs()),
            "python_matches": sum(
                independent_output(pair["input"]) == pair["output"]
                for pair in canonical_pairs()
            ),
            "outer_two_ring_matches": sum(
                outer_two_ring_output(pair["input"]) == pair["output"]
                for pair in canonical_pairs()
            ),
            "self_check_rejections": [
                module.self_check(pair["input"]) for pair in canonical_pairs()
            ],
        },
        "bands": {},
    }
    all_grids = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        profiles = Counter()
        unique = set()
        for i in range(per_band):
            seed = 100_000 * (band_index + 1) + i
            sample_index = i * 17 + band_index
            grid = module.generate(seed, sample_index, difficulty=band)
            all_grids.append(grid)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(
                seed, sample_index, difficulty=band
            )
            expected = independent_output(grid)
            counts["non_identity"] += expected != grid
            counts["outer_two_ring_disagreements"] += (
                outer_two_ring_output(grid) != expected
            )
            feature = path_features(grid)
            profiles[module.schedule_profile(seed, sample_index, difficulty=band)] += 1
            counts["deep_route"] += feature["max_boundary_depth"] >= 2
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        counts["distinct_inputs"] = len(unique)
        report["bands"][band] = dict(counts, schedule_profiles=dict(profiles))
    return report, all_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    code = int(
        report["canonical"]["python_matches"] != report["canonical"]["pairs"]
        or any(report["canonical"]["self_check_rejections"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["bands"].values())
    )
    if args.racket:
        selected = [pair["input"] for pair in canonical_pairs()] + grids[:64]
        outputs = racket_outputs(selected)
        mismatches = [
            index for index, (grid, output) in enumerate(zip(selected, outputs))
            if independent_output(grid) != output
        ]
        report["racket"] = {
            "status": "passed" if not mismatches else "failed",
            "checked": len(outputs),
            "mismatches": mismatches,
        }
        code = max(code, int(bool(mismatches)))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
