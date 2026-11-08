#!/usr/bin/env python3
"""Materialize and execute source-bound orientation-scope evidence."""
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
TASK_ID = "d09fae8197f6"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha256_text(json.dumps(grid, separators=(",", ":")))


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "_parametric_orientation_scope_d09fae8197f6", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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
    if type(inputs) is not list or not inputs:
        raise ValueError("inputs must be a nonempty list of grids")
    outputs = []
    with RacketBridge(timeout=30.0, max_calls_before_restart=128) as bridge:
        bridge.eval_text(f"(define __orientation_scope_rule {callable_rule(program)})")
        runtime = bridge.runtime_identity
        for index, grid in enumerate(inputs):
            bridge.define_grid(f"__orientation_scope_input_{index}", grid)
            outputs.append(
                bridge.eval_text(
                    f"(__orientation_scope_rule __orientation_scope_input_{index})"
                )
            )
    return outputs, runtime


def _pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_evidence(out: Path | str) -> dict[str, Any]:
    """Build both settings and prove every stored label with live Racket."""
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(
            f"refusing to mix evidence into nonempty directory: {out}"
        )
    out.mkdir(parents=True, exist_ok=True)

    proto = _load_prototype()
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root
    )
    settings = (("dihedral", 2026102301), ("rotations", 2026102302))
    programs = {
        scope: proto.racket_program(scope, root=root) for scope, _ in settings
    }
    for scope, program in programs.items():
        (out / f"rule_{scope}.rkt").write_text(program + "\n", encoding="utf-8")

    episodes: dict[str, Any] = {}
    public_challenges: dict[str, Any] = {}
    execution: dict[str, Any] = {}
    runtime_identity = None

    for scope, seed in settings:
        episode = proto.generate_episode(
            seed,
            orientation_scope=scope,
            root=root,
            demo_count=3,
            query_count=4,
        )
        rows = _pairs(episode)
        inputs = [row["input"] for row in rows]
        expected = [row["output"] for row in rows]
        actual, runtime = execute_program(programs[scope], inputs)
        runtime_identity = runtime_identity or runtime
        if runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed within evidence run")
        if actual != expected:
            raise AssertionError(f"Racket outputs disagree with stored {scope} episode")
        if any(generator.self_check(grid) for grid in inputs):
            raise AssertionError(f"{scope} episode emitted an input outside grammar")
        if not all(
            proto.apply_python(grid, scope) == output
            for grid, output in zip(inputs, actual)
        ):
            raise AssertionError(f"Python mirror disagrees with executed {scope} rule")
        if scope == "dihedral" and not all(
            generator._rule_output(grid) == output
            for grid, output in zip(inputs, actual)
        ):
            raise AssertionError("default dihedral setting changed canonical behavior")

        opposite = "rotations" if scope == "dihedral" else "dihedral"
        rival, rival_runtime = execute_program(programs[opposite], inputs)
        if rival_runtime != runtime_identity:
            raise AssertionError("Racket runtime identity changed on rival execution")
        demo_refutations = [
            rival[index] != expected[index]
            for index in range(len(episode["train"]))
        ]
        query_distinctions = [
            rival[len(episode["train"]) + index] != pair["output"]
            for index, pair in enumerate(episode["test"])
        ]
        if not all(demo_refutations):
            raise AssertionError(f"{scope} demonstrations fail to refute {opposite}")
        if not all(query_distinctions):
            raise AssertionError(f"{scope} queries fail to distinguish {opposite}")
        if not all(proto.apply_python(grid, "rotations") != grid for grid in inputs):
            raise AssertionError("rotations setting failed to stamp on a retained input")
        if not all(proto.apply_python(grid, "dihedral") != grid for grid in inputs):
            raise AssertionError("dihedral setting failed to stamp on a retained input")

        public = proto.public_challenge(episode)
        public_name = proto.public_filename(episode)
        if public_name in public_challenges:
            raise AssertionError("duplicate public visible challenge ID")
        public_challenges[public_name] = public
        episodes[scope] = episode
        execution[scope] = {
            "seed": seed,
            "orientation_scope": scope,
            "opposite_scope": opposite,
            "program_file": f"rule_{scope}.rkt",
            "program_sha256": _sha256_text(programs[scope]),
            "demo_count": len(episode["train"]),
            "query_count": len(episode["test"]),
            "pair_count": len(rows),
            "input_sha256": [_grid_hash(grid) for grid in inputs],
            "selected_output_sha256": [_grid_hash(grid) for grid in actual],
            "rival_output_sha256": [_grid_hash(grid) for grid in rival],
            "candidate_attempts": [row["candidate_attempt"] for row in rows],
            "racket_outputs_match_stored": True,
            "python_outputs_match_racket": True,
            "canonical_default_match": True if scope == "dihedral" else None,
            "all_demonstrations_refute_opposite_scope": True,
            "all_queries_distinguish_opposite_scope": True,
            "both_scopes_stamp_every_pair": True,
            "public_filename": public_name,
            "public_bytes_sha256": _sha256_bytes(public_challenge_bytes(public)),
        }

    prototype_path = HERE / "prototype.py"
    script_path = Path(__file__).resolve()
    readme_path = HERE / "README.md"
    test_paths = [
        root / "generators" / TASK_ID / "tests" / "test_parametric_orientation_scope.py",
        root / "generators" / TASK_ID / "tests" / "test_parametric_public_names.py",
    ]
    canonical_program = proto.canonical_record(root=root)["program_solution"]

    _write_json(out / "episodes.json", episodes)
    _write_json(out / "public_challenges.json", public_challenges)
    summary = {
        "schema": "d09fae8197f6-orientation-scope-evidence-v1",
        "status": "pass",
        "classification": "prototype_proposed_not_production_approved",
        "task_id": TASK_ID,
        "parameter": {
            "name": "orientation_scope",
            "allowed": ["dihedral", "rotations"],
            "default": "dihedral",
            "selected_once_per_episode": True,
            "input_grammar_changed": False,
        },
        "source": {
            "prototype_path": str(prototype_path.relative_to(root)),
            "prototype_sha256": _sha256_bytes(prototype_path.read_bytes()),
            "evidence_script_path": str(script_path.relative_to(root)),
            "evidence_script_sha256": _sha256_bytes(script_path.read_bytes()),
            "readme_path": str(readme_path.relative_to(root)),
            "readme_sha256": _sha256_bytes(readme_path.read_bytes()),
            "test_sha256": {
                str(path.relative_to(root)): _sha256_bytes(path.read_bytes())
                for path in test_paths
            },
            "canonical_generator_path": str(generator_path.relative_to(root)),
            "canonical_generator_sha256": generator_sha,
            "canonical_rule_hash": generator.RULE_HASH,
            "canonical_program_sha256": _sha256_text(canonical_program),
            "dihedral_program_is_exact_canonical_text": (
                programs["dihedral"] == canonical_program
            ),
            "canonical_authority_changed": False,
        },
        "execution": execution,
        "racket_runtime": runtime_identity,
        "command": {
            "payload": (
                "python3 generators/d09fae8197f6/workspace/parametric/"
                "build_evidence.py --out ../checks/parametric/orientation-scope-v1"
            ),
            "cwd": "repo",
            "argv_observed": sys.argv,
            "cwd_observed": os.getcwd(),
        },
        "artifacts": {
            "episodes": "episodes.json",
            "public_challenges": "public_challenges.json",
            "rules": ["rule_dihedral.rkt", "rule_rotations.rkt"],
        },
        "limitations": [
            "This is bounded two-setting evidence, not production catalog approval.",
            "The production generator, canonical Racket text, and RULE_HASH remain unchanged.",
            "Evidence covers two complete episodes (3 demonstrations and 4 queries each), not every seed.",
            "The prototype deliberately rejects lawful production inputs on which the two settings agree or rotations would not stamp.",
        ],
    }
    _write_json(out / "summary.json", summary)
    manifest = {
        "schema": "d09fae8197f6-orientation-scope-manifest-v1",
        "files": {
            path.name: _sha256_bytes(path.read_bytes())
            for path in sorted(out.iterdir())
            if path.is_file()
        },
    }
    _write_json(out / "manifest.json", manifest)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = write_evidence(args.out)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "out": str(args.out),
                "generator_sha256": summary["source"]["canonical_generator_sha256"],
                "program_sha256": {
                    scope: row["program_sha256"]
                    for scope, row in summary["execution"].items()
                },
                "counts": {
                    scope: {
                        "demo": row["demo_count"],
                        "query": row["query_count"],
                    }
                    for scope, row in summary["execution"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
