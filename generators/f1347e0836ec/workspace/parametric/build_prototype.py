#!/usr/bin/env python3
"""Build source-bound Racket evidence for both trigger-diagonal settings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

from prototype import (
    ALLOWED_TRIGGER_DIAGONALS,
    DEFAULT_TRIGGER_DIAGONAL,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    TASK_ID,
    check_identifiability,
    choose_parameters,
    execute_program,
    make_episode,
    public_challenge,
    public_filename,
    racket_program,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def first_seed_for(setting: str) -> int:
    for seed in range(10000):
        if choose_parameters(seed)[PARAMETER_NAME] == setting:
            return seed
    raise AssertionError(f"no deterministic seed found for setting {setting!r}")


def _canonical_parity(bridge: RacketBridge, root: Path) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    program = racket_program({PARAMETER_NAME: DEFAULT_TRIGGER_DIAGONAL})
    actual = execute_program(program, [pair["input"] for pair in pairs], bridge)
    rows = []
    for pair, got in zip(pairs, actual, strict=True):
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input": pair["input"],
                "expected": pair["output"],
                "actual": got,
                "passed": got == pair["output"],
            }
        )
    return {
        "schema": "arc-parametric-canonical-parity-v1",
        "task_id": TASK_ID,
        "setting": DEFAULT_TRIGGER_DIAGONAL,
        "pair_count": len(rows),
        "pairs": rows,
        "passed": bool(rows) and all(row["passed"] for row in rows),
    }


def _separating_witness(bridge: RacketBridge) -> dict[str, Any]:
    grid = [
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 6, 5],
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 5, 5],
        [5, 5, 5, 5, 5, 5],
    ]
    outputs = {
        setting: execute_program(
            racket_program({PARAMETER_NAME: setting}), [grid], bridge
        )[0]
        for setting in ALLOWED_TRIGGER_DIAGONALS
    }
    return {
        "schema": "arc-parametric-separating-witness-v1",
        "task_id": TASK_ID,
        "input": grid,
        "outputs": outputs,
        "passed": outputs["main"] != outputs["anti"],
    }


def _ambiguity_diagnostic(bridge: RacketBridge) -> dict[str, Any]:
    grid = [
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 8, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ]
    output = execute_program(
        racket_program({PARAMETER_NAME: DEFAULT_TRIGGER_DIAGONAL}), [grid], bridge
    )[0]
    result = check_identifiability(
        [{"input": grid, "output": output}], bridge=bridge
    )
    return {
        "schema": "arc-parametric-ambiguity-diagnostic-v1",
        "task_id": TASK_ID,
        "input": grid,
        "output": output,
        "identifiability": result,
        "passed": result["surviving_settings"] == list(ALLOWED_TRIGGER_DIAGONALS),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    if out_dir.exists():
        parser.error("--out-dir already exists; use a fresh path to preserve evidence")
    out_dir.mkdir(parents=True)

    root = find_root(__file__)
    generator_bundle = load_selected_generator(TASK_ID, root=root)
    _, generator_path, generator_sha256 = generator_bundle
    source_dir = Path(__file__).resolve().parent

    programs: dict[str, dict[str, str]] = {}
    for setting in ALLOWED_TRIGGER_DIAGONALS:
        source = racket_program({PARAMETER_NAME: setting})
        path = out_dir / f"program-{setting}.rkt"
        path.write_text(source + "\n", encoding="utf-8")
        programs[setting] = {
            "file": path.name,
            "sha256": sha256_file(path),
        }

    episodes: list[dict[str, Any]] = []
    public_redacted = True
    with RacketBridge(timeout=20, max_calls_before_restart=48) as bridge:
        for setting in ALLOWED_TRIGGER_DIAGONALS:
            seed = first_seed_for(setting)
            episode = make_episode(
                seed, bridge=bridge, generator_bundle=generator_bundle
            )
            if episode["parameters"][PARAMETER_NAME] != setting:
                raise AssertionError("seed-to-setting lookup changed during build")
            episode["racket_program_sha256"] = sha256_bytes(
                episode["racket_program"].encode("utf-8")
            )
            private_path = out_dir / f"episode-{setting}.json"
            write_json(private_path, episode)

            challenge = public_challenge(episode)
            challenge_path = out_dir / public_filename(challenge)
            write_json(challenge_path, challenge)
            challenge_text = challenge_path.read_text(encoding="utf-8").lower()
            leaked = any(
                secret in challenge_text
                for secret in (
                    '"seed"',
                    '"parameters"',
                    '"parameter_spec"',
                    '"trigger_diagonal"',
                    '"racket_program"',
                    '"input_generation"',
                )
            ) or set(challenge["query"]) != {"input"}
            public_redacted = public_redacted and not leaked
            episodes.append(
                {
                    "setting": setting,
                    "seed": seed,
                    "private_file": private_path.name,
                    "private_sha256": sha256_file(private_path),
                    "public_file": challenge_path.name,
                    "public_sha256": sha256_file(challenge_path),
                    "surviving_settings": episode["identifiability"][
                        "surviving_settings"
                    ],
                    "unique": episode["identifiability"]["unique"],
                }
            )

        canonical = _canonical_parity(bridge, root)
        witness = _separating_witness(bridge)
        ambiguity = _ambiguity_diagnostic(bridge)

    write_json(out_dir / "canonical-parity.json", canonical)
    write_json(out_dir / "separating-witness.json", witness)
    write_json(out_dir / "ambiguity-diagnostic.json", ambiguity)

    source_hashes = {
        "prototype.py": sha256_file(source_dir / "prototype.py"),
        "build_prototype.py": sha256_file(Path(__file__).resolve()),
        "selected_generator.py": generator_sha256,
    }
    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}
    receipt = {
        "schema": "arc-parametric-build-receipt-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "command": command,
        "selected_generator_path": str(generator_path),
        "source_hashes": source_hashes,
        "programs": programs,
    }
    write_json(out_dir / "receipt.json", receipt)

    unique_episodes = all(
        item["unique"] and item["surviving_settings"] == [item["setting"]]
        for item in episodes
    )
    checks = {
        "ambiguity_diagnostic_keeps_both_settings": ambiguity["passed"],
        "canonical_default_exact_parity": canonical["passed"],
        "public_challenges_redacted": public_redacted,
        "separating_witness_differs": witness["passed"],
        "unique_complete_episodes": unique_episodes,
    }
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "isolated-prototype-not-approved-production-api",
        "selected_canonical_authority_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": sorted(item["setting"] for item in episodes),
        "episodes": episodes,
        "checks": checks,
        "source_hashes": source_hashes,
        "programs": programs,
        "command": command,
        "limitations": [
            "Only the declared main/anti predicate settings were evaluated.",
            "The selected generator supplies lawful inputs; this prototype does not replace it.",
            "Finite deterministic evidence is not a proof over every possible valid grid.",
        ],
        "passed": all(checks.values()),
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
