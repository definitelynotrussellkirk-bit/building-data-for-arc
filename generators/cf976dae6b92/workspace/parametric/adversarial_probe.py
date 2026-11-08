#!/usr/bin/env python3
"""Bounded rival search for the cf976dae6b92 relay-policy lesson."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_cf976dae6b92_probe_subject_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
p = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(p)


def run_probe(*, seeds: Iterable[int] = range(64), demo_counts=(2, 3, 6)) -> dict:
    normalized_seeds = list(seeds)
    normalized_counts = list(demo_counts)
    query_changing = []
    survivor_rows = []
    max_shape = [0, 0]
    choices = set()
    episodes = 0
    for seed in normalized_seeds:
        for demos in normalized_counts:
            for policy in p.POLICIES:
                episode = p.generate(seed, {p.PARAMETER: policy}, demos=demos, queries=4)
                episodes += 1
                for pair in episode["train"] + episode["test"]:
                    max_shape[0] = max(max_shape[0], len(pair["input"]))
                    max_shape[1] = max(max_shape[1], len(pair["input"][0]))
                    choices.add(p.relay_choice(pair["input"], "nearest_to_2"))
                for name, rival in p._rival_rules(policy).items():
                    survives = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                    if not survives:
                        continue
                    disagreements = [
                        index
                        for index, pair in enumerate(episode["test"])
                        if rival(pair["input"]) != pair["output"]
                    ]
                    row = {
                        "seed": seed,
                        "demos": demos,
                        "policy": policy,
                        "rival": name,
                        "query_disagreements": disagreements,
                    }
                    survivor_rows.append(row)
                    if disagreements:
                        query_changing.append(row)
    return {
        "schema": "cf976dae6b92-adversarial-probe-v1",
        "status": "pass" if not query_changing else "fail",
        "seeds": normalized_seeds,
        "demo_counts": normalized_counts,
        "policies": list(p.POLICIES),
        "episodes_checked": episodes,
        "queries_per_episode": 4,
        "rival_rules": {policy: sorted(p._rival_rules(policy)) for policy in p.POLICIES},
        "rival_scope_limits": dict(p.RIVAL_SCOPE_LIMITS),
        "demo_survivors": survivor_rows,
        "query_changing_survivors": query_changing,
        "max_input_shape": max_shape,
        "relay_choices": sorted(choices),
        "limits": "Finite named-rival search; it does not prove unrestricted uniqueness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if type(args.seeds) is not int or not 1 <= args.seeds <= 1000:
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
