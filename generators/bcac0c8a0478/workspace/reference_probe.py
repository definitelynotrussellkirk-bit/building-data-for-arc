"""Independent path oracle and repeatable audit for bcac0c8a0478.

The Python solver here is test tooling, not label authority.  ``racket_outputs``
executes the selected canonical Racket rule and never silently falls back.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "bcac0c8a0478"
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError("canonical task is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _portal_destination(grid, position, *, enabled=True):
    if not enabled:
        return position
    r, c = position
    value = grid[r][c]
    if value not in (6, 7):
        return position
    hits = positions(grid, value)
    if len(hits) != 2:
        return position
    return hits[1] if position == hits[0] else hits[0]


def _position_path(grid, start, goal, *, portals=True):
    """Racket-order BFS between two positions, with immediate portal travel."""
    h, w = len(grid), len(grid[0])
    queue = deque([start])
    previous = {start: None}
    end = None
    while queue and end is None:
        current = queue.popleft()
        if current == goal:
            end = current
            break
        r, c = current
        for dr, dc in CARDINALS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            dest = _portal_destination(grid, (nr, nc), enabled=portals)
            if dest not in previous:
                previous[dest] = current
                queue.append(dest)
    if end is None:
        return None
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


def _state_path(grid, *, portals=True):
    """Exact selected-rule BFS state: (row, col, checkpoint-seen)."""
    starts, goals, checkpoints = positions(grid, 2), positions(grid, 3), positions(grid, 5)
    if not (len(starts) == len(goals) == len(checkpoints) == 1):
        return None
    start, goal, checkpoint = starts[0], goals[0], checkpoints[0]
    initial = (start[0], start[1], 0)
    queue = deque([initial])
    previous = {initial: None}
    end = None
    h, w = len(grid), len(grid[0])
    while queue and end is None:
        current = queue.popleft()
        r, c, hit = current
        if (r, c) == goal and hit == 1:
            end = current
            break
        for dr, dc in CARDINALS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            hit0 = int(hit == 1 or (nr, nc) == checkpoint)
            dest = _portal_destination(grid, (nr, nc), enabled=portals)
            hit2 = int(hit0 == 1 or dest == checkpoint)
            state = (dest[0], dest[1], hit2)
            if state not in previous:
                previous[state] = current
                queue.append(state)
    if end is None:
        return None
    path = []
    current = end
    while current is not None:
        path.append((current[0], current[1]))
        current = previous[current]
    path.reverse()
    return path


def _paint(grid, path):
    if path is None:
        return deepcopy(grid)
    out = deepcopy(grid)
    for r, c in path:
        if out[r][c] == 0:
            out[r][c] = 4
    return out


def intended_output(grid):
    return _paint(grid, _state_path(grid, portals=True))


def ignore_portals_output(grid):
    return _paint(grid, _state_path(grid, portals=False))


def direct_to_goal_output(grid):
    starts, goals = positions(grid, 2), positions(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return deepcopy(grid)
    return _paint(grid, _position_path(grid, starts[0], goals[0], portals=True))


def goal_first_output(grid):
    """Plausible canonical-fitting rival: route 2→3, then 3→5."""
    starts, goals, checkpoints = positions(grid, 2), positions(grid, 3), positions(grid, 5)
    if not (len(starts) == len(goals) == len(checkpoints) == 1):
        return deepcopy(grid)
    first = _position_path(grid, starts[0], goals[0], portals=True)
    second = _position_path(grid, goals[0], checkpoints[0], portals=True)
    if first is None or second is None:
        return deepcopy(grid)
    return _paint(_paint(grid, first), second)


def used_portal_colors(grid):
    path = _state_path(grid, portals=True) or []
    return {grid[r][c] for r, c in path if grid[r][c] in (6, 7)}


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "use_portal_6": int(len(positions(grid, 6)) == 2),
        "use_portal_7": int(len(positions(grid, 7)) == 2),
    }


def profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


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
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request["grids"]]
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


def audit(module, count):
    canonical_rows = canonical_pairs()
    counters = Counter()
    per_band = {}
    samples = []
    canonical_profiles = {profile(pair["input"]) for pair in canonical_rows}
    for band in ("easy", "medium", "hard"):
        stats = Counter()
        profiles = Counter()
        unique = set()
        for index in range(count):
            seed = 120_000 + index * 37
            grid = module.generate(seed, index * 11 + 5, difficulty=band)
            stats["samples"] += 1
            stats["self_check_errors"] += bool(module.self_check(grid))
            stats["nondeterministic"] += grid != module.generate(
                seed, index * 11 + 5, difficulty=band
            )
            stats["goal_first_counterexamples"] += (
                intended_output(grid) != goal_first_output(grid)
            )
            stats["direct_counterexamples"] += (
                intended_output(grid) != direct_to_goal_output(grid)
            )
            stats["ignore_portal_counterexamples"] += (
                intended_output(grid) != ignore_portals_output(grid)
            )
            stats["exact_canonical_profiles"] += profile(grid) in canonical_profiles
            profiles[profile(grid)] += 1
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if len(samples) < 24:
                samples.append(grid)
        stats["distinct_inputs"] = len(unique)
        per_band[band] = {**stats, "profiles": {str(k): v for k, v in profiles.items()}}
        counters.update(stats)
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "generator_sha256": hashlib.sha256(
            Path(module.__file__).read_bytes()
        ).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical": {
            "pairs": len(canonical_rows),
            "intended_matches": sum(
                intended_output(pair["input"]) == pair["output"] for pair in canonical_rows
            ),
            "goal_first_matches": sum(
                goal_first_output(pair["input"]) == pair["output"] for pair in canonical_rows
            ),
        },
        "counts": dict(counters),
        "per_band": per_band,
        "sampling_design": (
            "Deterministic independent seed/index schedule crossed with all three "
            "difficulty bands; Python oracle is supplementary, not label authority."
        ),
    }
    return report, [pair["input"] for pair in canonical_rows] + samples


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
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["counts"].get("self_check_errors", 0)
        or report["counts"].get("nondeterministic", 0)
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(grids, outputs))
                if intended_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # reported loudly; never treated as parity
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"canonical": report["canonical"], "counts": report["counts"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
