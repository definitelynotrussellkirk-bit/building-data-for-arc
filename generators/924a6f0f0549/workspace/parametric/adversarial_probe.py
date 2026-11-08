#!/usr/bin/env python3
"""Bounded protected-Racket parity and identifiability probe."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_924a6f0f0549_probe_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def run_probe(*, seeds=(0, 1, 2), demo_counts=(2, 6), bridge=None):
    seeds = list(seeds)
    demo_counts = list(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("seeds and demo_counts must be nonempty")
    owns_bridge = bridge is None
    active = prototype.RacketBridge(max_calls_before_restart=256) if owns_bridge else bridge
    episodes = 0
    evaluations = 0
    try:
        for seed in seeds:
            for demos in demo_counts:
                claims_by_mode = {
                    mode: prototype.generate_claims(
                        seed, render_mode=mode, demos=demos, queries=4
                    )
                    for mode in prototype.ALLOWED_MODES
                }
                reference_inputs = [
                    pair["input"]
                    for pair in claims_by_mode["outline"]["train"]
                    + claims_by_mode["outline"]["test"]
                ]
                for mode, claims in claims_by_mode.items():
                    rival = next(value for value in prototype.ALLOWED_MODES if value != mode)
                    if not all(
                        pair["output"] != prototype.python_mirror(
                            pair["input"], render_mode=rival
                        )
                        for pair in claims["train"]
                    ):
                        raise AssertionError("minimum demonstrations did not refute rival")
                    if [pair["input"] for pair in claims["train"] + claims["test"]] != reference_inputs:
                        raise AssertionError("settings changed visible inputs")
                    for pair in claims["train"] + claims["test"]:
                        actual = prototype.execute_rule(
                            claims["program_solution"], pair["input"], bridge=active
                        )
                        evaluations += 1
                        if actual != pair["output"]:
                            raise AssertionError("protected Racket disagrees with claim")
                    stress = claims["test"][-1]["input"]
                    if [len(stress), len(stress[0])] != [30, 30]:
                        raise AssertionError("last query is not 30x30")
                    episodes += 1
    finally:
        if owns_bridge:
            active.shutdown()
    return {
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "modes": list(prototype.ALLOWED_MODES),
        "seeds": seeds,
        "demo_counts": demo_counts,
        "episodes_checked": episodes,
        "racket_evaluations": evaluations,
        "queries_per_episode": 4,
        "max_input_shape": [30, 30],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 6])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(seeds=args.seeds, demo_counts=args.demo_counts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
