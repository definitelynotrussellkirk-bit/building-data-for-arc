#!/usr/bin/env python3
"""Protected-Racket authoring probe for the 083ba0fc4534 parametric family."""
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
TASK_ID = "083ba0fc4534"
STEP_A = "Discover the two full-height color-5 divider columns from the input."
INTERMEDIATE = (
    "The discovered divider pair and derived panel width/aligned lookup offsets "
    "(for the retained 30x29 witness, [9,19])."
)
STEP_B = (
    "Use those offsets to read the three aligned panel cells and apply the episode's "
    "majority or unanimity agreement predicate."
)
WHY_B_DEPENDS_ON_A = (
    "The offsets and output width cannot be chosen before the input-dependent divider "
    "positions are known; fixed [4,9] dividers read different cells and change both "
    "width and content."
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


def _public_projection(episode: dict[str, Any], agreement: str) -> dict[str, Any]:
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
        "settings_hidden": b"agreement" not in raw and agreement.encode() not in raw,
        "program_hidden": b"program_solution" not in raw and b"rule!" not in raw,
        "first_turn_matches_single_projection": turn_raw == direct_turn_raw,
        "first_turn_query_count": len(json.loads(turn_raw)["test"]),
        "future_queries_hidden_in_first_turn": len(json.loads(turn_raw)["test"]) == 1,
        "first_turn_sha256": hashlib.sha256(turn_raw).hexdigest(),
    }


def _job(evaluator: Evaluator, seed: int, demos: int, agreement: str) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = {"agreement": agreement}
    episode = ADAPTER.generate(seed, settings, demos, 4)
    candidate_programs = {
        "majority": ADAPTER.program({"agreement": "majority"}),
        "unanimous": ADAPTER.program({"agreement": "unanimous"}),
        "exactly_two": PROTOTYPE.EXACTLY_TWO_PROGRAM,
        "occupancy": PROTOTYPE.OCCUPANCY_PROGRAM,
        "fixed_dividers": PROTOTYPE.fixed_divider_program(agreement),
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
    if survivors != [agreement]:
        raise ValueError(
            f"demos did not identify {agreement}: survivors={survivors}, seed={seed}, demos={demos}"
        )

    selected_program = candidate_programs[agreement]
    selected_outputs = [
        evaluator.apply(selected_program, pair["input"])
        for pair in episode["train"] + episode["test"]
    ]
    labels = [pair["output"] for pair in episode["train"] + episode["test"]]
    label_matches = [output == label for output, label in zip(selected_outputs, labels, strict=True)]
    if not all(label_matches):
        raise ValueError("Python labels differ from protected Racket")

    metrics = [PROTOTYPE.input_metrics(pair["input"]) for pair in episode["train"] + episode["test"]]
    public_projection = _public_projection(episode, agreement)
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
        "agreement": agreement,
        "program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
        "survivors": survivors,
        "rivals_refuted": sorted(set(candidate_programs) - set(survivors)),
        "all_python_labels_match_racket": all(label_matches),
        "per_query_racket_match": label_matches[demos:],
        "input_sha256": [
            _sha_json(pair["input"]) for pair in episode["train"] + episode["test"]
        ],
        "demo_shapes": [[m["height"], m["width"]] for m in metrics[:demos]],
        "query_shapes": [[m["height"], m["width"]] for m in metrics[demos:]],
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
    majority_private = None
    try:
        for demos in demo_counts:
            for seed in seeds:
                for agreement in PROTOTYPE.AGREEMENTS:
                    row, private = _job(evaluator, seed, demos, agreement)
                    jobs.append(row)
                    if majority_private is None and agreement == "majority":
                        majority_private = private

        assert majority_private is not None
        large_pair = majority_private["episode"]["test"][-1]
        correct_program = majority_private["candidate_programs"]["majority"]
        skip_program = PROTOTYPE.fixed_divider_program("majority")
        correct_output = evaluator.apply(correct_program, large_pair["input"])
        skip_output = evaluator.apply(skip_program, large_pair["input"])
        correct_dividers = list(PROTOTYPE.divider_columns(large_pair["input"]))
        if correct_dividers != [9, 19] or correct_output == skip_output:
            raise ValueError("causal divider witness did not change the final output")

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
                    "settings": {"agreement": "majority"},
                    "intermediate_value": {
                        "dividers": correct_dividers,
                        "panel_width": correct_dividers[0],
                        "aligned_offsets": [0, correct_dividers[0] + 1, correct_dividers[1] + 1],
                    },
                    "program": correct_program,
                    "output": correct_output,
                    "ablation": "skip_a",
                    "counterfactual_program": skip_program,
                    "counterfactual_output": skip_output,
                }
            ],
        }

        report = {
            "schema": f"{TASK_ID}-parametric-authoring-v1",
            "task_id": TASK_ID,
            "family_version": PROTOTYPE.FAMILY_VERSION,
            "parameters": {"agreement": list(PROTOTYPE.AGREEMENTS)},
            "default": {"agreement": "majority"},
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
                "Finite programs only: the two declared settings, exactly-two agreement, "
                "color-blind occupancy, and a fixed-divider skip-A rival."
            ),
            "size_limit": (
                "30x29 is the maximum lawful large input under three equal vertical panels plus two dividers; "
                "exact 30x30 is incompatible with width=3*panel_width+2."
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
