#!/usr/bin/env python3
"""Retain bounded offline Racket evidence for the selector-role prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs

import prototype

HERE = Path(__file__).resolve().parent
REPO = prototype.ROOT


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_for(setting: str, start: int) -> int:
    for seed in range(start, start + 100_000):
        if prototype.choose_setting(seed) == setting:
            return seed
    raise RuntimeError(f"could not find deterministic seed for {setting!r}")


def _execute_program(
    program: str, inputs: list[list[list[int]]]
) -> tuple[list[list[list[int]]], dict[str, Any]]:
    bridge = RacketBridge()
    try:
        body = strip_rule_wrapper(program)
        bridge.eval_text(f"(define __selector_role_rule {body})")
        outputs: list[list[list[int]]] = []
        for index, grid in enumerate(inputs):
            name = f"__selector_role_input_{index}"
            bridge.define_grid(name, grid)
            result = bridge.eval_text(f"(__selector_role_rule {name})")
            if not (
                isinstance(result, list)
                and result
                and all(isinstance(row, list) and row for row in result)
            ):
                raise RuntimeError(f"Racket returned a non-grid for input {index}: {result!r}")
            outputs.append([[int(value) for value in row] for row in result])
        return outputs, dict(bridge.runtime_identity)
    finally:
        bridge.shutdown()


def _differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def verify(out_dir: Path) -> dict[str, Any]:
    out_dir = out_dir.resolve()
    if out_dir.exists():
        raise FileExistsError(f"output already exists; choose a fresh evidence path: {out_dir}")
    out_dir.mkdir(parents=True)

    settings = prototype.ALLOWED_SETTINGS
    programs = {setting: prototype.program_for(setting) for setting in settings}
    if programs[prototype.DEFAULT_SETTING] != prototype._canonical_program():
        raise AssertionError("default prototype program is not exact canonical authority")

    seeds = {setting: _seed_for(setting, 20261022) for setting in settings}
    episodes = {
        setting: prototype.build_episode(seeds[setting])
        for setting in settings
    }

    rules_dir = out_dir / "rules"
    rule_paths: dict[str, Path] = {}
    for setting, program in programs.items():
        path = rules_dir / f"selector-role-{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program + "\n", encoding="utf-8")
        rule_paths[setting] = path

    retained_inputs: list[list[list[int]]] = []
    spans: dict[str, tuple[int, int]] = {}
    for setting in settings:
        episode = episodes[setting]
        if episode["meta"][prototype.PARAMETER_NAME] != setting:
            raise AssertionError(f"seed {seeds[setting]} did not select {setting!r}")
        start = len(retained_inputs)
        retained_inputs.extend(
            pair["input"] for pair in episode["train"] + episode["test"]
        )
        spans[setting] = (start, len(retained_inputs))

    canonical = canonical_pairs(prototype.TASK_ID, root=REPO, labeled_only=True)
    canonical_inputs = [pair["input"] for pair in canonical]
    all_inputs = retained_inputs + canonical_inputs

    all_outputs: dict[str, list[list[list[int]]]] = {}
    runtime_identity: dict[str, Any] | None = None
    for setting, program in programs.items():
        outputs, identity = _execute_program(program, all_inputs)
        all_outputs[setting] = outputs
        if runtime_identity is None:
            runtime_identity = identity
        elif identity != runtime_identity:
            raise AssertionError("Racket runtime identity changed between settings")

    canonical_offset = len(retained_inputs)
    canonical_default_outputs = all_outputs[prototype.DEFAULT_SETTING][canonical_offset:]
    canonical_expected = [pair["output"] for pair in canonical]
    if canonical_default_outputs != canonical_expected:
        raise AssertionError("default Racket rule does not match every canonical label")

    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    episode_summaries: dict[str, Any] = {}
    for setting in settings:
        rival = next(value for value in settings if value != setting)
        start, stop = spans[setting]
        selected_outputs = all_outputs[setting][start:stop]
        rival_outputs = all_outputs[rival][start:stop]
        episode = episodes[setting]
        expected = [pair["output"] for pair in episode["train"] + episode["test"]]
        if selected_outputs != expected:
            raise AssertionError(f"executed Racket disagrees with Python for {setting!r}")

        train_count = len(episode["train"])
        train_disagreements = [
            index
            for index in range(train_count)
            if selected_outputs[index] != rival_outputs[index]
        ]
        query_disagreements = [
            index - train_count
            for index in range(train_count, stop - start)
            if selected_outputs[index] != rival_outputs[index]
        ]
        if not train_disagreements:
            raise AssertionError(f"demos for {setting!r} do not refute {rival!r}")
        if len(query_disagreements) != len(episode["test"]):
            raise AssertionError(f"query for {setting!r} does not depend on the setting")

        private_path = private_dir / f"episode-{setting}.json"
        private_record = {
            "schema": "a9f315ca9cc7-parametric-episode-v1",
            "task_id": prototype.TASK_ID,
            "seed": seeds[setting],
            "parameter_spec": prototype.PARAMETER_SPEC,
            "selected_setting": setting,
            "rival_setting": rival,
            "program": programs[setting],
            "program_sha256": _sha256_bytes(programs[setting].encode()),
            "episode": episode,
            "selected_racket_outputs": selected_outputs,
            "rival_racket_outputs": rival_outputs,
            "checks": {
                "parameter_chosen_once_for_episode": True,
                "three_demonstrations": train_count == 3,
                "one_query": len(episode["test"]) == 1,
                "all_outputs_from_executed_racket": True,
                "python_mirror_parity": True,
                "demos_distinguish_rival": bool(train_disagreements),
                "every_query_distinguishes_rival": (
                    len(query_disagreements) == len(episode["test"])
                ),
            },
        }
        _write_json(private_path, private_record)

        public = prototype.public_challenge(episode)
        serialized = json.dumps(public, sort_keys=True)
        for forbidden in (prototype.PARAMETER_NAME, "rule!", '"program"'):
            if forbidden in serialized:
                raise AssertionError(f"public challenge leaks {forbidden!r}")
        if any("output" in pair for pair in public["test"]):
            raise AssertionError("public challenge leaks a query answer")
        public_path = public_dir / f"episode-{setting}.json"
        _write_json(public_path, public)

        episode_summaries[setting] = {
            "seed": seeds[setting],
            "selected_setting": setting,
            "rival_setting": rival,
            "train_disagreement_indices": train_disagreements,
            "query_disagreement_indices": query_disagreements,
            "private_evidence": str(private_path.relative_to(out_dir)),
            "private_evidence_sha256": _sha256_file(private_path),
            "public_challenge": str(public_path.relative_to(out_dir)),
            "public_challenge_sha256": _sha256_file(public_path),
        }

    witness_setting = prototype.DEFAULT_SETTING
    witness_episode = episodes[witness_setting]
    witness_index = spans[witness_setting][0] + len(witness_episode["train"])
    witness_input = witness_episode["test"][0]["input"]
    witness_outputs = {
        setting: all_outputs[setting][witness_index]
        for setting in settings
    }
    if witness_outputs[settings[0]] == witness_outputs[settings[1]]:
        raise AssertionError("retained witness does not distinguish selector roles")
    witness_path = private_dir / "setting-difference-witness.json"
    _write_json(
        witness_path,
        {
            "task_id": prototype.TASK_ID,
            "input": witness_input,
            "input_self_check": prototype._PRODUCTION.self_check(witness_input),
            "outputs": witness_outputs,
            "differing_cells": _differing_cells(
                witness_outputs[settings[0]], witness_outputs[settings[1]]
            ),
            "checked_by": "both complete Racket programs",
        },
    )

    source_files = [
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        prototype.GENERATOR_PATH,
    ]
    report = {
        "schema": "a9f315ca9cc7-parametric-selector-role-v1",
        "status": "passed",
        "scope": "task-local proposed prototype; not canonical approval",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "parameter": prototype.PARAMETER_SPEC,
        "canonical_default_exact_program_match": True,
        "canonical_pairs_checked_with_default_racket": len(canonical),
        "canonical_pairs_passed_with_default_racket": len(canonical),
        "programs": {
            setting: {
                "text": programs[setting],
                "sha256": _sha256_bytes(programs[setting].encode()),
                "path": str(rule_paths[setting].relative_to(out_dir)),
                "file_sha256": _sha256_file(rule_paths[setting]),
            }
            for setting in settings
        },
        "episodes": episode_summaries,
        "distinguishing_witness": {
            "path": str(witness_path.relative_to(out_dir)),
            "sha256": _sha256_file(witness_path),
            "lawful_input": True,
            "outputs_differ": True,
        },
        "racket_runtime": runtime_identity,
        "source_hashes": {
            str(path.relative_to(REPO)): _sha256_file(path)
            for path in source_files
        },
        "command": {
            "cwd": os.getcwd(),
            "argv": [sys.executable, *sys.argv],
        },
        "limitations": [
            "Only the two declared selector roles and retained seeds are evidenced.",
            "The selected production generator and canonical Racket authority remain separate.",
            "This is a proposed authoring prototype, not catalog approval or runtime integration.",
            "Finite checks against the declared parameter rival do not exclude arbitrary programs.",
        ],
        "passed": True,
    }
    _write_json(out_dir / "report.json", report)
    _write_json(
        out_dir / "manifest.json",
        {
            "schema": "a9f315ca9cc7-parametric-manifest-v1",
            "report": "report.json",
            "report_sha256": _sha256_file(out_dir / "report.json"),
            "files": {
                str(path.relative_to(out_dir)): _sha256_file(path)
                for path in sorted(out_dir.rglob("*"))
                if path.is_file() and path.name != "manifest.json"
            },
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = verify(args.out_dir)
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "parameter": report["parameter"],
                "evidence": str(args.out_dir),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
