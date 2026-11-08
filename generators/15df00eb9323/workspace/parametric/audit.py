"""Reusable bounded self-audit for the native 15df00eb9323 family.

Run from the library root:

    python3 generators/15df00eb9323/workspace/parametric/audit.py \
        --seeds 40 --out generators/15df00eb9323/workspace/parametric/evidence/current/audit-summary.json

The audit independently reconstructs normalized components and support counts;
checks matched inputs, determinism, count boundaries, demo-only rule
identifiability, all three support levels, oracle parity, and the 30x30 stress
query; and reports bounded semantic-rival survival.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "15df00eb9323"
_HOME = Path(__file__).resolve().parent
_ADAPTER_PATH = _HOME / "adapter.py"


def _load_adapter():
    name = "_audit_adapter_15df00eb9323"
    spec = importlib.util.spec_from_file_location(name, _ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adapter: {_ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _validate_grid(grid) -> None:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise AssertionError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise AssertionError("grid must be rectangular within 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise AssertionError("grid cells must be exact ARC color integers")


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        result.append(frozenset((r - top, c - left) for r, c in cells))
    return result


def _support(grid):
    shapes = _components(grid)
    if len(shapes) != 3:
        raise AssertionError(f"expected exactly three source components, found {len(shapes)}")
    counts: dict[tuple[int, int], int] = {}
    for shape in shapes:
        for cell in shape:
            counts[cell] = counts.get(cell, 0) + 1
    return counts


def _crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        raise AssertionError("candidate overlay is empty")
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _predict(grid, rule: str):
    counts = _support(grid)
    height = max(r for r, _ in counts) + 1
    width = max(c for _, c in counts) + 1
    if rule == "union":
        predicate = lambda value: value >= 1
    elif rule == "majority":
        predicate = lambda value: value >= 2
    elif rule == "unanimous":
        predicate = lambda value: value >= 3
    elif rule == "exactly_two":
        predicate = lambda value: value == 2
    else:
        raise ValueError(rule)
    return _crop([
        [8 if predicate(counts.get((r, c), 0)) else 0 for c in range(width)]
        for r in range(height)
    ])


def _visible_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _occupied_span(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return max(r for r, _ in cells) - min(r for r, _ in cells), max(c for _, c in cells) - min(c for _, c in cells)


def run_audit(*, seed_count: int = 40, demo_counts=(2, 6)) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 1000:
        raise ValueError("seed_count must be an exact integer in 1..1000")
    if (not isinstance(demo_counts, (tuple, list)) or not demo_counts
            or any(type(value) is not int or not 2 <= value <= 6 for value in demo_counts)):
        raise ValueError("demo_counts must contain exact integers in 2..6")
    demo_counts = tuple(dict.fromkeys(demo_counts))
    adapter = _load_adapter()
    declared = ("majority", "unanimous")
    named_rivals = ("union", "exactly_two")
    declared_survivors = {level: set(declared) for level in declared}
    rival_episode_survivals = {level: {name: 0 for name in named_rivals} for level in declared}
    episode_count = pair_count = stress_count = 0

    for seed in range(seed_count):
        for demos in demo_counts:
            episodes = {
                level: adapter.generate(seed, {"consensus_level": level}, demos, 4)
                for level in declared
            }
            if _visible_inputs(episodes["majority"]) != _visible_inputs(episodes["unanimous"]):
                raise AssertionError(f"setting leaked into inputs for seed={seed}, demos={demos}")
            if adapter.generate(seed, {"consensus_level": "majority"}, demos, 4) != episodes["majority"]:
                raise AssertionError(f"nondeterministic episode for seed={seed}, demos={demos}")
            inputs = _visible_inputs(episodes["majority"])
            if len({_digest(grid) for grid in inputs}) != len(inputs):
                raise AssertionError(f"duplicate visible input for seed={seed}, demos={demos}")
            for grid in inputs:
                _validate_grid(grid)
                if set(_support(grid).values()) != {1, 2, 3}:
                    raise AssertionError("input lost one of the identifying support levels")
            for level, episode in episodes.items():
                episode_count += 1
                for pair in [*episode["train"], *episode["test"]]:
                    pair_count += 1
                    _validate_grid(pair["output"])
                    if pair["output"] != _predict(pair["input"], level):
                        raise AssertionError(f"oracle mismatch for {level}, seed={seed}, demos={demos}")
                surviving_declared = {
                    candidate for candidate in declared
                    if all(pair["output"] == _predict(pair["input"], candidate) for pair in episode["train"])
                }
                declared_survivors[level] &= surviving_declared
                for rival in named_rivals:
                    if all(pair["output"] == _predict(pair["input"], rival) for pair in episode["train"]):
                        rival_episode_survivals[level][rival] += 1
                stress = next(pair["input"] for pair in episode["test"] if (len(pair["input"]), len(pair["input"][0])) == (30, 30))
                if sum(value != 0 for row in stress for value in row) < 120 or min(_occupied_span(stress)) < 24:
                    raise AssertionError("30x30 stress profile lost substantive coverage")
                if sum(value != 0 for row in _predict(stress, "majority") for value in row) < 20:
                    raise AssertionError("30x30 majority intermediate became too small")
                stress_count += 1
            if any(
                left["output"] == right["output"]
                for left, right in zip(episodes["majority"]["train"], episodes["unanimous"]["train"])
            ):
                raise AssertionError("a demonstration failed to distinguish consensus levels")

    final_survivors = {level: sorted(values) for level, values in declared_survivors.items()}
    expected = {"majority": ["majority"], "unanimous": ["unanimous"]}
    if final_survivors != expected:
        raise AssertionError(f"declared programs not identified: {final_survivors}")
    if any(count for per_level in rival_episode_survivals.values() for count in per_level.values()):
        raise AssertionError(f"named semantic rival survived a lesson: {rival_episode_survivals}")
    return {
        "schema": "arcpuzzles-task-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "bounded": {
            "seed_start": 0,
            "seed_count": seed_count,
            "demo_counts": list(demo_counts),
            "settings": list(declared),
            "queries": 4,
        },
        "checks": {
            "episodes": episode_count,
            "pairs": pair_count,
            "stress_queries": stress_count,
            "setting_independent_inputs": True,
            "deterministic_replay": True,
            "all_visible_inputs_distinct_within_episode": True,
            "support_levels_present": [1, 2, 3],
            "independent_oracle_parity": True,
            "every_demo_distinguishes_declared_levels": True,
            "declared_program_survivors": final_survivors,
            "named_rival_episode_survivals": rival_episode_survivals,
            "thirty_by_thirty_substantive": True,
        },
        "limitations": (
            "Finite deterministic audit over the stated seeds and demo boundaries. "
            "Protected-Racket qualification and owner review remain separate."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=40)
    parser.add_argument("--demos", type=int, nargs="+", default=[2, 6])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_audit(seed_count=args.seeds, demo_counts=tuple(args.demos))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(payload)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(json.dumps({"status": report["status"], "out": str(args.out), "episodes": report["checks"]["episodes"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
