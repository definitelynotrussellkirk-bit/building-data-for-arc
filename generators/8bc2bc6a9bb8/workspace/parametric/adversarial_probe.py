#!/usr/bin/env python3
"""Bounded two-surface adversarial probe for the sort-key prototype."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import prototype


def run() -> dict:
    checks = []
    with prototype.RacketBridge(max_calls_before_restart=128) as bridge:
        for seed, demos, queries in ((0, 2, 1), (17, 6, 8)):
            for setting in prototype.ALLOWED_SORT_KEYS:
                episode = prototype.make_episode(
                    seed,
                    sort_key=setting,
                    demos=demos,
                    queries=queries,
                    bridge=bridge,
                )
                pairs = episode["train"] + episode["test"]
                assert len(pairs) == demos + queries
                assert len({prototype.grid_sha256(p["input"]) for p in pairs}) == len(pairs)
                assert all(
                    type(cell) is int and 0 <= cell <= 9
                    for pair in pairs
                    for grid in (pair["input"], pair["output"])
                    for row in grid
                    for cell in row
                )
                changed = copy.deepcopy(episode)
                changed["seed"] += 10_000
                changed["test"][0]["output"][0][0] ^= 1
                assert prototype.public_id(changed) == prototype.public_id(episode)
                checks.append(
                    {
                        "seed": seed,
                        "sort_key": setting,
                        "demos": demos,
                        "queries": queries,
                        "public_id": prototype.public_id(episode),
                        "status": "pass",
                    }
                )
    return {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "task_id": prototype.TASK_ID,
        "status": "pass",
        "checks": checks,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
