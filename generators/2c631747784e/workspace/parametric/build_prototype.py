#!/usr/bin/env python3
"""Materialize source-bound Racket evidence for both reverse-shift settings."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs

from prototype import (
    ALLOWED_REVERSE_SHIFTS,
    DEFAULT_REVERSE_SHIFT,
    GENERATOR_PATH,
    GENERATOR_SHA256,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    ROOT,
    TASK_ID,
    canonical_rule_source,
    choose_parameters,
    evaluate,
    instantiate_rule,
    make_episode,
    public_challenge,
    sha256,
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_seed_for(setting: int, start: int) -> int:
    for seed in range(start, start + 10_000):
        if choose_parameters(seed)[PARAMETER_NAME] == setting:
            return seed
    raise AssertionError(f"no deterministic seed found for reverse_shift={setting}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if type(args.seed) is not int or args.seed < 0:
        parser.error("--seed must be a nonnegative integer")

    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; use a fresh path to preserve evidence")
    out.mkdir(parents=True)

    source_dir = Path(__file__).resolve().parent
    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}
    canonical = canonical_rule_source()
    source_hashes = {
        "prototype.py": sha256((source_dir / "prototype.py").read_bytes()),
        "build_prototype.py": sha256(Path(__file__).read_bytes()),
        "selected_generator.py": GENERATOR_SHA256,
        "canonical_racket": sha256(canonical),
    }

    for setting in ALLOWED_REVERSE_SHIFTS:
        rule_path = out / "private" / "rules" / f"reverse-shift-{setting}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(instantiate_rule(setting), encoding="utf-8")

    episodes: list[dict[str, Any]] = []
    canonical_checks: list[dict[str, Any]] = []
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        runtime = {
            "racket_version": bridge.eval_text("(version)"),
            "prelude_sha256": sha256(Path(bridge.prelude_path).read_bytes()),
        }
        default_program = instantiate_rule(DEFAULT_REVERSE_SHIFT)
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            actual = evaluate(bridge, default_program, pair["input"])
            passed = actual == pair["output"]
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "passed": passed,
                    "actual": actual,
                    "expected": pair["output"],
                }
            )
            if not passed:
                raise AssertionError("default setting failed a labeled canonical pair")

        for index, setting in enumerate(ALLOWED_REVERSE_SHIFTS):
            seed = first_seed_for(setting, args.seed)
            episode = make_episode(bridge, seed)
            if episode["parameters"][PARAMETER_NAME] != setting:
                raise AssertionError("episode seed selected the wrong setting")
            challenge = public_challenge(episode)
            public_path = out / "public" / f"episode-{index + 1:03d}.json"
            private_path = out / "private" / f"episode-{index + 1:03d}.json"
            write_json(public_path, challenge)
            private_payload = {
                **episode,
                "parameter_spec": PARAMETER_SPEC,
                "source_hashes": source_hashes,
                "generator_path": str(Path(GENERATOR_PATH).relative_to(ROOT)),
                "command": command,
            }
            write_json(private_path, private_payload)
            episodes.append(
                {
                    "index": index,
                    "seed": seed,
                    "setting": setting,
                    "public_challenge": str(public_path.relative_to(out)),
                    "public_challenge_sha256": sha256(public_path.read_bytes()),
                    "private_evidence": str(private_path.relative_to(out)),
                    "private_evidence_sha256": sha256(private_path.read_bytes()),
                    "racket_sha256": episode["racket_sha256"],
                    "checks": episode["checks"],
                    "refuting_demonstration_indices": episode["rival"][
                        "refuting_demonstration_indices"
                    ],
                }
            )

    passed = (
        sorted(row["setting"] for row in episodes)
        == sorted(ALLOWED_REVERSE_SHIFTS)
        and all(row["passed"] for row in canonical_checks)
        and all(
            row["checks"]["all_labels_executed_in_racket"]
            and row["checks"]["python_mirror_parity"]
            and row["checks"]["demos_distinguish_alternative"]
            and row["checks"]["every_pair_distinguishes_alternative"]
            for row in episodes
        )
    )
    summary = {
        "schema": "2c631747784e-reverse-shift-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "passed": passed,
        "prototype_version": PROTOTYPE_VERSION,
        "selected_canonical_execution_path_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "choice_policy": "reverse_shift = episode_seed modulo 2, fixed for all pairs",
        "lesson_policy": "three demonstrations followed by one query",
        "settings_covered": sorted(row["setting"] for row in episodes),
        "source_hashes": source_hashes,
        "runtime": runtime,
        "canonical_checks": canonical_checks,
        "episodes": episodes,
        "command": command,
        "limitations": [
            "This is an isolated proposed prototype, not a production API or approval.",
            "Evidence covers two settings and one deterministic episode per setting.",
            "Only the declared alternative setting is tested; rule uniqueness is not claimed.",
            "Inputs come from the selected canonical generator, whose repeated colors make the one-step shift visible but do not exhaust all lawful paths.",
        ],
    }
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
