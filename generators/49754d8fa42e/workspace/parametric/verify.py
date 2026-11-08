#!/usr/bin/env python3
"""Retain bounded offline Racket evidence for the rotation prototype."""
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
REPO = HERE.parents[3]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_for(setting: int, start: int) -> int:
    seed = start
    while prototype.choose_setting(seed) != setting:
        seed += 1
    return seed


def _canonical_program() -> str:
    found: set[str] = set()
    for line in prototype.CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == prototype.TASK_ID:
            found.add(record["program_solution"])
    if len(found) != 1:
        raise AssertionError(f"expected one exact canonical program, found {len(found)}")
    return next(iter(found))


def _execute_program(program: str, inputs: list[list[list[int]]]) -> list[list[list[int]]]:
    bridge = RacketBridge()
    try:
        body = strip_rule_wrapper(program)
        bridge.eval_text(f"(define __parametric_rule {body})")
        outputs: list[list[list[int]]] = []
        for index, grid in enumerate(inputs):
            name = f"__parametric_input_{index}"
            bridge.define_grid(name, grid)
            outputs.append(bridge.eval_text(f"(__parametric_rule {name})"))
        return outputs
    finally:
        bridge.shutdown()


def _differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def verify(out_path: Path) -> dict[str, Any]:
    canonical_program = _canonical_program()
    if prototype.program_for(prototype.DEFAULT_SETTING) != canonical_program:
        raise AssertionError("default prototype program is not exact canonical authority")

    settings = prototype.ALLOWED_SETTINGS
    seeds = {setting: _seed_for(setting, 20261020) for setting in settings}
    programs = {setting: prototype.program_for(setting) for setting in settings}
    episodes = {setting: prototype.build_episode(seeds[setting]) for setting in settings}

    private_dir = out_path.parent / "private"
    rules_dir = private_dir / "rules"
    rule_files: dict[int, Path] = {}
    for setting, program in programs.items():
        path = rules_dir / f"quarter-turns-{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program + "\n", encoding="utf-8")
        rule_files[setting] = path

    # Execute each complete rule once over every retained input.  Slicing the
    # results by episode lets each setting be checked against all three rivals
    # without relying on the Python mirror for disagreement evidence.
    flattened_inputs: list[list[list[int]]] = []
    spans: dict[int, tuple[int, int]] = {}
    for setting in settings:
        episode = episodes[setting]
        if episode["meta"][prototype.PARAMETER_NAME] != setting:
            raise AssertionError(f"seed {seeds[setting]} did not select setting {setting}")
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        start = len(flattened_inputs)
        flattened_inputs.extend(inputs)
        spans[setting] = (start, len(flattened_inputs))

    all_outputs = {
        setting: _execute_program(program, flattened_inputs)
        for setting, program in programs.items()
    }

    episode_records: dict[int, Any] = {}
    for selected in settings:
        episode = episodes[selected]
        start, stop = spans[selected]
        selected_outputs = all_outputs[selected][start:stop]
        expected = [pair["output"] for pair in episode["train"] + episode["test"]]
        if selected_outputs != expected:
            raise AssertionError(f"Racket/Python mismatch for setting {selected}")

        train_disagreements_by_rival: dict[int, list[int]] = {}
        query_disagrees_by_rival: dict[int, bool] = {}
        rival_outputs: dict[int, list[list[list[int]]]] = {}
        train_count = len(episode["train"])
        for rival in settings:
            if rival == selected:
                continue
            outputs = all_outputs[rival][start:stop]
            rival_outputs[rival] = outputs
            disagreements = [
                index
                for index in range(train_count)
                if selected_outputs[index] != outputs[index]
            ]
            query_disagreements = [
                selected_outputs[index] != outputs[index]
                for index in range(train_count, stop - start)
            ]
            if not disagreements:
                raise AssertionError(
                    f"training for setting {selected} does not distinguish rival {rival}"
                )
            if not query_disagreements or not all(query_disagreements):
                raise AssertionError(
                    f"not every query for setting {selected} depends on rival {rival}"
                )
            train_disagreements_by_rival[rival] = disagreements
            query_disagrees_by_rival[rival] = True

        private_episode = private_dir / f"episode-{selected}.json"
        private_record = {
            "seed": seeds[selected],
            "selected_setting": selected,
            "train_disagreements_by_rival": train_disagreements_by_rival,
            "query_disagrees_by_rival": query_disagrees_by_rival,
            "episode": episode,
            "selected_racket_outputs": selected_outputs,
            "rival_racket_outputs": rival_outputs,
        }
        _write_json(private_episode, private_record)
        episode_records[selected] = {
            "seed": seeds[selected],
            "selected_setting": selected,
            "train_disagreements_by_rival": train_disagreements_by_rival,
            "query_disagrees_by_rival": query_disagrees_by_rival,
            "private_episode_path": str(private_episode.relative_to(out_path.parent)),
            "private_episode_sha256": _sha256_file(private_episode),
        }

    witness_episode = episodes[prototype.DEFAULT_SETTING]
    witness_offset = spans[prototype.DEFAULT_SETTING][0] + len(witness_episode["train"])
    witness_input = witness_episode["test"][0]["input"]
    witness_outputs = {
        setting: all_outputs[setting][witness_offset]
        for setting in settings
    }
    if len({json.dumps(value) for value in witness_outputs.values()}) != len(settings):
        raise AssertionError("retained witness does not distinguish all rotation settings")
    witness_path = private_dir / "distinguishing-witness.json"
    _write_json(
        witness_path,
        {
            "input": witness_input,
            "mode_color": prototype.mode_color(witness_input),
            "outputs": witness_outputs,
            "differing_cells_from_default": {
                setting: _differing_cells(
                    witness_outputs[prototype.DEFAULT_SETTING], output
                )
                for setting, output in witness_outputs.items()
                if setting != prototype.DEFAULT_SETTING
            },
        },
    )

    public_dir = HERE / "public"
    public_files: dict[str, Path] = {}
    for label, setting in zip(("a", "b", "c", "d"), settings, strict=True):
        challenge = prototype.public_challenge(episodes[setting])
        serialized = json.dumps(challenge, sort_keys=True)
        for forbidden in (prototype.PARAMETER_NAME, "rule!", '"program"'):
            if forbidden in serialized:
                raise AssertionError(f"public episode-{label} leaks {forbidden!r}")
        if any("output" in pair for pair in challenge["test"]):
            raise AssertionError(f"public episode-{label} leaks a query answer")
        path = public_dir / f"episode-{label}.json"
        _write_json(path, challenge)
        public_files[f"episode-{label}"] = path

    source_files = [
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        prototype.GENERATOR_PATH,
    ]
    report: dict[str, Any] = {
        "schema": "49754d8fa42e-parametric-rotation-v1",
        "status": "passed",
        "scope": "task-local proposed prototype; not canonical approval",
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(settings),
            "original_default": prototype.DEFAULT_SETTING,
            "selection": "one deterministic SHA-256-derived value per episode seed",
            "invariants": [
                "the nonzero mode remains the classifier",
                "mode 1/2/3 retain plus/T/right-facing-L glyph identities before rotation",
                "output dimensions remain 3x3 and drawn only with colors 0 and 5",
                "the chosen quarter-turn count is fixed across all demonstrations and queries",
            ],
            "input_constraint": (
                "five demonstrations cover mode classes 1, 2, and 3; both queries use "
                "rotation-sensitive mode classes 2 and 3"
            ),
        },
        "canonical_default_exact_match": True,
        "canonical_program_sha256": _sha256_bytes(canonical_program.encode()),
        "programs": {
            setting: {
                "text": program,
                "sha256": _sha256_bytes(program.encode()),
                "path": str(rule_files[setting].relative_to(out_path.parent)),
                "file_sha256": _sha256_file(rule_files[setting]),
            }
            for setting, program in programs.items()
        },
        "episodes": episode_records,
        "distinguishing_witness": {
            "path": str(witness_path.relative_to(out_path.parent)),
            "sha256": _sha256_file(witness_path),
            "all_four_outputs_distinct": True,
        },
        "public_challenges": {
            episode_id: {
                "path": str(path.relative_to(HERE)),
                "sha256": _sha256_file(path),
            }
            for episode_id, path in public_files.items()
        },
        "prototype_sources": {
            str(path.relative_to(REPO)): _sha256_file(path)
            for path in source_files
        },
        "command": (
            "python3 review.py run python3 "
            "generators/49754d8fa42e/workspace/parametric/verify.py "
            "--out ../checks/parametric/verification.json"
        ),
        "limitations": [
            "Only four declared quarter-turn settings and retained seeds are evidenced.",
            "The selected production generator and canonical Racket authority remain separate.",
            "This extension is proposed, not catalog-approved or runtime-integrated.",
            "Finite rival checks do not prove uniqueness against arbitrary programs.",
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
