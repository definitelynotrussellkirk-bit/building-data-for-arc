#!/usr/bin/env python3
"""Bounded adversarial authoring audit for a06827026857's native family."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_a06827026857", HERE / "adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


def _largest_foreground(grid):
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    maximum = max(counts.values())
    selected = min(color for color, count in counts.items() if count == maximum)
    return ADAPTER._paint(grid, selected)


def audit(seeds: list[int]) -> dict[str, object]:
    jobs = labels = stress_jobs = matched_inputs = prefix_checks = 0
    first_color_survivors = largest_foreground_survivors = 0
    first_query_positions: set[int] = set()
    setting_disagreements = 0
    for seed in seeds:
        baseline = ADAPTER.generate(seed, {"window_scope": "all_windows"}, 6, 4)
        first_query_positions.add(ADAPTER.query_source_order(seed)[0])
        baseline_inputs = [p["input"] for p in baseline["train"] + baseline["test"]]
        for scope in ADAPTER.SETTINGS:
            setting = {"window_scope": scope}
            full = ADAPTER.generate(seed, setting, 6, 4)
            assert [p["input"] for p in full["train"] + full["test"]] == baseline_inputs
            matched_inputs += len(baseline_inputs)
            for demos in (2, 3, 6):
                jobs += 1
                episode = ADAPTER.generate(seed, setting, demos, 4)
                labels += demos + 4
                assert ADAPTER.surviving_settings(episode["train"]) == [setting]
                small = ADAPTER.generate(seed, setting, 2, 1)
                assert small["train"] == episode["train"][:2]
                assert small["test"] == episode["test"][:1]
                prefix_checks += 2
                stress = [pair for pair in episode["test"]
                          if (len(pair["input"]), len(pair["input"][0])) == (30, 30)]
                assert len(stress) == 1
                stress_jobs += 1
                if all(ADAPTER.predict_first_color(p["input"]) == p["output"]
                       for p in episode["train"]):
                    first_color_survivors += 1
                if all(_largest_foreground(p["input"]) == p["output"]
                       for p in episode["train"]):
                    largest_foreground_survivors += 1
                for other_scope in ADAPTER.SETTINGS:
                    other = {"window_scope": other_scope}
                    if other != setting and any(
                        ADAPTER.predict(pair["input"], other) != pair["output"]
                        for pair in episode["test"]
                    ):
                        setting_disagreements += 1
        case = ADAPTER.dependency_case(seed, {"window_scope": "dominant_color"})
        assert case["counterfactual_output"] != case["output"]
    assert len(first_query_positions) > 1
    assert first_color_survivors == 0
    assert largest_foreground_survivors == 0
    return {
        "schema": "arcpuzzles-parametric-authoring-audit-v1",
        "task_id": ADAPTER.TASK_ID,
        "status": "passed",
        "seeds": seeds,
        "settings": [{"window_scope": scope} for scope in ADAPTER.SETTINGS],
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "jobs": jobs,
        "labels_checked_in_python": labels,
        "stress_30x30_jobs": stress_jobs,
        "matched_input_checks": matched_inputs,
        "prefix_checks": prefix_checks,
        "first_query_source_positions": sorted(first_query_positions),
        "first_color_survivors": first_color_survivors,
        "largest_foreground_survivors": largest_foreground_survivors,
        "query_setting_disagreements": setting_disagreements,
        "limits": "Finite deterministic seeds, two declared settings, and two plausible bypass rivals only; protected Racket qualification and causal replay are separate.",
        "training_admitted": False
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[0, 17, 97, 211])
    args = parser.parse_args()
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
