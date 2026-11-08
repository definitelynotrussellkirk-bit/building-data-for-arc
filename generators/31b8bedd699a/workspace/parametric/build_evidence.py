#!/usr/bin/env python3
"""Build source-bound live-Racket evidence for the frame token/tie prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "31b8bedd699a"
HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "token_tie_prototype_31b8bedd699a", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _all_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def _setting_key(setting: tuple[int, str]) -> str:
    return f"{setting[0]}-{setting[1]}"


_RULE_LAMBDA = re.compile(
    r"\(rule!\s+\(lambda\s+\(\s*([A-Za-z_][A-Za-z0-9_?!-]*)\s*\)\s*"
)


def _rule_lambda(program: str) -> tuple[str, str]:
    """Return the lambda parameter and its single parenthesized rule body.

    The shared extraction helper is intentionally tailored to generators whose
    parameter is named ``g``.  Canonical ARC programs are not required to use
    that spelling, so evidence execution binds the name actually present in
    the program instead of rewriting source text.
    """
    match = _RULE_LAMBDA.search(program)
    if match is None:
        raise ValueError("program does not contain a rule! lambda")
    parameter = match.group(1)
    start = match.end()
    while start < len(program) and program[start].isspace():
        start += 1
    if start >= len(program) or program[start] != "(":
        raise ValueError("rule! lambda body must be one parenthesized expression")

    depth = 0
    end = None
    in_string = False
    escaped = False
    for index in range(start, len(program)):
        char = program[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
            if depth < 0:
                raise ValueError("unbalanced parentheses in rule! lambda body")
    if end is None:
        raise ValueError("unterminated rule! lambda body")

    tail = program[end:].strip()
    if len(tail) < 2 or set(tail) != {")"}:
        raise ValueError("unexpected content after rule! lambda body")
    return parameter, program[start:end]


def _racket_apply_many(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
) -> list[list[list[int]]]:
    parameter, body = _rule_lambda(program)
    outputs = []
    for grid in grids:
        bridge.define_grid(parameter, grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def _masked_public(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and bool(public["train"])
        and bool(public["test"])
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def _validate_settings(proto, settings: Iterable[tuple[int, str]]) -> tuple[tuple[int, str], ...]:
    settings = tuple(tuple(setting) for setting in settings)
    if len(settings) < 2:
        raise ValueError("at least two distinct settings are required")
    validated = []
    for setting in settings:
        if len(setting) != 2:
            raise ValueError(f"setting must be (token_size, tie_policy), got {setting!r}")
        token_size, tie_policy = setting
        proto.racket_program(token_size, tie_policy, root=find_root(__file__))
        validated.append((token_size, tie_policy))
    if len(set(validated)) != len(validated):
        raise ValueError("duplicate settings are not allowed")
    default = (proto.DEFAULT_TOKEN_SIZE, proto.DEFAULT_TIE_POLICY)
    if default not in validated:
        raise ValueError(f"canonical default setting {default!r} must be included")
    return tuple(validated)


def write_evidence(
    out: Path | str,
    *,
    seed: int = 20261023,
    settings: Iterable[tuple[int, str]] | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Write exact programs, private episodes, masked challenges, and receipts."""
    out = Path(out).resolve()
    proto = _load_prototype()
    root = find_root(__file__)
    selected_settings = _validate_settings(
        proto, proto.ALL_SETTINGS if settings is None else settings
    )
    if out.exists():
        if not out.is_dir() or any(out.iterdir()):
            raise FileExistsError(
                f"refusing to mix evidence into nonempty destination: {out}"
            )
    else:
        out.mkdir(parents=True)

    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root
    )
    programs = {
        setting: proto.racket_program(*setting, root=root)
        for setting in selected_settings
    }
    default_setting = (proto.DEFAULT_TOKEN_SIZE, proto.DEFAULT_TIE_POLICY)
    canonical_program = proto.canonical_record(root=root)["program_solution"]
    planned = {
        setting: proto.generate_episode(
            seed,
            token_size=setting[0],
            tie_policy=setting[1],
            demo_count=demo_count,
            query_count=query_count,
            root=root,
        )
        for setting in selected_settings
    }

    shared_inputs = [
        deepcopy(pair["input"])
        for pair in _all_pairs(planned[selected_settings[0]])
    ]
    shared_input_hashes = [_sha256_json(grid) for grid in shared_inputs]
    for setting, episode in planned.items():
        candidate_hashes = [
            _sha256_json(pair["input"]) for pair in _all_pairs(episode)
        ]
        if candidate_hashes != shared_input_hashes:
            raise AssertionError(
                f"input sampler depends on hidden setting {_setting_key(setting)}"
            )

    private_dir = out / "private"
    programs_dir = private_dir / "programs"
    public_dir = out / "public"
    programs_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    for setting, program in programs.items():
        (programs_dir / f"setting-{_setting_key(setting)}.rkt").write_text(
            program, encoding="utf-8"
        )

    outputs_by_setting: dict[tuple[int, str], list[list[list[int]]]] = {}
    python_by_setting: dict[tuple[int, str], list[list[list[int]]]] = {}
    runtime_identity = None
    bridge = RacketBridge()
    try:
        runtime_identity = bridge.runtime_identity
        for setting in selected_settings:
            racket_outputs = _racket_apply_many(
                bridge, programs[setting], shared_inputs
            )
            python_outputs = [
                proto.apply_python(grid, *setting) for grid in shared_inputs
            ]
            if racket_outputs != python_outputs:
                raise AssertionError(
                    f"Python mirror disagrees with Racket for {_setting_key(setting)}"
                )
            outputs_by_setting[setting] = racket_outputs
            python_by_setting[setting] = python_outputs
    finally:
        bridge.shutdown()

    if programs[default_setting] != canonical_program:
        raise AssertionError("canonical default program is not exact canonical text")
    default_generator_outputs = [
        generator.rule_mirror(grid) for grid in shared_inputs
    ]
    if outputs_by_setting[default_setting] != default_generator_outputs:
        raise AssertionError(
            "canonical default variant disagrees with selected generator mirror"
        )

    prepared: dict[tuple[int, str], dict[str, Any]] = {}
    for setting in selected_settings:
        episode = deepcopy(planned[setting])
        intended = outputs_by_setting[setting]
        for pair, output in zip(_all_pairs(episode), intended, strict=True):
            pair["output"] = output

        alternatives = [other for other in selected_settings if other != setting]
        demo_refutations = {
            _setting_key(other): [
                outputs_by_setting[other][index] != intended[index]
                for index in range(demo_count)
            ]
            for other in alternatives
        }
        query_distinctions = {
            _setting_key(other): [
                outputs_by_setting[other][demo_count + index]
                != intended[demo_count + index]
                for index in range(query_count)
            ]
            for other in alternatives
        }
        demos_identify = all(any(values) for values in demo_refutations.values())
        query_discriminative = [
            any(
                query_distinctions[_setting_key(other)][index]
                for other in alternatives
            )
            for index in range(query_count)
        ]
        shortcut_refutations = [
            proto.known_distribution_shortcut(grid, setting[0])
            != intended[demo_count + index]
            for index, grid in enumerate(shared_inputs[demo_count:])
        ]
        verifier_errors = proto.episode_errors(episode, root=root)
        public = proto.public_challenge(episode)
        public_bytes = public_challenge_bytes(public)
        public_id = public_challenge_id(public)
        prepared[setting] = {
            "episode": episode,
            "intended": intended,
            "python": python_by_setting[setting],
            "demo_refutations": demo_refutations,
            "query_distinctions": query_distinctions,
            "demos_identify": demos_identify,
            "query_discriminative": query_discriminative,
            "shortcut_refutations": shortcut_refutations,
            "verifier_errors": verifier_errors,
            "public": public,
            "public_bytes": public_bytes,
            "public_id": public_id,
            "public_masked": _masked_public(public),
        }
        if not demos_identify:
            raise AssertionError(
                f"demonstrations do not identify {_setting_key(setting)}"
            )
        if not all(query_discriminative):
            raise AssertionError(
                f"one or more queries are nondiscriminative for {_setting_key(setting)}"
            )
        if not any(shortcut_refutations):
            raise AssertionError(
                f"queries do not refute the known shortcut for {_setting_key(setting)}"
            )
        if verifier_errors:
            raise AssertionError(
                f"episode verifier failed for {_setting_key(setting)}: {verifier_errors}"
            )

    public_ids = [prepared[setting]["public_id"] for setting in selected_settings]
    if len(set(public_ids)) != len(public_ids):
        raise ValueError("duplicate visible public challenge payloads")
    public_rows = sorted(
        ((prepared[setting]["public_id"], setting) for setting in selected_settings),
        key=lambda item: item[0],
    )
    for public_id, setting in public_rows:
        (public_dir / f"challenge-{public_id}.json").write_bytes(
            prepared[setting]["public_bytes"]
        )

    with (private_dir / "episodes.jsonl").open("w", encoding="utf-8") as stream:
        for setting in selected_settings:
            stream.write(
                json.dumps(
                    prepared[setting]["episode"],
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )

    witness_outputs = {
        _setting_key(setting): outputs_by_setting[setting][0]
        for setting in selected_settings
    }
    witness = {
        "input": shared_inputs[0],
        "input_profile": planned[selected_settings[0]]["train"][0]["profile"],
        "outputs_by_setting": witness_outputs,
        "all_outputs_distinct": len(
            {_sha256_json(output) for output in witness_outputs.values()}
        )
        == len(selected_settings),
    }
    _write_json(private_dir / "cross-setting-witness.json", witness)

    execution: dict[str, Any] = {}
    for setting in selected_settings:
        row = prepared[setting]
        key = _setting_key(setting)
        execution[key] = {
            "token_size": setting[0],
            "tie_policy": setting[1],
            "seed": seed,
            "demo_count": demo_count,
            "query_count": query_count,
            "program_file": f"private/programs/setting-{key}.rkt",
            "program_sha256": _sha256_text(programs[setting]),
            "program_is_exact_canonical_text": (
                setting == default_setting and programs[setting] == canonical_program
            ),
            "public_id": row["public_id"],
            "public_file": f"public/challenge-{row['public_id']}.json",
            "public_sha256": _sha256_bytes(row["public_bytes"]),
            "public_answer_masked": row["public_masked"],
            "racket_outputs_match_stored": all(
                pair["output"] == output
                for pair, output in zip(
                    _all_pairs(row["episode"]), row["intended"], strict=True
                )
            ),
            "python_outputs_match_racket": row["python"] == row["intended"],
            "demos_identify_selected_setting": row["demos_identify"],
            "all_queries_discriminate_some_alternative": all(
                row["query_discriminative"]
            ),
            "query_shortcut_refutations": sum(row["shortcut_refutations"]),
            "episode_verifier_errors": row["verifier_errors"],
            "demonstration_refutations": row["demo_refutations"],
            "query_distinctions": row["query_distinctions"],
            "input_sha256": shared_input_hashes,
            "racket_output_sha256": [
                _sha256_json(output) for output in row["intended"]
            ],
        }

    prototype_path = HERE / "prototype.py"
    builder_path = Path(__file__).resolve()
    summary = {
        "schema": "31b8bedd699a-token-size-tie-policy-evidence-v1",
        "status": "pass",
        "classification": "prototype_proposed_not_production_approved",
        "task_id": TASK_ID,
        "parameters": proto.PARAMETERS,
        "source": {
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": generator_sha,
            "generator_version": generator.VERSION,
            "canonical_rule_hash": generator.RULE_HASH,
            "prototype_path": str(prototype_path.relative_to(root)),
            "prototype_sha256": _sha256_bytes(prototype_path.read_bytes()),
            "builder_path": str(builder_path.relative_to(root)),
            "builder_sha256": _sha256_bytes(builder_path.read_bytes()),
            "canonical_program_sha256": _sha256_text(canonical_program),
            "default_program_is_exact_canonical_text": (
                programs[default_setting] == canonical_program
            ),
            "canonical_authority_changed": False,
        },
        "execution": execution,
        "shared_input_count": len(shared_inputs),
        "shared_input_sha256": shared_input_hashes,
        "all_racket_outputs_match_stored": all(
            row["racket_outputs_match_stored"] for row in execution.values()
        ),
        "all_python_outputs_match_racket": all(
            row["python_outputs_match_racket"] for row in execution.values()
        ),
        "all_demos_identify_selected_settings": all(
            row["demos_identify_selected_setting"] for row in execution.values()
        ),
        "all_queries_discriminate_some_alternative": all(
            row["all_queries_discriminate_some_alternative"]
            for row in execution.values()
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in execution.values()
        ),
        "all_episode_verifiers_pass": all(
            not row["episode_verifier_errors"] for row in execution.values()
        ),
        "known_shortcut_refuted_by_every_episode": all(
            row["query_shortcut_refutations"] >= 1 for row in execution.values()
        ),
        "cross_setting_witness": witness,
        "racket_runtime": runtime_identity,
        "artifacts": {
            "private_episodes": "private/episodes.jsonl",
            "cross_setting_witness": "private/cross-setting-witness.json",
            "programs": [
                f"private/programs/setting-{_setting_key(setting)}.rkt"
                for setting in selected_settings
            ],
            "public_challenges": [
                f"public/challenge-{public_id}.json" for public_id, _ in public_rows
            ],
        },
        "command": {"cwd": os.getcwd(), "argv": list(sys.argv)},
        "limitations": [
            "This is a task-local proposed rule family, not production approval or training admission.",
            "Evidence covers one deterministic seven-input episode per setting.",
            "A tie demonstration intentionally identifies tie_policy; token dimensions identify token_size.",
            "The selected generator and canonical Racket authority remain unchanged.",
        ],
    }
    _write_json(out / "manifest.json", summary)
    return summary


def _parse_setting(text: str) -> tuple[int, str]:
    try:
        size_text, policy = text.split(":", 1)
        return int(size_text), policy
    except (ValueError, TypeError) as error:
        raise argparse.ArgumentTypeError(
            "setting must have form TOKEN_SIZE:TIE_POLICY"
        ) from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument(
        "--setting",
        dest="settings",
        type=_parse_setting,
        action="append",
        help="repeat TOKEN_SIZE:TIE_POLICY; default materializes all six settings",
    )
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args(argv)
    summary = write_evidence(
        args.out,
        seed=args.seed,
        settings=args.settings,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "out": str(args.out),
                "settings": list(summary["execution"]),
                "shared_input_count": summary["shared_input_count"],
                "all_racket_outputs_match_stored": summary[
                    "all_racket_outputs_match_stored"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
