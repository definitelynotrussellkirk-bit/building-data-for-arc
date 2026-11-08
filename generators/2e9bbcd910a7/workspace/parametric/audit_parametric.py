#!/usr/bin/env python3
"""Run a bounded, source-local learnability audit for the parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def _load_prototype():
    path = Path(__file__).resolve().with_name("prototype.py")
    name = "_arc_2e9bbcd910a7_audit_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTO = _load_prototype()
GEN = PROTO.GEN


def _paint(grid, cells):
    output = [list(row) for row in grid]
    for row, col in cells:
        output[row][col] = 8
    return output


def _global_runner_up(grid):
    ranked = GEN._ranked_runs(grid)
    if len(ranked) < 2:
        raise ValueError("runner-up rival requires at least two runs")
    return _paint(grid, ranked[1]["cells"])


def _opposite_champion(grid):
    ranked = GEN._ranked_runs(grid)
    winner = ranked[0]
    candidates = [
        run
        for run in ranked[1:]
        if run["direction"] != winner["direction"]
        and len(run["cells"]) < len(winner["cells"])
    ]
    if not candidates:
        raise ValueError("opposite-champion rival requires an eligible run")
    return _paint(grid, candidates[0]["cells"])


def run_audit(*, seeds=(0, 17), demos=3, queries=4):
    settings_report = {
        "winner": {"pairs": 0, "crossing_follower_mismatches": 0},
        "crossing_follower": {
            "pairs": 0,
            "winner_mismatches": 0,
            "global_runner_up_mismatches": 0,
            "opposite_champion_mismatches": 0,
        },
    }
    coverage = {"winner_lengths": set(), "winner_directions": set(), "shapes": set()}
    episodes = 0
    total_pairs = 0
    episode_records = []
    for target in PROTO.PAINT_TARGETS:
        setting = {"paint_target": target}
        for seed in seeds:
            episode = PROTO.generate(seed, setting, demos, queries)
            pairs = episode["train"] + episode["test"]
            inputs = {json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}
            if len(inputs) != len(pairs):
                raise AssertionError("audit episode contains duplicate inputs")
            record = {
                "seed": seed,
                "setting": target,
                "demos": demos,
                "queries": queries,
                "pairs": [],
            }
            for index, pair in enumerate(pairs):
                grid, expected = pair["input"], pair["output"]
                if GEN.self_check(grid):
                    raise AssertionError("audit input left the reviewed grammar")
                ranked = GEN._ranked_runs(grid)
                winner = ranked[0]
                follower = PROTO.select_crossing_follower(grid)
                coverage["winner_lengths"].add(len(winner["cells"]))
                coverage["winner_directions"].add(winner["direction"])
                coverage["shapes"].add((len(grid), len(grid[0])))
                winner_output = GEN.rule_mirror(grid)
                follower_output = PROTO.solve_python(
                    grid, {"paint_target": "crossing_follower"}
                )
                runner_up_output = _global_runner_up(grid)
                opposite_output = _opposite_champion(grid)
                if expected != PROTO.solve_python(grid, setting):
                    raise AssertionError("saved Python label differs from selected setting")
                row = {
                    "index": index,
                    "winner": {
                        "direction": winner["direction"],
                        "length": len(winner["cells"]),
                        "start": list(winner["start"]),
                    },
                    "follower": {
                        "direction": follower["direction"],
                        "length": len(follower["cells"]),
                        "start": list(follower["start"]),
                        "crosses_winner": bool(
                            set(winner["cells"]) & set(follower["cells"])
                        ),
                    },
                }
                if target == "winner":
                    settings_report[target]["pairs"] += 1
                    settings_report[target]["crossing_follower_mismatches"] += (
                        follower_output != expected
                    )
                else:
                    settings_report[target]["pairs"] += 1
                    settings_report[target]["winner_mismatches"] += winner_output != expected
                    settings_report[target]["global_runner_up_mismatches"] += (
                        runner_up_output != expected
                    )
                    settings_report[target]["opposite_champion_mismatches"] += (
                        opposite_output != expected
                    )
                record["pairs"].append(row)
                total_pairs += 1
            episode_records.append(record)
            episodes += 1
    return {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": PROTO.TASK_ID,
        "scope": "Finite Python mirror audit; protected Racket qualification is separate.",
        "seeds": list(seeds),
        "demos": demos,
        "queries": queries,
        "episodes": episodes,
        "pairs": total_pairs,
        "settings": settings_report,
        "coverage": {
            "winner_lengths": sorted(coverage["winner_lengths"]),
            "winner_directions": sorted(coverage["winner_directions"]),
            "shapes": [list(shape) for shape in sorted(coverage["shapes"])],
        },
        "episodes_detail": episode_records,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    report = run_audit(
        seeds=tuple(args.seeds or (0, 17)), demos=args.demos, queries=args.queries
    )
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
