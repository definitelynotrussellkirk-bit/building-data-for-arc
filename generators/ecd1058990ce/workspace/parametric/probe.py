"""Bounded protected-Racket study for the causal scale-map prototype."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes


HERE = Path(__file__).resolve().parent


def load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_causal_scale_probe_impl", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_report(prototype, reference):
    cases = []
    failures = []
    start_calls = reference.calls
    for mode in prototype.MODES:
        for seed in (0, 17):
            for demos in (2, 3, 6):
                settings = {"scale_mode": mode}
                try:
                    episode = prototype.generate(seed, settings, demos, 4)
                    certificate = prototype.verify_episode(episode, reference)
                    one = prototype.generate(seed, settings, demos, 1)
                    first = {
                        "train": episode["train"],
                        "test": [{"input": episode["test"][0]["input"]}],
                    }
                    if public_challenge_bytes(first) != public_challenge_bytes(one):
                        raise ValueError("first-turn projection changed with requested query count")
                    cases.append(
                        {
                            "settings": settings,
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "survivors": certificate["survivors"],
                            "program_sha256": certificate["program_sha256"]["setting:" + mode],
                            "query_shapes": [
                                [len(pair["output"]), len(pair["output"][0])]
                                for pair in episode["test"]
                            ],
                            "first_turn_prefix_equal": True,
                        }
                    )
                except Exception as exc:  # retained in evidence; CLI fails closed below
                    failures.append(
                        {
                            "settings": settings,
                            "seed": seed,
                            "demos": demos,
                            "error": type(exc).__name__,
                            "message": str(exc),
                        }
                    )

    causal_input = prototype.sample_input(0, "train", 0)
    causal_settings = {"scale_mode": "target_weighted"}
    causal_state = prototype.target_weighted_state(causal_input)
    correct = reference.apply(prototype.program(causal_settings), causal_input)
    wrong_program = prototype.hypotheses(causal_settings)["wrong_order"]
    wrong = reference.apply(wrong_program, causal_input)
    boundary_episode = prototype.generate(0, causal_settings, 2, 4)
    shortcut_program = prototype.hypotheses(causal_settings)["heavy_rows_only"]
    shortcut_fit = prototype.fit_demonstrations(
        boundary_episode["train"], causal_settings, reference
    )
    shortcut_query_disagreements = [
        index
        for index, pair in enumerate(boundary_episode["test"])
        if reference.apply(shortcut_program, pair["input"]) != pair["output"]
    ]
    shortcut_case = {
        "name": "heavy_rows_only",
        "rejected_by_demo_indices": shortcut_fit["rejected_by_demo"].get(
            "heavy_rows_only", []
        ),
        "heavy_rows_only_rejected_by_demo": (
            "heavy_rows_only" in shortcut_fit["rejected_by_demo"]
        ),
        "query_disagreement_indices": shortcut_query_disagreements,
        "heavy_rows_only_query_disagreement": bool(shortcut_query_disagreements),
    }
    report = {
        "schema": "causal-scale-map-probe-v1",
        "status": "passed" if not failures else "failed",
        "task_id": prototype.TASK_ID,
        "case_count": len(cases),
        "cases": cases,
        "failures": failures,
        "shortcut_case": shortcut_case,
        "causal_case": {
            "input": causal_input,
            "row_scales": causal_state["row_scales"],
            "original_column_counts": causal_state["original_column_counts"],
            "intermediate_column_counts": causal_state["intermediate_column_counts"],
            "selected_column": causal_state["selected_column"],
            "wrong_order_changes_output": correct != wrong,
            "correct_shape": [len(correct), len(correct[0])],
            "counterfactual_shape": [len(wrong), len(wrong[0])],
        },
        "boundary": {
            "target_weighted_query_shapes": [
                [len(pair["output"]), len(pair["output"][0])]
                for pair in boundary_episode["test"]
            ],
            "largest_distinct_colors": len(
                {cell for row in boundary_episode["test"][0]["output"] for cell in row}
            ),
        },
        "source_sha256": prototype.source_bindings(),
        "racket": reference.bridge.runtime_identity,
        "racket_calls": reference.calls - start_calls,
        "limits": (
            "Finite seeds 0/17, demo counts 2/3/6, four queries, two declared "
            "settings, and the prototype's named finite rival family."
        ),
    }
    if not report["causal_case"]["wrong_order_changes_output"]:
        report["status"] = "failed"
        report["failures"].append({"error": "CausalWitnessFailure", "message": "wrong-order output matched"})
    if not shortcut_case["heavy_rows_only_rejected_by_demo"]:
        report["status"] = "failed"
        report["failures"].append(
            {"error": "ShortcutTeachingFailure", "message": "heavy-rows-only survived two demos"}
        )
    if not shortcut_case["heavy_rows_only_query_disagreement"]:
        report["status"] = "failed"
        report["failures"].append(
            {"error": "ShortcutWitnessFailure", "message": "heavy-rows-only matched every query"}
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    prototype = load_prototype()
    with prototype.Reference() as reference:
        report = build_report(prototype, reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "case_count": report["case_count"],
        "failures": len(report["failures"]),
        "racket_calls": report["racket_calls"],
        "output": str(args.out),
    }, sort_keys=True))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
