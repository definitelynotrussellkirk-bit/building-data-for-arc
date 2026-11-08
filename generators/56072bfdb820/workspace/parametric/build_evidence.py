#!/usr/bin/env python3
"""Materialize and execute source-bound clip/wrap prototype evidence."""
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
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK_ID = "56072bfdb820"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_parametric_56072bfdb820", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def callable_rule(program: str) -> str:
    """Normalize either lambda-form or body-form ``rule!`` text portably.

    The repository's higher-level ``wrap_rule`` helper imports an optional
    ``scripts`` package that is absent from the documented repository-layout
    payload.  This helper uses only the public lexical peelers.  Lambda-form
    authorities, including this task, are already callable after removing
    ``rule!``; body-form authorities receive the runtime-equivalent g/h/w shell.
    """
    body = strip_rule_wrapper(strip_line_comments(program)).strip()
    if body.startswith("(lambda"):
        return body
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def execute_program(
    program: str,
    inputs: list[list[list[int]]],
) -> tuple[list[list[list[int]]], dict[str, Any]]:
    """Execute one exact materialized program over a bounded input batch."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket text")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("inputs must be a nonempty list of grids")
    outputs = []
    with RacketBridge(timeout=30.0, max_calls_before_restart=128) as bridge:
        bridge.eval_text(f"(define __boundary_mode_rule {callable_rule(program)})")
        runtime = bridge.runtime_identity
        for index, grid in enumerate(inputs):
            bridge.define_grid(f"__boundary_mode_input_{index}", grid)
            outputs.append(
                bridge.eval_text(
                    f"(__boundary_mode_rule __boundary_mode_input_{index})"
                )
            )
    return outputs, runtime


def _pair_rows(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(out: Path | str) -> dict[str, Any]:
    """Build two complete episodes and prove their exact programs by execution."""
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to mix evidence into nonempty directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    proto = _load_prototype()
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)

    settings = (("clip", 2026101901), ("wrap", 2026101902))
    episodes: dict[str, Any] = {}
    public: dict[str, Any] = {}
    execution: dict[str, Any] = {}
    runtime_identity = None

    programs = {
        mode: proto.racket_program(mode, root=root)
        for mode, _ in settings
    }
    for mode, program in programs.items():
        (out / f"rule_{mode}.rkt").write_text(program + "\n", encoding="utf-8")

    for mode, seed in settings:
        episode = proto.generate_episode(seed, boundary_mode=mode, root=root)
        pairs = _pair_rows(episode)
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        actual, runtime = execute_program(programs[mode], inputs)
        runtime_identity = runtime_identity or runtime
        if runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed within evidence run")
        if actual != expected:
            raise AssertionError(f"Racket outputs disagree with stored {mode} episode")
        if any(generator.self_check(grid) for grid in inputs):
            raise AssertionError(f"{mode} episode emitted an input outside canonical grammar")
        if not all(
            proto.apply_python(grid, mode) == output
            for grid, output in zip(inputs, actual)
        ):
            raise AssertionError(f"Python mirror disagrees with executed {mode} program")
        if mode == "clip" and not all(
            generator.rule_mirror(grid) == output
            for grid, output in zip(inputs, actual)
        ):
            raise AssertionError("default clip setting changed canonical behavior")

        opposite = "wrap" if mode == "clip" else "clip"
        opposite_actual, opposite_runtime = execute_program(programs[opposite], inputs)
        if opposite_runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed on rival execution")
        demo_refutations = [
            opposite_actual[index] != expected[index]
            for index in range(len(episode["train"]))
        ]
        if not all(demo_refutations):
            raise AssertionError(f"{mode} demonstrations fail to refute {opposite}")
        query_distinctions = [
            opposite_actual[len(episode["train"]) + index] != pair["output"]
            for index, pair in enumerate(episode["test"])
        ]
        if not all(query_distinctions):
            raise AssertionError(f"{mode} query does not distinguish {opposite}")

        episodes[mode] = episode
        public[mode] = proto.public_challenge(episode)
        execution[mode] = {
            "seed": seed,
            "boundary_mode": mode,
            "program_file": f"rule_{mode}.rkt",
            "program_sha256": _sha256_text(programs[mode]),
            "pair_indices": [pair["pair_index"] for pair in pairs],
            "pair_count": len(pairs),
            "train_count": len(episode["train"]),
            "query_count": len(episode["test"]),
            "racket_outputs_match_stored": True,
            "python_outputs_match_racket": True,
            "canonical_default_match": True if mode == "clip" else None,
            "opposite_setting": opposite,
            "all_demonstrations_refute_opposite_setting": True,
            "all_queries_distinguish_opposite_setting": True,
            "demo_refutations": demo_refutations,
            "query_distinctions": query_distinctions,
            "racket_outputs": actual,
            "opposite_racket_outputs": opposite_actual,
        }

    witness = episodes["clip"]["train"][0]["input"]
    clip_witness, clip_runtime = execute_program(programs["clip"], [witness])
    wrap_witness, wrap_runtime = execute_program(programs["wrap"], [witness])
    if clip_runtime != runtime_identity or wrap_runtime != runtime_identity:
        raise AssertionError("Racket runtime identity changed on cross-setting witness")
    if clip_witness[0] == wrap_witness[0]:
        raise AssertionError("materialized settings agree on the cross-setting witness")

    prototype_path = HERE / "prototype.py"
    script_path = Path(__file__).resolve()
    canonical_program = proto.canonical_record(root=root)["program_solution"]
    summary = {
        "schema": "56072bfdb820-boundary-mode-evidence-v1",
        "status": "pass",
        "classification": "prototype_proposed_not_production_approved",
        "task_id": TASK_ID,
        "parameter": {
            "name": "boundary_mode",
            "allowed": ["clip", "wrap"],
            "default": "clip",
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
            "clip_program_is_exact_canonical_text": programs["clip"] == canonical_program,
            "canonical_authority_changed": False,
        },
        "execution": execution,
        "cross_setting_witness": {
            "source_episode": {"boundary_mode": "clip", "seed": settings[0][1], "train_index": 0},
            "input": witness,
            "clip_output": clip_witness[0],
            "wrap_output": wrap_witness[0],
            "outputs_differ": True,
        },
        "racket_runtime": runtime_identity,
        "command": {
            "payload": (
                "python3 generators/56072bfdb820/workspace/parametric/"
                "build_evidence.py --out ../checks/parametric"
            ),
            "cwd": "repo",
            "argv_observed": sys.argv,
            "cwd_observed": os.getcwd(),
        },
        "artifacts": {
            "episodes": "episodes.json",
            "public_challenges": "public_challenges.json",
            "rules": ["rule_clip.rkt", "rule_wrap.rkt"],
        },
        "limitations": [
            "This is bounded two-setting evidence, not production catalog approval.",
            "The production generator and canonical RULE_HASH remain unchanged by the prototype.",
            "Evidence covers two complete materialized episodes plus one shared witness, not every seed.",
            "All emitted pairs deliberately use placements where clip and wrap produce different labels.",
        ],
    }

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
            mode: row["program_sha256"]
            for mode, row in summary["execution"].items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
