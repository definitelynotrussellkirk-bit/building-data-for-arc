#!/usr/bin/env python3
"""Rebuild the fd2ddef14b82 ignored-control and shortcut audit evidence."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
PACKET = HERE.parents[3]
REPO = PACKET / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

TASK = "fd2ddef14b82"
GENERATOR_PATH = REPO / "generators" / TASK / "generator.py"
SEED = 456
SAMPLE_INDEX = 7
DIFFICULTY = "hard"
REQUEST_A = {
    "n_doors": 0,
    "n_walls": 0,
    "use_key": 0,
    "palette_kind": "default",
    "palette_size": 2,
    "n_distinct_colors": 2,
}
REQUEST_B = {
    "n_doors": 3,
    "n_walls": 18,
    "use_key": 1,
    "palette_kind": "warm",
    "palette_size": 5,
    "n_distinct_colors": 5,
}


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_fd2ddef14b82", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ordinary_bfs_doors_always_blocked(grid):
    """Rival: ordinary UDLR BFS; walls and doors are always blocked."""
    height, width = len(grid), len(grid[0])
    start = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    goal = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    queue = deque([start])
    previous = {start: None}
    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + drow, col + dcol)
            rr, cc = nxt
            if not (0 <= rr < height and 0 <= cc < width):
                continue
            if nxt in previous or grid[rr][cc] in (5, 7):
                continue
            previous[nxt] = (row, col)
            queue.append(nxt)
    if goal not in previous:
        return [list(row) for row in grid]
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = previous[current]
    output = [list(row) for row in grid]
    for row, col in reversed(path):
        if output[row][col] == 0:
            output[row][col] = 4
    return output


def main() -> int:
    generator = load_generator()
    first = generator.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **REQUEST_A)
    second = generator.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **REQUEST_B)
    racket_path = HERE.with_name("racket.json")
    if not racket_path.is_file():
        raise FileNotFoundError("run the supported arcpuzzles apply command first")
    racket = json.loads(racket_path.read_text())
    actual = racket["results"][0]["output"]
    rival = ordinary_bfs_doors_always_blocked(second)
    counts = Counter(value for row in second for value in row)
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "finding": (
            "Advertised exact controls are ignored: opposite requests emit the same lawful input. "
            "The retained case asks for 18 walls and 3 doors but contains 6 walls and no doors; "
            "therefore ordinary BFS with doors permanently blocked matches the selected key/door authority."
        ),
        "generator": {
            "path": f"repo/generators/{TASK}/generator.py",
            "sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
            "assigned_sha256": "a9d722becada2f6e60573ff813851af0eed555008d0684ca3ae68842b9b4df18",
            "version": generator.VERSION,
        },
        "rule": {
            "executed_rule_hash": racket["executed_rule_hash"],
            "rule_text_sha256": racket["rule_text_sha256"],
        },
        "generation": {
            "seed": SEED,
            "sample_index": SAMPLE_INDEX,
            "difficulty": DIFFICULTY,
            "override_request_a": REQUEST_A,
            "override_request_b": REQUEST_B,
            "byte_identical": first == second,
            "self_check": generator.self_check(second),
        },
        "observed": {
            "height": len(second),
            "width": len(second[0]),
            "counts": {str(key): value for key, value in sorted(counts.items())},
            "n_walls": counts[5],
            "use_key": int(counts[6] > 0),
            "n_doors": counts[7],
            "nonzero_colors": sorted(key for key in counts if key),
        },
        "input": second,
        "actual_racket_output": actual,
        "rival": {
            "name": "ordinary_bfs_doors_always_blocked",
            "output": rival,
            "matches_actual": rival == actual,
        },
        "commands": [
            {
                "cwd": "repo",
                "argv": [
                    "python3", "../run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                    TASK, "--input", f"../checks/audit/{TASK}/input.json", "--out",
                    f"../checks/audit/{TASK}/racket.json",
                ],
            },
            {
                "cwd": "packet_root",
                "argv": ["python3", f"checks/audit/{TASK}/build_reproducer.py"],
            },
        ],
        "domain_statement": (
            "The input is emitted by the documented hard-band production sampler and passes self_check. "
            "Request B asks for 18 walls and 3 doors; the observed grid has 6 walls and 0 doors."
        ),
    }
    HERE.with_name("control-and-shortcut-reproducer.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "byte_identical": first == second,
        "self_check": report["generation"]["self_check"],
        "observed": report["observed"],
        "rival_matches_actual": report["rival"]["matches_actual"],
    }, indent=2, sort_keys=True))
    return 0 if first == second and not report["generation"]["self_check"] and rival == actual else 1


if __name__ == "__main__":
    raise SystemExit(main())
