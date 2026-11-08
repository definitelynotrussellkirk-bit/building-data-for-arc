#!/usr/bin/env python3
"""Execute and retain bounded Racket evidence for the task-local prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

import prototype


HERE = Path(__file__).resolve().parent


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _seed_for(setting: str, start: int) -> int:
    seed = start
    while prototype.choose_setting(seed) != setting:
        seed += 1
    return seed


def _execute_program(program: str, inputs: list[list[list[int]]]) -> list[list[list[int]]]:
    bridge = RacketBridge()
    try:
        # Both prototype programs are body-form rules.  Avoid the production
        # source-conversion path here: the bounded review packet deliberately
        # omits its optional authoring-only ``scripts`` package.
        body = strip_rule_wrapper(program)
        callable_text = f"(lambda (g) {body})"
        bridge.eval_text(f"(define __parametric_rule {callable_text})")
        outputs = []
        for index, grid in enumerate(inputs):
            bridge.define_grid(f"__parametric_input_{index}", grid)
            outputs.append(
                bridge.eval_text(
                    f"(__parametric_rule __parametric_input_{index})"
                )
            )
        return outputs
    finally:
        bridge.shutdown()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify(out_path: Path) -> dict[str, Any]:
    seeds = {
        "all": _seed_for("all", 20261019),
        "cross_only": _seed_for("cross_only", 20261019),
    }
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    episodes = {
        setting: prototype.build_episode(seed)
        for setting, seed in seeds.items()
    }

    episode_records: dict[str, Any] = {}
    for setting, episode in episodes.items():
        assert episode["meta"][prototype.PARAMETER_NAME] == setting
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        expected = [pair["output"] for pair in pairs]
        racket_outputs = _execute_program(programs[setting], inputs)
        if racket_outputs != expected:
            raise AssertionError(f"Racket/Python mismatch for setting {setting}")

        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != setting)
        rival_outputs = _execute_program(programs[rival], inputs)
        train_disagreements = [
            index
            for index in range(len(episode["train"]))
            if racket_outputs[index] != rival_outputs[index]
        ]
        query_index = len(episode["train"])
        if not train_disagreements:
            raise AssertionError(
                f"training pairs do not distinguish {setting} from {rival}"
            )
        if racket_outputs[query_index] == rival_outputs[query_index]:
            raise AssertionError(
                f"query does not depend on selected setting {setting}"
            )

        episode_records[setting] = {
            "seed": seeds[setting],
            "selected_setting": setting,
            "rival_setting": rival,
            "train_disagreement_indices": train_disagreements,
            "query_disagrees_with_rival": True,
            "episode": episode,
            "racket_outputs": racket_outputs,
            "rival_racket_outputs": rival_outputs,
        }

    public_dir = HERE / "public"
    public_files = {
        "episode-a": public_dir / "episode-a.json",
        "episode-b": public_dir / "episode-b.json",
    }
    opaque_mapping = {
        "episode-a": "all",
        "episode-b": "cross_only",
    }
    for episode_id, setting in opaque_mapping.items():
        challenge = prototype.public_challenge(episodes[setting])
        serialized = json.dumps(challenge, sort_keys=True)
        forbidden = (
            prototype.PARAMETER_NAME,
            setting,
            "rule!",
            '"output"}], "test"',
        )
        if any(token in serialized for token in forbidden[:3]):
            raise AssertionError(f"public {episode_id} leaks hidden rule metadata")
        if any("output" in pair for pair in challenge["test"]):
            raise AssertionError(f"public {episode_id} leaks a query answer")
        _write_json(public_files[episode_id], challenge)

    source_files = [HERE / "prototype.py", HERE / "verify.py", HERE / "README.md"]
    report = {
        "schema": "de49e9901e3a-parametric-prototype-v1",
        "status": "passed",
        "scope": "task-local proposed prototype; not canonical approval",
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_SETTINGS),
            "original_default": prototype.DEFAULT_SETTING,
            "selection": "one deterministic SHA-256-derived value per episode seed",
            "input_constraint": (
                "every episode includes at least one non-cross 4-connected object "
                "in demonstrations and query so all vs cross_only is observable"
            ),
        },
        "programs": {
            setting: {
                "text": program,
                "sha256": _sha256_bytes(program.encode()),
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
            "generators/de49e9901e3a/workspace/parametric/verify.py "
            "--out ../checks/parametric/verification.json"
        ),
        "limitations": [
            "Only the two declared settings and the retained seeds are evidenced.",
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
