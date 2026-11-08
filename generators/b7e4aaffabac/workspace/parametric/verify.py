#!/usr/bin/env python3
"""Replay and materialize overlap-policy authoring evidence in protected Racket."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
)

HERE = Path(__file__).resolve().parent
_ROOT = find_root(__file__)


def _load_prototype():
    path = HERE / "prototype.py"
    body = path.read_bytes()
    name = "_overlap_policy_verify_prototype_" + hashlib.sha256(
        str(path).encode() + body
    ).hexdigest()
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


prototype = _load_prototype()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    if pretty:
        text = json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    else:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    return (text + "\n").encode("utf-8")


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha_bytes(_json_bytes(grid))


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _runtime_identity(identity: dict) -> dict:
    keys = (
        "schema",
        "backend",
        "protected",
        "binary_sha256",
        "prelude_sha256",
        "bridge_sha256",
        "boot_script_sha256",
        "candidate_symbol_policy_sha256",
    )
    return {key: identity[key] for key in keys if key in identity}


def _source_hashes() -> dict[str, str]:
    paths = (
        _ROOT / "generators" / prototype.TASK_ID / "generator.py",
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "verify.py",
    )
    return {
        path.relative_to(_ROOT).as_posix(): _sha_bytes(path.read_bytes())
        for path in paths
    }


def _assert_public_only(challenge: dict) -> None:
    if set(challenge) != {"train", "test"}:
        raise AssertionError("public challenge may contain only train/test")
    if any(set(pair) != {"input", "output"} for pair in challenge["train"]):
        raise AssertionError("public demonstrations must contain only input/output")
    if any(set(pair) != {"input"} for pair in challenge["test"]):
        raise AssertionError("public queries must contain only input")
    text = json.dumps(challenge, sort_keys=True)
    forbidden = (
        prototype.PARAMETER_NAME,
        "program_solution",
        "program_sha256",
        "settings",
        "intermediates",
        "seed",
    )
    leaked = [token for token in forbidden if token in text]
    if leaked:
        raise AssertionError(f"public challenge leaks private fields: {leaked}")


def _write_materialization(
    out_dir: Path,
    *,
    report: dict,
    episodes: dict[str, dict],
    programs: dict[str, str],
    rival_programs: dict[str, dict[str, str]],
    publics: dict[str, bytes],
) -> None:
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(exist_ok=False)
    public_dir = out_dir / "public"
    private_dir = out_dir / "private"
    (private_dir / "episodes").mkdir(parents=True)
    (private_dir / "rules").mkdir(parents=True)
    public_dir.mkdir()

    for public_id, payload in sorted(publics.items()):
        (public_dir / f"{public_id}.json").write_bytes(payload)
    for setting, episode in episodes.items():
        (private_dir / "episodes" / f"{setting}.json").write_bytes(
            _json_bytes(episode, pretty=True)
        )
        (private_dir / "rules" / f"{setting}.rkt").write_text(
            programs[setting] + "\n", encoding="utf-8"
        )
        for name, program in rival_programs[setting].items():
            (private_dir / "rules" / f"{setting}__{name}.rkt").write_text(
                program + "\n", encoding="utf-8"
            )
    (private_dir / "verification.json").write_bytes(_json_bytes(report, pretty=True))
    inventory = {
        "schema": "b7e4aaffabac-overlap-policy-materialization-v1",
        "status": "complete",
        "task_id": prototype.TASK_ID,
        "public_files": [
            {
                "public_id": public_id,
                "path": f"public/{public_id}.json",
                "sha256": _sha_bytes(payload),
                "bytes": len(payload),
            }
            for public_id, payload in sorted(publics.items())
        ],
        "private_report": "private/verification.json",
        "source_hashes": report["source_hashes"],
        "limitations": report["limitations"],
    }
    (private_dir / "manifest.json").write_bytes(_json_bytes(inventory, pretty=True))


def verify(*, seed: int, out_dir: Path) -> dict:
    if type(seed) is not int or not 0 <= seed <= prototype.MAX_SEED:
        raise ValueError(f"seed must be an exact integer in 0..{prototype.MAX_SEED}")
    out_dir = Path(out_dir)
    if out_dir.exists() or out_dir.is_symlink():
        raise ValueError("out_dir must not already exist")

    generator, _, _ = load_selected_generator(prototype.TASK_ID, root=_ROOT)
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    rivals = {
        setting: prototype.rival_programs(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    episodes = {
        setting: prototype.build_claimed_episode(seed, setting, 3, 4)
        for setting in prototype.ALLOWED_SETTINGS
    }
    boundary_demo_counts = (2, 6)
    boundary_episodes = {
        setting: {
            demos: prototype.build_claimed_episode(seed, setting, demos, 4)
            for demos in boundary_demo_counts
        }
        for setting in prototype.ALLOWED_SETTINGS
    }

    reference_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[prototype.DEFAULT_SETTING][split]
    ]
    for setting, episode in episodes.items():
        inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        if inputs != reference_inputs:
            raise AssertionError(f"input sampling depends on setting: {setting}")
        if episode["program_solution"] != programs[setting]:
            raise AssertionError(f"episode program mismatch: {setting}")
        if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != len(inputs):
            raise AssertionError(f"duplicate inputs for setting {setting}")
        for grid in inputs:
            errors = generator.self_check(grid)
            if errors:
                raise AssertionError(f"production grammar rejected parametric input: {errors}")
            if generator.canonical_profile_signature(grid) is not None:
                raise AssertionError("parametric sampler replayed a literal canonical input")

    primary_queries = [pair["input"] for pair in episodes[prototype.DEFAULT_SETTING]["test"]]
    for demos in boundary_demo_counts:
        reference = boundary_episodes[prototype.DEFAULT_SETTING][demos]
        reference_inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in reference[split]
        ]
        if [pair["input"] for pair in reference["test"]] != primary_queries:
            raise AssertionError("query sampling changed with demonstration count")
        expected_prefix = prototype.build_claimed_episode(
            seed, prototype.DEFAULT_SETTING, 6, 4
        )["train"][:demos]
        if reference["train"] != expected_prefix:
            raise AssertionError("demonstration prefixes changed with requested count")
        for setting in prototype.ALLOWED_SETTINGS:
            episode = boundary_episodes[setting][demos]
            inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episode[split]
            ]
            if inputs != reference_inputs:
                raise AssertionError(
                    f"boundary input sampling depends on setting: {setting}/{demos}"
                )
            if episode["program_solution"] != programs[setting]:
                raise AssertionError(f"boundary episode program mismatch: {setting}/{demos}")
            for grid in inputs:
                errors = generator.self_check(grid)
                if errors:
                    raise AssertionError(
                        f"production grammar rejected boundary input: {errors}"
                    )
                if generator.canonical_profile_signature(grid) is not None:
                    raise AssertionError("boundary sampler replayed a literal canonical input")

    evaluation_count = 0
    setting_rows: list[dict] = []
    all_pair_rows: dict[str, list[dict]] = {}
    boundary_rows: list[dict] = []
    selected_symbols: dict[str, str] = {}

    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        runtime = _runtime_identity(bridge.runtime_identity)
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise AssertionError("verification requires a protected Racket backend")

        for setting_index, setting in enumerate(prototype.ALLOWED_SETTINGS):
            candidates = {"selected": programs[setting], **rivals[setting]}
            symbols: dict[str, str] = {}
            for candidate_index, (name, source) in enumerate(candidates.items()):
                symbol = f"__overlap_{setting_index}_{candidate_index}"
                bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
                symbols[name] = symbol
            selected_symbols[setting] = symbols["selected"]

            pair_rows = []
            flattened = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episodes[setting][split])
            ]
            for split, index, pair in flattened:
                literal = _grid_literal(pair["input"])
                outputs = {}
                for name, symbol in symbols.items():
                    outputs[name] = bridge.eval_text(f"({symbol} {literal})")
                    evaluation_count += 1
                selected_exact = outputs["selected"] == pair["output"]
                if not selected_exact:
                    raise AssertionError(
                        f"selected Racket label mismatch for {setting} {split}[{index}]"
                    )
                info = prototype.analyze_intermediate(pair["input"])
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "orientation": info["orientation"],
                        "shape": [len(pair["input"]), len(pair["input"][0])],
                        "input_sha256": _grid_hash(pair["input"]),
                        "output_sha256": _grid_hash(pair["output"]),
                        "selected_racket_matches_claim": selected_exact,
                        "rival_differs": {
                            name: output != pair["output"]
                            for name, output in outputs.items()
                            if name != "selected"
                        },
                    }
                )

            demo_rows = [row for row in pair_rows if row["split"] == "train"]
            if [row["orientation"] for row in demo_rows[:2]] != ["horizontal", "vertical"]:
                raise AssertionError("minimum teaching prefix lost mixed orientation")
            declared_survivors = [
                candidate
                for candidate in prototype.ALLOWED_SETTINGS
                if all(
                    prototype.apply_python(pair["input"], candidate) == pair["output"]
                    for pair in episodes[setting]["train"]
                )
            ]
            if declared_survivors != [setting]:
                raise AssertionError(
                    f"demonstrations do not uniquely identify {setting}: {declared_survivors}"
                )

            rival_rows = []
            for name, program in rivals[setting].items():
                demo_mismatches = [
                    row["index"]
                    for row in pair_rows
                    if row["split"] == "train" and row["rival_differs"][name]
                ]
                query_mismatches = [
                    row["index"]
                    for row in pair_rows
                    if row["split"] == "test" and row["rival_differs"][name]
                ]
                if not demo_mismatches:
                    raise AssertionError(f"teaching examples failed to reject {setting}/{name}")
                rival_rows.append(
                    {
                        "name": name,
                        "program_sha256": _sha_text(program),
                        "demo_mismatch_indices": demo_mismatches,
                        "query_mismatch_indices": query_mismatches,
                    }
                )

            all_pair_rows[setting] = pair_rows
            setting_rows.append(
                {
                    "setting": setting,
                    "program_sha256": _sha_text(programs[setting]),
                    "declared_survivors_from_demos": declared_survivors,
                    "teaching_orientations": [row["orientation"] for row in demo_rows],
                    "literal_canonical_replays": 0,
                    "rivals": rival_rows,
                    "pairs": pair_rows,
                }
            )

        for setting in prototype.ALLOWED_SETTINGS:
            symbol = selected_symbols[setting]
            for demos in boundary_demo_counts:
                episode = boundary_episodes[setting][demos]
                matches = []
                pair_count = 0
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = bridge.eval_text(
                            f"({symbol} {_grid_literal(pair['input'])})"
                        )
                        evaluation_count += 1
                        pair_count += 1
                        exact = actual == pair["output"]
                        matches.append(exact)
                        if not exact:
                            raise AssertionError(
                                f"boundary Racket label mismatch for {setting} "
                                f"demos={demos} {split}[{index}]"
                            )
                declared_survivors = [
                    candidate
                    for candidate in prototype.ALLOWED_SETTINGS
                    if all(
                        prototype.apply_python(pair["input"], candidate)
                        == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                if declared_survivors != [setting]:
                    raise AssertionError(
                        f"boundary demonstrations do not uniquely identify "
                        f"{setting}/{demos}: {declared_survivors}"
                    )
                boundary_rows.append(
                    {
                        "setting": setting,
                        "demos": demos,
                        "queries": 4,
                        "racket_checked_pairs": pair_count,
                        "selected_racket_matches_all_claims": all(matches),
                        "declared_survivors_from_demos": declared_survivors,
                        "query_input_sha256": [
                            _grid_hash(pair["input"]) for pair in episode["test"]
                        ],
                    }
                )

    publics: dict[str, bytes] = {}
    public_rows = []
    for setting, episode in episodes.items():
        public = prototype.public_challenge(episode)
        _assert_public_only(public)
        payload = public_challenge_bytes(public)
        public_id = _sha_bytes(payload)
        if public_id in publics:
            raise AssertionError("distinct settings produced a duplicate visible challenge")
        publics[public_id] = payload

        private_mutation = deepcopy(episode)
        private_mutation["settings"] = {prototype.PARAMETER_NAME: "private-mutation"}
        private_mutation["program"] = "private-mutation"
        private_mutation["program_solution"] = "private-mutation"
        private_mutation["test"][0]["output"] = [[9]]
        if public_challenge_bytes(prototype.public_challenge(private_mutation)) != payload:
            raise AssertionError("private fields changed public bytes")
        first_turn = prototype.sequential_turn(episode, 0)
        _assert_public_only(first_turn)
        if first_turn["test"] != [{"input": episode["test"][0]["input"]}]:
            raise AssertionError("first sequential turn exposes the wrong query")
        public_rows.append(
            {
                "setting": setting,
                "public_id": public_id,
                "sha256": _sha_bytes(payload),
                "bytes": len(payload),
                "train_count": len(public["train"]),
                "query_count": len(public["test"]),
                "first_turn_sha256": _sha_bytes(public_challenge_bytes(first_turn)),
            }
        )

    maximum = episodes[prototype.DEFAULT_SETTING]["test"][-1]
    maximum_row = all_pair_rows[prototype.DEFAULT_SETTING][-1]
    if maximum_row["shape"] != [30, 30] or not maximum_row["selected_racket_matches_claim"]:
        raise AssertionError("maximum query is not a protected-Racket-checked 30x30 case")
    changed = sum(
        before != after
        for source_row, output_row in zip(maximum["input"], maximum["output"])
        for before, after in zip(source_row, output_row)
    )
    if changed <= 30:
        raise AssertionError("maximum query is not substantive")

    report = {
        "schema": "b7e4aaffabac-overlap-policy-verification-v1",
        "status": "passed",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "counts": {
            "settings": len(prototype.ALLOWED_SETTINGS),
            "demonstrations_per_setting": 3,
            "queries_per_setting": 4,
            "boundary_demo_counts": list(boundary_demo_counts),
            "primary_racket_checked_pairs": sum(
                len(rows) for rows in all_pair_rows.values()
            ),
            "boundary_racket_checked_pairs": sum(
                row["racket_checked_pairs"] for row in boundary_rows
            ),
            "racket_checked_pairs": (
                sum(len(rows) for rows in all_pair_rows.values())
                + sum(row["racket_checked_pairs"] for row in boundary_rows)
            ),
            "racket_program_evaluations": evaluation_count,
        },
        "racket": runtime,
        "source_hashes": _source_hashes(),
        "settings": setting_rows,
        "boundary_replays": boundary_rows,
        "public_challenges": sorted(public_rows, key=lambda row: row["setting"]),
        "maximum_query": {
            "setting": prototype.DEFAULT_SETTING,
            "split": "test",
            "index": 3,
            "shape": maximum_row["shape"],
            "changed_cells": changed,
            "input_sha256": maximum_row["input_sha256"],
            "output_sha256": maximum_row["output_sha256"],
            "selected_racket_matches_claim": maximum_row["selected_racket_matches_claim"],
        },
        "checks": {
            "matched_inputs_across_settings": True,
            "distinct_inputs_within_episode": True,
            "minimum_prefix_mixes_orientation": True,
            "minimum_and_maximum_demo_counts_racket_replayed": True,
            "queries_stable_across_demo_counts": True,
            "literal_canonical_replay_count": 0,
            "private_fields_do_not_change_public_bytes": True,
            "query_outputs_are_masked": True,
            "default_program_is_exact_canonical": programs[prototype.DEFAULT_SETTING]
            == prototype.canonical_program(),
        },
        "limitations": [
            "Finite authoring evidence covers the two declared settings, one retained seed, 2/3/6 demonstration counts, four queries, and three explicit rivals on the three-demo episodes.",
            "It does not prove learning benefit, owner acceptance, training admission, or behavior outside the declared grammar and request limits.",
        ],
    }
    _write_materialization(
        out_dir,
        report=report,
        episodes=episodes,
        programs=programs,
        rival_programs=rivals,
        publics=publics,
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = verify(seed=args.seed, out_dir=args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "counts": report["counts"],
                "racket": report["racket"],
                "maximum_query": report["maximum_query"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
