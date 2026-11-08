"""Bounded protected-Racket study for the room-fill policy family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes


HERE = Path(__file__).resolve().parent


def load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_room_fill_probe_impl", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_report(prototype, reference):
    cases = []
    failures = []
    start_calls = reference.calls
    for mode in prototype.MODES:
        for seed in (0, 17):
            for demos in (2, 3, 6):
                settings = {"fill_policy": mode}
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
                except Exception as exc:
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
    causal_settings = {"fill_policy": "strict_majority"}
    causal_state = prototype.strict_majority_state(causal_input)
    correct = reference.apply(prototype.program(causal_settings), causal_input)
    wrong_program = prototype.hypotheses(causal_settings)["first_seed"]
    wrong = reference.apply(wrong_program, causal_input)
    boundary_episode = prototype.generate(0, causal_settings, 2, 4)

    shortcut_cases = {}
    for shortcut, mode in (
        ("seed_count_lookup", "unique_color"),
        ("three_of_four_only", "strict_majority"),
    ):
        settings = {"fill_policy": mode}
        episode = prototype.generate(0, settings, 2, 4)
        fit = prototype.fit_demonstrations(episode["train"], settings, reference)
        source = prototype.hypotheses(settings)[shortcut]
        disagreements = [
            index
            for index, pair in enumerate(episode["test"])
            if reference.apply(source, pair["input"]) != pair["output"]
        ]
        shortcut_cases[shortcut] = {
            "setting": mode,
            "rejected_by_demo": shortcut in fit["rejected_by_demo"],
            "rejected_by_demo_indices": fit["rejected_by_demo"].get(shortcut, []),
            "query_disagreement_indices": disagreements,
        }

    unique_output = prototype.transform(causal_input, {"fill_policy": "unique_color"})
    majority_output = prototype.transform(causal_input, causal_settings)
    collisions = {}
    for cells in prototype._regions(causal_input):
        seed_total = len(prototype._seed_sequence(causal_input, cells))
        unique_fills = any(
            causal_input[r][c] == 0 and unique_output[r][c] != 0 for r, c in cells
        )
        majority_fills = any(
            causal_input[r][c] == 0 and majority_output[r][c] != 0 for r, c in cells
        )
        collisions.setdefault(str(seed_total), set()).add(
            (unique_fills, majority_fills)
        )
    cardinality_collisions = {
        total: [list(outcome) for outcome in sorted(outcomes)]
        for total, outcomes in sorted(collisions.items(), key=lambda item: int(item[0]))
    }
    report = {
        "schema": "room-fill-policy-probe-v1",
        "status": "passed" if not failures else "failed",
        "task_id": prototype.TASK_ID,
        "case_count": len(cases),
        "cases": cases,
        "failures": failures,
        "shortcut_cases": shortcut_cases,
        "cardinality_collisions": cardinality_collisions,
        "causal_case": {
            "input": causal_input,
            "intermediate": causal_state,
            "first_seed_changes_output": correct != wrong,
            "correct_shape": [len(correct), len(correct[0])],
            "counterfactual_shape": [len(wrong), len(wrong[0])],
        },
        "boundary": {
            "query_shapes": [
                [len(pair["output"]), len(pair["output"][0])]
                for pair in boundary_episode["test"]
            ],
            "largest_changed_cells": max(
                sum(a != b for row_a, row_b in zip(pair["input"], pair["output"]) for a, b in zip(row_a, row_b))
                for pair in boundary_episode["test"]
            ),
        },
        "source_sha256": prototype.source_bindings(),
        "racket": reference.bridge.runtime_identity,
        "racket_calls": reference.calls - start_calls,
        "limits": (
            "Finite seeds 0/17, demo counts 2/3/6, four shuffled queries, two "
            "declared settings, and the prototype's named finite rival family."
        ),
    }
    if not report["causal_case"]["first_seed_changes_output"]:
        report["status"] = "failed"
        report["failures"].append(
            {"error": "CausalWitnessFailure", "message": "first-seed ablation matched"}
        )
    for shortcut, result in shortcut_cases.items():
        if not result["rejected_by_demo"]:
            report["status"] = "failed"
            report["failures"].append(
                {"error": "ShortcutTeachingFailure", "message": f"{shortcut} survived two demos"}
            )
        if not result["query_disagreement_indices"]:
            report["status"] = "failed"
            report["failures"].append(
                {"error": "ShortcutWitnessFailure", "message": f"{shortcut} matched every query"}
            )
    if cardinality_collisions.get("5") != [[False, False], [False, True], [True, True]]:
        report["status"] = "failed"
        report["failures"].append(
            {"error": "CardinalityCollisionFailure", "message": "seed total 5 lacks all three actions"}
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
