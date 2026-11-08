#!/usr/bin/env python3
"""Bounded protected-Racket self-audit for the f98b43c1996b family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_audit_f98_adapter", HERE / "adapter.py")
assert _SPEC and _SPEC.loader
ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ADAPTER
_SPEC.loader.exec_module(ADAPTER)
FAMILY = ADAPTER.family


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        return sum(len(row) for row in left) + sum(len(row) for row in right)
    return sum(a != b for ra, rb in zip(left, right) for a, b in zip(ra, rb))


def audit(seeds: list[int]) -> dict[str, object]:
    bridge = RacketBridge(max_calls_before_restart=64)
    jobs: list[dict[str, object]] = []
    evaluations = 0
    matched = prefix = stress = 0
    shapes: set[tuple[int, int]] = set()
    block_counts: set[int] = set()
    try:
        identity = bridge.runtime_identity
        assert identity.get("backend") == "racket" and identity.get("protected") is True
        wrapped = {
            setting: wrap_rule(FAMILY.program({"finish": setting}))
            for setting in FAMILY.SETTINGS
        }
        wrong_wrapped = wrap_rule(FAMILY.counterfactual_program())

        def execute(wrapped_program: str, grid: list[list[int]]):
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(f"({wrapped_program} {_literal(grid)})")

        for seed in seeds:
            full = {
                setting: FAMILY.generate(seed, {"finish": setting}, 6, 4)
                for setting in FAMILY.SETTINGS
            }
            left_pairs = full[FAMILY.SETTINGS[0]]["train"] + full[FAMILY.SETTINGS[0]]["test"]
            right_pairs = full[FAMILY.SETTINGS[1]]["train"] + full[FAMILY.SETTINGS[1]]["test"]
            for left, right in zip(left_pairs, right_pairs):
                assert left["input"] == right["input"]
                matched += 1

            for demos in (2, 3, 6):
                for setting in FAMILY.SETTINGS:
                    episode = FAMILY.generate(seed, {"finish": setting}, demos, 4)
                    survivors = [
                        hypothesis
                        for hypothesis in FAMILY.HYPOTHESES
                        if all(
                            FAMILY.predict(pair["input"], hypothesis) == pair["output"]
                            for pair in episode["train"]
                        )
                    ]
                    assert survivors == [setting]
                    for pair in episode["train"] + episode["test"]:
                        got = execute(wrapped[setting], pair["input"])
                        assert got == pair["output"]
                        state = FAMILY.analyze(pair["input"])
                        assert state["pre_winner_unique"] and state["post_winner_unique"]
                        assert state["pre_winner"] != state["post_winner"]
                        shapes.add((state["height"], state["width"]))
                        block_counts.add(len(state["solid_windows"]))
                    large = episode["test"][3]
                    state = FAMILY.analyze(large["input"])
                    assert (state["height"], state["width"]) == (30, 30)
                    assert sum(cell != 0 for row in large["input"] for cell in row) >= 55
                    stress += 1
                    smaller = FAMILY.generate(seed, {"finish": setting}, 2, 1)
                    assert smaller["train"] == episode["train"][:2]
                    assert smaller["test"] == episode["test"][:1]
                    prefix += 2
                    jobs.append({
                        "seed": seed,
                        "demos": demos,
                        "finish": setting,
                        "survivors": survivors,
                    })

        causal_episode = FAMILY.generate(
            seeds[0], {"finish": "highlight_most_frequent_post_color"}, 2, 4
        )
        causal_pair = causal_episode["test"][3]
        intended = execute(wrapped["highlight_most_frequent_post_color"], causal_pair["input"])
        wrong = execute(wrong_wrapped, causal_pair["input"])
        assert intended == causal_pair["output"]
        assert wrong == FAMILY.predict(causal_pair["input"], "highlight_pre_frequency")
        assert wrong != intended
        state = FAMILY.analyze(causal_pair["input"])
        return {
            "schema": "arcpuzzles-parametric-authoring-audit-v1",
            "task_id": FAMILY.TASK_ID,
            "status": "passed",
            "seeds": seeds,
            "settings": list(FAMILY.SETTINGS),
            "demo_counts": [2, 3, 6],
            "queries": 4,
            "jobs": jobs,
            "job_count": len(jobs),
            "protected_racket_labels": evaluations,
            "matched_input_checks": matched,
            "prefix_checks": prefix,
            "stress_30x30_jobs": stress,
            "grid_shapes": [list(shape) for shape in sorted(shapes)],
            "solid_window_counts": sorted(block_counts),
            "declared_hypotheses": list(FAMILY.HYPOTHESES),
            "causal_counterfactual": {
                "ablation": "wrong_intermediate",
                "pre_winner": state["pre_winner"],
                "post_winner": state["post_winner"],
                "changed_output_cells": _changed(intended, wrong),
            },
            "racket": {
                key: identity.get(key)
                for key in ("backend", "protected", "binary_sha256", "prelude_sha256")
            },
            "limits": "Finite deterministic seeds and declared rivals only; not universal identifiability or measured learning gain.",
            "training_admitted": False,
        }
    finally:
        bridge.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[0, 17])
    args = parser.parse_args()
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "jobs": report["job_count"],
        "protected_racket_labels": report["protected_racket_labels"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
