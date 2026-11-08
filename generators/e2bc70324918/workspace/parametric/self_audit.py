#!/usr/bin/env python3
"""Bounded protected-Racket parity audit for the endpoint-stamp family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e2bc_parametric_audit_prototype", HERE / "prototype.py")
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

    evaluations = 0
    pairs = 0
    distinctions = 0
    programs = {
        mode: prototype.program_for(mode, root=prototype.ROOT)
        for mode in prototype.ALLOWED_MODES
    }
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires protected Racket")
        for seed in (0, 17):
            for demos in (2, 3, 6):
                claims = {
                    mode: prototype.generate_claims(
                        seed, stamp_mode=mode, demos=demos, queries=4, root=prototype.ROOT
                    )
                    for mode in prototype.ALLOWED_MODES
                }
                visible = [p["input"] for p in claims["copy"]["train"] + claims["copy"]["test"]]
                other = [p["input"] for p in claims["dilate4"]["train"] + claims["dilate4"]["test"]]
                if visible != other:
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
                    pairs += 1
                    if outputs["copy"] == outputs["dilate4"]:
                        raise AssertionError("pair did not distinguish settings")
                    distinctions += 1
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
        "protected_racket_evaluations": evaluations,
        "distinguishing_pairs": distinctions,
        "racket": {
            "backend": identity.get("backend"),
            "protected": identity.get("protected"),
            "binary_sha256": identity.get("binary_sha256"),
        },
        "program_sha256": {
            mode: hashlib.sha256(program.encode()).hexdigest()
            for mode, program in programs.items()
        },
        "limits": "Bounded author self-audit only; no owner acceptance or training admission.",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
