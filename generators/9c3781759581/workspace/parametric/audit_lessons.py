"""Reproduce bounded teaching, causal-ablation, and Racket checks."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, public_challenge_bytes

HERE = Path(__file__).resolve().parent
TASK_ID = "9c3781759581"
SETTINGS = (
    {"crop_policy": "fixed_color_9"},
    {"crop_policy": "selector_parity"},
)


def _load(name: str):
    path = HERE / f"{name}.py"
    module_name = f"_audit_{TASK_ID}_{name}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _crop(grid: list[list[int]], color: int) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    if not cells:
        raise ValueError(f"missing color {color}")
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [values[col0 : col1 + 1] for values in grid[row0 : row1 + 1]]


def _racket_receipt(adapter: Any, episodes: list[tuple[dict[str, str], dict[str, Any]]]) -> dict[str, Any]:
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    root = find_root(__file__)
    runtime = root / "shared" / "runtime"
    evaluations = 0
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for settings, episode in episodes:
                source = adapter.program(settings)
                for pair in episode["train"] + episode["test"]:
                    evaluations += 1
                    actual = apply(source, pair["input"])
                    if actual != pair["output"]:
                        raise ValueError(
                            f"protected Racket mismatch for {settings} at label {evaluations}"
                        )
        finally:
            bridge.close()
    return {
        "executed": True,
        "protected": True,
        "all_labels_match": True,
        "evaluations": evaluations,
        "identity": identity,
    }


def build_report(seed: int = 0, execute_racket: bool = False) -> dict[str, Any]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(execute_racket) is not bool:
        raise ValueError("execute_racket must be bool")

    adapter = _load("adapter")
    episodes = [
        (settings, adapter.generate(seed, settings, demos=2, queries=4))
        for settings in SETTINGS
    ]
    canonical = episodes[0][1]
    alternate = episodes[1][1]
    canonical_inputs = [
        pair["input"] for split in ("train", "test") for pair in canonical[split]
    ]
    alternate_inputs = [
        pair["input"] for split in ("train", "test") for pair in alternate[split]
    ]
    if canonical_inputs != alternate_inputs:
        raise ValueError("settings did not receive matched inputs")

    demos = alternate["train"]
    selector_counts = [
        sum(value == 2 for row in pair["input"] for value in row) for pair in demos
    ]
    selected_targets = [5 if count % 2 else 9 for count in selector_counts]
    independent_matches = all(
        pair["output"] == _crop(pair["input"], target)
        for pair, target in zip(demos, selected_targets, strict=True)
    )
    fixed5_mismatches = sum(
        pair["output"] != _crop(pair["input"], 5) for pair in demos
    )
    fixed9_mismatches = sum(
        pair["output"] != _crop(pair["input"], 9) for pair in demos
    )
    if selector_counts != [1, 2] or selected_targets != [5, 9]:
        raise ValueError("minimum teaching set does not expose both selector parities")
    if not independent_matches or fixed5_mismatches == 0 or fixed9_mismatches == 0:
        raise ValueError("minimum teaching set did not reject fixed-target rivals")

    public_raw = public_challenge_bytes(alternate)
    public = json.loads(public_raw)
    query_outputs_hidden = all(set(pair) == {"input"} for pair in public["test"])
    private_metadata_hidden = (
        b"program_solution" not in public_raw and b"crop_policy" not in public_raw
    )
    if not query_outputs_hidden or not private_metadata_hidden:
        raise ValueError("public projection leaked private fields")

    causal_pair = demos[0]
    causal_intermediate = {
        "selector_count": selector_counts[0],
        "selector_parity": "odd",
        "target_color": selected_targets[0],
    }
    counterfactual_output = _crop(causal_pair["input"], 9)
    if counterfactual_output == causal_pair["output"]:
        raise ValueError("wrong-intermediate ablation did not change the final output")

    large = alternate["test"][-1]["input"]
    height, width = len(large), len(large[0])
    boundary_touches = {
        "top": any(value != 0 for value in large[0]),
        "bottom": any(value != 0 for value in large[-1]),
        "left": any(row[0] != 0 for row in large),
        "right": any(row[-1] != 0 for row in large),
    }

    report = {
        "schema": "arcpuzzles-selector-parity-lesson-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": list(SETTINGS),
        "matched_inputs": True,
        "minimum_teaching_set": {
            "selector_counts": selector_counts,
            "selected_targets": selected_targets,
            "fixed_color_5_mismatched_demos": fixed5_mismatches,
            "fixed_color_9_mismatched_demos": fixed9_mismatches,
            "all_alternate_labels_match_independent_crop": independent_matches,
        },
        "public_projection": {
            "sha256": hashlib.sha256(public_raw).hexdigest(),
            "query_outputs_hidden": query_outputs_hidden,
            "private_metadata_hidden": private_metadata_hidden,
        },
        "causal_case": {
            "split": "train",
            "pair_index": 0,
            "intermediate_value": causal_intermediate,
            "counterfactual_changed": counterfactual_output != causal_pair["output"],
            "counterfactual_output": counterfactual_output,
        },
        "large_query": {
            "shape": [height, width],
            "nonzero_cells": sum(value != 0 for row in large for value in row),
            "boundary_touches": boundary_touches,
            "touches_all_boundaries": all(boundary_touches.values()),
        },
        "program_sha256": {
            settings["crop_policy"]: hashlib.sha256(
                adapter.program(settings).encode("utf-8")
            ).hexdigest()
            for settings in SETTINGS
        },
        "racket": _racket_receipt(adapter, episodes) if execute_racket else {"executed": False},
        "limits": (
            "Bounded authored seeds and the two declared programs only; this records "
            "matched inputs, concrete fixed-target counterexamples, a wrong-intermediate "
            "ablation, and optional protected-Racket parity, not universal uniqueness or "
            "measured learning gain."
        ),
    }
    if report["large_query"]["shape"] != [30, 30]:
        raise ValueError("fourth query is not the required 30x30 stress case")
    if report["large_query"]["nonzero_cells"] < 90:
        raise ValueError("30x30 query is too sparse")
    if not report["large_query"]["touches_all_boundaries"]:
        raise ValueError("30x30 query does not touch every boundary")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(seed=args.seed, execute_racket=args.racket)
    raw = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")


if __name__ == "__main__":
    main()
