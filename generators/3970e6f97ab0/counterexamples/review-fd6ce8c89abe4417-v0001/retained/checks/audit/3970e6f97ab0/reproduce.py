#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
TASK_ID = "3970e6f97ab0"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"
EXPECTED_SHA = "4feb28045863ff797e58b583f967b16c58f2f6f6f31c9128df1b930a19bd291f"
OUT = Path(__file__).resolve().parent / "analysis.json"
RETAINED_EPISODE = (
    REPO / "generators" / TASK_ID / "counterexamples" /
    "review-2039f1d410b22dbf-v0001" / "retained" / "checks" /
    "audit" / TASK_ID / "episode.jsonl"
)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid) -> str:
    return digest_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_generator():
    digest = digest_bytes(GEN_PATH.read_bytes())
    assert digest == EXPECTED_SHA, (digest, EXPECTED_SHA)
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def intended_or(grid):
    return [
        [1 if row[c] != 0 or row[c + 7] != 0 else 0 for c in range(6)]
        for row in grid
    ]


def left_only(grid):
    return [[1 if row[c] != 0 else 0 for c in range(6)] for row in grid]


def differences(actual, rival):
    return [
        [r, c, actual[r][c], rival[r][c]]
        for r in range(len(actual))
        for c in range(len(actual[0]))
        if actual[r][c] != rival[r][c]
    ]


def main():
    gen, source_sha = load_generator()
    retained = json.loads(RETAINED_EPISODE.read_text().splitlines()[0])
    assert retained["seed"] == 1
    assert retained["sample_indices"] == [0, 1, 2, 3]
    assert retained["provenance"]["difficulty"] == "medium"

    generated = [gen.generate(1, index, difficulty="medium") for index in range(4)]
    retained_inputs = [pair["input"] for pair in retained["train"] + retained["test"]]
    assert generated == retained_inputs, "current generator no longer reproduces retained lesson"

    outputs = [intended_or(grid) for grid in generated]
    retained_outputs = [pair["output"] for pair in retained["train"] + retained["test"]]
    assert outputs == retained_outputs, "independent OR oracle disagrees with retained Racket outputs"
    rival_outputs = [left_only(grid) for grid in generated]
    train_matches = [rival_outputs[i] == outputs[i] for i in range(3)]
    query_diff = differences(outputs[3], rival_outputs[3])
    assert train_matches == [True, True, True]
    assert len(query_diff) == 18
    assert all(not gen.self_check(grid) for grid in generated)

    per_band = {}
    first_extra = None
    for band_index, band in enumerate(("easy", "medium", "hard")):
        ambiguous = 0
        dangerous = 0
        rejected = 0
        unique_inputs = set()
        for lesson_index in range(100):
            seed = 397000 + band_index * 10000 + lesson_index
            grids = [gen.generate(seed, index, difficulty=band) for index in range(4)]
            ys = [intended_or(grid) for grid in grids]
            for grid in grids:
                unique_inputs.add(grid_sha(grid))
                rejected += bool(gen.self_check(grid))
            survives = all(left_only(grids[i]) == ys[i] for i in range(3))
            if survives:
                ambiguous += 1
                if left_only(grids[3]) != ys[3]:
                    dangerous += 1
                    if first_extra is None:
                        first_extra = {"band": band, "seed": seed, "sample_indices": [0, 1, 2, 3]}
        per_band[band] = {
            "lessons": 100,
            "pairs": 400,
            "unique_inputs": len(unique_inputs),
            "self_check_rejections": rejected,
            "left_only_fits_all_three_demos": ambiguous,
            "left_only_fits_demos_but_differs_on_query": dangerous,
        }

    result = {
        "task_id": TASK_ID,
        "generator_path": str(GEN_PATH.relative_to(WORK)),
        "generator_sha256": source_sha,
        "retained_executed_rule_hash": retained["executed_rule_hash"],
        "rival": "ignore the right panel and output the left panel's nonzero occupancy mask",
        "concrete_generated_lesson": {
            "seed": 1,
            "difficulty": "medium",
            "sample_indices": [0, 1, 2, 3],
            "current_generation_matches_retained_racket_episode": True,
            "train_matches": train_matches,
            "query_matches": False,
            "query_difference_count": len(query_diff),
            "query_difference_actual_then_rival": query_diff,
            "input_sha256": [grid_sha(grid) for grid in generated],
            "output_sha256": [grid_sha(y) for y in outputs],
            "rival_output_sha256": [grid_sha(y) for y in rival_outputs],
            "self_check_errors": [gen.self_check(grid) for grid in generated],
            "query_input": generated[3],
            "query_intended_output": outputs[3],
            "query_rival_output": rival_outputs[3],
        },
        "generated_census": {
            "sampler": "100 deterministic 3-demo+1-query lessons per band",
            "per_band": per_band,
            "first_additional_counterexample": first_extra,
        },
        "root_cause": (
            "The generator applies the same panel_pattern to both panels. Structured profiles "
            "therefore often have identical occupancy masks, allowing a left-only rule to survive "
            "all three demonstrations even when the held-out right panel adds occupied cells."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "source_sha256": source_sha,
        "train_matches": train_matches,
        "query_difference_count": len(query_diff),
        "per_band": per_band,
    }, indent=2))


if __name__ == "__main__":
    main()
