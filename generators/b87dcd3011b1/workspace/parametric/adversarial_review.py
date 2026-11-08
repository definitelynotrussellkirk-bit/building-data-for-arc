"""Reusable finite rival audit for the b87dcd3011b1 portal-policy lessons."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(filename)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("_b87_adversarial_prototype", "prototype.py")
adapter = _load("_b87_adversarial_adapter", "adapter.py")

RIVALS = (
    "no_portals",
    "fixed_4",
    "fixed_5",
    "fixed_6",
    "lowest_color",
    "highest_color",
    "narrowest_manhattan",
    "widest_euclidean",
    "max_vertical",
    "max_horizontal",
    "nearest_start",
    "nearest_goal",
    "fastest_single",
    "first_scan",
    "last_scan",
)


def _apply(grid, name: str):
    if name in prototype.POLICIES:
        return prototype.apply_policy(grid, name)
    return prototype.apply_selector(grid, name)


def review_episode(seed: int, setting: str, *, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = adapter.generate(seed, {"portal_policy": setting}, demos, queries)
    survivors = []
    for rival in RIVALS:
        if all(_apply(pair["input"], rival) == pair["output"] for pair in episode["train"]):
            survivors.append(rival)
    query_failures = [
        {"rival": rival, "query": index}
        for rival in survivors
        for index, pair in enumerate(episode["test"])
        if _apply(pair["input"], rival) != pair["output"]
    ]
    return {
        "seed": seed,
        "setting": setting,
        "demos": demos,
        "queries": queries,
        "rivals_tested": list(RIVALS),
        "surviving_wrong_rivals": survivors,
        "query_failures": query_failures,
        "demo_widest_colors": [prototype.widest_portal_color(p["input"]) for p in episode["train"]],
        "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
    }


def run(*, seeds=range(48), demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seeds = tuple(seeds)
    rows = [review_episode(seed, setting, demos=demos, queries=queries)
            for seed in seeds for setting in prototype.POLICIES]
    failures = [row for row in rows if row["surviving_wrong_rivals"] or row["query_failures"]]
    return {
        "schema": "b87dcd3011b1-adversarial-selector-audit-v1",
        "episodes": len(rows),
        "seeds": len(seeds),
        "demos": demos,
        "queries": queries,
        "rivals": list(RIVALS),
        "failures": failures,
        "status": "passed" if not failures else "failed",
        "limits": "Finite selector bank; not a proof of universal uniqueness or human learnability.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
