#!/usr/bin/env python3
"""Build Racket-executed evidence for both parametric settings."""
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
    ALLOWED_ERASE_SCOPES,
    DEFAULT_ERASE_SCOPE,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    TASK_ID,
    choose_parameters,
    grid_literal,
    public_challenge,
    python_reference,
    racket_program,
)

BANDS = ("easy", "medium", "hard")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_seed_for(scope: str) -> int:
    for seed in range(10000):
        if choose_parameters(seed)[PARAMETER_NAME] == scope:
            return seed
    raise AssertionError(f"no deterministic seed found for {scope}")


def execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    result = bridge.eval_text(f"({source} {grid_literal(grid)})")
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) for row in result)
    ):
        raise RuntimeError(f"Racket returned a non-grid: {result!r}")
    return [[int(value) for value in row] for row in result]


def build_episode(gen: Any, bridge: RacketBridge, seed: int) -> dict[str, Any]:
    parameters = choose_parameters(seed)
    scope = parameters[PARAMETER_NAME]
    source = racket_program(parameters)
    alternative_sources = {
        other: racket_program({PARAMETER_NAME: other})
        for other in ALLOWED_ERASE_SCOPES
        if other != scope
    }

    pairs: list[dict[str, Any]] = []
    rival_outputs: list[dict[str, Any]] = []
    for index in range(4):
        grid = gen.generate(seed * 1000 + 137, index, difficulty=BANDS[index % len(BANDS)])
        output = execute(bridge, source, grid)
        mirror = python_reference(grid, erase_scope=scope)
        if output != mirror:
            raise AssertionError("prototype Python mirror disagrees with executed Racket")
        if scope == DEFAULT_ERASE_SCOPE and output != gen.rule_mirror(grid):
            raise AssertionError("default prototype setting diverges from canonical rule")
        alternatives = {
            other: execute(bridge, other_source, grid)
            for other, other_source in alternative_sources.items()
        }
        if any(other_output == output for other_output in alternatives.values()):
            raise AssertionError("episode pair does not distinguish the rule settings")
        pairs.append({"input": grid, "output": output})
        rival_outputs.append(alternatives)

    episode = {"demos": pairs[:3], "query": pairs[3]}
    demos_distinguish = {
        other: any(
            rival_outputs[index][other] != pairs[index]["output"]
            for index in range(3)
        )
        for other in alternative_sources
    }
    if not all(demos_distinguish.values()):
        raise AssertionError("demonstrations do not identify the chosen parameter setting")

    return {
        "schema": "arc-parametric-episode-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": parameters,
        "parameter_spec": PARAMETER_SPEC,
        "racket_program": source,
        "racket_sha256": sha256_bytes(source.encode()),
        "episode": episode,
        "alternative_outputs": rival_outputs,
        "checks": {
            "parameter_chosen_once_for_episode": True,
            "three_demonstrations": len(episode["demos"]) == 3,
            "query_present": "output" in episode["query"],
            "all_outputs_from_executed_racket": True,
            "python_mirror_parity": True,
            "default_matches_selected_canonical_rule": (
                scope != DEFAULT_ERASE_SCOPE
                or all(
                    pair["output"] == gen.rule_mirror(pair["input"])
                    for pair in pairs
                )
            ),
            "demos_distinguish_each_alternative": demos_distinguish,
            "every_pair_distinguishes_each_alternative": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; use a new path to preserve evidence")
    out.mkdir(parents=True)

    root = find_root(__file__)
    gen, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    source_dir = Path(__file__).resolve().parent
    command = {
        "cwd": os.getcwd(),
        "argv": [sys.executable, *sys.argv],
    }
    episodes: list[dict[str, Any]] = []
    with RacketBridge(timeout=20, max_calls_before_restart=48) as bridge:
        for index, scope in enumerate(ALLOWED_ERASE_SCOPES):
            seed = first_seed_for(scope)
            evidence = build_episode(gen, bridge, seed)
            challenge = public_challenge(evidence["episode"])
            challenge_path = out / f"challenge-{index:03d}.json"
            evidence_path = out / f"evidence-{index:03d}.json"
            write_json(challenge_path, challenge)
            evidence.update(
                {
                    "public_challenge": challenge_path.name,
                    "public_challenge_sha256": sha256_file(challenge_path),
                    "source_hashes": {
                        "prototype.py": sha256_file(source_dir / "prototype.py"),
                        "build_prototype.py": sha256_file(Path(__file__).resolve()),
                        "selected_generator.py": generator_sha256,
                    },
                    "command": command,
                }
            )
            write_json(evidence_path, evidence)
            episodes.append(
                {
                    "index": index,
                    "seed": seed,
                    "setting": scope,
                    "challenge": challenge_path.name,
                    "challenge_sha256": sha256_file(challenge_path),
                    "evidence": evidence_path.name,
                    "evidence_sha256": sha256_file(evidence_path),
                    "racket_sha256": evidence["racket_sha256"],
                    "checks": evidence["checks"],
                }
            )

    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "selected_canonical_path_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": sorted(item["setting"] for item in episodes),
        "episodes": episodes,
        "command": command,
        "limitations": [
            "This is an isolated prototype, not an approved production API.",
            "Only two erase-scope settings and two deterministic episode seeds were executed.",
            "All generated inputs intentionally expose the top marker, so the settings are easy to distinguish; broader input grammars were not assessed.",
        ],
        "passed": (
            sorted(item["setting"] for item in episodes)
            == sorted(ALLOWED_ERASE_SCOPES)
            and all(
                item["checks"]["all_outputs_from_executed_racket"]
                and all(item["checks"]["demos_distinguish_each_alternative"].values())
                for item in episodes
            )
        ),
    }
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
