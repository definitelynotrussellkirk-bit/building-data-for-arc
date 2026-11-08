#!/usr/bin/env python3
"""Bounded Racket-backed audit for the e78f94d8f5bc parametric family.

This tool is intentionally task-local so later agents can rerun the same
public/private projection, finite-rival, matched-input, and count-boundary checks
without reconstructing the authoring logic.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import find_root, public_challenge_bytes

_HOME = Path(__file__).resolve().parent
_PROTO_PATH = _HOME / "prototype.py"
_spec = importlib.util.spec_from_file_location("_e78f94d8f5bc_branch_policy_audit_proto", _PROTO_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - import machinery guard
    raise ImportError(f"could not load {_PROTO_PATH}")
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    bridge.define_grid("g", grid)
    output = bridge.eval_text(expression)
    if (
        type(output) is not list
        or not output
        or type(output[0]) is not list
        or not output[0]
        or any(type(row) is not list or len(row) != len(output[0]) for row in output)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in output for cell in row)
    ):
        raise ValueError("Racket program did not return a rectangular exact-integer ARC grid")
    return output


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _assert_public_projection(episode: dict) -> tuple[dict, list[dict]]:
    public = prototype.public_challenge(episode)
    raw = public_challenge_bytes(public)
    if set(public) != {"train", "test"}:
        raise AssertionError("public challenge contains unexpected top-level fields")
    if any(set(pair) != {"input", "output"} for pair in public["train"]):
        raise AssertionError("public demonstrations must contain only input/output")
    if any(set(pair) != {"input"} for pair in public["test"]):
        raise AssertionError("public queries must contain only input")
    forbidden = (b"branch_policy", b"largest_branch", b"program", b"seed", b"settings")
    if any(token in raw for token in forbidden):
        raise AssertionError("public challenge leaked private metadata")
    turns = [prototype.sequential_turn(episode, index) for index in range(len(episode["test"]))]
    if turns[0] != prototype.public_challenge(episode, query_indices=[0]):
        raise AssertionError("first sequential turn must equal the one-query public challenge")
    for index, turn in enumerate(turns[1:], 1):
        expected = {"test": [{"input": episode["test"][index]["input"]}]}
        if turn != expected:
            raise AssertionError("later turns must reveal only the next query input")
    return public, turns


def _sweep(seed_count: int) -> dict:
    failures: list[dict] = []
    episode_count = 0
    pair_count = 0
    matched_comparisons = 0
    sequential_turns = 0
    for seed in range(seed_count):
        for demos in range(prototype.MIN_DEMOS, prototype.MAX_DEMOS + 1):
            episodes = {
                setting: prototype.build_claimed_episode(seed, setting, demos, 4)
                for setting in prototype.ALLOWED_SETTINGS
            }
            episode_count += len(episodes)
            pair_count += len(episodes) * (demos + 4)
            left, right = (episodes[setting] for setting in prototype.ALLOWED_SETTINGS)
            matched_comparisons += 1
            try:
                if _inputs(left) != _inputs(right):
                    raise AssertionError("settings did not receive matched inputs")
                keys = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(left)]
                if len(keys) != len(set(keys)):
                    raise AssertionError("episode contains duplicate visible inputs")
                for setting, episode in episodes.items():
                    report = prototype.teaching_report(episode)
                    if report["surviving_rivals"]:
                        raise AssertionError(
                            f"{setting} demos leave rivals {report['surviving_rivals']}"
                        )
                    if not report["all_queries_match_selected"]:
                        raise AssertionError(f"{setting} query claim mismatch")
                    _, turns = _assert_public_projection(episode)
                    sequential_turns += len(turns)
                    if (len(episode["test"][-1]["input"]), len(episode["test"][-1]["input"][0])) != (30, 30):
                        raise AssertionError("last query is not 30x30 stress")
            except Exception as exc:  # retain every bounded failure in the report
                failures.append({"seed": seed, "demos": demos, "error": str(exc)})
    return {
        "seed_count": seed_count,
        "demo_counts": [2, 3, 4, 5, 6],
        "episodes": episode_count,
        "pairs": pair_count,
        "matched_input_comparisons": matched_comparisons,
        "sequential_turn_projections": sequential_turns,
        "failures": failures,
    }


def verify(*, seed: int, out_dir: Path | str, sweep_seeds: int = 20) -> dict:
    if type(seed) is not int or not 0 <= seed <= prototype.MAX_SEED:
        raise ValueError("seed must be an exact integer in [0, 2**63-1]")
    if type(sweep_seeds) is not int or not 1 <= sweep_seeds <= 200:
        raise ValueError("sweep_seeds must be an exact integer in 1..200")
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing nonempty evidence directory: {out}")
    public_dir = out / "public"
    episode_dir = out / "private" / "episodes"
    rule_dir = out / "private" / "rules"
    public_dir.mkdir(parents=True, exist_ok=True)
    episode_dir.mkdir(parents=True, exist_ok=True)
    rule_dir.mkdir(parents=True, exist_ok=True)

    episodes = {
        setting: prototype.build_claimed_episode(seed, setting, 3, 4)
        for setting in prototype.ALLOWED_SETTINGS
    }
    left, right = (episodes[setting] for setting in prototype.ALLOWED_SETTINGS)
    matched = _inputs(left) == _inputs(right)
    if not matched:
        raise AssertionError("settings did not receive matched inputs")

    setting_rows = []
    selected_checked = 0
    evaluation_count = 0
    bridge = RacketBridge()
    try:
        for setting, episode in episodes.items():
            selected_program = prototype.program_for(setting)
            pairs = episode["train"] + episode["test"]
            selected_outputs = []
            for pair in pairs:
                output = _execute(bridge, selected_program, pair["input"])
                evaluation_count += 1
                selected_checked += 1
                if output != pair["output"]:
                    raise AssertionError(f"selected Racket output mismatch for {setting}")
                selected_outputs.append(output)

            rivals = []
            for name, rival_program in prototype.rival_programs(setting).items():
                safe_name = name.replace("/", "_")
                (rule_dir / f"{setting}__{safe_name}.rkt").write_text(rival_program, encoding="utf-8")
                outputs = []
                for pair in pairs:
                    outputs.append(_execute(bridge, rival_program, pair["input"]))
                    evaluation_count += 1
                fits_demos = all(
                    output == pair["output"]
                    for output, pair in zip(outputs[: len(episode["train"])], episode["train"], strict=True)
                )
                query_disagreements = [
                    index
                    for index, (output, pair) in enumerate(
                        zip(outputs[len(episode["train"]):], episode["test"], strict=True)
                    )
                    if output != pair["output"]
                ]
                rivals.append(
                    {
                        "name": name,
                        "rejected_by_demonstrations": not fits_demos,
                        "query_disagreements": query_disagreements,
                        "program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
                    }
                )
                if fits_demos:
                    raise AssertionError(f"{setting} demonstrations do not reject rival {name}")

            public, turns = _assert_public_projection(episode)
            raw = public_challenge_bytes(public)
            public_path = public_dir / f"{hashlib.sha256(raw).hexdigest()}.json"
            public_path.write_bytes(raw)
            _write_json(episode_dir / f"{setting}.json", episode)
            (rule_dir / f"{setting}.rkt").write_text(selected_program, encoding="utf-8")
            setting_rows.append(
                {
                    "setting": setting,
                    "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                    "selected_racket_exact": True,
                    "demos_identify_setting": True,
                    "all_queries_checked": True,
                    "public_sha256": public_path.stem,
                    "sequential_turns_checked": len(turns),
                    "rivals": rivals,
                }
            )
    finally:
        bridge.shutdown()

    stress = left["test"][-1]["input"]
    nonwall = sum(cell != 1 for row in stress for cell in row)
    causal_episode = episodes["largest_branch"]
    causal_pair = causal_episode["test"][0]
    causal_program = prototype.program_for("largest_branch")
    counterfactual_program = prototype.rival_programs("largest_branch")[
        "skip_path_largest_zero_region"
    ]
    bridge = RacketBridge()
    try:
        causal_output = _execute(bridge, causal_program, causal_pair["input"])
        counterfactual_output = _execute(bridge, counterfactual_program, causal_pair["input"])
        evaluation_count += 2
    finally:
        bridge.shutdown()
    if causal_output == counterfactual_output:
        raise AssertionError("causal skip-path counterfactual did not change the output")
    causal_case = {
        "settings": {prototype.PARAMETER_NAME: "largest_branch"},
        "program": causal_program,
        "input": causal_pair["input"],
        "output": causal_output,
        "counterfactual_program": counterfactual_program,
        "counterfactual_output": counterfactual_output,
        "intermediate_value": prototype.intermediate_record(causal_pair["input"]),
        "ablation": "skip_a",
    }
    _write_json(out / "private" / "causal-case.json", causal_case)

    sweep = _sweep(sweep_seeds)
    status = "passed" if not sweep["failures"] else "failed"
    report = {
        "schema": "e78f94d8f5bc-branch-policy-verification-v1",
        "status": status,
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "racket": {"backend": "racket", "protected": True},
        "matched_inputs_across_settings": matched,
        "counts": {
            "settings": len(episodes),
            "demonstrations_per_setting": 3,
            "queries_per_setting": 4,
            "selected_racket_checked_pairs": selected_checked,
            "racket_program_evaluations": evaluation_count,
        },
        "maximum_query": {
            "shape": [len(stress), len(stress[0])],
            "nonwall_cells": nonwall,
            "all_quadrants_occupied": all(
                any(stress[r][c] != 1 for r in rows for c in cols)
                for rows, cols in (
                    (range(0, 15), range(0, 15)),
                    (range(0, 15), range(15, 30)),
                    (range(15, 30), range(0, 15)),
                    (range(15, 30), range(15, 30)),
                )
            ),
        },
        "settings": setting_rows,
        "causal_case_path": "private/causal-case.json",
        "sweep": sweep,
        "source_hashes": {
            str(path.relative_to(find_root(__file__))): _sha256_file(path)
            for path in (
                find_root(__file__) / "generators" / prototype.TASK_ID / "generator.py",
                _HOME / "prototype.py",
                _HOME / "adapter.py",
                _HOME / "promotion.json",
                _HOME / "canonical.rkt",
                _HOME / "largest_branch.rkt",
                _HOME / "audit.py",
            )
        },
        "limits": (
            "Finite audit of the declared setting and six executable rivals over one "
            "protected-Racket 3-demo/4-query episode per setting, plus a deterministic "
            f"Python sweep of {sweep_seeds} seeds across demo counts 2..6."
        ),
    }
    _write_json(out / "private" / "verification.json", report)
    if status != "passed":
        raise AssertionError(f"bounded sweep failures: {sweep['failures'][:3]}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sweep-seeds", type=int, default=20)
    args = parser.parse_args()
    report = verify(seed=args.seed, out_dir=args.out, sweep_seeds=args.sweep_seeds)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
