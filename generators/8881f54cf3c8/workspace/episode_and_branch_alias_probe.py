#!/usr/bin/env python3
"""Audit production episode scheduling and canonical operation-branch aliases.

This is task-local reviewer tooling, not a label authority.  It discovers all
single-key operation substitutions that reproduce every canonical pair, then
checks whether generated examples provide a counterexample.  It also models the
actual four-demo/one-query episode assembled by ``runner.run_batch``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "8881f54cf3c8"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator(path: Path):
    source = path.resolve()
    spec = importlib.util.spec_from_file_location(
        f"review_probe_{TASK_ID}_{hashlib.sha256(str(source).encode()).hexdigest()[:10]}",
        source,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grids_equal(left: Any, right: Any) -> bool:
    return left == right


def branch_alias(gen, key: int, replacement: int) -> Callable[[Any], list[list[int]]]:
    def solve(grid):
        if int(grid[0][0]) != key:
            return gen.rule_mirror(grid)
        return gen._apply_boolean(grid, forced_op=replacement)

    return solve


def declared_equivalents(gen, candidate, pairs, witness_grid) -> list[str]:
    names: list[str] = []
    for name, declared in sorted(getattr(gen, "CANONICAL_SHORTCUTS", {}).items()):
        try:
            canonical_same = all(
                grids_equal(
                    declared(copy.deepcopy(pair["input"])),
                    candidate(copy.deepcopy(pair["input"])),
                )
                for pair in pairs
            )
            witness_same = grids_equal(
                declared(copy.deepcopy(witness_grid)),
                candidate(copy.deepcopy(witness_grid)),
            )
        except Exception:
            continue
        if canonical_same and witness_same:
            names.append(name)
    return names


def audit(generator_path: Path, seeds: int) -> dict[str, Any]:
    gen = load_generator(generator_path)
    pairs = canonical_pairs(TASK_ID, root=find_root(HERE))
    source_bytes = generator_path.read_bytes()
    report: dict[str, Any] = {
        "schema": "arc-review-episode-branch-alias-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "generator_version": getattr(gen, "VERSION", None),
        "seed_range": [0, seeds - 1],
        "canonical_pairs": len(pairs),
        "episode_schedule": {},
        "declared_canonical_shortcuts": {},
        "canonical_branch_aliases": [],
        "errors": [],
        "warnings": [],
        "status": "running",
    }

    # Production-shaped episodes: run_batch starts each independent seed at 0,
    # then consumes indices 0..3 as demos and index 4 as the query.
    for difficulty in (None, "easy", "medium", "hard"):
        label = "default" if difficulty is None else difficulty
        orders: Counter[str] = Counter()
        query_ops: Counter[str] = Counter()
        match_positions: Counter[str] = Counter()
        complete = 0
        for seed in range(seeds):
            ops = [
                int(gen.generate(seed, index, difficulty=difficulty)[0][0])
                for index in range(5)
            ]
            orders["".join(map(str, ops[:4]))] += 1
            query_ops[str(ops[4])] += 1
            positions = [index for index, value in enumerate(ops[:4]) if value == ops[4]]
            match_positions[",".join(map(str, positions))] += 1
            complete += int(set(ops[:4]) == {1, 2, 3, 4})
        row = {
            "episodes": seeds,
            "complete_demo_operation_coverage": complete,
            "distinct_demo_orders": len(orders),
            "demo_order_counts": dict(sorted(orders.items())),
            "query_operation_counts": dict(sorted(query_ops.items())),
            "query_matches_demo_positions": dict(sorted(match_positions.items())),
        }
        report["episode_schedule"][label] = row
        if complete != seeds:
            report["errors"].append(
                f"{label}: only {complete}/{seeds} episodes cover all four operations in demos"
            )
        if set(query_ops) != {"1", "2", "3", "4"}:
            report["errors"].append(
                f"{label}: production query operations cover {sorted(query_ops)}, expected 1..4"
            )
        if len(match_positions) == 1:
            report["warnings"].append(
                f"{label}: query operation always matches the same demo position(s): "
                f"{next(iter(match_positions))}"
            )

    # Validate the contract meaning of CANONICAL_SHORTCUTS itself.
    for name, rival in sorted(getattr(gen, "CANONICAL_SHORTCUTS", {}).items()):
        fit = 0
        failures: list[dict[str, Any]] = []
        for index, pair in enumerate(pairs):
            try:
                predicted = rival(copy.deepcopy(pair["input"]))
                matched = grids_equal(predicted, pair["output"])
            except Exception as exc:
                matched = False
                failures.append({"pair": index, "error": f"{type(exc).__name__}: {exc}"})
            fit += int(matched)
            if not matched and not failures:
                failures.append({"pair": index, "reason": "output mismatch"})
        report["declared_canonical_shortcuts"][name] = {
            "fits": fit,
            "of": len(pairs),
            "fits_all": fit == len(pairs),
            "failures": failures,
        }
        if fit != len(pairs):
            report["errors"].append(
                f"CANONICAL_SHORTCUTS[{name!r}] fits {fit}/{len(pairs)} canonical pairs"
            )

    # Exhaustively search the natural family: change exactly one key's Boolean
    # operation to one of the other three operations, leaving all other keys intact.
    for key in range(1, 5):
        for replacement in range(1, 5):
            if replacement == key:
                continue
            candidate = branch_alias(gen, key, replacement)
            fits = sum(
                grids_equal(candidate(copy.deepcopy(pair["input"])), pair["output"])
                for pair in pairs
            )
            if fits != len(pairs):
                continue

            witness = None
            witness_grid = None
            for difficulty in (None, "easy", "medium", "hard"):
                for seed in range(seeds):
                    grid = gen.generate(
                        seed,
                        seed % 17,
                        difficulty=difficulty,
                        op=key,
                    )
                    intended = gen.rule_mirror(copy.deepcopy(grid))
                    rival_output = candidate(copy.deepcopy(grid))
                    if not grids_equal(intended, rival_output):
                        witness_grid = grid
                        witness = {
                            "difficulty": "default" if difficulty is None else difficulty,
                            "seed": seed,
                            "sample_index": seed % 17,
                            "overrides": {"op": key},
                            "input": grid,
                            "intended": intended,
                            "rival": rival_output,
                        }
                        break
                if witness is not None:
                    break

            aliases = declared_equivalents(gen, candidate, pairs, witness_grid) if witness_grid else []
            row = {
                "key": key,
                "replacement_operation": replacement,
                "canonical_fit": f"{fits}/{len(pairs)}",
                "declared_equivalent_names": aliases,
                "generated_counterexample": witness,
            }
            report["canonical_branch_aliases"].append(row)
            if witness is None:
                report["errors"].append(
                    f"canonical branch alias key {key}->{replacement} had no generated counterexample"
                )
            if not aliases:
                report["errors"].append(
                    f"canonical branch alias key {key}->{replacement} is not declared in CANONICAL_SHORTCUTS"
                )

    report["status"] = "pass" if not report["errors"] else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=TASK_HOME / "generator.py",
        help="generator source to load",
    )
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 4:
        parser.error("--seeds must be at least 4")
    report = audit(args.generator, args.seeds)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
