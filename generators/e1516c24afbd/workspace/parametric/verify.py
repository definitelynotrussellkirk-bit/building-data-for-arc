#!/usr/bin/env python3
"""Execute every proposed Racket setting and retain source-bound evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, normalize_grid

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("expected one (rule! BODY) source form")
    body = stripped[len("(rule!") : -1].strip()
    return body if body.startswith("(lambda") else f"(lambda (g) {body})"


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute(source: str, grid: list[list[int]], bridge: RacketBridge) -> list[list[int]]:
    expression = f"({_callable(source)} {_grid_literal(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _setting_name(setting: tuple[str, int]) -> str:
    return f"state-{setting[0]}_color-{setting[1]}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    parser.add_argument("--seed-base", type=int, default=0)
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = prototype.canonical_source(root=root)
    if prototype.materialize_rule() != canonical:
        raise SystemExit("default setting is not byte-for-byte canonical")
    if _sha256(canonical) != prototype.CANONICAL_SHA256:
        raise SystemExit("canonical source hash mismatch")

    programs = {
        setting: prototype.materialize_rule(*setting, source=canonical)
        for setting in prototype.SETTINGS
    }
    if len(set(programs.values())) != len(prototype.SETTINGS):
        raise SystemExit("declared settings do not materialize unique programs")

    seeds = [args.seed_base + offset for offset in range(len(prototype.SETTINGS))]
    episodes = [prototype.build_episode(seed) for seed in seeds]
    selected = {
        (episode["parameter"]["target_state"], episode["parameter"]["output_color"])
        for episode in episodes
    }
    if selected != set(prototype.SETTINGS):
        raise SystemExit("retained seeds do not cover every declared setting")
    for episode in episodes:
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"episode {episode['seed']} invalid: {errors}")

    checks: list[dict[str, Any]] = []
    canonical_replay: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=96)
    try:
        runtime_identity = bridge.runtime_identity
        for row in canonical_pairs(prototype.TASK_ID, root=root, labeled_only=True):
            actual = execute(canonical, row["input"], bridge)
            canonical_replay.append(
                {
                    "variant": row["variant"],
                    "split": row["split"],
                    "pair_index": row["pair_index"],
                    "matches": actual == row["output"],
                    "expected_sha256": _sha256(json.dumps(row["output"], separators=(",", ":"))),
                    "actual_sha256": _sha256(json.dumps(actual, separators=(",", ":"))),
                }
            )
        if not canonical_replay or not all(row["matches"] for row in canonical_replay):
            raise SystemExit("canonical default failed canonical pair replay")

        for episode in episodes:
            selected_setting = (
                episode["parameter"]["target_state"],
                episode["parameter"]["output_color"],
            )
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    selected_python = prototype.apply_python(pair["input"], *selected_setting)
                    selected_racket = execute(programs[selected_setting], pair["input"], bridge)
                    if selected_racket != selected_python or selected_racket != pair["output"]:
                        raise SystemExit(
                            f"selected Racket/Python mismatch for seed {episode['seed']} "
                            f"{split}[{pair_index}]"
                        )
                    rival_receipts = []
                    for alternative in prototype.SETTINGS:
                        if alternative == selected_setting:
                            continue
                        rival_python = prototype.apply_python(pair["input"], *alternative)
                        rival_racket = execute(programs[alternative], pair["input"], bridge)
                        if rival_racket != rival_python:
                            raise SystemExit(
                                f"rival Racket/Python mismatch for {alternative} "
                                f"seed {episode['seed']} {split}[{pair_index}]"
                            )
                        rival_receipts.append(
                            {
                                "setting": {
                                    "target_state": alternative[0],
                                    "output_color": alternative[1],
                                },
                                "output": rival_racket,
                                "disagrees": rival_racket != selected_racket,
                            }
                        )
                    checks.append(
                        {
                            "seed": episode["seed"],
                            "selected_setting": episode["parameter"],
                            "split": split,
                            "pair_index": pair_index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "selected_output": selected_racket,
                            "rivals": rival_receipts,
                        }
                    )
    finally:
        bridge.shutdown()

    train_checks = [row for row in checks if row["split"] == "train"]
    if not train_checks or not all(
        all(rival["disagrees"] for rival in row["rivals"]) for row in train_checks
    ):
        raise SystemExit("not every training pair refutes every alternative setting")

    report = {
        "schema": "e1516c24afbd-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; production authority unchanged",
        "task_id": prototype.TASK_ID,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "seed_base": args.seed_base,
        "parameters": {
            "target_state": {
                "allowed": list(prototype.ALLOWED_TARGET_STATES),
                "canonical_default": prototype.DEFAULT_TARGET_STATE,
            },
            "output_color": {
                "allowed": list(prototype.ALLOWED_OUTPUT_COLORS),
                "canonical_default": prototype.DEFAULT_OUTPUT_COLOR,
            },
            "chosen_once_per_episode": True,
            "selection": "SETTINGS[seed % 4] before pair construction",
            "input_dependency": (
                "all fixtures contain 00, 10, 01, and 11 and use input colors 1/9, "
                "so all four parameter settings are distinguishable"
            ),
        },
        "canonical_source_sha256": _sha256(canonical),
        "prototype_source_sha256": _sha256((HERE / "prototype.py").read_bytes()),
        "generator_source_sha256": episodes[0]["generator_source_sha256"],
        "racket_runtime": runtime_identity,
        "programs": {
            _setting_name(setting): {
                "parameter": {
                    "target_state": setting[0],
                    "output_color": setting[1],
                },
                "sha256": _sha256(source),
                "source": source,
            }
            for setting, source in programs.items()
        },
        "canonical_replay": canonical_replay,
        "episode_errors": {
            str(episode["seed"]): prototype.episode_errors(episode)
            for episode in episodes
        },
        "counts": {
            "settings": len(programs),
            "episodes": len(episodes),
            "train_pairs": len(train_checks),
            "test_pairs": len(checks) - len(train_checks),
            "canonical_pairs_replayed": len(canonical_replay),
            "racket_selected_pair_checks": len(checks),
            "racket_rival_pair_checks": sum(len(row["rivals"]) for row in checks),
            "fully_distinguishing_train_pairs": sum(
                all(rival["disagrees"] for rival in row["rivals"])
                for row in train_checks
            ),
        },
        "exact_disagreement": checks[0],
        "checks": checks,
        "limitations": [
            "The prototype is proposed evidence and is not wired into production selection.",
            "Only the declared two-by-two parameter family is exhaustively checked.",
            "Inputs are deliberately constrained to contain all four occupancy states.",
        ],
    }

    out_path = Path(args.out)
    _write_json(out_path, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "schema": "e1516c24afbd-parametric-materialization-v1",
            "prototype_source_sha256": report["prototype_source_sha256"],
            "generator_source_sha256": report["generator_source_sha256"],
            "files": {},
        }
        for setting, source in programs.items():
            name = _setting_name(setting)
            episode = next(
                episode
                for episode in episodes
                if (
                    episode["parameter"]["target_state"],
                    episode["parameter"]["output_color"],
                )
                == setting
            )
            files = {
                f"private/rules/{name}.rkt": source + "\n",
                f"private/{name}-episode.json": json.dumps(
                    episode, indent=2, sort_keys=True
                )
                + "\n",
                f"public/{name}-challenge.json": json.dumps(
                    prototype.public_challenge(episode), indent=2, sort_keys=True
                )
                + "\n",
            }
            for relative, body in files.items():
                path = artifact_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
                manifest["files"][relative] = {
                    "sha256": _sha256(body),
                    "bytes": len(body.encode("utf-8")),
                }
        _write_json(artifact_dir / "manifest.json", manifest)

    print(json.dumps({"status": "passed", "out": str(out_path), "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
