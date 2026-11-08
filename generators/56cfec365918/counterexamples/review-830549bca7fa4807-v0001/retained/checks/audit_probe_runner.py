from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))

# The review runtime mounts shared/tools as the historical ``scripts`` package.
# Recreate that namespace when this standalone probe imports rule_wrap directly.
import types
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)

from puzzle_generators import runner


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_source(task_id: str) -> str:
    with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row["program_solution"]
    raise KeyError(task_id)


def execute(task_id: str, grid):
    source = canonical_source(task_id)
    bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(source))
    try:
        output = runner._apply_rule(bridge, name, grid)
    finally:
        bridge.shutdown()
    return source, output


def rival_per_color_extremes(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for color in sorted({cell for row in grid for cell in row} - {0}):
        cells = sorted(
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == color
        )
        if cells:
            for r, c in (cells[0], cells[-1]):
                out[r][c] = color
    return out


def rival_supporting_line_intersection(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(twos) == 2 and len(threes) == 2:
        row = twos[0][0]
        col = threes[0][1]
        if 0 <= row < h and 0 <= col < w:
            out[row][col] = 8
    return out


def count_repeated_color_blocks(module):
    hits = 0
    total = 0
    for seed in range(20):
        for sample_index in range(10):
            grid = module.generate(seed, sample_index, difficulty="medium")
            total += 1
            counts = {}
            h, w = len(grid), len(grid[0])
            seen = set()
            for r in range(h):
                for c in range(w):
                    color = grid[r][c]
                    if color == 0 or (r, c) in seen:
                        continue
                    stack = [(r, c)]
                    seen.add((r, c))
                    while stack:
                        rr, cc = stack.pop()
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            p = (rr + dr, cc + dc)
                            if (
                                0 <= p[0] < h
                                and 0 <= p[1] < w
                                and p not in seen
                                and grid[p[0]][p[1]] == color
                            ):
                                seen.add(p)
                                stack.append(p)
                    counts[color] = counts.get(color, 0) + 1
            if any(value >= 2 for value in counts.values()):
                hits += 1
    return hits, total


def count_noncrossing_spans(module):
    hits = 0
    total = 0
    for seed in range(20):
        for sample_index in range(10):
            grid = module.generate(seed, sample_index, difficulty="medium")
            total += 1
            twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
            threes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
            if len(twos) != 2 or len(threes) != 2:
                continue
            row = twos[0][0]
            col = threes[0][1]
            h_contains = min(c for _, c in twos) <= col <= max(c for _, c in twos)
            v_contains = min(r for r, _ in threes) <= row <= max(r for r, _ in threes)
            if not (h_contains and v_contains):
                hits += 1
    return hits, total


def record(task_id, grid, rival_name, rival_fn, scan_name, scan_fn):
    module, generator_path = load_generator(task_id)
    source, actual = execute(task_id, grid)
    rival = rival_fn(grid)
    scan_hits, scan_total = scan_fn(module)
    return {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "target_task_id": task_id,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
        "canonical_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "input_origin": "hand-constructed adversarial probe",
        "seed": None,
        "sample_index": None,
        "overrides": {},
        "input": grid,
        "actual_racket_output": actual,
        "rival_name": rival_name,
        "rival_output": rival,
        "rival_disagrees": rival != actual,
        "validator_errors": list(module.self_check(copy.deepcopy(grid)) or []),
        "validator_accepts": not bool(module.self_check(copy.deepcopy(grid)) or []),
        "default_generator_scan": {
            "description": scan_name,
            "seed_range": "0..19",
            "sample_index_range": "0..9",
            "difficulty": "medium",
            "hits": scan_hits,
            "draws": scan_total,
        },
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit_probe_runner.py",
        ],
        "cwd": "packet_root",
    }


def main():
    same_color_blocks = [[0] * 8 for _ in range(8)]
    for r0, c0 in ((1, 1), (5, 5)):
        for r in range(r0, r0 + 2):
            for c in range(c0, c0 + 2):
                same_color_blocks[r][c] = 4

    noncrossing = [[0] * 8 for _ in range(7)]
    noncrossing[2][1] = noncrossing[2][3] = 2
    noncrossing[0][6] = noncrossing[4][6] = 3

    outputs = {
        "56cfec365918": record(
            "56cfec365918",
            same_color_blocks,
            "for each nonzero color keep only its lexicographically first and last cell",
            rival_per_color_extremes,
            "generated inputs containing two disconnected components of the same nonzero color",
            count_repeated_color_blocks,
        ),
        "a79fb4ad1f55": record(
            "a79fb4ad1f55",
            noncrossing,
            "paint the intersection of the infinite supporting row and column",
            rival_supporting_line_intersection,
            "generated inputs whose supporting lines meet outside at least one finite endpoint span",
            count_noncrossing_spans,
        ),
    }
    for task_id, payload in outputs.items():
        path = ROOT / "checks" / f"audit-{task_id}-counterexample.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(path.relative_to(ROOT), payload["rival_disagrees"], payload["validator_accepts"])


if __name__ == "__main__":
    main()
