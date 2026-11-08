#!/usr/bin/env python3
"""Bounded protected-Racket and shortcut probe for the packing-order family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_e5ead55c33e7_probe_prototype", _HOME / "prototype.py"
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
    signatures = set()
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("probe requires protected Racket")
        for seed in seeds:
            for demos in demo_counts:
                families = {
                    order: prototype.generate_claims(
                        seed, packing_order=order, demos=demos, queries=4
                    )
                    for order in prototype.PACKING_ORDERS
                }
                visible = [
                    pair["input"]
                    for pair in families["front_first"]["train"]
                    + families["front_first"]["test"]
                ]
                for order in prototype.PACKING_ORDERS:
                    episode = families[order]
                    assert visible == [
                        pair["input"] for pair in episode["train"] + episode["test"]
                    ]
                    rival = "rear_first" if order == "front_first" else "front_first"
                    assert all(
                        pair["output"]
                        != prototype.solve_python(pair["input"], packing_order=rival)
                        for pair in episode["train"]
                    )
                    for pair in episode["train"]:
                        objects = prototype.extract_objects(pair["input"])
                        signatures.add(
                            tuple(obj["color"] for obj in sorted(objects, key=lambda obj: obj["c2"]))
                        )
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
        if len(signatures) < 4:
            raise AssertionError("color/horizontal signatures did not vary enough")
        witness = prototype.build_input(0, role="train", index=0)
        assert prototype.solve_python(witness, packing_order="front_first") != prototype.solve_python(
            witness, packing_order="rear_first"
        )
    finally:
        bridge.close()
    return {
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "packing_orders": list(prototype.PACKING_ORDERS),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": episodes,
        "racket_evaluations": evaluations,
        "max_input_shape": max_shape,
        "distinct_color_order_signatures": len(signatures),
        "shortcut_bank": [
            "fixed_color_to_slot",
            "fixed_horizontal_location",
            "wrong_object_order_intermediate",
        ],
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
