#!/usr/bin/env python3
"""Materialize and execute source-bound column/row tie-policy evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

HERE = Path(__file__).resolve().parent
TASK_ID = "ec9cf2c80d58"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_parametric_ec9cf2c80d58", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def callable_rule(program: str) -> str:
    """Normalize lambda-form or body-form ``rule!`` text into a callable."""
    body = strip_rule_wrapper(strip_line_comments(program)).strip()
    if body.startswith("(lambda"):
        return body
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def execute_program(
    program: str,
    inputs: list[list[list[int]]],
) -> tuple[list[list[list[int]]], dict[str, Any]]:
    """Execute one exact materialized Racket program over a bounded batch."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket text")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("inputs must be a nonempty list of grids")
    outputs = []
    with RacketBridge(timeout=30.0, max_calls_before_restart=128) as bridge:
        bridge.eval_text(f"(define __tie_policy_rule {callable_rule(program)})")
        runtime = bridge.runtime_identity
        for index, grid in enumerate(inputs):
            bridge.define_grid(f"__tie_policy_input_{index}", grid)
            outputs.append(
                bridge.eval_text(f"(__tie_policy_rule __tie_policy_input_{index})")
            )
    return outputs, runtime


def _pair_rows(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _register_public_challenge(
    public: dict[str, Any], proto: Any, episode: dict[str, Any]
) -> str:
    """Add one visible challenge under its content ID, rejecting collisions."""
    name = proto.public_filename(episode)
    if name in public:
        raise ValueError(f"duplicate public challenge: {name}")
    public[name] = proto.public_challenge(episode)
    return name


def write_evidence(out: Path | str) -> dict[str, Any]:
    """Build both settings and prove all stored labels with live Racket."""
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to mix evidence into nonempty directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    proto = _load_prototype()
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    settings = (("column", 2026102201), ("row", 2026102202))
    programs = {
        policy: proto.racket_program(policy, root=root)
        for policy, _ in settings
    }
    for policy, program in programs.items():
        (out / f"rule_{policy}.rkt").write_text(program + "\n", encoding="utf-8")

    episodes: dict[str, Any] = {}
    public: dict[str, Any] = {}
    execution: dict[str, Any] = {}
    runtime_identity = None

    for policy, seed in settings:
        episode = proto.generate_episode(seed, tie_policy=policy, root=root)
        pairs = _pair_rows(episode)
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        actual, runtime = execute_program(programs[policy], inputs)
        runtime_identity = runtime_identity or runtime
        if runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed within evidence run")
        if actual != expected:
            raise AssertionError(f"Racket outputs disagree with stored {policy} episode")
        if any(generator.self_check(grid) for grid in inputs):
            raise AssertionError(f"{policy} episode emitted an input outside grammar")
        if not all(
            proto.apply_python(grid, policy) == output
            for grid, output in zip(inputs, actual)
        ):
            raise AssertionError(f"Python mirror disagrees with executed {policy} program")
        if policy == "column" and not all(
            generator.rule_model(grid) == output
            for grid, output in zip(inputs, actual)
        ):
            raise AssertionError("default column setting changed canonical behavior")

        opposite = "row" if policy == "column" else "column"
        opposite_actual, opposite_runtime = execute_program(programs[opposite], inputs)
        if opposite_runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed on rival execution")
        demo_refutations = [
            opposite_actual[index] != expected[index]
            for index in range(len(episode["train"]))
        ]
        query_distinctions = [
            opposite_actual[len(episode["train"]) + index] != pair["output"]
            for index, pair in enumerate(episode["test"])
        ]
        if not all(demo_refutations):
            raise AssertionError(f"{policy} demonstrations fail to refute {opposite}")
        if not all(query_distinctions):
            raise AssertionError(f"{policy} queries fail to distinguish {opposite}")

        episodes[policy] = episode
        _register_public_challenge(public, proto, episode)
        execution[policy] = {
            "seed": seed,
            "tie_policy": policy,
            "program_file": f"rule_{policy}.rkt",
            "program_sha256": _sha256_text(programs[policy]),
            "generator_slots": [
                {
                    "seed": pair["generator_seed"],
                    "sample_index": pair["sample_index"],
                    "difficulty": pair["difficulty"],
                }
                for pair in pairs
            ],
            "pair_count": len(pairs),
            "train_count": len(episode["train"]),
            "query_count": len(episode["test"]),
            "racket_outputs_match_stored": True,
            "python_outputs_match_racket": True,
            "canonical_default_match": True if policy == "column" else None,
            "opposite_setting": opposite,
            "all_demonstrations_refute_opposite_setting": True,
            "all_queries_distinguish_opposite_setting": True,
            "demo_refutations": demo_refutations,
            "query_distinctions": query_distinctions,
            "racket_outputs": actual,
            "opposite_racket_outputs": opposite_actual,
        }

    witness = episodes["column"]["train"][0]["input"]
    column_witness, column_runtime = execute_program(programs["column"], [witness])
    row_witness, row_runtime = execute_program(programs["row"], [witness])
    if column_runtime != runtime_identity or row_runtime != runtime_identity:
        raise AssertionError("Racket runtime identity changed on cross-setting witness")
    if column_witness[0] == row_witness[0]:
        raise AssertionError("materialized settings agree on cross-setting witness")

    prototype_path = HERE / "prototype.py"
    script_path = Path(__file__).resolve()
    canonical_program = proto.canonical_record(root=root)["program_solution"]
    summary = {
        "schema": "ec9cf2c80d58-tie-policy-evidence-v1",
        "status": "pass",
        "classification": "prototype_proposed_not_production_approved",
        "task_id": TASK_ID,
        "parameter": {
            "name": "tie_policy",
            "allowed": ["column", "row"],
            "default": "column",
            "selected_once_per_episode": True,
            "input_grammar_changed": False,
        },
        "source": {
            "prototype_path": str(prototype_path.relative_to(root)),
            "prototype_sha256": _sha256_bytes(prototype_path.read_bytes()),
            "evidence_script_path": str(script_path.relative_to(root)),
            "evidence_script_sha256": _sha256_bytes(script_path.read_bytes()),
            "canonical_generator_path": str(generator_path.relative_to(root)),
            "canonical_generator_sha256": generator_sha,
            "canonical_rule_hash": generator.RULE_HASH,
            "canonical_program_sha256": _sha256_text(canonical_program),
            "column_program_is_exact_canonical_text": programs["column"] == canonical_program,
            "canonical_authority_changed": False,
        },
        "execution": execution,
        "cross_setting_witness": {
            "source_episode": {
                "tie_policy": "column",
                "seed": settings[0][1],
                "train_index": 0,
            },
            "input": witness,
            "column_output": column_witness[0],
            "row_output": row_witness[0],
            "outputs_differ": True,
        },
        "racket_runtime": runtime_identity,
        "command": {
            "payload": (
                "python3 generators/ec9cf2c80d58/workspace/parametric/"
                "build_evidence.py --out ../checks/parametric"
            ),
            "cwd": "repo",
            "argv_observed": sys.argv,
            "cwd_observed": os.getcwd(),
        },
        "artifacts": {
            "episodes": "episodes.json",
            "public_challenges": "public_challenges.json",
            "rules": ["rule_column.rkt", "rule_row.rkt"],
        },
        "limitations": [
            "This is bounded two-setting evidence, not production catalog approval.",
            "The production generator and canonical RULE_HASH remain unchanged.",
            "Evidence covers two complete episodes plus one shared witness, not every seed.",
            "Every emitted pair deliberately contains a tie whose label changes by setting.",
        ],
    }

    public_dir = out / "public"
    public_dir.mkdir()
    for name, challenge in sorted(public.items()):
        (public_dir / name).write_bytes(public_challenge_bytes(challenge))

    _write_json(out / "episodes.json", episodes)
    _write_json(out / "public_challenges.json", public)
    _write_json(out / "summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = write_evidence(args.out)
    print(json.dumps({
        "status": summary["status"],
        "out": str(args.out),
        "generator_sha256": summary["source"]["canonical_generator_sha256"],
        "program_sha256": {
            policy: row["program_sha256"]
            for policy, row in summary["execution"].items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
