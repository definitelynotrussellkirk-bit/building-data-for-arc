#!/usr/bin/env python3
"""Bounded protected-Racket audit for the 22e428cda452 native family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_adapter_22e", HERE / "adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def audit(seeds: list[int]) -> dict[str, object]:
    jobs = pairs = racket_labels = matched_inputs = stress = prefix_checks = 0
    survivor_counts = {name: 0 for name in ADAPTER.HYPOTHESES}
    winner_branch_counts = {"has_top_marker": 0, "bottom_only": 0}
    marker_counts: set[int] = set()
    grid_shapes: set[tuple[int, int]] = set()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        identity = bridge.runtime_identity
        assert identity.get("backend") == "racket" and identity.get("protected") is True
        wrapped = {
            finish: wrap_rule(ADAPTER.program({"finish": finish}))
            for finish in ADAPTER.SETTINGS
        }
        wrapped["highlight_most_source_markers"] = wrap_rule(ADAPTER.counterfactual_program())
        for seed in seeds:
            full = {
                finish: ADAPTER.generate(seed, {"finish": finish}, 6, 4)
                for finish in ADAPTER.SETTINGS
            }
            for left, right in zip(
                full["project_only"]["train"] + full["project_only"]["test"],
                full["highlight_most_projected_color"]["train"]
                + full["highlight_most_projected_color"]["test"],
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
                    survivor_counts[finish] += 1
                    for pair in episode["train"] + episode["test"]:
                        got = bridge.eval_text(f"({wrapped[finish]} {_literal(pair['input'])})")
                        assert got == pair["output"]
                        racket_labels += 1
                        state = ADAPTER.observe(pair["input"])
                        assert state["largest_projected_count"] == 1
                        marker_counts.add(state["source_marker_count"])
                        grid_shapes.add((state["height"], state["width"]))
                        branch = "has_top_marker" if state["winner_has_top_marker"] else "bottom_only"
                        winner_branch_counts[branch] += 1
                    large = [
                        pair for pair in episode["test"]
                        if len(pair["input"]) == len(pair["input"][0]) == 30
                    ]
                    assert len(large) == 1
                    large_state = ADAPTER.observe(large[0]["input"])
                    assert large_state["source_marker_count"] == 4
                    assert set(large_state["touches"]) == {"top", "bottom", "left", "right"}
                    stress += 1
                    prefix = ADAPTER.generate(seed, {"finish": finish}, 2, 1)
                    assert prefix["train"] == episode["train"][:2]
                    assert prefix["test"] == episode["test"][:1]
                    prefix_checks += 2

        witness = ADAPTER.generate(
            seeds[0], {"finish": "highlight_most_projected_color"}, 2, 1
        )["train"][0]
        wrong = bridge.eval_text(
            f"({wrapped['highlight_most_source_markers']} {_literal(witness['input'])})"
        )
        assert wrong == ADAPTER.predict(witness["input"], "highlight_most_source_markers")
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
            "source_marker_counts": sorted(marker_counts),
            "grid_shapes": [list(shape) for shape in sorted(grid_shapes)],
            "winner_branch_counts": winner_branch_counts,
            "declared_hypotheses": list(ADAPTER.HYPOTHESES),
            "survivor_counts": survivor_counts,
            "causal_counterfactual": {
                "ablation": "wrong_intermediate",
                "largest_projected_color": dependency["largest_projected_color"],
                "most_source_markers_color": dependency["most_source_markers_color"],
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
