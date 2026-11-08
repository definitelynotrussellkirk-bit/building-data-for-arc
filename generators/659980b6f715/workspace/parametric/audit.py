#!/usr/bin/env python3
"""Bounded learnability, boundary and protected-Racket audit for 659980b6f715."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"


def _load():
    name = "parametric_659980b6f715_audit_source"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load()


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _failure(rows: list[dict[str, Any]], kind: str, **details: Any) -> None:
    rows.append({"kind": kind, **details})


def build_audit(
    *,
    seeds=(0, 17),
    demo_counts=(2, 3, 6),
    query_counts=(1, 4),
    execute_racket=True,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    totals = {
        "seeds": len(seeds),
        "requests": 0,
        "episodes": 0,
        "labeled_pairs": 0,
        "matched_input_requests": 0,
        "stress_30x30_episodes": 0,
        "racket_evaluations": 0,
    }
    survivors: dict[str, Any] = {}
    bridge = None
    wrapped = {}
    if execute_racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
        wrapped = {name: wrap_rule(P.program_for(name)) for name in P.ALIGNMENTS}

    def execute(name, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        totals["racket_evaluations"] += 1
        return bridge.eval_text(f"({wrapped[name]} {literal})")

    try:
        for seed in seeds:
            base = P.episode_inputs(seed, demos=2, queries=4)
            survivors[str(seed)] = {}
            for chosen in P.ALIGNMENTS:
                labels = [P.solve(grid, chosen) for grid in base["train"]]
                names = [
                    name for name in P.CANDIDATE_RULES
                    if all(P.solve_candidate(grid, name) == expected for grid, expected in zip(base["train"], labels))
                ]
                survivors[str(seed)][chosen] = names
                if names != [chosen]:
                    _failure(failures, "finite_rival_survivor", seed=seed, chosen=chosen, survivors=names)
            if execute_racket:
                for chosen in P.ALIGNMENTS:
                    episode = P.generate_episode(seed, chosen, demos=2, queries=4)
                    for pair in (episode["train"][0], episode["test"][3]):
                        if execute(chosen, pair["input"]) != pair["output"]:
                            _failure(failures, "racket_label_mismatch", seed=seed, chosen=chosen)

            for demos in demo_counts:
                for queries in query_counts:
                    totals["requests"] += 1
                    episodes = {
                        mode: P.generate_episode(seed, mode, demos=demos, queries=queries)
                        for mode in P.ALIGNMENTS
                    }
                    totals["episodes"] += len(episodes)
                    totals["labeled_pairs"] += len(episodes) * (demos + queries)
                    inputs = [
                        [pair["input"] for split in ("train", "test") for pair in episode[split]]
                        for episode in episodes.values()
                    ]
                    if inputs[1:] == inputs[:-1]:
                        totals["matched_input_requests"] += 1
                    else:
                        _failure(failures, "settings_input_confound", seed=seed, demos=demos, queries=queries)
                    if len({_freeze(grid) for grid in inputs[0]}) != demos + queries:
                        _failure(failures, "duplicate_visible_input", seed=seed, demos=demos, queries=queries)
                    full = P.generate_episode(seed, P.DEFAULT_ALIGNMENT, demos=6, queries=4)
                    current = episodes[P.DEFAULT_ALIGNMENT]
                    if current["train"] != full["train"][:demos] or current["test"] != full["test"][:queries]:
                        _failure(failures, "prefix_instability", seed=seed, demos=demos, queries=queries)
                    one = P.generate_episode(seed, P.DEFAULT_ALIGNMENT, demos=demos, queries=1)
                    if P.public_view(current, 0) != P.public_view(one, 0):
                        _failure(failures, "first_turn_instability", seed=seed, demos=demos, queries=queries)
                    if queries == 4:
                        for episode in episodes.values():
                            grid = episode["test"][3]["input"]
                            if len(grid) == 30 and len(grid[0]) == 30:
                                totals["stress_30x30_episodes"] += 1
                            else:
                                _failure(failures, "missing_30x30_stress", seed=seed, demos=demos)
    finally:
        if bridge is not None:
            bridge.close()

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": P.TASK_ID,
        "status": "passed" if not failures else "failed",
        "settings": list(P.ALIGNMENTS),
        "finite_candidates": list(P.CANDIDATE_RULES),
        "finite_rival_survivors": survivors,
        "totals": totals,
        "failures": failures,
        "limits": "Finite authored seeds/count boundaries and declared rivals only; not universal identifiability.",
        "training_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    report = build_audit(seeds=tuple(args.seeds), execute_racket=not args.no_racket)
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "totals": report["totals"], "failures": len(report["failures"])}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
