#!/usr/bin/env python3
"""Bounded native audit for the border-to-clockwise-corner family.

The audit covers the full count envelope on two fixed seeds, executes every
full-bank label and the causal counterfactual through protected Racket, and
emits source-bound JSON for later reviewers.  It does not approve source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parent
TASK = "5ee8de1860a7"
SETTINGS = ({"finish_rule": "border_only"}, {"finish_rule": "clockwise_segment"})
SEEDS = (0, 17)
COUNTS = ((2, 1), (3, 4), (6, 4))


def _load():
    path = HOME / "prototype.py"
    name = f"_{TASK}_audit_prototype"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case-out", type=Path, required=True)
    args = parser.parse_args()
    prototype = _load()
    label_evaluations = 0
    counterfactual_evaluations = 0
    episodes_checked = 0
    prefix_checks = 0
    lesson_checks = 0
    matched_checks = 0
    sides: set[str] = set()
    segment_lengths: list[int] = []
    case = None

    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        for seed in SEEDS:
            full = {
                setting["finish_rule"]: prototype.generate(seed, setting, 6, 4)
                for setting in SETTINGS
            }
            assert _inputs(full["border_only"]) == _inputs(full["clockwise_segment"])
            matched_checks += 1
            for setting in SETTINGS:
                mode = setting["finish_rule"]
                episode = full[mode]
                assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)}) == 10
                report = prototype.lesson_report(
                    {"train": episode["train"][:2], "test": episode["test"]}, setting
                )
                assert report["setting_survivors"] == [mode]
                assert report["harmful_shortcut_survivors"] == []
                lesson_checks += 1
                wrapped = wrap_rule(prototype.program(setting))
                for pair in episode["train"] + episode["test"]:
                    actual = bridge.eval_text(f"({wrapped} {_literal(pair['input'])})")
                    assert actual == pair["output"]
                    label_evaluations += 1
                for demos, queries in COUNTS:
                    candidate = prototype.generate(seed, setting, demos, queries)
                    assert candidate["train"] == episode["train"][:demos]
                    assert candidate["test"] == episode["test"][:queries]
                    prefix_checks += 1
                    episodes_checked += 1
            assert (len(full["clockwise_segment"]["test"][3]["input"]),
                    len(full["clockwise_segment"]["test"][3]["input"][0])) == (30, 30)
            for pair in full["clockwise_segment"]["train"] + full["clockwise_segment"]["test"]:
                intermediate = prototype.route_intermediate(pair["input"])
                sides.add(intermediate["hit_side"])
                segment_lengths.append(intermediate["segment_length"])
            causal = prototype.causal_case(full["clockwise_segment"]["test"][3]["input"])
            actual_cf = bridge.eval_text(
                f"({wrap_rule(causal['counterfactual_program'])} {_literal(causal['input'])})"
            )
            assert actual_cf == causal["counterfactual_output"]
            assert actual_cf != causal["output"]
            counterfactual_evaluations += 1
            if case is None:
                case = causal

    assert sides == {"top", "right", "bottom", "left"}
    assert min(segment_lengths) >= 3 and max(segment_lengths) >= 15
    assert prototype.program(SETTINGS[0]) == (HOME / "canonical.rkt").read_text(encoding="utf-8")
    verification = {
        "schema": "arcpuzzles-task-local-bounded-audit-v1",
        "task_id": TASK,
        "status": "pass",
        "seeds": list(SEEDS),
        "count_requests": [list(value) for value in COUNTS],
        "settings": list(SETTINGS),
        "episodes_checked": episodes_checked,
        "matched_input_checks": matched_checks,
        "prefix_checks": prefix_checks,
        "lesson_checks": lesson_checks,
        "protected_racket_label_evaluations": label_evaluations,
        "protected_racket_counterfactual_evaluations": counterfactual_evaluations,
        "hit_sides": sorted(sides),
        "segment_length_range": [min(segment_lengths), max(segment_lengths)],
        "checks": [
            "exact canonical default",
            "matched inputs across settings",
            "2-6 demonstration and 1-4 query prefix stability",
            "ten distinct full-bank inputs",
            "two-demo setting identification",
            "declared harmful-shortcut rejection",
            "all four border-hit sides",
            "substantive 30x30 fourth query",
            "protected-Racket parity for every full-bank label",
            "protected-Racket skip-A disagreement",
        ],
        "source_sha256": {
            name: _sha(HOME / name)
            for name in ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "clockwise_segment.rkt", "skip_border.rkt")
        },
    }
    assert case is not None
    causal_candidate = {
        "settings": case["settings"],
        "program": case["program"],
        "input": case["input"],
        "output": case["output"],
        "counterfactual_program": case["counterfactual_program"],
        "counterfactual_output": case["counterfactual_output"],
        "intermediate_value": case["intermediate_value"],
        "ablation": case["ablation"],
        "step_a": case["step_a"],
        "intermediate": case["intermediate"],
        "step_b": case["step_b"],
        "why_b_depends_on_a": case["why_b_depends_on_a"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.case_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.case_out.write_text(json.dumps(causal_candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
