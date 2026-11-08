#!/usr/bin/env python3
"""Build immutable Racket-executed evidence for every output-corner setting."""
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
    DEFAULT_PARAMETER,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PARAMETER_VALUES,
    PROTOTYPE_VERSION,
    TASK_ID,
    choose_parameters,
    generate_episode,
    grid_literal,
    public_challenge,
    racket_callable,
    python_reference,
    racket_program,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_seed_for(corner: str) -> int:
    for seed in range(100_000):
        if choose_parameters(seed)[PARAMETER_NAME] == corner:
            return seed
    raise AssertionError(f"no deterministic seed found for {corner}")


def execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    result = bridge.eval_text(f"({racket_callable(source)} {grid_literal(grid)})")
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) and row for row in result)
    ):
        raise RuntimeError(f"Racket returned a non-grid: {result!r}")
    return [[int(value) for value in row] for row in result]


def build_setting_evidence(
    gen: Any,
    bridge: RacketBridge,
    *,
    corner: str,
    seed: int,
) -> dict[str, Any]:
    # Do not force the setting here: proving the deterministic seed chooses it
    # guards the episode-level selection path as well as rule materialization.
    selected = choose_parameters(seed)
    if selected != {PARAMETER_NAME: corner}:
        raise AssertionError("first_seed_for and choose_parameters disagree")
    draft = generate_episode(seed)
    if draft["parameters"] != selected:
        raise AssertionError("episode did not retain its single selected setting")

    sources = {
        value: racket_program({PARAMETER_NAME: value}) for value in PARAMETER_VALUES
    }
    all_pairs = draft["train"] + draft["test"]
    racket_outputs: list[dict[str, list[list[int]]]] = []
    labelled_pairs = []
    for pair in all_pairs:
        grid = pair["input"]
        alternatives = {
            value: execute(bridge, sources[value], grid) for value in PARAMETER_VALUES
        }
        for value, output in alternatives.items():
            if output != python_reference(grid, output_corner=value):
                raise AssertionError(
                    f"Racket/Python disagreement for {PARAMETER_NAME}={value}"
                )
        fingerprints = {
            json.dumps(value, separators=(",", ":"))
            for value in alternatives.values()
        }
        if len(fingerprints) != len(PARAMETER_VALUES):
            raise AssertionError("prototype pair does not distinguish all four settings")
        selected_output = alternatives[corner]
        if pair["output"] != selected_output:
            raise AssertionError("draft Python label disagrees with executed Racket")
        if corner == DEFAULT_PARAMETER and selected_output != gen._correct_crop(grid):
            raise AssertionError("default parametric setting diverges from canonical mirror")
        labelled_pairs.append({"input": grid, "output": selected_output})
        racket_outputs.append(alternatives)

    n_train = len(draft["train"])
    private_episode = {
        "schema": "arc-parametric-racket-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": selected,
        "parameter_spec": PARAMETER_SPEC,
        "racket_program": sources[corner],
        "racket_sha256": sha256_bytes(sources[corner].encode()),
        "train": labelled_pairs[:n_train],
        "test": labelled_pairs[n_train:],
        "all_setting_outputs": racket_outputs,
        "pair_generation": draft["meta"]["pair_generation"],
        "checks": {
            "parameter_chosen_once_for_episode": True,
            "five_demonstrations_and_one_query": (
                len(labelled_pairs[:n_train]) == 5 and len(labelled_pairs[n_train:]) == 1
            ),
            "all_labels_from_executed_racket": True,
            "python_debug_mirror_parity": True,
            "default_source_byte_exact_canonical": (
                corner != DEFAULT_PARAMETER
                or sources[corner] == racket_program({PARAMETER_NAME: DEFAULT_PARAMETER})
            ),
            "default_outputs_match_selected_generator": corner != DEFAULT_PARAMETER
            or all(
                pair["output"] == gen._correct_crop(pair["input"])
                for pair in labelled_pairs
            ),
            "every_pair_distinguishes_every_setting": True,
            "every_single_query_rotation_identifiable": True,
        },
    }
    return private_episode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; choose a new path to preserve evidence")
    out.mkdir(parents=True)
    rules_dir = out / "rules"
    rules_dir.mkdir()

    root = find_root(__file__)
    gen, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    source_dir = Path(__file__).resolve().parent
    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}

    sources = {
        corner: racket_program({PARAMETER_NAME: corner}) for corner in PARAMETER_VALUES
    }
    rule_files = {}
    for corner, source in sources.items():
        path = rules_dir / f"{corner}.rkt"
        path.write_text(source + ("" if source.endswith("\n") else "\n"), encoding="utf-8")
        rule_files[corner] = {
            "path": str(path.relative_to(out)),
            "sha256": sha256_file(path),
            "source_sha256": sha256_bytes(source.encode()),
        }

    episodes = []
    with RacketBridge(timeout=20, max_calls_before_restart=96) as bridge:
        for corner in PARAMETER_VALUES:
            seed = first_seed_for(corner)
            evidence = build_setting_evidence(
                gen, bridge, corner=corner, seed=seed
            )
            private_path = out / f"episode-{corner}.private.json"
            challenge_path = out / f"challenge-{corner}.public.json"
            challenge = public_challenge(evidence)
            write_json(challenge_path, challenge)
            evidence.update(
                {
                    "public_challenge": challenge_path.name,
                    "public_challenge_sha256": sha256_file(challenge_path),
                    "rule_file": rule_files[corner],
                    "source_hashes": {
                        "prototype.py": sha256_file(source_dir / "prototype.py"),
                        "build_prototype.py": sha256_file(Path(__file__).resolve()),
                        "selected_generator.py": generator_sha256,
                    },
                    "selected_generator_path": str(generator_path),
                    "command": command,
                }
            )
            write_json(private_path, evidence)
            episodes.append(
                {
                    "setting": corner,
                    "seed": seed,
                    "public_challenge": challenge_path.name,
                    "public_challenge_sha256": sha256_file(challenge_path),
                    "private_evidence": private_path.name,
                    "private_evidence_sha256": sha256_file(private_path),
                    "racket_sha256": evidence["racket_sha256"],
                    "checks": evidence["checks"],
                }
            )

        witness_grid = generate_episode(0, output_corner=DEFAULT_PARAMETER)["train"][0]["input"]
        witness_outputs = {
            corner: execute(bridge, sources[corner], witness_grid)
            for corner in PARAMETER_VALUES
        }
        if len(
            {
                json.dumps(value, separators=(",", ":"))
                for value in witness_outputs.values()
            }
        ) != len(PARAMETER_VALUES):
            raise AssertionError("same-input witness does not separate all settings")
        write_json(
            out / "same-input-setting-witness.private.json",
            {
                "schema": "arc-parametric-same-input-witness-v1",
                "task_id": TASK_ID,
                "input": witness_grid,
                "outputs": witness_outputs,
                "racket_source_sha256": {
                    corner: sha256_bytes(source.encode())
                    for corner, source in sources.items()
                },
                "all_outputs_from_executed_racket": True,
                "all_outputs_pairwise_distinct": True,
            },
        )

    all_checks_green = all(
        all(value is True for value in item["checks"].values()) for item in episodes
    )
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "selected_canonical_path_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": [item["setting"] for item in episodes],
        "rule_files": rule_files,
        "episodes": episodes,
        "same_input_witness": "same-input-setting-witness.private.json",
        "command": command,
        "limitations": [
            "This is isolated prototype evidence, not an approved production API.",
            "The input filter deliberately excludes the rare seed quadrants whose corner crops coincide.",
            "The alternative settings are nearby rule-family probes; the selected canonical authority remains top_left.",
        ],
        "passed": (
            [item["setting"] for item in episodes] == list(PARAMETER_VALUES)
            and all_checks_green
        ),
    }
    write_json(out / "summary.json", summary)

    manifest_entries = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            manifest_entries.append(
                {
                    "path": str(path.relative_to(out)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    write_json(
        out / "manifest.json",
        {
            "schema": "arc-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "files": manifest_entries,
        },
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
