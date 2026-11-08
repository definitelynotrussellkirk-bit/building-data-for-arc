#!/usr/bin/env python3
"""Bounded adversarial probe for the portal-phase family."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_4cea2727fcf9_probe_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _paint_all_walkable(grid):
    return [[7 if value == 0 else value for value in row] for row in grid]


def run_probe(*, seeds=(0, 1), demo_counts=(2, 6), bridge=None):
    seeds = list(seeds)
    demo_counts = list(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("probe needs nonempty seeds and demo counts")
    owns = bridge is None
    active = prototype.RacketBridge() if owns else bridge
    declared = {
        phase: prototype.program_for(phase, root=prototype.ROOT)
        for phase in prototype.ALLOWED_PHASES
    }
    never = prototype.never_portal_program(root=prototype.ROOT)
    episodes = 0
    max_shape = [0, 0]
    first_turn_checks = 0
    shortcut_survivors = {}
    try:
        for seed in seeds:
            for demos in demo_counts:
                for chosen in prototype.ALLOWED_PHASES:
                    episode = prototype.make_episode(
                        seed,
                        portal_phase=chosen,
                        demos=demos,
                        queries=4,
                        root=prototype.ROOT,
                    )
                    replay = prototype.make_episode(
                        seed,
                        portal_phase=chosen,
                        demos=demos,
                        queries=4,
                        root=prototype.ROOT,
                    )
                    if replay != episode:
                        raise AssertionError("episode replay is nondeterministic")
                    episodes += 1
                    expected = [pair["output"] for pair in episode["train"]]
                    survivors = []
                    for phase, program in declared.items():
                        outputs = [
                            prototype.execute_rule(program, pair["input"], bridge=active)
                            for pair in episode["train"]
                        ]
                        if outputs == expected:
                            survivors.append(phase)
                    if survivors != [chosen]:
                        raise AssertionError(
                            f"declared phase survivors {survivors} for {chosen}, seed={seed}, demos={demos}"
                        )

                    shortcut_predictions = {
                        "ignore_portals": [
                            prototype.execute_rule(never, pair["input"], bridge=active)
                            for pair in episode["train"]
                        ],
                        "skip_checkpoint": [
                            prototype.execute_rule(
                                prototype.checkpoint_skip_program(chosen, root=prototype.ROOT),
                                pair["input"],
                                bridge=active,
                            )
                            for pair in episode["train"]
                        ],
                        "identity": [copy.deepcopy(pair["input"]) for pair in episode["train"]],
                        "paint_all_walkable": [
                            _paint_all_walkable(pair["input"]) for pair in episode["train"]
                        ],
                    }
                    for name, predictions in shortcut_predictions.items():
                        if predictions == expected:
                            shortcut_survivors.setdefault(name, []).append(
                                {"seed": seed, "demos": demos, "phase": chosen}
                            )

                    for pair in episode["train"] + episode["test"]:
                        h, w = len(pair["input"]), len(pair["input"][0])
                        max_shape = [max(max_shape[0], h), max(max_shape[1], w)]
                    first = prototype.first_turn_bytes(episode)
                    future = copy.deepcopy(episode)
                    future["program"] = "private mutation"
                    future["parameters"]["portal_phase"] = "always"
                    future["test"][1]["input"][0][0] ^= 1
                    future["test"][3]["output"][0][0] ^= 1
                    if prototype.first_turn_bytes(future) != first:
                        raise AssertionError("first turn leaked private or future-query data")
                    first_turn_checks += 1

                    stress = episode["test"][-1]["input"]
                    walls = sum(value == 8 for row in stress for value in row)
                    if (len(stress), len(stress[0])) != (30, 30) or walls < 90:
                        raise AssertionError("stress scene is not substantive 30x30")
        if shortcut_survivors:
            raise AssertionError(f"shortcut rivals survived: {shortcut_survivors}")
        return {
            "schema": "portal-phase-adversarial-probe-v1",
            "status": "pass",
            "phases": list(prototype.ALLOWED_PHASES),
            "seeds": seeds,
            "demo_counts": demo_counts,
            "episodes_checked": episodes,
            "queries_per_episode": 4,
            "max_input_shape": max_shape,
            "shortcut_survivors": shortcut_survivors,
            "first_turn_invariance_checks": first_turn_checks,
            "attacks": [
                "wrong portal phase",
                "ignore portals",
                "skip checkpoint stage",
                "identity",
                "paint every walkable cell",
                "future-query/private leakage",
                "duplicate/nondeterministic episode replay",
                "non-substantive 30x30 padding",
            ],
            "limits": (
                "Finite declared rivals and sampled seeds/count corners; no claim of universal "
                "rule uniqueness or all-seed sampler completeness."
            ),
        }
    finally:
        if owns:
            active.shutdown()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
