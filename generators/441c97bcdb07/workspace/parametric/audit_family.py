#!/usr/bin/env python3
"""Build compact protected-Racket and finite-rival evidence for this family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, normalize_grid, public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "441c97bcdb07"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_audit_parametric_441c97bcdb07", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _evaluate(bridge: RacketBridge, source: str, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


def _sha256(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def build_report(out: Path, seeds: tuple[int, ...]) -> dict:
    prototype = _load_prototype()
    exact_checks = 0
    finite_episodes = 0
    finite_pairs = 0
    settings = (prototype.CANONICAL, prototype.ALTERNATE)
    public_ids = []
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=96) as bridge:
        for seed in seeds:
            for selected in settings:
                episode = prototype.generate_episode(seed, selected, 2, 4)
                audit = prototype.audit_episode(episode, selected)
                if audit["surviving_declared_rules"] != [selected] or audit["surviving_shortcuts"]:
                    raise AssertionError({"seed": seed, "selected": selected, "audit": audit})
                finite_episodes += 1
                finite_pairs += len(episode["train"]) + len(episode["test"])
                source = prototype.program_for(selected)
                for pair in episode["train"] + episode["test"]:
                    actual = _evaluate(bridge, source, pair["input"])
                    if actual != pair["output"]:
                        raise AssertionError({"seed": seed, "selected": selected, "input": pair["input"]})
                    exact_checks += 1
                public = prototype.public_turn(episode, 0)
                raw = public_challenge_bytes(public)
                forbidden = (b"completion_transform", b"program_solution", selected.encode())
                if any(value in raw for value in forbidden):
                    raise AssertionError("public projection leaked private metadata")
                visible_id = public_challenge_id(public)
                if visible_id != _sha256(raw):
                    raise AssertionError("public ID is not the visible-byte SHA256")
                public_ids.append(visible_id)

        witness_input = prototype.build_input(seeds[0], "query", 2)
        analysis = prototype.analyze_input(witness_input)
        correct_source = prototype.alternate_program()
        wrong_source = prototype.wrong_intermediate_program()
        correct_output = _evaluate(bridge, correct_source, witness_input)
        wrong_output = _evaluate(bridge, wrong_source, witness_input)
        exact_checks += 2
        differing_cells = sum(
            left != right
            for left_row, right_row in zip(correct_output, wrong_output, strict=True)
            for left, right in zip(left_row, right_row, strict=True)
        )
        if differing_cells <= 0:
            raise AssertionError("wrong-intermediate witness did not change the final output")
        identity = bridge.runtime_identity

    # Broader sampler/teaching sweep without multiplying Racket startup cost.
    sampler_episodes = 0
    sampler_pairs = 0
    for seed in range(128):
        for selected in settings:
            for demos in (2, 3, 6):
                episode = prototype.generate_episode(seed, selected, demos, 4)
                audit = prototype.audit_episode(episode, selected)
                if audit["surviving_declared_rules"] != [selected] or audit["surviving_shortcuts"]:
                    raise AssertionError({"seed": seed, "selected": selected, "demos": demos, "audit": audit})
                sampler_episodes += 1
                sampler_pairs += demos + 4

    report = {
        "schema": "441c97bcdb07-parametric-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "settings": list(settings),
        "seeds": list(seeds),
        "protected_racket": {
            "evaluations": exact_checks,
            "runtime_identity": identity,
            "canonical_sha256": _sha256(prototype.canonical_program()),
            "alternate_sha256": _sha256(prototype.alternate_program()),
        },
        "finite_self_review": {
            "episodes": finite_episodes,
            "pairs": finite_pairs,
            "declared_shortcuts": list(prototype.DECLARED_SHORTCUTS),
            "surviving_shortcuts": [],
            "scope": "two-demo/four-query lessons for the listed seeds and declared finite rivals only",
        },
        "sampler_sweep": {
            "episodes": sampler_episodes,
            "pairs": sampler_pairs,
            "seeds": [0, 127],
            "demo_counts": [2, 3, 6],
            "query_count": 4,
            "failures": [],
        },
        "public_projection": {
            "checked": len(public_ids),
            "distinct_visible_ids": len(set(public_ids)),
            "private_fields_absent": True,
        },
        "sequential_dependency": {
            "step_a": "locate TL/TR/BL copies and compare row-span with col-span",
            "intermediate": analysis["dominant_span"],
            "step_b": "choose clockwise or counterclockwise quarter-turn and paint at the inferred fourth corner",
            "why_b_depends_on_a": "the selected turn direction is the result of the span comparison and cannot be selected before it",
            "wrong_intermediate": "vertical" if analysis["dominant_span"] == "horizontal" else "horizontal",
            "input": witness_input,
            "correct_program_sha256": _sha256(correct_source),
            "wrong_program_sha256": _sha256(wrong_source),
            "correct_output": correct_output,
            "wrong_output": wrong_output,
            "differing_cells": differing_cells,
            "executed_with_protected_racket": True,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=(0, 17))
    args = parser.parse_args()
    report = build_report(args.out, tuple(args.seeds))
    print(json.dumps({
        "status": report["status"],
        "racket_evaluations": report["protected_racket"]["evaluations"],
        "sampler_episodes": report["sampler_sweep"]["episodes"],
        "witness_differing_cells": report["sequential_dependency"]["differing_cells"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
