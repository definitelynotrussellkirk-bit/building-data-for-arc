#!/usr/bin/env python3
"""Build source-bound live-Racket evidence for the pass-budget prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "135219aecdb4"
HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "pass_budget_prototype_135219aecdb4", path
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
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _racket_apply_many(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
) -> list[list[list[int]]]:
    body = _program_body(program)
    outputs = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def _all_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def _masked_public(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and bool(public["train"])
        and bool(public["test"])
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def _validate_settings(proto, pass_counts: Iterable[int]) -> tuple[int, ...]:
    settings = tuple(pass_counts)
    if not settings:
        raise ValueError("at least two pass_count settings are required")
    for pass_count in settings:
        proto.racket_program(pass_count, root=find_root(__file__))
    if len(set(settings)) != len(settings):
        raise ValueError("duplicate pass_count settings are not allowed")
    if len(settings) < 2:
        raise ValueError("at least two distinct pass_count settings are required")
    if proto.DEFAULT_PASS_COUNT not in settings:
        raise ValueError(
            f"default pass_count={proto.DEFAULT_PASS_COUNT} must be included"
        )
    return settings


def write_evidence(
    out: Path | str,
    *,
    seed: int = 17,
    pass_counts: Iterable[int] = (1, 2, 3),
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Write exact programs, private episodes, public challenges, and receipts."""
    out = Path(out).resolve()
    proto = _load_prototype()
    root = find_root(__file__)
    settings = _validate_settings(proto, pass_counts)
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
        pass_count: proto.racket_program(pass_count, root=root)
        for pass_count in settings
    }
    canonical_program = proto.racket_program(proto.DEFAULT_PASS_COUNT, root=root)

    private_dir = out / "private"
    programs_dir = private_dir / "programs"
    public_dir = out / "public"
    programs_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    for pass_count, program in programs.items():
        (programs_dir / f"pass-{pass_count}.rkt").write_text(
            program, encoding="utf-8"
        )

    prepared: dict[int, dict[str, Any]] = {}
    runtime_identity = None
    bridge = RacketBridge()
    try:
        runtime_identity = bridge.runtime_identity
        for pass_count in settings:
            planned = proto.generate_episode(
                seed,
                pass_count=pass_count,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
            )
            pairs = _all_pairs(planned)
            inputs = [deepcopy(pair["input"]) for pair in pairs]
            intended = _racket_apply_many(bridge, programs[pass_count], inputs)
            python_outputs = [
                proto.apply_python(grid, pass_count) for grid in inputs
            ]
            if intended != python_outputs:
                raise AssertionError(
                    f"Python mirror disagrees with Racket for pass_count={pass_count}"
                )

            episode = deepcopy(planned)
            for pair, output in zip(_all_pairs(episode), intended, strict=True):
                pair["output"] = output

            if pass_count == proto.DEFAULT_PASS_COUNT:
                if programs[pass_count] != canonical_program:
                    raise AssertionError("default program is not exact canonical text")
                canonical_outputs = [generator.rule_mirror(grid) for grid in inputs]
                if intended != canonical_outputs:
                    raise AssertionError(
                        "default pass-count outputs disagree with selected generator"
                    )

            alternatives = [value for value in settings if value != pass_count]
            alternative_outputs: dict[int, list[list[list[int]]]] = {}
            demo_refutations: dict[str, list[bool]] = {}
            query_distinctions: dict[str, list[bool]] = {}
            for alternative in alternatives:
                outputs = _racket_apply_many(bridge, programs[alternative], inputs)
                alternative_outputs[alternative] = outputs
                demo_refutations[str(alternative)] = [
                    outputs[index] != intended[index]
                    for index in range(demo_count)
                ]
                query_distinctions[str(alternative)] = [
                    outputs[demo_count + index] != intended[demo_count + index]
                    for index in range(query_count)
                ]

            if not all(all(values) for values in demo_refutations.values()):
                raise AssertionError(
                    f"demonstrations do not identify pass_count={pass_count}"
                )
            if not all(all(values) for values in query_distinctions.values()):
                raise AssertionError(
                    f"queries are not setting-sensitive for pass_count={pass_count}"
                )

            public = proto.public_challenge(episode)
            public_bytes = public_challenge_bytes(public)
            public_id = public_challenge_id(public)
            if public_bytes != (
                json.dumps(
                    public,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            ).encode("utf-8"):
                raise AssertionError("public projection bytes are not canonical")

            prepared[pass_count] = {
                "episode": episode,
                "inputs": inputs,
                "intended": intended,
                "python_outputs": python_outputs,
                "alternative_outputs": alternative_outputs,
                "demo_refutations": demo_refutations,
                "query_distinctions": query_distinctions,
                "public": public,
                "public_bytes": public_bytes,
                "public_id": public_id,
                "public_masked": _masked_public(public),
            }
    finally:
        bridge.shutdown()

    public_ids = [prepared[value]["public_id"] for value in settings]
    if len(set(public_ids)) != len(public_ids):
        raise ValueError("duplicate visible public challenge payloads")

    public_rows = sorted(
        ((prepared[value]["public_id"], value) for value in settings),
        key=lambda item: item[0],
    )
    for public_id, pass_count in public_rows:
        (public_dir / f"challenge-{public_id}.json").write_bytes(
            prepared[pass_count]["public_bytes"]
        )

    private_path = private_dir / "episodes.jsonl"
    with private_path.open("w", encoding="utf-8") as stream:
        for pass_count in settings:
            stream.write(
                json.dumps(
                    prepared[pass_count]["episode"],
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )

    witness_input = deepcopy(prepared[settings[0]]["inputs"][0])
    witness_outputs = {
        str(pass_count): prepared[pass_count]["intended"][0]
        for pass_count in settings
    }
    witness = {
        "input": witness_input,
        "outputs_by_pass_count": witness_outputs,
        "all_outputs_distinct": len(
            {_sha256_json(output) for output in witness_outputs.values()}
        )
        == len(settings),
    }
    _write_json(private_dir / "witness.json", witness)

    all_input_hashes = {
        _sha256_json(grid)
        for pass_count in settings
        for grid in prepared[pass_count]["inputs"]
    }
    execution: dict[str, Any] = {}
    for pass_count in settings:
        row = prepared[pass_count]
        public_file = f"public/challenge-{row['public_id']}.json"
        program_file = f"private/programs/pass-{pass_count}.rkt"
        alternatives = [value for value in settings if value != pass_count]
        execution[str(pass_count)] = {
            "pass_count": pass_count,
            "seed": seed,
            "train_count": demo_count,
            "query_count": query_count,
            "program_file": program_file,
            "program_sha256": _sha256_text(programs[pass_count]),
            "program_is_exact_canonical_text": (
                programs[pass_count] == canonical_program
                if pass_count == proto.DEFAULT_PASS_COUNT
                else False
            ),
            "public_id": row["public_id"],
            "public_file": public_file,
            "public_sha256": _sha256_bytes(row["public_bytes"]),
            "public_answer_masked": row["public_masked"],
            "alternative_settings": alternatives,
            "racket_outputs_match_stored": all(
                pair["output"] == output
                for pair, output in zip(
                    _all_pairs(row["episode"]), row["intended"], strict=True
                )
            ),
            "python_outputs_match_racket": row["python_outputs"] == row["intended"],
            "all_demonstrations_refute_alternatives": all(
                all(values) for values in row["demo_refutations"].values()
            ),
            "all_queries_distinguish_alternatives": all(
                all(values) for values in row["query_distinctions"].values()
            ),
            "demonstration_refutations": row["demo_refutations"],
            "query_distinctions": row["query_distinctions"],
            "input_sha256": [_sha256_json(grid) for grid in row["inputs"]],
            "racket_output_sha256": [
                _sha256_json(output) for output in row["intended"]
            ],
        }

    prototype_path = HERE / "prototype.py"
    builder_path = Path(__file__).resolve()
    summary = {
        "schema": "135219aecdb4-pass-budget-evidence-v1",
        "status": "pass",
        "classification": "prototype_proposed_not_production_approved",
        "task_id": TASK_ID,
        "parameter": {
            "name": "pass_count",
            "allowed": list(proto.ALLOWED_PASS_COUNTS),
            "default": proto.DEFAULT_PASS_COUNT,
            "selected_once_per_episode": True,
            "input_grammar_changed": False,
        },
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
                programs.get(proto.DEFAULT_PASS_COUNT) == canonical_program
            ),
            "canonical_authority_changed": False,
        },
        "execution": execution,
        "all_racket_outputs_match_stored": all(
            row["racket_outputs_match_stored"] for row in execution.values()
        ),
        "all_python_outputs_match_racket": all(
            row["python_outputs_match_racket"] for row in execution.values()
        ),
        "all_demos_refute_alternative_settings": all(
            row["all_demonstrations_refute_alternatives"]
            for row in execution.values()
        ),
        "all_queries_distinguish_alternative_settings": all(
            row["all_queries_distinguish_alternatives"]
            for row in execution.values()
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in execution.values()
        ),
        "unique_input_count": len(all_input_hashes),
        "cross_setting_witness": witness,
        "racket_runtime": runtime_identity,
        "artifacts": {
            "private_episodes": "private/episodes.jsonl",
            "witness": "private/witness.json",
            "programs": [
                f"private/programs/pass-{value}.rkt" for value in settings
            ],
            "public_challenges": [
                f"public/challenge-{public_id}.json"
                for public_id, _ in public_rows
            ],
        },
        "command": {
            "cwd": os.getcwd(),
            "argv": list(sys.argv),
        },
        "limitations": [
            "This is a task-local proposed rule family, not production approval.",
            "Evidence covers one deterministic six-input episode per setting.",
            "All retained inputs require exactly three synchronous passes, so the three settings are deliberately identifiable from demonstrations.",
            "The selected generator and canonical Racket authority remain three-pass.",
        ],
    }
    _write_json(out / "manifest.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--pass-count",
        dest="pass_counts",
        type=int,
        action="append",
        help="fixed setting to materialize; repeat for multiple settings",
    )
    parser.add_argument("--demo-count", type=int, default=2)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args(argv)
    settings = tuple(args.pass_counts or (1, 2, 3))
    summary = write_evidence(
        args.out,
        seed=args.seed,
        pass_counts=settings,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "out": str(args.out),
                "settings": list(summary["execution"]),
                "unique_input_count": summary["unique_input_count"],
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
