"""Finite adversarial shortcut audit for the densest-tile lesson.

This does not prove uniqueness.  It checks a small, named family of plausible
shortcut rules against the minimum two visible demonstrations and records any
survivor that would disagree on one of the four private queries.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from typing import Callable

HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("ba29_rival_audit_prototype", HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

Selector = Callable[[dict], list[int]]


def _apply(grid: list[list[int]], selector: Selector) -> list[list[int]]:
    info = prototype.analyze(grid)
    selected = set(selector(info))
    out = deepcopy(grid)
    for record in info["tiles"]:
        if record["index"] not in selected:
            continue
        ra, rb, ca, cb = record["bounds"]
        mirrored = [row[::-1] for row in record["tile"]]
        for r in range(rb - ra):
            for c in range(cb - ca):
                out[ra + r][ca + c] = mirrored[r][c]
    return out


def _rivals() -> dict[str, Selector]:
    values: dict[str, Selector] = {
        "first_tile": lambda info: [0],
        "last_tile": lambda info: [len(info["tiles"]) - 1],
        "sparsest_tile": lambda info: [info["sparsest"]["index"]],
        "exactly_one_blank": lambda info: [
            record["index"]
            for record in info["tiles"]
            if record["count"] == len(record["tile"]) * len(record["tile"][0]) - 1
        ],
        "majority_filled": lambda info: [
            record["index"]
            for record in info["tiles"]
            if 2 * record["count"] > len(record["tile"]) * len(record["tile"][0])
        ],
    }
    for fixed_index in range(8):
        values[f"fixed_index_{fixed_index}"] = (
            lambda info, fixed_index=fixed_index: [fixed_index]
        )
    return values


def run(seed_count: int = 256) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an integer in 1..4096")
    rivals = _rivals()
    survivors: list[dict] = []
    harmful: list[dict] = []
    for seed in range(seed_count):
        episode = prototype.generate_episode(
            seed, tile_scope="densest_only", demos=2, queries=4
        )
        for name, selector in rivals.items():
            if not all(
                _apply(pair["input"], selector) == pair["output"]
                for pair in episode["train"]
            ):
                continue
            query_disagreements = [
                index
                for index, pair in enumerate(episode["test"])
                if _apply(pair["input"], selector) != pair["output"]
            ]
            row = {
                "seed": seed,
                "rival": name,
                "query_disagreements": query_disagreements,
            }
            survivors.append(row)
            if query_disagreements:
                harmful.append(row)
    return {
        "schema": "ba29d14676d1-rival-audit-v1",
        "status": "pass" if not survivors else "fail",
        "setting": {"tile_scope": "densest_only"},
        "demonstrations": 2,
        "queries": 4,
        "seed_count": seed_count,
        "candidate_rules": sorted(rivals),
        "all_demo_survivors": survivors,
        "harmful_survivors": harmful,
        "limits": "Finite named rival library over consecutive seeds; not a universal uniqueness proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=256)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seeds)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
