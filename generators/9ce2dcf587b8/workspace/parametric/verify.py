#!/usr/bin/env python3
"""Execute and retain bounded Racket evidence for the parametric prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

import prototype

HERE = Path(__file__).resolve().parent
TASK_ROOT = HERE.parents[1]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _normalized_rule_hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def _load_generator():
    path = TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_9ce2dcf587b8_verify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _seed_for(setting: str, start: int) -> int:
    seed = start
    while prototype.choose_setting(seed) != setting:
        seed += 1
    return seed


def _callable_text(program: str) -> str:
    """Build the bare-bridge callable without optional authoring packages."""
    body = strip_rule_wrapper(program)
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"


def _execute_program(program: str, inputs: list[list[list[int]]]) -> list[list[list[int]]]:
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define __parametric_rule {_callable_text(program)})")
        outputs = []
        for index, grid in enumerate(inputs):
            bridge.define_grid(f"__parametric_input_{index}", grid)
            outputs.append(
                bridge.eval_text(f"(__parametric_rule __parametric_input_{index})")
            )
        return outputs
    finally:
        bridge.shutdown()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify(out_path: Path) -> dict[str, Any]:
    generator, generator_path = _load_generator()
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    if programs["both"] != prototype._canonical_program():
        raise AssertionError("default prototype program is not exact canonical text")
    if _normalized_rule_hash(programs["both"]) != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("default prototype program no longer matches RULE_HASH")
    if generator.RULE_HASH != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("selected generator and prototype rule pins disagree")

    seeds = {
        setting: _seed_for(setting, 20261020)
        for setting in prototype.ALLOWED_SETTINGS
    }
    episodes = {
        setting: prototype.build_episode(seed)
        for setting, seed in seeds.items()
    }

    episode_records: dict[str, Any] = {}
    for setting, episode in episodes.items():
        if episode["meta"][prototype.PARAMETER_NAME] != setting:
            raise AssertionError(f"seed did not select retained setting {setting}")
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        selected_outputs = _execute_program(programs[setting], inputs)
        if selected_outputs != expected:
            raise AssertionError(f"Racket/Python mismatch for setting {setting}")

        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != setting)
        rival_outputs = _execute_program(programs[rival], inputs)
        train_disagreements = [
            index
            for index in range(len(episode["train"]))
            if selected_outputs[index] != rival_outputs[index]
        ]
        query_index = len(episode["train"])
        if len(train_disagreements) != len(episode["train"]):
            raise AssertionError(
                f"not every demonstration distinguishes {setting} from {rival}"
            )
        if selected_outputs[query_index] == rival_outputs[query_index]:
            raise AssertionError(f"query does not depend on setting {setting}")

        episode_records[setting] = {
            "seed": seeds[setting],
            "selected_setting": setting,
            "rival_setting": rival,
            "train_disagreement_indices": train_disagreements,
            "query_disagrees_with_rival": True,
            "episode": episode,
            "racket_outputs": selected_outputs,
            "rival_racket_outputs": rival_outputs,
        }

    public_files = {
        "episode-a": HERE / "public" / "episode-a.json",
        "episode-b": HERE / "public" / "episode-b.json",
    }
    opaque_mapping = {"episode-a": "both", "episode-b": "main_only"}
    for episode_id, setting in opaque_mapping.items():
        challenge = prototype.public_challenge(episodes[setting])
        serialized = json.dumps(challenge, sort_keys=True)
        if any(
            token in serialized
            for token in (prototype.PARAMETER_NAME, setting, "rule!")
        ):
            raise AssertionError(f"public {episode_id} leaks hidden rule metadata")
        if any("output" in pair for pair in challenge["test"]):
            raise AssertionError(f"public {episode_id} leaks a query answer")
        _write_json(public_files[episode_id], challenge)

    source_files = [HERE / "prototype.py", HERE / "verify.py", HERE / "README.md"]
    report = {
        "schema": "9ce2dcf587b8-parametric-prototype-v1",
        "status": "passed",
        "scope": "task-local proposed prototype; not canonical approval",
        "generator": {
            "path": str(generator_path.relative_to(generator_path.parents[2])),
            "sha256": _sha256_file(generator_path),
            "canonical_rule_hash": generator.RULE_HASH,
        },
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_SETTINGS),
            "original_default": prototype.DEFAULT_SETTING,
            "selection": "one deterministic SHA-256-derived value per episode seed",
            "input_constraint": (
                "every pair contains one interior marker, so both diagonal axes "
                "and the main-axis-only setting produce distinct outputs"
            ),
            "invariants": [
                "same marker/object role",
                "same-color painting",
                "source markers preserved",
                "rays continue to the boundary through original zero cells",
                "one setting shared by every demonstration and query",
            ],
        },
        "programs": {
            setting: {
                "text": program,
                "sha256": _sha256_bytes(program.encode()),
                "normalized_rule_hash": _normalized_rule_hash(program),
            }
            for setting, program in programs.items()
        },
        "episodes": episode_records,
        "public_challenges": {
            episode_id: {
                "path": str(path.relative_to(HERE)),
                "sha256": _sha256_file(path),
            }
            for episode_id, path in public_files.items()
        },
        "prototype_sources": {
            str(path.relative_to(HERE)): _sha256_file(path)
            for path in source_files
        },
        "command": (
            "python3 review.py run python3 "
            "generators/9ce2dcf587b8/workspace/parametric/verify.py "
            "--out ../checks/parametric/verification.json"
        ),
        "limitations": [
            "Only the two declared settings and retained seeds are evidenced.",
            "The production generator and selected canonical authority remain unchanged.",
            "This prototype is proposed, not catalog-approved or runtime-integrated.",
        ],
    }
    _write_json(out_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "parameter": report["parameter"],
                "evidence": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
