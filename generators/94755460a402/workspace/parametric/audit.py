"""Bounded teaching, privacy, boundary, and protected-Racket audit."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "94755460a402"
SETTINGS = (
    {"command_source": "header"},
    {"command_source": "selected_marker"},
)


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "_audit_command_source_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expect_error(fn, name: str) -> dict[str, str]:
    try:
        fn()
    except Exception as error:  # evidence records exact rejected class/message
        return {"name": name, "error": type(error).__name__, "message": str(error)}
    raise ValueError(f"negative check unexpectedly succeeded: {name}")


def _racket_receipt(prototype: Any, episodes: list[tuple[dict[str, str], dict[str, Any]]]):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    root = find_root(__file__)
    runtime = root / "shared/runtime"
    evaluations = 0
    causal = None
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for settings, episode in episodes:
                source = prototype.program(settings)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = apply(source, pair["input"])
                        evaluations += 1
                        if actual != pair["output"]:
                            raise ValueError(
                                f"Racket label mismatch for {settings} {split}[{index}]"
                            )
            alt_settings = {"command_source": "selected_marker"}
            alt_episode = next(ep for settings, ep in episodes if settings == alt_settings)
            pair = alt_episode["train"][0]
            info = prototype.analyze(pair["input"])
            intended_program = prototype.program(alt_settings)
            counterfactual_program = prototype.counterfactual_program("skip_a")
            intended = apply(intended_program, pair["input"])
            skipped = apply(counterfactual_program, pair["input"])
            evaluations += 2
            if intended == skipped:
                raise ValueError("skip-A counterfactual did not change final output")
            causal = {
                "seed": 0,
                "split": "train",
                "pair_index": 0,
                "input": pair["input"],
                "settings": alt_settings,
                "intermediate_value": info["selected_marker"],
                "header_command": info["header_command"],
                "program": intended_program,
                "program_sha256": hashlib.sha256(intended_program.encode()).hexdigest(),
                "output": intended,
                "counterfactual_program": counterfactual_program,
                "counterfactual_program_sha256": hashlib.sha256(
                    counterfactual_program.encode()
                ).hexdigest(),
                "counterfactual_output": skipped,
                "ablation": "skip_a",
            }
        finally:
            bridge.close()
    return {
        "executed": True,
        "all_labels_match": True,
        "evaluations": evaluations,
        "identity": identity,
        "causal_case": causal,
    }


def build_report(seeds: list[int], execute_racket: bool) -> dict[str, Any]:
    if (type(seeds) is not list or not seeds
            or any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seeds)
            or len(set(seeds)) != len(seeds)):
        raise ValueError("seeds must be a nonempty list of distinct exact integers")
    if type(execute_racket) is not bool:
        raise ValueError("execute_racket must be bool")
    prototype = _load()
    episodes: list[tuple[dict[str, str], dict[str, Any]]] = []
    teaching = []
    shapes = set()
    frame_counts = set()
    selected_indices = set()
    header_commands = set()
    marker_commands = set()
    duplicate_cases = 0
    public_checks = []

    for seed in seeds:
        by_setting = []
        for settings in SETTINGS:
            episode = prototype.generate(seed, settings, demos=2, queries=4)
            episodes.append((settings, episode))
            by_setting.append(episode)
            teaching_report = prototype.teaching_check(episode)
            if not teaching_report["ok"]:
                raise ValueError(f"teaching failure for seed {seed}, {settings}: {teaching_report}")
            teaching.append({"seed": seed, "settings": settings, **teaching_report})
            for pair in episode["train"] + episode["test"]:
                info = prototype.analyze(pair["input"])
                shapes.add((len(pair["input"]), len(pair["input"][0])))
                frame_counts.add(info["frame_count"])
                selected_indices.add(info["selected_index"])
                header_commands.add(info["header_command"])
                marker_commands.add(info["selected_marker"])
                duplicate_cases += len(info["matching_indices"]) > 1
            public = prototype.public_challenge(episode)
            raw = public_challenge_bytes(public)
            if b"command_source" in raw or b"rule!" in raw:
                raise ValueError("private settings/program leaked into public projection")
            if any(set(pair) != {"input"} for pair in public["test"]):
                raise ValueError("public query projection leaked a private label")
            first_turn = prototype.public_turn(episode, 0)
            one_query = {**episode, "test": episode["test"][:1]}
            if first_turn != prototype.public_turn(one_query, 0):
                raise ValueError("first-turn content changed under one-query stopping")
            mutated = deepcopy(episode)
            mutated["test"][0]["output"] = [[9]]
            mutated["program_solution"] = "changed private program"
            mutated["private"] = {"command_source": "other"}
            if public_challenge_id(episode) != public_challenge_id(mutated):
                raise ValueError("public ID depends on private query labels/settings/program")
            public_checks.append({
                "seed": seed,
                "settings": settings,
                "public_id": public_challenge_id(episode),
                "public_bytes": len(raw),
                "first_turn_sha256": hashlib.sha256(
                    public_challenge_bytes(first_turn)
                ).hexdigest(),
            })
        inputs = [
            [pair["input"] for split in ("train", "test") for pair in episode[split]]
            for episode in by_setting
        ]
        if inputs[0] != inputs[1]:
            raise ValueError(f"settings did not receive matched inputs for seed {seed}")

    stress = prototype.generate(
        seeds[-1], {"command_source": "selected_marker"}, demos=3, queries=4
    )["test"][3]["input"]
    stress_info = prototype.analyze(stress)
    boundary = {
        "top": any(value for value in stress[0]),
        "bottom": any(value for value in stress[-1]),
        "left": any(row[0] for row in stress),
        "right": any(row[-1] for row in stress),
    }
    if (len(stress) != 30 or len(stress[0]) != 30 or stress_info["frame_count"] != 4
            or not all(boundary.values())):
        raise ValueError("large query lost its exact 30x30 four-boundary stress contract")

    negative_checks = [
        _expect_error(
            lambda: prototype.program({"command_source": "selected_marker", "extra": True}),
            "extra_setting_key",
        ),
        _expect_error(
            lambda: prototype.generate(0, {"command_source": "header"}, 2, 3),
            "short_query_count",
        ),
        _expect_error(
            lambda: prototype.public_turn(
                prototype.generate(0, {"command_source": "header"}, 2, 4), 4
            ),
            "future_query_index",
        ),
    ]

    racket = _racket_receipt(prototype, episodes) if execute_racket else {"executed": False}
    return {
        "schema": "arcpuzzles-command-source-audit-v1",
        "task_id": TASK_ID,
        "seeds": seeds,
        "settings": list(SETTINGS),
        "episode_counts": {"demos": 2, "queries": 4, "episodes": len(episodes)},
        "matched_inputs_across_settings": True,
        "teaching": teaching,
        "coverage": {
            "input_shapes": [list(shape) for shape in sorted(shapes)],
            "frame_counts": sorted(frame_counts),
            "selected_indices": sorted(selected_indices),
            "header_commands": sorted(header_commands),
            "selected_marker_commands": sorted(marker_commands),
            "duplicate_selector_pair_occurrences": duplicate_cases,
            "stress": {
                "shape": [30, 30],
                "frame_count": stress_info["frame_count"],
                "selected_crop_shape": [
                    len(stress_info["cropped"]), len(stress_info["cropped"][0])
                ],
                "nonzero_cells": sum(value != 0 for row in stress for value in row),
                "boundary_contacts": boundary,
            },
        },
        "public_projection": {
            "all_queries_masked": True,
            "private_field_invariance": True,
            "first_turn_stable": True,
            "checks": public_checks,
        },
        "negative_checks": negative_checks,
        "program_sha256": {
            settings["command_source"]: hashlib.sha256(
                prototype.program(settings).encode()
            ).hexdigest()
            for settings in SETTINGS
        },
        "racket": racket,
        "limits": (
            "Bounded to the declared settings, finite rivals, named seeds, and generated grammar; "
            "not universal uniqueness, owner acceptance, measured learning benefit, or training admission."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(args.seed or [0, 17], args.racket)
    raw = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")


if __name__ == "__main__":
    main()
