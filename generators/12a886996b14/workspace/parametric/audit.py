#!/usr/bin/env python3
"""Bounded protected-Racket authoring audit for 12a886996b14."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_ID = "12a886996b14"
FINISHES = ("translate_only", "cue_payload")
WITNESS_SCHEMA = "arcpuzzles-sequential-dependency-witness-v1"
STEP_A = "Infer the input-derived red-to-green displacement and translate the yellow object by that vector."
INTERMEDIATE = (
    "The translated yellow footprint and the unique cue color orthogonally adjacent to that destination footprint."
)
STEP_B = (
    "Select the remote payload having that cue color, recolor the payload cyan, and retain the translated yellow object."
)
WHY_B_DEPENDS_ON_A = (
    "The scene also contains source-footprint and green-marker cue decoys; the correct cue and payload "
    "cannot be selected until Step A determines the translated destination footprint."
)


def _load(name: str):
    path = HERE / f"{name}.py"
    module_name = f"_audit_{TASK_ID}_{name}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("adapter")
PROTOTYPE = _load("prototype")


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_raw(value)).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, value: Any) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(
        (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    )
    temporary.replace(path)


def build_sequential_witness(
    source_binding: dict[str, Any], raw_case: dict[str, Any]
) -> dict[str, Any]:
    """Normalize one replayed counterfactual into the owner-admission schema."""
    if not isinstance(source_binding, dict) or source_binding.get("task_id") != TASK_ID:
        raise ValueError("source binding must identify this task")
    required = {
        "settings",
        "intermediate_value",
        "input",
        "output",
        "counterfactual_output",
        "ablation",
        "program",
        "counterfactual_program",
    }
    if not isinstance(raw_case, dict) or not required <= set(raw_case):
        raise ValueError("raw causal case is incomplete")
    if raw_case.get("ablation") not in {"skip_a", "wrong_intermediate", "wrong_order"}:
        raise ValueError("unsupported causal ablation")
    if raw_case["output"] == raw_case["counterfactual_output"]:
        raise ValueError("counterfactual must change the final output")
    return {
        "schema": WITNESS_SCHEMA,
        "task_id": TASK_ID,
        "source_binding": deepcopy(source_binding),
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
        "cases": [deepcopy(raw_case)],
        "verification_status": "reviewer_replayed",
        "limits": (
            "One bounded protected-Racket counterfactual; this demonstrates the named dependency "
            "for the retained case, not universal algorithmic depth."
        ),
    }


def _load_source_binding(path: Path) -> dict[str, Any]:
    qualification = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(qualification, dict)
        or qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
        or not isinstance(qualification.get("source_binding"), dict)
    ):
        raise ValueError("qualification must be a qualified native receipt for this task")
    return qualification["source_binding"]


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class Evaluator:
    def __init__(self) -> None:
        self.bridge = RacketBridge()
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise ValueError("audit requires a live protected Racket backend")
        self.identity = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }
        self.wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        if program not in self.wrapped:
            self.wrapped[program] = wrap_rule(program)
        result = self.bridge.eval_text(f"({self.wrapped[program]} {_literal(grid)})")
        self.evaluations += 1
        if (
            type(result) is not list
            or not result
            or type(result[0]) is not list
            or not result[0]
            or any(
                type(row) is not list
                or len(row) != len(result[0])
                or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                for row in result
            )
        ):
            raise ValueError("Racket program returned a non-grid")
        return result

    def close(self) -> None:
        self.bridge.close()


def _public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    visible = PROTOTYPE.public_turn(episode, 0)
    payload = public_challenge_bytes(visible)
    parsed = json.loads(payload)
    changed = deepcopy(episode)
    changed["settings"] = {"finish": "translate_only"}
    changed["seed"] = -1
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[0]]
    if len(changed["test"]) > 1:
        changed["test"][1]["input"] = [[9]]
    changed_payload = public_challenge_bytes(PROTOTYPE.public_turn(changed, 0))
    direct = public_challenge_bytes(
        {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    )
    return {
        "public_id": public_challenge_id(visible),
        "public_sha256": hashlib.sha256(payload).hexdigest(),
        "query_answers_hidden": all(set(pair) == {"input"} for pair in parsed["test"]),
        "future_queries_hidden": len(parsed["test"]) == 1,
        "private_mutation_stable": changed_payload == payload,
        "settings_hidden": b"finish" not in payload and b"cue_payload" not in payload,
        "program_hidden": b"rule!" not in payload and b"program_solution" not in payload,
        "first_turn_matches_direct_projection": payload == direct,
    }


def _job(evaluator: Evaluator, seed: int, demos: int, finish: str) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = {"finish": finish}
    episode = ADAPTER.generate(seed, settings, demos, 4)
    programs = {name: ADAPTER.program({"finish": name}) for name in FINISHES}
    declared_survivors = []
    for name, program in programs.items():
        outputs = [evaluator.apply(program, pair["input"]) for pair in episode["train"]]
        if all(output == pair["output"] for output, pair in zip(outputs, episode["train"], strict=True)):
            declared_survivors.append(name)
    if declared_survivors != [finish]:
        raise ValueError(
            f"demonstrations do not identify {finish}: survivors={declared_survivors}, seed={seed}, demos={demos}"
        )
    actual = [
        evaluator.apply(programs[finish], pair["input"])
        for pair in episode["train"] + episode["test"]
    ]
    claimed = [pair["output"] for pair in episode["train"] + episode["test"]]
    matches = [left == right for left, right in zip(actual, claimed, strict=True)]
    if not all(matches):
        raise ValueError("Python label differs from protected Racket")
    teaching = PROTOTYPE.teaching_check(episode, settings)
    if teaching["declared_survivors"] != [finish] or teaching["harmful_survivors"]:
        raise ValueError(f"finite teaching audit failed: {teaching}")
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    if len({_sha(grid) for grid in inputs}) != len(inputs):
        raise ValueError("episode contains duplicate inputs")
    metrics = [PROTOTYPE.intermediate(grid) for grid in inputs]
    public = _public_projection(episode)
    required_public = (
        "query_answers_hidden",
        "future_queries_hidden",
        "private_mutation_stable",
        "settings_hidden",
        "program_hidden",
        "first_turn_matches_direct_projection",
    )
    if not all(public[key] for key in required_public):
        raise ValueError(f"public projection failed: {public}")
    if metrics[-1]["shape"] != [30, 30]:
        raise ValueError("fourth query is not 30x30")
    return (
        {
            "seed": seed,
            "demos": demos,
            "queries": 4,
            "finish": finish,
            "program_sha256": hashlib.sha256(programs[finish].encode()).hexdigest(),
            "declared_survivors": declared_survivors,
            "tested_survivors": teaching["survivors"],
            "tested_harmful_survivors": teaching["harmful_survivors"],
            "tested_rivals": teaching["tested_rivals"],
            "all_python_labels_match_racket": all(matches),
            "per_query_racket_match": matches[demos:],
            "input_sha256": [_sha(grid) for grid in inputs],
            "demo_shapes": [item["shape"] for item in metrics[:demos]],
            "query_shapes": [item["shape"] for item in metrics[demos:]],
            "demo_destination_cue_colors": [item["destination_cue_color"] for item in metrics[:demos]],
            "largest_query_nonzero_cells": sum(cell != 0 for row in inputs[-1] for cell in row),
            "public_projection": public,
        },
        {"settings": settings, "episode": episode},
    )


def run(
    seeds: list[int], demo_counts: list[int], source_binding: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    evaluator = Evaluator()
    try:
        rows: list[dict[str, Any]] = []
        private: list[dict[str, Any]] = []
        for seed in seeds:
            for demos in demo_counts:
                paired = []
                for finish in FINISHES:
                    row, hidden = _job(evaluator, seed, demos, finish)
                    rows.append(row)
                    private.append(hidden)
                    paired.append(hidden["episode"])
                left_inputs = [pair["input"] for pair in paired[0]["train"] + paired[0]["test"]]
                right_inputs = [pair["input"] for pair in paired[1]["train"] + paired[1]["test"]]
                if left_inputs != right_inputs:
                    raise ValueError("input sampling depends on private setting")

        relay = next(
            item
            for item in private
            if item["settings"] == {"finish": "cue_payload"}
            and len(item["episode"]["train"]) == 3
            and item["episode"]["train"]
        )
        pair = relay["episode"]["train"][0]
        correct_program = ADAPTER.program({"finish": "cue_payload"})
        wrong_program = (HERE / "source_cue_payload.rkt").read_text(encoding="utf-8")
        output = evaluator.apply(correct_program, pair["input"])
        wrong_output = evaluator.apply(wrong_program, pair["input"])
        if output == wrong_output:
            raise ValueError("wrong-order causal counterfactual did not change final output")
        info = PROTOTYPE.intermediate(pair["input"])
        raw_case = {
            "settings": {"finish": "cue_payload"},
            "intermediate_value": {
                "translated_yellow": info["translated_yellow"],
                "destination_cue_color": info["destination_cue_color"],
            },
            "input": pair["input"],
            "output": output,
            "counterfactual_output": wrong_output,
            "ablation": "wrong_order",
            "program": correct_program,
            "counterfactual_program": wrong_program,
            "source_cue_color": info["source_cue_color"],
            "differing_cells": sum(
                left != right
                for left_row, right_row in zip(output, wrong_output, strict=True)
                for left, right in zip(left_row, right_row, strict=True)
            ),
            "verification_status": "reviewer_replayed",
        }
        case = build_sequential_witness(source_binding, raw_case)
        source_paths = [
            HERE / "adapter.py",
            HERE / "audit.py",
            HERE / "prototype.py",
            HERE / "promotion.json",
            HERE / "canonical.rkt",
            HERE / "cue_payload.rkt",
            HERE / "source_cue_payload.rkt",
            HERE / "green_cue_payload.rkt",
        ]
        report = {
            "schema": "12a886996b14-parametric-authoring-v1",
            "task_id": TASK_ID,
            "settings": [{"finish": name} for name in FINISHES],
            "seeds": seeds,
            "demo_counts": demo_counts,
            "queries": 4,
            "matched_inputs_across_settings": True,
            "jobs": rows,
            "racket": evaluator.identity,
            "racket_evaluations": evaluator.evaluations,
            "source_files": [
                {"path": path.name, "sha256": _sha_file(path)} for path in sorted(source_paths)
            ],
            "causal_case_sha256": _sha(case),
            "limits": (
                "Bounded protected-Racket replay over the listed seeds/demo counts and finite rivals; "
                "not universal uniqueness, owner acceptance, or training admission."
            ),
        }
        return report, case
    finally:
        evaluator.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--demos", action="append", type=int)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args(argv)
    seeds = args.seed or [0, 17, 97]
    demo_counts = args.demos or [2, 3, 6]
    for seed in seeds:
        _ = PROTOTYPE._integer("seed", seed, 0, 2**63 - 1)
    for demos in demo_counts:
        _ = PROTOTYPE._integer("demos", demos, 2, 6)
    source_binding = _load_source_binding(args.qualification)
    report, case = run(seeds, demo_counts, source_binding)
    _write_new(args.out, report)
    _write_new(args.case, case)
    print(json.dumps({
        "status": "passed",
        "jobs": len(report["jobs"]),
        "racket_evaluations": report["racket_evaluations"],
        "report": str(args.out),
        "case": str(args.case),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
