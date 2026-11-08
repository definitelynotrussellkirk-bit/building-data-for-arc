#!/usr/bin/env python3
"""Bounded protected-Racket audit for the c00 native parametric family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_adapter_c00", HERE / "adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def audit(seeds: list[int]) -> dict[str, object]:
    jobs = pairs = racket_labels = matched_inputs = stress = prefix_checks = 0
    declared_survivors = {name: 0 for name in ADAPTER.HYPOTHESES}
    area_positions: set[tuple[int, int]] = set()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        identity = bridge.runtime_identity
        assert identity.get("backend") == "racket" and identity.get("protected") is True
        wrapped = {
            finish: wrap_rule(ADAPTER.program({"finish": finish}))
            for finish in ADAPTER.SETTINGS
        }
        wrapped["highlight_largest_perimeter"] = wrap_rule(ADAPTER.counterfactual_program())
        for seed in seeds:
            full = {
                finish: ADAPTER.generate(seed, {"finish": finish}, 6, 4)
                for finish in ADAPTER.SETTINGS
            }
            for left, right in zip(
                full["colors_only"]["train"] + full["colors_only"]["test"],
                full["highlight_largest_rectangle"]["train"] + full["highlight_largest_rectangle"]["test"],
            ):
                assert left["input"] == right["input"]
                matched_inputs += 1
            for demos in (2, 3, 6):
                for finish in ADAPTER.SETTINGS:
                    jobs += 1
                    episode = ADAPTER.generate(seed, {"finish": finish}, demos, 4)
                    pairs += len(episode["train"]) + len(episode["test"])
                    cert = ADAPTER.certificate(
                        episode["train"], [pair["input"] for pair in episode["test"]]
                    )
                    assert cert["survivors"] == [finish]
                    declared_survivors[finish] += 1
                    for pair in episode["train"] + episode["test"]:
                        got = bridge.eval_text(f"({wrapped[finish]} {_literal(pair['input'])})")
                        assert got == pair["output"]
                        racket_labels += 1
                        state = ADAPTER.observe(pair["input"])
                        assert state["largest_area_position"] != state["largest_perimeter_position"]
                        area_positions.add(tuple(state["largest_area_position"]))
                    large = [pair for pair in episode["test"] if len(pair["input"]) == len(pair["input"][0]) == 30]
                    assert len(large) == 1
                    assert set(ADAPTER.observe(large[0]["input"])["touches"]) == {"top", "bottom", "left", "right"}
                    stress += 1
                    prefix = ADAPTER.generate(seed, {"finish": finish}, 2, 1)
                    assert prefix["train"] == episode["train"][:2]
                    assert prefix["test"] == episode["test"][:1]
                    prefix_checks += 2
        witness = ADAPTER.generate(
            seeds[0], {"finish": "highlight_largest_rectangle"}, 2, 1
        )["train"][0]
        wrong = bridge.eval_text(
            f"({wrapped['highlight_largest_perimeter']} {_literal(witness['input'])})"
        )
        assert wrong == ADAPTER.predict(witness["input"], "highlight_largest_perimeter")
        assert wrong != witness["output"]
        dependency = ADAPTER.explain_dependency(witness["input"])
        return {
            "schema": "arcpuzzles-parametric-authoring-audit-v1",
            "task_id": ADAPTER.TASK_ID,
            "status": "passed",
            "seeds": seeds,
            "settings": list(ADAPTER.SETTINGS),
            "demo_counts": [2, 3, 6],
            "queries": 4,
            "jobs": jobs,
            "pairs": pairs,
            "protected_racket_labels": racket_labels + 1,
            "matched_input_checks": matched_inputs,
            "prefix_checks": prefix_checks,
            "stress_30x30_jobs": stress,
            "area_winner_positions": [list(value) for value in sorted(area_positions)],
            "declared_hypotheses": list(ADAPTER.HYPOTHESES),
            "survivor_counts": declared_survivors,
            "causal_counterfactual": {
                "ablation": "wrong_intermediate",
                "largest_area_position": dependency["largest_area_position"],
                "largest_perimeter_position": dependency["largest_perimeter_position"],
                "changed_output_cells": _changed(witness["output"], wrong),
            },
            "racket": {
                "backend": identity.get("backend"),
                "protected": identity.get("protected"),
                "binary_sha256": identity.get("binary_sha256"),
                "prelude_sha256": identity.get("prelude_sha256"),
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
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
