#!/usr/bin/env python3
"""Execute and retain Racket/Python evidence for the arm-rotation prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

import arm_rotation


HERE = Path(__file__).resolve().parent


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _callable_rule_text(program: str) -> str:
    """Return one grid->grid callable without double-wrapping lambda rules."""
    body = strip_rule_wrapper(program)
    stripped = body.lstrip()
    if stripped.startswith("(lambda ") or stripped.startswith("(lambda(") or stripped.startswith("(λ "):
        return body
    return f"(lambda (g) {body})"


def _execute_matrix(
    programs: dict[int, str],
    episode_inputs: dict[int, list[list[list[int]]]],
) -> dict[int, dict[int, list[list[list[int]]]]]:
    """Execute every fixed program against every episode in one Racket session.

    Racket startup dominates this small verifier.  Keeping one bridge for the
    complete finite matrix makes the evidence command bounded and repeatable
    without changing any program or comparison.
    """
    bridge = RacketBridge()
    try:
        for program_setting, program in programs.items():
            callable_text = _callable_rule_text(program)
            bridge.eval_text(
                f"(define __arm_rotation_rule_{program_setting} {callable_text})"
            )

        matrix: dict[int, dict[int, list[list[list[int]]]]] = {}
        for episode_setting, inputs in episode_inputs.items():
            names = []
            for index, grid in enumerate(inputs):
                name = f"__arm_rotation_input_{episode_setting}_{index}"
                bridge.define_grid(name, grid)
                names.append(name)
            matrix[episode_setting] = {
                program_setting: [
                    bridge.eval_text(
                        f"(__arm_rotation_rule_{program_setting} {name})"
                    )
                    for name in names
                ]
                for program_setting in programs
            }
        return matrix
    finally:
        bridge.shutdown()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    programs = {
        setting: arm_rotation.racket_program(setting)
        for setting in arm_rotation.SETTINGS
    }
    episodes = {
        setting: arm_rotation.build_episode(
            20261021 + setting,
            setting=setting,
            difficulty="medium",
        )
        for setting in arm_rotation.SETTINGS
    }

    episode_inputs = {
        setting: [
            pair["input"]
            for pair in episode["train"] + episode["test"]
        ]
        for setting, episode in episodes.items()
    }
    racket_matrix = _execute_matrix(programs, episode_inputs)

    records: dict[str, Any] = {}
    for setting, episode in episodes.items():
        errors = arm_rotation.episode_identifiability_errors(episode)
        if errors:
            raise AssertionError(f"setting {setting}: {errors}")
        pairs = episode["train"] + episode["test"]
        expected = [pair["output"] for pair in pairs]
        racket_outputs = racket_matrix[setting][setting]
        if racket_outputs != expected:
            raise AssertionError(f"Racket/Python mismatch for setting {setting}")

        rival_disagreements = {}
        for rival in arm_rotation.SETTINGS:
            if rival == setting:
                continue
            rival_outputs = racket_matrix[setting][rival]
            train_indices = [
                index
                for index in range(len(episode["train"]))
                if rival_outputs[index] != expected[index]
            ]
            query_differs = rival_outputs[len(episode["train"])] != expected[-1]
            if not train_indices or not query_differs:
                raise AssertionError(
                    f"setting {setting} is not distinguished from rival {rival}"
                )
            rival_disagreements[str(rival)] = {
                "train_indices": train_indices,
                "query_differs": query_differs,
            }

        public_path = out_dir / f"public-setting-{setting}.json"
        private_path = out_dir / f"private-setting-{setting}.json"
        _write_json(public_path, arm_rotation.public_challenge(episode))
        _write_json(private_path, episode)
        records[str(setting)] = {
            "episode_seed": episode["meta"]["seed"],
            "program_sha256": _sha256_bytes(programs[setting].encode()),
            "public_path": str(public_path),
            "public_sha256": _sha256_file(public_path),
            "private_path": str(private_path),
            "private_sha256": _sha256_file(private_path),
            "rival_disagreements": rival_disagreements,
        }

    source_files = [HERE / "arm_rotation.py", HERE / "verify.py", HERE / "README.md"]
    report = {
        "schema": "08f1d9bdd2ef-arm-rotation-verification-v1",
        "status": "passed",
        "scope": "task-local proposed prototype; not canonical or training approval",
        "parameter": {
            "name": arm_rotation.PARAMETER_NAME,
            "allowed_values": list(arm_rotation.SETTINGS),
            "default": arm_rotation.DEFAULT_SETTING,
            "selection": "one deterministic hidden value per episode",
        },
        "canonical_default": {
            "selected_rule_hash": "99b51630ed1d",
            "prototype_program_sha256": _sha256_bytes(programs[0].encode()),
        },
        "settings": records,
        "sources": {
            str(path.relative_to(HERE)): _sha256_file(path)
            for path in source_files
        },
        "limitations": [
            "Only four quarter-turn assignments are proposed and tested.",
            "Inputs do not encode the hidden setting; demonstrations must teach it.",
            "The production generator and selected canonical Racket rule are unchanged.",
            "This prototype is proposed and unapproved.",
        ],
    }
    _write_json(out_dir / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.out)
    print(json.dumps({"status": report["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
