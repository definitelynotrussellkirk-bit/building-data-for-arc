#!/usr/bin/env python3
"""Execute and retain evidence for both extension-mode prototype settings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator

from prototype import (
    ALLOWED_EXTENSION_MODES,
    DEFAULT_EXTENSION_MODE,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    TASK_ID,
    choose_parameters,
    episode_inputs,
    grid_literal,
    public_challenge,
    python_reference,
    racket_program,
)

RULE_WRAPPER = "(define (rule! f) f)"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_seed_for(mode: str) -> int:
    for seed in range(10_000):
        if choose_parameters(seed)[PARAMETER_NAME] == mode:
            return seed
    raise AssertionError(f"no deterministic seed found for {mode!r}")


def execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    bridge.eval_text(f"(define prototype-rule {source})")
    result = bridge.eval_text(f"(prototype-rule {grid_literal(grid)})")
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) for row in result)
    ):
        raise RuntimeError(f"Racket returned a non-grid: {result!r}")
    return [[int(value) for value in row] for row in result]


def build_episode(gen: Any, bridge: RacketBridge, seed: int) -> dict[str, Any]:
    parameters = choose_parameters(seed)
    mode = parameters[PARAMETER_NAME]
    source = racket_program(parameters)
    alternative_mode = next(item for item in ALLOWED_EXTENSION_MODES if item != mode)
    alternative_source = racket_program({PARAMETER_NAME: alternative_mode})

    pairs: list[dict[str, Any]] = []
    rival_outputs: list[dict[str, Any]] = []
    for grid in episode_inputs(seed):
        generator_errors = gen.self_check(grid)
        if generator_errors:
            raise AssertionError(
                "prototype input rejected by selected canonical generator: "
                + "; ".join(generator_errors)
            )
        output = execute(bridge, source, grid)
        mirror = python_reference(grid, extension_mode=mode)
        if output != mirror:
            raise AssertionError("executed Racket disagrees with the Python debug mirror")
        if mode == DEFAULT_EXTENSION_MODE and normalized_rule_hash(source) != gen.RULE_HASH:
            raise AssertionError("default prototype source diverges from the selected canonical rule")
        alternative_output = execute(bridge, alternative_source, grid)
        if alternative_output == output:
            raise AssertionError("prototype settings are not observable on a retained input")
        pairs.append({"input": grid, "output": output})
        rival_outputs.append(
            {"setting": alternative_mode, "output": alternative_output}
        )

    episode = {"demos": pairs[:3], "query": pairs[3]}
    demos_distinguish = any(
        rival_outputs[index]["output"] != pairs[index]["output"]
        for index in range(3)
    )
    if not demos_distinguish:
        raise AssertionError("demonstrations do not identify the chosen setting")

    return {
        "schema": "arc-parametric-episode-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": parameters,
        "parameter_spec": PARAMETER_SPEC,
        "racket_program": source,
        "racket_sha256": sha256_bytes(source.encode()),
        "normalized_rule_hash": normalized_rule_hash(source),
        "episode": episode,
        "alternative_setting": alternative_mode,
        "alternative_racket_program": alternative_source,
        "alternative_racket_sha256": sha256_bytes(alternative_source.encode()),
        "alternative_outputs": rival_outputs,
        "checks": {
            "parameter_chosen_once_for_episode": True,
            "three_demonstrations": len(episode["demos"]) == 3,
            "query_present": "output" in episode["query"],
            "all_inputs_pass_selected_generator_self_check": True,
            "all_outputs_from_executed_racket": True,
            "python_mirror_parity": True,
            "default_matches_selected_canonical_rule": (
                mode != DEFAULT_EXTENSION_MODE
                or normalized_rule_hash(source) == gen.RULE_HASH
            ),
            "demos_distinguish_alternative": demos_distinguish,
            "every_pair_distinguishes_alternative": all(
                rival["output"] != pair["output"]
                for rival, pair in zip(rival_outputs, pairs)
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; use a new path to preserve evidence")
    private = out / "private"
    public = out / "public"
    private.mkdir(parents=True)
    public.mkdir()

    root = find_root(__file__)
    gen, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    source_dir = Path(__file__).resolve().parent
    default_source = racket_program({PARAMETER_NAME: DEFAULT_EXTENSION_MODE})
    canonical_hash = normalized_rule_hash(default_source)
    if canonical_hash != gen.RULE_HASH:
        raise AssertionError(
            f"default prototype hash {canonical_hash} != selected RULE_HASH {gen.RULE_HASH}"
        )

    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}
    episodes: list[dict[str, Any]] = []
    with RacketBridge(timeout=20, max_calls_before_restart=48) as bridge:
        bridge.eval_text(RULE_WRAPPER)
        runtime_identity = bridge.runtime_identity
        for index, mode in enumerate(ALLOWED_EXTENSION_MODES):
            seed = first_seed_for(mode)
            evidence = build_episode(gen, bridge, seed)
            challenge = public_challenge(evidence["episode"])
            challenge_name = f"challenge-{index:03d}.json"
            evidence_name = f"evidence-{index:03d}.json"
            challenge_path = public / challenge_name
            evidence_path = private / evidence_name
            write_json(challenge_path, challenge)
            evidence.update(
                {
                    "public_challenge": f"public/{challenge_name}",
                    "public_challenge_sha256": sha256_file(challenge_path),
                    "source_hashes": {
                        "prototype.py": sha256_file(source_dir / "prototype.py"),
                        "build_prototype.py": sha256_file(Path(__file__).resolve()),
                        "selected_generator.py": generator_sha256,
                    },
                    "selected_generator_path": str(generator_path),
                    "command": command,
                    "racket_runtime": runtime_identity,
                }
            )
            write_json(evidence_path, evidence)
            episodes.append(
                {
                    "index": index,
                    "seed": seed,
                    "setting": mode,
                    "public_challenge": challenge_name,
                    "public_challenge_sha256": sha256_file(challenge_path),
                    "private_evidence": evidence_name,
                    "private_evidence_sha256": sha256_file(evidence_path),
                    "racket_sha256": evidence["racket_sha256"],
                    "checks": evidence["checks"],
                }
            )

    settings_covered = sorted(item["setting"] for item in episodes)
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "selected_canonical_path_unchanged": True,
        "canonical_default_rule_hash": canonical_hash,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": settings_covered,
        "episodes": episodes,
        "command": command,
        "rule_wrapper": RULE_WRAPPER,
        "rule_wrapper_sha256": sha256_bytes(RULE_WRAPPER.encode()),
        "limitations": [
            "This is an isolated authoring prototype, not an approved production API.",
            "Only forward and both-direction continuation were exercised.",
            "Each retained input intentionally exposes both ends; broader grammars were not assessed.",
            "Identifiability is finite against the single declared parameter rival, not all programs.",
        ],
        "passed": (
            settings_covered == sorted(ALLOWED_EXTENSION_MODES)
            and canonical_hash == gen.RULE_HASH
            and all(
                item["checks"]["all_outputs_from_executed_racket"]
                and item["checks"]["python_mirror_parity"]
                and item["checks"]["demos_distinguish_alternative"]
                and item["checks"]["every_pair_distinguishes_alternative"]
                for item in episodes
            )
        ),
    }
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
