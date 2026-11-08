#!/usr/bin/env python3
"""Build source-bound, Racket-executed evidence for both connectivity settings."""
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
    ALLOWED_CONNECTIVITY,
    DEFAULT_CONNECTIVITY,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    TASK_ID,
    choose_parameters,
    make_input,
    public_challenge,
    python_reference,
    racket_callable,
    racket_program,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def first_seed_for(setting: str) -> int:
    for seed in range(10_000):
        if choose_parameters(seed)[PARAMETER_NAME] == setting:
            return seed
    raise AssertionError(f"no deterministic seed found for {setting}")


def execute(
    bridge: RacketBridge,
    setting: str,
    grid: list[list[int]],
    receipts: list[dict[str, Any]],
    *,
    label: str,
) -> list[list[int]]:
    parameters = {PARAMETER_NAME: setting}
    source = racket_program(parameters)
    callable_source = racket_callable(parameters)
    bridge.define_grid("g", grid)
    result = bridge.eval_text(f"({callable_source} g)")
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) and row for row in result)
    ):
        raise RuntimeError(f"Racket returned a non-grid: {result!r}")
    output = [[int(value) for value in row] for row in result]
    receipts.append(
        {
            "label": label,
            "setting": setting,
            "program_sha256": sha256_bytes(source.encode()),
            "callable_sha256": sha256_bytes(callable_source.encode()),
            "input_sha256": grid_sha256(grid),
            "output_sha256": grid_sha256(output),
            "input": grid,
            "output": output,
        }
    )
    return output


