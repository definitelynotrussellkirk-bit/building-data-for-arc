#!/usr/bin/env python3
"""Bounded rival and sampler audit for 59d146376904."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_59d146376904_probe_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
p = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(p)


def run_probe(*, seeds: Iterable[int] = range(64), demo_counts=(2, 3, 6)) -> dict:
    normalized_seeds = list(seeds)
    normalized_counts = list(demo_counts)
    episodes = 0
    query_changing = []
    demo_survivors = []
    rank_orders = set()
    majority_colors = set()
    shapes = set()
    max_nonzero = 0
    for seed in normalized_seeds:
        for demos in normalized_counts:
            for settings in p.SETTINGS:
                episode = p.generate(seed, settings, demos=demos, queries=4)
                episodes += 1
                survivors = p.lesson_rival_survivors(episode["train"], settings)
                if survivors:
                    demo_survivors.append({"seed": seed, "demos": demos, "settings": settings, "rivals": survivors})
                rows = p.query_changing_survivors(episode, settings)
                if rows:
                    query_changing.extend(
                        {"seed": seed, "demos": demos, "settings": settings, **row}
                        for row in rows
                    )
                for pair in episode["train"] + episode["test"]:
                    facts = p.analyze_input(pair["input"])
                    rank_orders.add(facts["majority_rank"])
                    majority_colors.update(item["majority_color"] for item in facts["quadrants"])
                    shapes.add((facts["height"], facts["width"]))
                    max_nonzero = max(max_nonzero, sum(cell != 0 for row in pair["input"] for cell in row))
    status = "pass" if not demo_survivors and not query_changing else "fail"
    return {
        "schema": "59d146376904-adversarial-probe-v1",
        "status": status,
        "seeds": normalized_seeds,
        "demo_counts": normalized_counts,
        "settings": p.SETTINGS,
        "episodes_checked": episodes,
        "queries_per_episode": 4,
        "rival_count_by_setting": {json.dumps(s, sort_keys=True): len(p._rival_rules(s)) for s in p.SETTINGS},
        "demo_survivors": demo_survivors,
        "query_changing_survivors": query_changing,
        "rank_orders": [list(order) for order in sorted(rank_orders)],
        "majority_colors": sorted(majority_colors),
        "input_shapes": [list(shape) for shape in sorted(shapes)],
        "max_nonzero_cells": max_nonzero,
        "limits": p.RIVAL_SCOPE_LIMITS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 1000:
        parser.error("--seeds must be in 1..1000")
    report = run_probe(seeds=range(args.seeds))
    body = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
