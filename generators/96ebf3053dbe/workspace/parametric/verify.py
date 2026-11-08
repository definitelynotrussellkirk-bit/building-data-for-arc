#!/usr/bin/env python3
"""Replay and materialize endpoint-policy authoring evidence in protected Racket."""
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
from reviewer_support import find_root, public_challenge_bytes

HERE = Path(__file__).resolve().parent
_ROOT = find_root(__file__)


def _load_prototype():
    path = HERE / "prototype.py"
    body = path.read_bytes()
    name = "_endpoint_policy_verify_prototype_" + hashlib.sha256(
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
        text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
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
    rival_programs: dict[str, str],
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
    for name, program in rival_programs.items():
        (private_dir / "rules" / f"{name}.rkt").write_text(
            program + "\n", encoding="utf-8"
        )
    (private_dir / "verification.json").write_bytes(_json_bytes(report, pretty=True))
    inventory = {
        "schema": "96ebf3053dbe-endpoint-policy-materialization-v1",
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
    if out_dir.exists():
        raise ValueError("out_dir must not already exist")

    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    shared_rivals = {
        "skip_anchor": prototype.skip_anchor_program(),
        "erase_only": prototype.erase_only_program(),
    }
    episodes = {
        setting: prototype.build_claimed_episode(seed, setting, 3, 4)
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

    evaluation_count = 0
    setting_rows: list[dict] = []
    all_pair_rows: dict[str, list[dict]] = {}
    program_outputs: dict[tuple[str, int, str], list[list[int]]] = {}

    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        runtime = _runtime_identity(bridge.runtime_identity)
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise AssertionError("verification requires a protected Racket backend")

        for setting_index, setting in enumerate(prototype.ALLOWED_SETTINGS):
            alternate = next(
                value for value in prototype.ALLOWED_SETTINGS if value != setting
            )
            candidates = {
                "selected": programs[setting],
                "alternate_setting": programs[alternate],
                **shared_rivals,
            }
            symbols = {}
            for candidate_index, (name, source) in enumerate(candidates.items()):
                symbol = f"__endpoint_{setting_index}_{candidate_index}"
                bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
                symbols[name] = symbol

            pair_rows = []
            flattened = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episodes[setting][split])
            ]
            for global_index, (split, index, pair) in enumerate(flattened):
                outputs = {}
                literal = _grid_literal(pair["input"])
                for name, symbol in symbols.items():
                    outputs[name] = bridge.eval_text(f"({symbol} {literal})")
                    evaluation_count += 1
                    program_outputs[(setting, global_index, name)] = outputs[name]
                selected_exact = outputs["selected"] == pair["output"]
                if not selected_exact:
                    raise AssertionError(
                        f"selected Racket label mismatch for {setting} {split}[{index}]"
                    )
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
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

            rivals = []
            for name in ("alternate_setting", "skip_anchor", "erase_only"):
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
                rivals.append(
                    {
                        "name": name,
                        "program_sha256": _sha_text(candidates[name]),
                        "demo_mismatch_indices": demo_mismatches,
                        "query_mismatch_indices": query_mismatches,
                        "rejected_by_demonstrations": bool(demo_mismatches),
                    }
                )
            selected_exact = all(
                row["selected_racket_matches_claim"] for row in pair_rows
            )
            demos_identify = all(
                rival["rejected_by_demonstrations"] for rival in rivals
            )
            if not demos_identify:
                raise AssertionError(f"finite rivals survive demonstrations: {setting}")
            setting_rows.append(
                {
                    "setting": setting,
                    "program_sha256": _sha_text(programs[setting]),
                    "selected_racket_exact": selected_exact,
                    "demos_identify_setting": demos_identify,
                    "all_queries_checked": all(
                        row["selected_racket_matches_claim"]
                        for row in pair_rows
                        if row["split"] == "test"
                    ),
                    "rivals": rivals,
                    "pairs": pair_rows,
                }
            )
            all_pair_rows[setting] = pair_rows

    default_episode = episodes[prototype.DEFAULT_SETTING]
    stress_index = len(default_episode["train"]) + len(default_episode["test"]) - 1
    stress_pair = default_episode["test"][-1]
    stress_row = all_pair_rows[prototype.DEFAULT_SETTING][-1]

    witness_index = next(
        index
        for index, row in enumerate(all_pair_rows[prototype.DEFAULT_SETTING])
        if row["rival_differs"]["skip_anchor"]
    )
    if witness_index < len(default_episode["train"]):
        witness_pair = default_episode["train"][witness_index]
        witness_intermediate = default_episode["intermediates"]["train"][witness_index]
    else:
        query_index = witness_index - len(default_episode["train"])
        witness_pair = default_episode["test"][query_index]
        witness_intermediate = default_episode["intermediates"]["test"][query_index]

    publics: dict[str, bytes] = {}
    public_inventory = []
    for setting, episode in episodes.items():
        challenge = prototype.public_challenge(episode)
        _assert_public_only(challenge)
        payload = public_challenge_bytes(challenge)
        public_id = _sha_bytes(payload)
        if public_id in publics:
            raise AssertionError("duplicate visible public challenges")
        publics[public_id] = payload
        public_inventory.append(
            {
                "public_id": public_id,
                "setting_private": setting,
                "sha256": _sha_bytes(payload),
                "demonstrations": len(challenge["train"]),
                "queries": len(challenge["test"]),
            }
        )

    selected_endpoints = [
        item["selected_endpoint"] for item in witness_intermediate
    ]
    counterfactual = {
        "settings": {prototype.PARAMETER_NAME: prototype.DEFAULT_SETTING},
        "input": deepcopy(witness_pair["input"]),
        "intermediate_value": {
            "selected_endpoints": selected_endpoints,
            "anchor_directions": [
                item["anchor_direction"] for item in witness_intermediate
            ],
        },
        "program": programs[prototype.DEFAULT_SETTING],
        "program_output": deepcopy(
            program_outputs[(prototype.DEFAULT_SETTING, witness_index, "selected")]
        ),
        "counterfactual_program": shared_rivals["skip_anchor"],
        "counterfactual_output": deepcopy(
            program_outputs[(prototype.DEFAULT_SETTING, witness_index, "skip_anchor")]
        ),
        "ablation": "skip_a",
    }
    if counterfactual["program_output"] == counterfactual["counterfactual_output"]:
        raise AssertionError("counterfactual witness does not change the final output")

    report = {
        "schema": "96ebf3053dbe-endpoint-policy-verification-v1",
        "status": "passed",
        "scope": "bounded task-local proposal; not owner acceptance",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_SETTINGS),
            "canonical_default": prototype.DEFAULT_SETTING,
            "chosen_once_per_episode": True,
            "input_sampling_independent_of_setting": True,
        },
        "racket": runtime,
        "counts": {
            "settings": len(episodes),
            "demonstrations_per_setting": 3,
            "queries_per_setting": 4,
            "racket_checked_pairs": sum(
                len(episode["train"]) + len(episode["test"])
                for episode in episodes.values()
            ),
            "racket_program_evaluations": evaluation_count,
        },
        "settings": setting_rows,
        "maximum_query": {
            "shape": [len(stress_pair["input"]), len(stress_pair["input"][0])],
            "input_sha256": _grid_hash(stress_pair["input"]),
            "output_sha256": _grid_hash(stress_pair["output"]),
            "selected_racket_matches_claim": stress_row[
                "selected_racket_matches_claim"
            ],
            "global_pair_index": stress_index,
        },
        "public_inventory": sorted(public_inventory, key=lambda row: row["public_id"]),
        "source_hashes": _source_hashes(),
        "counterfactual_draft": counterfactual,
        "limitations": [
            "Finite evidence covers two settings at one seed, three demonstrations and four queries each.",
            "The alternate setting and two explicit shortcuts are refuted; arbitrary programs are not exhausted.",
            "The family remains proposed until exact integrated owner qualification and acceptance.",
            "The largest lawful mirrored stress is 29x30 because the central divider requires odd height.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/96ebf3053dbe/workspace/parametric/verify.py",
                "--seed",
                str(seed),
                "--out",
                str(out_dir),
            ],
        },
    }
    _write_materialization(
        out_dir,
        report=report,
        episodes=episodes,
        programs=programs,
        rival_programs=shared_rivals,
        publics=publics,
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = verify(seed=args.seed, out_dir=args.out)
    except (AssertionError, OSError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "counts": report["counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
