#!/usr/bin/env python3
"""Bounded authoring audit for the d377a54f20c6 native stroke-relay family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_adapter_d377", HERE / "adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


def _changed(left, right):
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def audit(seeds: list[int]) -> dict[str, object]:
    jobs = pairs = stress = prefix_checks = matched_input_checks = 0
    rival_survivors = {name: 0 for name in ADAPTER.HYPOTHESES}
    first_query_source_positions: set[int] = set()
    proxy_checks = 0
    for seed in seeds:
        canonical = ADAPTER.generate(seed, {"finish": "redraw_only"}, 6, 4)
        alternate = ADAPTER.generate(seed, {"finish": "highlight_most_stroke_cells"}, 6, 4)
        for left, right in zip(canonical["train"] + canonical["test"], alternate["train"] + alternate["test"]):
            assert left["input"] == right["input"]
            matched_input_checks += 1
            info = ADAPTER.observe(left["input"])
            target = info["stroke_winner"]
            for name in (
                "largest_area", "largest_perimeter", "tallest", "widest",
                "most_input_markers", "fewest_input_markers", "first_object", "last_object",
                "highest_marker_color", "lowest_marker_color", "smallest_stroke",
            ):
                assert info[name] != target, (seed, name)
                proxy_checks += 1
        raw = [ADAPTER._scene(seed, "query", index) for index in range(4)]
        first = canonical["test"][0]["input"]
        first_query_source_positions.add(next(index for index, grid in enumerate(raw) if grid == first))
        for demos in (2, 3, 6):
            for finish in ADAPTER.SETTINGS:
                jobs += 1
                episode = ADAPTER.generate(seed, {"finish": finish}, demos, 4)
                pairs += len(episode["train"]) + len(episode["test"])
                certificate = ADAPTER.certificate(episode["train"], [p["input"] for p in episode["test"]])
                assert certificate["survivors"] == [finish]
                assert set(certificate["query_disagreements"]) == set(ADAPTER.HYPOTHESES) - {finish}
                for hypothesis in certificate["survivors"]:
                    rival_survivors[hypothesis] += 1
                large = [p for p in episode["test"] if len(p["input"]) == len(p["input"][0]) == 30]
                assert len(large) == 1
                assert set(ADAPTER.observe(large[0]["input"])["touches"]) == {"top", "bottom", "left", "right"}
                stress += 1
                small = ADAPTER.generate(seed, {"finish": finish}, 2, 1)
                assert small["train"] == episode["train"][:2]
                assert small["test"] == episode["test"][:1]
                prefix_checks += 2
    assert len(first_query_source_positions) > 1, "first query source profile never changes"
    causal_input = ADAPTER.generate(seeds[0], {"finish": "highlight_most_stroke_cells"}, 2, 1)["train"][0]["input"]
    correct = ADAPTER.predict(causal_input, "highlight_most_stroke_cells")
    wrong = ADAPTER.predict(causal_input, "highlight_most_input_markers")
    dependency = ADAPTER.explain_dependency(causal_input)
    assert correct != wrong
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
        "stress_30x30_jobs": stress,
        "matched_input_checks": matched_input_checks,
        "prefix_checks": prefix_checks,
        "proxy_separation_checks": proxy_checks,
        "first_query_source_positions": sorted(first_query_source_positions),
        "declared_hypotheses": list(ADAPTER.HYPOTHESES),
        "survivor_counts": rival_survivors,
        "causal_counterfactual": {
            "ablation": "wrong_intermediate",
            "stroke_counts": dependency["stroke_counts"],
            "input_marker_counts": dependency["input_marker_counts"],
            "correct_object": dependency["correct_object"],
            "wrong_object": dependency["wrong_input_marker_object"],
            "changed_cells": _changed(correct, wrong),
        },
        "limits": "Finite deterministic seeds and declared rivals only; not universal identifiability or measured learning gain.",
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[0, 17, 97])
    args = parser.parse_args()
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
