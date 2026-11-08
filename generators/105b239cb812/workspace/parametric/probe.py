#!/usr/bin/env python3
"""Protected-Racket authoring probe for the 105b239cb812 parametric family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "105b239cb812"
STEP_A = "Compare transformed complete panel A against panel B to infer the unique A-to-B transform."
INTERMEDIATE = "The input-dependent inferred transform name (for the retained witness, cw)."
STEP_B = (
    "Apply that transform directly to panel C for the direct setting, or apply its inverse "
    "for the inverse setting."
)
WHY_B_DEPENDS_ON_A = (
    "The output transform cannot be selected before the A-to-B comparison returns its unique name; "
    "substituting 180 for the inferred cw transform changes the final grid."
)


def _load(name: str):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("adapter")
PROTOTYPE = _load("prototype")


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class Evaluator:
    def __init__(self) -> None:
        self.bridge = RacketBridge()
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise ValueError("probe requires a live protected Racket backend")
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
        self._wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        if program not in self._wrapped:
            self._wrapped[program] = wrap_rule(program)
        result = self.bridge.eval_text(f"({self._wrapped[program]} {_grid_literal(grid)})")
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


def _sha_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(raw, encoding="utf-8")
    temporary.replace(path)


def _public_projection(episode: dict[str, Any], application: str) -> dict[str, Any]:
    public_source = {"train": episode["train"], "test": episode["test"]}
    raw = public_challenge_bytes(public_source)
    parsed = json.loads(raw)
    changed_private = copy.deepcopy(public_source)
    changed_private["test"][0]["output"][0][0] = (
        changed_private["test"][0]["output"][0][0] + 1
    ) % 10
    turn = PROTOTYPE.public_turn(episode, 0)
    turn_raw = public_challenge_bytes(turn)
    direct_turn_raw = public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][0]]}
    )
    return {
        "public_id": public_challenge_id(public_source),
        "public_sha256": hashlib.sha256(raw).hexdigest(),
        "query_answers_hidden": all(set(pair) == {"input"} for pair in parsed["test"]),
        "private_mutation_id_stable": public_challenge_id(changed_private)
        == public_challenge_id(public_source),
        "settings_hidden": b"application" not in raw and application.encode() not in raw,
        "program_hidden": b"program_solution" not in raw and b"rule!" not in raw,
        "first_turn_matches_single_projection": turn_raw == direct_turn_raw,
        "first_turn_query_count": len(json.loads(turn_raw)["test"]),
        "future_queries_hidden_in_first_turn": len(json.loads(turn_raw)["test"]) == 1,
        "first_turn_sha256": hashlib.sha256(turn_raw).hexdigest(),
    }


def _job(evaluator: Evaluator, seed: int, demos: int, application: str) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = {"application": application}
    episode = ADAPTER.generate(seed, settings, demos, 4)
    candidate_programs = {
        "direct": ADAPTER.program({"application": "direct"}),
        "inverse": ADAPTER.program({"application": "inverse"}),
        "copy_c": PROTOTYPE.fixed_transform_program("id"),
        "fixed_cw": PROTOTYPE.fixed_transform_program("cw"),
        "fixed_ccw": PROTOTYPE.fixed_transform_program("ccw"),
        "fixed_180": PROTOTYPE.fixed_transform_program("180"),
        "local_crop_direct": PROTOTYPE.local_crop_program("direct"),
        "local_crop_inverse": PROTOTYPE.local_crop_program("inverse"),
    }

    demo_outputs: dict[str, list[list[list[int]]]] = {}
    survivors = []
    for name, program in candidate_programs.items():
        outputs = [evaluator.apply(program, pair["input"]) for pair in episode["train"]]
        demo_outputs[name] = outputs
        if all(
            output == pair["output"]
            for output, pair in zip(outputs, episode["train"], strict=True)
        ):
            survivors.append(name)
    if survivors != [application]:
        raise ValueError(
            f"demos did not identify {application}: survivors={survivors}, seed={seed}, demos={demos}"
        )

    selected_program = candidate_programs[application]
    selected_outputs = [
        evaluator.apply(selected_program, pair["input"])
        for pair in episode["train"] + episode["test"]
    ]
    labels = [pair["output"] for pair in episode["train"] + episode["test"]]
    label_matches = [
        output == label for output, label in zip(selected_outputs, labels, strict=True)
    ]
    if not all(label_matches):
        raise ValueError("Python labels differ from protected Racket")

    metrics = [
        PROTOTYPE.input_metrics(pair["input"])
        for pair in episode["train"] + episode["test"]
    ]
    public_projection = _public_projection(episode, application)
    if not all(
        public_projection[key]
        for key in (
            "query_answers_hidden",
            "private_mutation_id_stable",
            "settings_hidden",
            "program_hidden",
            "first_turn_matches_single_projection",
            "future_queries_hidden_in_first_turn",
        )
    ):
        raise ValueError(f"public projection check failed: {public_projection}")

    row = {
        "seed": seed,
        "demos": demos,
        "queries": 4,
        "application": application,
        "program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
        "survivors": survivors,
        "rivals_refuted": sorted(set(candidate_programs) - set(survivors)),
        "all_python_labels_match_racket": all(label_matches),
        "per_query_racket_match": label_matches[demos:],
        "input_sha256": [
            _sha_json(pair["input"]) for pair in episode["train"] + episode["test"]
        ],
        "demo_shapes": [m["input_shape"] for m in metrics[:demos]],
        "query_shapes": [m["input_shape"] for m in metrics[demos:]],
        "largest_query_metrics": metrics[-1],
        "public_projection": public_projection,
    }
    private = {
        "episode": episode,
        "candidate_programs": candidate_programs,
        "demo_outputs": demo_outputs,
    }
    return row, private


def build_report(
    seeds: list[int],
    demo_counts: list[int],
    source_binding: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not seeds or any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seeds):
        raise ValueError("seeds must be nonempty exact integers in range")
    if not demo_counts or any(type(count) is not int or not 2 <= count <= 6 for count in demo_counts):
        raise ValueError("demo counts must be nonempty exact integers in 2..6")

    evaluator = Evaluator()
    jobs = []
    direct_private = None
    try:
        for demos in demo_counts:
            for seed in seeds:
                for application in PROTOTYPE.APPLICATIONS:
                    row, private = _job(evaluator, seed, demos, application)
                    jobs.append(row)
                    if direct_private is None and application == "direct":
                        direct_private = private

        assert direct_private is not None
        large_pair = direct_private["episode"]["test"][-1]
        correct_program = direct_private["candidate_programs"]["direct"]
        wrong_program = PROTOTYPE.fixed_transform_program("180")
        correct_output = evaluator.apply(correct_program, large_pair["input"])
        wrong_output = evaluator.apply(wrong_program, large_pair["input"])
        inferred = PROTOTYPE.infer_transform(large_pair["input"])
        if inferred != "cw" or correct_output == wrong_output:
            raise ValueError("causal transform witness did not change the final output")

        witness = {
            "schema": "arcpuzzles-sequential-dependency-witness-v1",
            "task_id": TASK_ID,
            "source_binding": copy.deepcopy(source_binding),
            "racket": {"backend": "racket", "protected": True},
            "step_a": STEP_A,
            "intermediate": INTERMEDIATE,
            "step_b": STEP_B,
            "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
            "cases": [
                {
                    "input": large_pair["input"],
                    "settings": {"application": "direct"},
                    "intermediate_value": {
                        "inferred_transform": inferred,
                        "applied_transform": inferred,
                    },
                    "program": correct_program,
                    "output": correct_output,
                    "ablation": "wrong_intermediate",
                    "counterfactual_intermediate_value": {
                        "inferred_transform": "180",
                        "applied_transform": "180",
                    },
                    "counterfactual_program": wrong_program,
                    "counterfactual_output": wrong_output,
                }
            ],
        }

        report = {
            "schema": f"{TASK_ID}-parametric-authoring-v1",
            "task_id": TASK_ID,
            "family_version": PROTOTYPE.FAMILY_VERSION,
            "parameters": {"application": list(PROTOTYPE.APPLICATIONS)},
            "default": {"application": "direct"},
            "limits": {"demos": list(PROTOTYPE.DEMO_LIMITS), "queries": [4, 4]},
            "seeds": seeds,
            "demo_counts": demo_counts,
            "jobs": jobs,
            "racket": evaluator.identity,
            "racket_evaluations": evaluator.evaluations,
            "source_sha256": {
                name: _sha_file(HERE / name)
                for name in ("adapter.py", "prototype.py", "promotion.json", "probe.py")
            },
            "self_review_scope": (
                "Finite programs only: direct, inverse, copy-C, fixed clockwise, "
                "fixed counterclockwise, fixed 180-degree application, and crop-local direct/inverse transforms."
            ),
            "size_limit": (
                "9x29 is the lawful maximum under square panels and canonical width=3*rows+2; "
                "10 rows would require width 32, so exact 30x30 is incompatible with this grammar."
            ),
            "causal_witness_sha256": _sha_json(witness),
            "training_admitted": False,
        }
        return report, witness
    finally:
        evaluator.close()


def _qualification_source_binding(path: Path) -> dict[str, Any]:
    qualification = json.loads(path.read_text(encoding="utf-8"))
    binding = qualification.get("source_binding")
    if (
        qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
        or type(binding) is not dict
    ):
        raise ValueError("qualification must be a qualified native report for this task")
    return copy.deepcopy(binding)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", action="append", type=int, dest="demo_counts")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    args = parser.parse_args()
    seeds = args.seeds if args.seeds is not None else [5, 23]
    demo_counts = args.demo_counts if args.demo_counts is not None else [2, 6]
    source_binding = _qualification_source_binding(args.qualification)
    report, witness = build_report(seeds, demo_counts, source_binding)
    _write(args.out, report)
    _write(args.witness, witness)
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "jobs": len(report["jobs"]),
                "racket_evaluations": report["racket_evaluations"],
                "out": str(args.out),
                "witness": str(args.witness),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
