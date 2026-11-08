#!/usr/bin/env python3
"""Deterministic task-local verifier for generator 351de765e33f.

This intentionally avoids the packet battery internals so a future reviewer can
replay the semantic checks with only the repository checkout and Python.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import sys
import json
from collections import Counter, defaultdict
from pathlib import Path

TASK_ID = "351de765e33f"
EXPECTED_RULE_HASH = "f074243a0544"
CANONICAL_INPUTS = [
    [
        [0,0,0,0,0,0,0,0,0],
        [0,2,2,0,0,0,0,0,0],
        [0,2,2,0,0,0,3,3,0],
        [0,0,0,0,0,0,3,3,0],
        [0,0,0,0,4,4,4,0,0],
        [0,0,0,0,4,4,4,0,0],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
    ],
    [
        [0,0,0,0,0,0,0,0,0],
        [0,1,1,1,0,0,0,0,0],
        [0,1,1,1,0,0,0,0,0],
        [0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,2,2,0,0,0],
        [0,0,0,0,2,2,0,0,0],
        [0,0,0,0,0,0,3,3,0],
    ],
    [
        [0,0,0,0,0,0,0,0,0,0],
        [0,2,2,2,0,0,0,0,0,0],
        [0,2,2,2,0,0,0,0,0,0],
        [0,0,0,0,0,0,3,3,0,0],
        [0,0,0,0,0,0,3,3,0,0],
        [0,0,0,0,4,4,4,4,0,0],
        [0,0,0,0,4,4,4,4,0,0],
        [0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0],
    ],
]
_DIR4 = ((-1,0),(1,0),(0,-1),(0,1))


def _independent_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                here = stack.pop()
                cells.append(here)
                for dr, dc in _DIR4:
                    nxt = (here[0] + dr, here[1] + dc)
                    if (
                        0 <= nxt[0] < h and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            objects.append((len(cells), min(r for r, _ in cells), min(c for _, c in cells), tuple(cells)))
    return sorted(objects, key=lambda obj: (-obj[0], obj[1], obj[2]))


def independent_rule(grid):
    objects = _independent_components(grid)
    out = [row[:] for row in grid]
    if not objects:
        return out
    target = objects[1] if len(objects) >= 2 else objects[0]
    for row, col in target[3]:
        out[row][col] = 8
    return out


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator(repo: Path):
    """Load the selected source without requiring packet runtime staging."""
    runtime = repo / "shared" / "runtime"
    for entry in (repo, runtime):
        if entry.exists() and str(entry) not in sys.path:
            sys.path.insert(0, str(entry))
    source_path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"arcpuzzles_repair_{TASK_ID}", source_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator source: {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(repo: Path) -> dict:
    generator = _load_generator(repo)
    source_path = repo / "generators" / TASK_ID / "generator.py"
    failures = []
    checks = []

    def require(condition, label, detail=None):
        if not condition:
            failures.append({"check": label, "detail": detail})
        else:
            checks.append(label)

    require(generator.RULE_HASH == EXPECTED_RULE_HASH, "canonical-rule-hash")
    require(generator.VERSION == "3.1.0", "generator-version")
    require(generator.LESSON_SCHEDULE_PERIOD == 8, "declared-schedule-period")
    require(generator.strict_canonical_like is generator.self_check, "strict-canonical-hook")
    require(
        set(generator.CANONICAL_SHORTCUTS)
        == {"second_largest_distinct_size", "colorblind_4_connected"},
        "canonical-shortcut-declarations",
    )
    require(
        all(generator.self_check(grid) == [] for grid in CANONICAL_INPUTS),
        "canonical-input-acceptance",
        [generator.self_check(grid) for grid in CANONICAL_INPUTS],
    )
    intended = [independent_rule(grid) for grid in CANONICAL_INPUTS]
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        require(
            [rival(grid) for grid in CANONICAL_INPUTS] == intended,
            f"canonical-shortcut-fits:{name}",
        )

    invalid_calls = [
        ("difficulty-float", lambda: generator.generate(0, 0, difficulty=1.0)),
        ("difficulty-bool", lambda: generator.generate(0, 0, difficulty=True)),
        ("difficulty-string", lambda: generator.generate(0, 0, difficulty="bogus")),
        ("seed-bool", lambda: generator.generate(True, 0)),
        ("seed-negative", lambda: generator.generate(-1, 0)),
        ("index-bool", lambda: generator.generate(0, True)),
        ("index-negative", lambda: generator.generate(0, -1)),
        ("profile-type", lambda: generator.generate(0, 0, scene_profile=7)),
        ("profile-value", lambda: generator.generate(0, 0, scene_profile="bogus")),
    ]
    for name, call in invalid_calls:
        try:
            call()
        except (TypeError, ValueError):
            checks.append(f"strict-call:{name}")
        else:
            failures.append({"check": f"strict-call:{name}", "detail": "accepted"})

    counts = defaultdict(Counter)
    hashes = set()
    independent_parity = 0
    draws = 0
    for difficulty in (None, "easy", "medium", "hard"):
        band = "all" if difficulty is None else difficulty
        for seed in range(64):
            for sample_index in range(16):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                draws += 1
                errors = generator.self_check(grid)
                require(not errors, "generated-self-check", (band, seed, sample_index, errors))
                signature = generator.semantic_signature(grid)
                counts[band][signature["scene_profile"]] += 1
                counts[band][signature["contact_kind"]] += 1
                hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
                require(
                    generator.rule_mirror(grid) == independent_rule(grid),
                    "independent-oracle-parity",
                    (band, seed, sample_index),
                )
                independent_parity += 1
                if seed < 4:
                    replay = generator.generate(seed, sample_index, difficulty=difficulty)
                    require(replay == grid, "deterministic-replay")
                    require(
                        replay is not grid and all(a is not b for a, b in zip(replay, grid)),
                        "fresh-return",
                    )
        for seed in range(8):
            grids = [generator.generate(seed, index, difficulty=difficulty) for index in range(16)]
            for start in range(8):
                demos = grids[start:start+5]
                require(
                    any(generator.rule_mirror(grid) != generator._second_largest_distinct_size(grid) for grid in demos),
                    "five-window-distinct-size-witness",
                    (band, seed, start),
                )
                require(
                    any(generator.rule_mirror(grid) != generator._colorblind_4_connected(grid) for grid in demos),
                    "five-window-colorblind4-witness",
                    (band, seed, start),
                )
                require(
                    any(generator.rule_mirror(grid) != generator._colorblind_8_connected(grid) for grid in demos),
                    "five-window-colorblind8-witness",
                    (band, seed, start),
                )

    for difficulty in (None, "easy", "medium", "hard"):
        for profile in generator.SCENE_PROFILES:
            for seed in range(16):
                grid = generator.generate(
                    seed,
                    seed % generator.LESSON_SCHEDULE_PERIOD,
                    difficulty=difficulty,
                    scene_profile=profile,
                )
                require(
                    generator.observe_overrides(grid) == {"scene_profile": profile},
                    "override-observability",
                    (difficulty, profile, seed),
                )
                require(generator.self_check(grid) == [], "override-self-check")

    sample = generator.generate(777, 0, difficulty="hard")
    frozen = copy.deepcopy(sample)
    for name, rival in generator.LESSON_COMPETITORS.items():
        first = rival(sample)
        second = rival(sample)
        require(first == second, f"rival-determinism:{name}")
        require(sample == frozen, f"rival-input-purity:{name}")
        require(
            first is not second and all(a is not b for a, b in zip(first, second)),
            f"rival-freshness:{name}",
        )

    prototype_receipt_path = repo / "generators" / TASK_ID / "workspace" / "parametric" / "evidence" / "receipt.json"
    prototype_receipt = json.loads(prototype_receipt_path.read_text())
    require(prototype_receipt["status"] == "complete", "parametric-materialization")
    require(
        prototype_receipt["canonical_rank_two_rule_hash"] == EXPECTED_RULE_HASH,
        "parametric-canonical-rule-hash",
    )
    require(
        prototype_receipt["differing_pair_indexes"] == [0,1,2,3],
        "parametric-settings-differ",
    )

    return {
        "status": "PASS" if not failures else "FAIL",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "source_sha256": _sha(source_path),
        "draws_checked": draws,
        "unique_inputs": len(hashes),
        "independent_oracle_parity_cases": independent_parity,
        "profile_and_topology_counts": {band: dict(counter) for band, counter in counts.items()},
        "passed_assertions": len(checks),
        "failures": failures[:50],
        "racket_execution": prototype_receipt["verification"]["racket_execution_performed"],
        "racket_note": prototype_receipt["verification"]["racket_execution_note"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    receipt = verify(args.repo.resolve())
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    print(text, end="")
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
