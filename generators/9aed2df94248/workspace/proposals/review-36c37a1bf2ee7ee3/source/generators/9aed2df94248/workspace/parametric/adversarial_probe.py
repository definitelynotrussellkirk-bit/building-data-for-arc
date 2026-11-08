#!/usr/bin/env python3
"""Bounded protected-Racket and shortcut probe for the analogy family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_9aed2df94248_probe_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _execute(bridge: RacketBridge, program: str, grid):
    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({wrap_rule(program)} g)")


def run_probe(*, seeds=(0, 17), demo_counts=(2, 3, 6)) -> dict:
    episodes = 0
    evaluations = 0
    max_shape = [0, 0]
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("probe requires protected Racket")
        for seed in seeds:
            for demos in demo_counts:
                families = {
                    direction: prototype.generate_claims(
                        seed, direction=direction, demos=demos, queries=4
                    )
                    for direction in prototype.DIRECTIONS
                }
                visible = [
                    pair["input"]
                    for pair in families["forward"]["train"] + families["forward"]["test"]
                ]
                for direction in prototype.DIRECTIONS:
                    episode = families[direction]
                    assert visible == [
                        pair["input"] for pair in episode["train"] + episode["test"]
                    ]
                    rival = "reverse" if direction == "forward" else "forward"
                    assert any(
                        pair["output"]
                        != prototype.solve_python(pair["input"], direction=rival)
                        for pair in episode["train"]
                    )
                    # A fixed transform of C cannot fit all demonstrations.
                    for code in range(8):
                        guessed = [
                            prototype.apply_transform(prototype.split_panels(pair["input"])[2], code)
                            for pair in episode["train"]
                        ]
                        assert guessed != [pair["output"] for pair in episode["train"]]
                    for pair in episode["train"] + episode["test"]:
                        actual = _execute(bridge, episode["program_solution"], pair["input"])
                        evaluations += 1
                        if actual != pair["output"]:
                            raise AssertionError("Racket/Python label mismatch")
                        max_shape[0] = max(max_shape[0], len(pair["input"]))
                        max_shape[1] = max(max_shape[1], len(pair["input"][0]))
                    stress = episode["test"][-1]["input"]
                    assert [len(stress), len(stress[0])] == [30, 30]
                    episodes += 1
        # Explicit wrong-intermediate witness: replacing inferred rot-cw with identity changes output.
        witness = prototype.generate_claims(0, direction="forward", demos=2, queries=4)["train"][0]
        _, _, c = prototype.split_panels(witness["input"])
        assert prototype.infer_transform(witness["input"]) == 1
        assert witness["output"] != c
    finally:
        bridge.close()
    return {
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "directions": list(prototype.DIRECTIONS),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": episodes,
        "racket_evaluations": evaluations,
        "max_input_shape": max_shape,
        "shortcut_bank": ["fixed_transform_0_through_7", "wrong_identity_intermediate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
