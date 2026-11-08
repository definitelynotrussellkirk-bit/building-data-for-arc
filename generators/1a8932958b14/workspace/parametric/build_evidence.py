#!/usr/bin/env python3
"""Execute both proposed parameter settings through the included Racket bridge."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
TASK_ID = "1a8932958b14"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_parametric_prototype_evidence", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _callable_rule(program: str) -> str:
    """Apply the runtime's body-form rule! wrapping without optional syntax imports.

    The shared ``wrap_rule`` helper currently imports ``scripts.comment_solutions``
    for syntax forms even when this simple program contains none.  That package is
    absent from the documented repository-layout payload path.  These generated
    programs are known body-form ``rule!`` expressions, so the runtime-equivalent
    transformation is bounded and explicit here.
    """
    body = strip_rule_wrapper(strip_line_comments(program))
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def _execute_program(program: str, inputs: list[list[list[int]]]) -> tuple[list[list[list[int]]], dict[str, Any]]:
    callable_text = _callable_rule(program)
    outputs = []
    with RacketBridge(timeout=20.0) as bridge:
        bridge.eval_text(f"(define __parametric_rule {callable_text})")
        runtime = bridge.runtime_identity
        for index, grid in enumerate(inputs):
            bridge.define_grid(f"__parametric_input_{index}", grid)
            outputs.append(
                bridge.eval_text(f"(__parametric_rule __parametric_input_{index})")
            )
    return outputs, runtime


def _pair_rows(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="evidence directory, relative to repo or absolute")
    args = parser.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    proto = _load_prototype()
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)

    settings = ((1, 202610191), (2, 202610192))
    episodes: dict[str, Any] = {}
    execution: dict[str, Any] = {}
    runtime_identity = None

    for multiplier, seed in settings:
        episode = proto.generate_episode(seed, vector_multiplier=multiplier)
        pairs = _pair_rows(episode)
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        program = episode["program"]
        actual, runtime = _execute_program(program, inputs)
        runtime_identity = runtime_identity or runtime
        if runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed within one evidence run")
        if actual != expected:
            raise AssertionError(f"Racket outputs disagree for vector_multiplier={multiplier}")
        if any(generator.self_check(grid) for grid in inputs):
            raise AssertionError("prototype emitted an input outside the canonical input grammar")
        if multiplier == 1 and any(
            generator.rule_mirror(grid) != output for grid, output in zip(inputs, actual)
        ):
            raise AssertionError("default prototype setting does not preserve canonical behavior")

        opposite = 3 - multiplier
        opposite_program = proto.racket_program(opposite)
        opposite_actual, opposite_runtime = _execute_program(opposite_program, inputs)
        if opposite_runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed on rival execution")
        demo_refutations = [
            opposite_actual[index] != expected[index]
            for index in range(len(episode["train"]))
        ]
        if not all(demo_refutations):
            raise AssertionError(
                f"demonstrations do not distinguish vector_multiplier={multiplier} from {opposite}"
            )

        key = str(multiplier)
        episodes[key] = episode
        execution[key] = {
            "seed": seed,
            "vector_multiplier": multiplier,
            "program_sha256": _sha256_text(program),
            "program_file": f"rule_multiplier_{multiplier}.rkt",
            "pair_count": len(pairs),
            "train_count": len(episode["train"]),
            "query_count": len(episode["test"]),
            "racket_outputs_match_stored": True,
            "python_outputs_match_racket": all(
                proto.apply_python(grid, multiplier) == output
                for grid, output in zip(inputs, actual)
            ),
            "canonical_default_match": (
                all(generator.rule_mirror(grid) == output for grid, output in zip(inputs, actual))
                if multiplier == 1
                else None
            ),
            "opposite_setting": opposite,
            "all_demonstrations_refute_opposite_setting": all(demo_refutations),
            "demo_refutations": demo_refutations,
            "racket_outputs": actual,
            "opposite_racket_outputs": opposite_actual,
        }
        (out / f"rule_multiplier_{multiplier}.rkt").write_text(program + "\n", encoding="utf-8")

    shared_input = episodes["1"]["train"][0]["input"]
    output_1, runtime_1 = _execute_program(proto.racket_program(1), [shared_input])
    output_2, runtime_2 = _execute_program(proto.racket_program(2), [shared_input])
    if runtime_1 != runtime_identity or runtime_2 != runtime_identity:
        raise AssertionError("Racket runtime identity changed on cross-setting witness")
    if output_1[0] == output_2[0]:
        raise AssertionError("settings did not change executed transformation on witness input")

    prototype_sha = _sha256_bytes((HERE / "prototype.py").read_bytes())
    evidence_script_sha = _sha256_bytes(Path(__file__).read_bytes())
    summary = {
        "schema": "task-local-parametric-evidence-v1",
        "status": "pass",
        "classification": "prototype_proposed_not_production_approved",
        "task_id": TASK_ID,
        "parameter": {
            "name": "vector_multiplier",
            "allowed": [1, 2],
            "default": 1,
            "selected_once_per_episode": True,
            "input_constraint": proto.PARAMETERS["vector_multiplier"]["input_constraint"],
        },
        "source": {
            "prototype_path": str((HERE / "prototype.py").relative_to(root)),
            "prototype_sha256": prototype_sha,
            "evidence_script_path": str(Path(__file__).relative_to(root)),
            "evidence_script_sha256": evidence_script_sha,
            "canonical_generator_path": str(generator_path.relative_to(root)),
            "canonical_generator_sha256": generator_sha,
            "canonical_authority_changed": False,
        },
        "execution": execution,
        "cross_setting_witness": {
            "source_episode": {"vector_multiplier": 1, "seed": settings[0][1], "train_index": 0},
            "output_multiplier_1": output_1[0],
            "output_multiplier_2": output_2[0],
            "outputs_differ": output_1[0] != output_2[0],
        },
        "racket_runtime": runtime_identity,
        "command": {
            "payload": "python3 generators/1a8932958b14/workspace/parametric/build_evidence.py --out ../checks/parametric",
            "cwd": "repo",
            "argv_observed": sys.argv,
            "cwd_observed": os.getcwd(),
        },
        "artifacts": {
            "episodes": "episodes.json",
            "public_challenges": "public_challenges.json",
            "rules": ["rule_multiplier_1.rkt", "rule_multiplier_2.rkt"],
        },
        "limitations": [
            "This is bounded two-setting evidence, not production catalog approval.",
            "The production generator and canonical RULE_HASH remain unchanged by this prototype.",
            "Only the materialized episodes and one shared-input witness were executed here; this is not exhaustive over seeds.",
            "Inputs are deliberately constrained so both multiplier settings remain in bounds.",
        ],
    }

    public = {key: proto.public_challenge(episode) for key, episode in episodes.items()}
    (out / "episodes.json").write_text(json.dumps(episodes, indent=2) + "\n", encoding="utf-8")
    (out / "public_challenges.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "prototype_sha256": prototype_sha,
        "generator_sha256": generator_sha,
        "program_hashes": {key: row["program_sha256"] for key, row in execution.items()},
        "out": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
