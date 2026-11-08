#!/usr/bin/env python3
"""Bounded protected-Racket parity and wrong-order audit for 956425dc719c."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("parametric_956_audit_prototype", HERE / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def apply(bridge, program, grid):
    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({wrap_rule(program)} g)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    programs = {mode: prototype.program_for(mode, root=prototype.ROOT) for mode in prototype.ALLOWED_MODES}
    wrong = prototype.wrong_order_program(root=prototype.ROOT)
    evaluations = pairs = distinctions = wrong_order_differences = 0
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires protected Racket")
        for seed in (0, 17):
            for demos in (2, 3, 6):
                claims = {
                    mode: prototype.generate_claims(seed, post_select=mode, demos=demos, queries=4, root=prototype.ROOT)
                    for mode in prototype.ALLOWED_MODES
                }
                visible = [p["input"] for p in claims["none"]["train"] + claims["none"]["test"]]
                for mode in prototype.ALLOWED_MODES[1:]:
                    if [p["input"] for p in claims[mode]["train"] + claims[mode]["test"]] != visible:
                        raise AssertionError("settings did not share visible inputs")
                for index, grid in enumerate(visible):
                    outputs = {}
                    for mode in prototype.ALLOWED_MODES:
                        expected = (claims[mode]["train"] + claims[mode]["test"])[index]["output"]
                        actual = apply(bridge, programs[mode], grid)
                        evaluations += 1
                        if actual != expected:
                            raise AssertionError(f"Racket/Python mismatch seed={seed} demos={demos} mode={mode} index={index}")
                        outputs[mode] = actual
                    if len({prototype._grid_key(value) for value in outputs.values()}) != 3:
                        raise AssertionError("pair did not distinguish all settings")
                    distinctions += 1
                    wrong_actual = apply(bridge, wrong, grid)
                    evaluations += 1
                    if wrong_actual != prototype.python_wrong_order_largest(grid):
                        raise AssertionError("wrong-order Racket/Python mismatch")
                    if wrong_actual == outputs["largest"]:
                        raise AssertionError("wrong order did not change final output")
                    wrong_order_differences += 1
                    pairs += 1
    finally:
        bridge.shutdown()

    report = {
        "schema": "arcpuzzles-task-local-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed",
        "approved": False,
        "seeds": [0, 17],
        "demo_counts": [2, 3, 6],
        "settings": list(prototype.ALLOWED_MODES),
        "pairs_checked": pairs,
        "distinguishing_pairs": distinctions,
        "wrong_order_differences": wrong_order_differences,
        "protected_racket_evaluations": evaluations,
        "racket": {
            "backend": identity.get("backend"),
            "protected": identity.get("protected"),
            "binary_sha256": identity.get("binary_sha256"),
        },
        "program_sha256": {
            **{mode: hashlib.sha256(program.encode()).hexdigest() for mode, program in programs.items()},
            "wrong_order_largest": hashlib.sha256(wrong.encode()).hexdigest(),
        },
        "limits": "Bounded author self-audit only; no owner acceptance or training admission.",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
