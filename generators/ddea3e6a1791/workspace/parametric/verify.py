#!/usr/bin/env python3
"""Execute both proposed background-color settings with the pinned Racket runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must use one `(rule! BODY)` form")
    body = stripped[len("(rule!") : -1].strip()
    return f"(lambda (g) {body})"


def _racket_grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _racket_application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_racket_grid_literal(grid)})"


def _canonical_program(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program missing")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = _canonical_program(root)
    programs = {value: prototype.program_for(value) for value in prototype.ALLOWED_VALUES}
    if _normalized_hash(programs[0]) != _normalized_hash(canonical):
        raise SystemExit("background_color=0 no longer matches the canonical program")

    episodes = {
        value: prototype.build_episode(
            args.seed, background_color=value, n_train=3, n_test=1
        )
        for value in prototype.ALLOWED_VALUES
    }
    for value, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"background {value} episode invalid: {errors}")

    bridge = RacketBridge(timeout=30, max_calls_before_restart=64)
    checks: list[dict[str, Any]] = []
    try:
        runtime_identity = bridge.runtime_identity
        for value, episode in episodes.items():
            alternative = prototype.other_value(value)
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    selected_racket = bridge.eval_text(
                        _racket_application(programs[value], pair["input"])
                    )
                    alternative_racket = bridge.eval_text(
                        _racket_application(programs[alternative], pair["input"])
                    )
                    selected_python = prototype.apply_python(pair["input"], value)
                    alternative_python = prototype.apply_python(
                        pair["input"], alternative
                    )
                    if selected_racket != pair["output"] or selected_racket != selected_python:
                        raise SystemExit(
                            f"Racket/Python mismatch for background {value} {split}[{index}]"
                        )
                    if alternative_racket != alternative_python:
                        raise SystemExit(
                            "alternative Racket/Python mismatch for "
                            f"background {value} {split}[{index}]"
                        )
                    checks.append(
                        {
                            "setting": value,
                            "alternative": alternative,
                            "split": split,
                            "pair_index": index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "selected_output": selected_racket,
                            "alternative_output": alternative_racket,
                            "settings_disagree": selected_racket != alternative_racket,
                        }
                    )
    finally:
        bridge.shutdown()

    demo_checks = [row for row in checks if row["split"] == "train"]
    if not demo_checks or not all(row["settings_disagree"] for row in demo_checks):
        raise SystemExit("not every retained demonstration distinguishes the settings")

    generator_sha = next(iter(episodes.values()))["generator_sha256"]
    if any(episode["generator_sha256"] != generator_sha for episode in episodes.values()):
        raise SystemExit("episodes used different generator bytes")

    report = {
        "schema": "ddea3e6a1791-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed prototype; not selected canonical execution",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_VALUES),
            "default": prototype.DEFAULT_VALUE,
            "chosen_once_per_episode": True,
            "input_dependency": (
                "the selected background fills the canvas; swapping 0 and 9 preserves "
                "foreground geometry and makes the wrong setting return the full canvas"
            ),
        },
        "programs": {
            str(value): {
                "source": source,
                "sha256": hashlib.sha256(source.encode()).hexdigest(),
                "normalized_sha256": _normalized_hash(source),
            }
            for value, source in programs.items()
        },
        "canonical_program_normalized_sha256": _normalized_hash(canonical),
        "generator_sha256": generator_sha,
        "racket_runtime": runtime_identity,
        "episode_errors": {
            str(value): prototype.episode_errors(episode)
            for value, episode in episodes.items()
        },
        "counts": {
            "settings": len(episodes),
            "train_pairs_per_setting": 3,
            "test_pairs_per_setting": 1,
            "racket_checked_pairs": len(checks),
            "distinguishing_train_pairs": sum(
                row["settings_disagree"] for row in demo_checks
            ),
            "train_pairs": len(demo_checks),
        },
        "exact_disagreement": checks[0],
        "checks": checks,
        "limitations": [
            "Only background colors 0 and 9 were checked at one retained seed.",
            "The alternative changes the input color role as well as the executed predicate.",
            "The prototype is not wired into production generation or approval metadata.",
            "Finite demonstrations distinguish the declared rival, not every imaginable rule.",
        ],
    }

    out_path = Path(args.out)
    _write_json(out_path, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "schema": "ddea3e6a1791-parametric-materialization-v1",
            "seed": args.seed,
            "generator_sha256": generator_sha,
            "files": {},
        }
        for value, episode in episodes.items():
            files = {
                f"background-{value}.rkt": programs[value] + "\n",
                f"background-{value}-episode.json": json.dumps(
                    episode, indent=2, sort_keys=True
                )
                + "\n",
                f"background-{value}-public.json": json.dumps(
                    prototype.public_challenge(episode), indent=2, sort_keys=True
                )
                + "\n",
            }
            for name, body in files.items():
                path = artifact_dir / name
                path.write_text(body, encoding="utf-8")
                manifest["files"][name] = {
                    "sha256": hashlib.sha256(body.encode()).hexdigest(),
                    "bytes": len(body.encode()),
                }
        _write_json(artifact_dir / "manifest.json", manifest)

    print(
        json.dumps(
            {"status": "passed", "out": str(out_path), "counts": report["counts"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