def build_episode(
    bridge: RacketBridge,
    episode_seed: int,
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    parameters = choose_parameters(episode_seed)
    setting = parameters[PARAMETER_NAME]
    alternatives = [
        other for other in ALLOWED_CONNECTIVITY if other != setting
    ]

    pairs: list[dict[str, Any]] = []
    rival_outputs: list[dict[str, list[list[int]]]] = []
    for index in range(4):
        grid = make_input(episode_seed * 10_000 + 137, index)
        output = execute(
            bridge,
            setting,
            grid,
            receipts,
            label=f"episode-{episode_seed}-pair-{index}-{setting}",
        )
        mirror = python_reference(grid, connectivity=setting)
        if output != mirror:
            raise AssertionError("executed Racket disagrees with Python debug mirror")
        candidates = {
            other: execute(
                bridge,
                other,
                grid,
                receipts,
                label=f"episode-{episode_seed}-pair-{index}-rival-{other}",
            )
            for other in alternatives
        }
        if any(candidate == output for candidate in candidates.values()):
            raise AssertionError("pair does not distinguish connectivity settings")
        pairs.append({"input": grid, "output": output})
        rival_outputs.append(candidates)

    episode = {
        "seed": episode_seed,
        "parameters": parameters,
        "racket_program": racket_program(parameters),
        "demos": pairs[:3],
        "query": pairs[3],
    }
    demos_distinguish = {
        other: any(
            rival_outputs[index][other] != pairs[index]["output"]
            for index in range(3)
        )
        for other in alternatives
    }
    if not all(demos_distinguish.values()):
        raise AssertionError("demonstrations do not identify the episode setting")

    return {
        "schema": "arc-parametric-flood-connectivity-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "episode": episode,
        "parameter_spec": PARAMETER_SPEC,
        "rival_outputs": rival_outputs,
        "checks": {
            "parameter_chosen_once_for_episode": True,
            "three_demonstrations": len(episode["demos"]) == 3,
            "query_present_in_private_evidence": "output" in episode["query"],
            "all_outputs_from_executed_racket": True,
            "python_debug_mirror_parity": True,
            "demos_distinguish_each_alternative": demos_distinguish,
            "every_pair_distinguishes_each_alternative": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; use a new path to preserve evidence")
    out.mkdir(parents=True)
    (out / "public").mkdir()
    (out / "private").mkdir()
    (out / "private" / "programs").mkdir()

    root = find_root(__file__)
    _, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    source_dir = Path(__file__).resolve().parent
    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}
    receipts: list[dict[str, Any]] = []

    programs: dict[str, dict[str, str]] = {}
    for setting in ALLOWED_CONNECTIVITY:
        source = racket_program({PARAMETER_NAME: setting})
        path = out / "private" / "programs" / f"connectivity-{setting}.rkt"
        path.write_text(source + "\n", encoding="utf-8")
        programs[setting] = {
            "file": str(path.relative_to(out)),
            "sha256": sha256_bytes(source.encode()),
            "text": source,
            "callable_sha256": sha256_bytes(
                racket_callable({PARAMETER_NAME: setting}).encode()
            ),
        }

    canonical_checks: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    with RacketBridge(timeout=20, max_calls_before_restart=64) as bridge:
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root)):
            actual = execute(
                bridge,
                DEFAULT_CONNECTIVITY,
                pair["input"],
                receipts,
                label=f"canonical-{index}-{DEFAULT_CONNECTIVITY}",
            )
            canonical_checks.append(
                {
                    "index": index,
                    "input": pair["input"],
                    "expected": pair["output"],
                    "actual": actual,
                    "passed": actual == pair["output"],
                }
            )
        if not all(row["passed"] for row in canonical_checks):
            raise AssertionError("default setting does not match canonical pairs")

        for index, setting in enumerate(ALLOWED_CONNECTIVITY):
            seed = first_seed_for(setting)
            evidence = build_episode(bridge, seed, receipts)
            challenge = public_challenge(evidence["episode"])
            challenge_path = out / "public" / f"episode-{index:03d}.json"
            evidence_path = out / "private" / f"episode-{index:03d}.json"
            write_json(challenge_path, challenge)
            evidence.update(
                {
                    "public_challenge": str(challenge_path.relative_to(out)),
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
            episode_rows.append(
                {
                    "index": index,
                    "seed": seed,
                    "setting": setting,
                    "challenge": str(challenge_path.relative_to(out)),
                    "challenge_sha256": sha256_file(challenge_path),
                    "evidence": str(evidence_path.relative_to(out)),
                    "evidence_sha256": sha256_file(evidence_path),
                    "checks": evidence["checks"],
                }
            )

        counterfactual_input = make_input(271_828, 0)
        counterfactual_outputs = {
            setting: execute(
                bridge,
                setting,
                counterfactual_input,
                receipts,
                label=f"counterfactual-{setting}",
            )
            for setting in ALLOWED_CONNECTIVITY
        }

    canonical_path = out / "private" / "canonical-checks.json"
    counterfactual_path = out / "private" / "counterfactual.json"
    receipts_path = out / "private" / "bridge-receipts.json"
    write_json(canonical_path, canonical_checks)
    write_json(
        counterfactual_path,
        {
            "input": counterfactual_input,
            "outputs": counterfactual_outputs,
            "outputs_differ": len(
                {
                    json.dumps(value, separators=(",", ":"))
                    for value in counterfactual_outputs.values()
                }
            )
            == len(ALLOWED_CONNECTIVITY),
        },
    )
    write_json(receipts_path, receipts)

    settings_covered = sorted(row["setting"] for row in episode_rows)
    summary: dict[str, Any] = {
        "schema": "arc-parametric-flood-connectivity-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "selected_canonical_path_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": settings_covered,
        "programs": programs,
        "canonical_checks": {
            "file": str(canonical_path.relative_to(out)),
            "count": len(canonical_checks),
            "passed": all(row["passed"] for row in canonical_checks),
        },
        "episodes": episode_rows,
        "bridge_receipts": {
            "file": str(receipts_path.relative_to(out)),
            "count": len(receipts),
        },
        "counterfactual": str(counterfactual_path.relative_to(out)),
        "source_hashes": {
            "prototype.py": sha256_file(source_dir / "prototype.py"),
            "build_prototype.py": sha256_file(Path(__file__).resolve()),
            "selected_generator.py": generator_sha256,
            "selected_generator_path": str(generator_path),
        },
        "command": command,
        "limitations": [
            "This is an isolated proposed prototype, not a production rule API or approval.",
            "Only two connectivity settings and two deterministic complete episodes were retained.",
            "The bounded constructor intentionally makes every pair distinguish the settings; broader natural wall fields were not sampled.",
            "The alternate Racket implementation relies on unique seed colors and one seed per component, both explicit prototype-domain constraints.",
            "Finite Racket execution and rival checks do not establish universal induction or training eligibility.",
        ],
    }
    summary["passed"] = (
        settings_covered == sorted(ALLOWED_CONNECTIVITY)
        and summary["canonical_checks"]["passed"]
        and json.loads(counterfactual_path.read_text())["outputs_differ"]
        and all(
            row["checks"]["all_outputs_from_executed_racket"]
            and all(
                row["checks"]["demos_distinguish_each_alternative"].values()
            )
            for row in episode_rows
        )
    )
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
