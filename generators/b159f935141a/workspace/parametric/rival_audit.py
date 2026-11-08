"""Finite adversarial shortcut audit for the rarest-color lesson.

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
_SPEC = importlib.util.spec_from_file_location("b159_rival_audit_prototype", HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

Selector = Callable[[dict], list[int]]


def _apply(grid: list[list[int]], selector: Selector) -> list[list[int]]:
    info = prototype.analyze(grid)
    selected = set(selector(info))
    out = deepcopy(grid)
    for r, c, color in info["qualifying_centers"]:
        if color in selected:
            out[r][c] = color
    return out


def _rivals() -> dict[str, Selector]:
    return {
        "singleton_only": lambda info: [
            color for color, count in info["counts_by_color"].items() if count == 1
        ],
        "lowest_numeric_color": lambda info: [min(info["counts_by_color"])],
        "highest_numeric_color": lambda info: [max(info["counts_by_color"])],
        "first_qualifying_color": lambda info: [info["qualifying_centers"][0][2]],
        "last_qualifying_color": lambda info: [info["qualifying_centers"][-1][2]],
        "most_common_color": lambda info: [info["most_common_color"]],
    }


def run(seed_count: int = 256) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an integer in 1..4096")
    rivals = _rivals()
    survivors: list[dict] = []
    harmful: list[dict] = []
    for seed in range(seed_count):
        episode = prototype.generate_episode(
            seed, fill_scope="rarest_color_only", demos=2, queries=4
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
        "schema": "b159f935141a-rival-audit-v1",
        "status": "pass" if not survivors else "fail",
        "setting": {"fill_scope": "rarest_color_only"},
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
