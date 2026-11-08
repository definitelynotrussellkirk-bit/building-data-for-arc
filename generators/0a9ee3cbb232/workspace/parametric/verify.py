#!/usr/bin/env python3
"""Execute both run-axis Racket programs and retain source-bound evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import normalize_grid

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def callable_source(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("expected one (rule! BODY) source form")
    body = stripped[len("(rule!") : -1].strip()
    return body if body.startswith("(lambda") else f"(lambda (g) {body})"


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    expression = f"({callable_source(source)} {grid_literal(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261021)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    programs = {axis: prototype.program_for(axis) for axis in prototype.ALLOWED_AXES}
    if programs[prototype.DEFAULT_AXIS] != prototype.canonical_program():
        raise SystemExit("default program is not byte-for-byte canonical")
    if len(set(programs.values())) != len(programs):
        raise SystemExit("axis settings did not materialize distinct programs")

    episodes = {
        axis: prototype.build_episode(args.seed, run_axis=axis)
        for axis in prototype.ALLOWED_AXES
    }
    for axis, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"{axis} episode invalid: {errors}")

    checks: list[dict[str, Any]] = []
    canonical_replay: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=96)
    try:
        runtime_identity = bridge.runtime_identity
        record = prototype.canonical_record()
        canonical_pairs = list(record["train"]) + list(record["test"])
        for index, pair in enumerate(canonical_pairs):
            actual = execute(bridge, programs["horizontal"], pair["input"])
            canonical_replay.append(
                {"pair_index": index, "matches": actual == pair["output"], "actual": actual}
            )
        if not canonical_replay or not all(row["matches"] for row in canonical_replay):
            raise SystemExit("canonical horizontal default failed canonical replay")

        for axis, episode in episodes.items():
            alternative = prototype.other_axis(axis)
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    selected = execute(bridge, programs[axis], pair["input"])
                    rival = execute(bridge, programs[alternative], pair["input"])
                    selected_python = prototype.apply_python(pair["input"], axis)
                    rival_python = prototype.apply_python(pair["input"], alternative)
                    if selected != selected_python or selected != pair["output"]:
                        raise SystemExit(
                            f"selected Racket/Python mismatch for {axis} {split}[{pair_index}]"
                        )
                    if rival != rival_python:
                        raise SystemExit(
                            f"rival Racket/Python mismatch for {axis} {split}[{pair_index}]"
                        )
                    checks.append(
                        {
                            "setting": axis,
                            "alternative": alternative,
                            "split": split,
                            "pair_index": pair_index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "selected_output": selected,
                            "alternative_output": rival,
                            "settings_disagree": selected != rival,
                        }
                    )
    finally:
        bridge.shutdown()

    train_checks = [row for row in checks if row["split"] == "train"]
    if not train_checks or not all(row["settings_disagree"] for row in train_checks):
        raise SystemExit("not every retained demonstration distinguishes run_axis")
    if not all(row["settings_disagree"] for row in checks):
        raise SystemExit("a retained query does not distinguish run_axis")

    report = {
        "schema": "0a9ee3cbb232-parametric-run-axis-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; canonical production authority unchanged",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_AXES),
            "canonical_default": prototype.DEFAULT_AXIS,
            "chosen_once_per_episode": True,
            "selection_when_unpinned": "ALLOWED_AXES[seed % 2]",
            "input_dependency": (
                "inputs come from the selected canonical sampler and must make "
                "horizontal and vertical tallies disagree"
            ),
        },
        "programs": {
            axis: {
                "sha256": sha256(source),
                "normalized_sha256": sha256(" ".join(source.split())),
                "source": source,
            }
            for axis, source in programs.items()
        },
        "prototype_source_sha256": sha256((HERE / "prototype.py").read_bytes()),
        "selected_generator_sha256": next(
            iter({episode["generator_sha256"] for episode in episodes.values()})
        ),
        "racket_runtime": runtime_identity,
        "canonical_replay": canonical_replay,
        "episodes": episodes,
        "counts": {
            "canonical_pairs_replayed": len(canonical_replay),
            "settings": len(episodes),
            "train_pairs_per_setting": 3,
            "test_pairs_per_setting": 1,
            "racket_checked_variant_pairs": len(checks),
            "distinguishing_train_pairs": sum(row["settings_disagree"] for row in train_checks),
            "distinguishing_all_pairs": sum(row["settings_disagree"] for row in checks),
        },
        "exact_disagreement": checks[0],
        "checks": checks,
        "limitations": [
            "This is bounded evidence for two run-axis settings at one retained seed, not production approval.",
            "The selected generator and canonical Racket authority remain fixed to horizontal runs.",
            "Every retained pair refutes only the declared other-axis rival; undeclared rivals are not exhausted.",
            "Vertical counts may exceed six and are intentionally truncated by the unchanged 2x3 tally semantics.",
        ],
    }
    out = Path(args.out)
    write_json(out, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "0a9ee3cbb232-parametric-materialization-v1",
            "seed": args.seed,
            "files": {},
        }
        for axis, source in programs.items():
            payloads = {
                f"{axis}.rkt": source + "\n",
                f"{axis}-episode.json": json.dumps(episodes[axis], indent=2, sort_keys=True) + "\n",
                f"{axis}-public.json": json.dumps(
                    prototype.public_challenge(episodes[axis]), indent=2, sort_keys=True
                ) + "\n",
            }
            for name, body in payloads.items():
                path = artifact_dir / name
                path.write_text(body, encoding="utf-8")
                manifest["files"][name] = {
                    "sha256": sha256(body),
                    "bytes": len(body.encode("utf-8")),
                }
        write_json(artifact_dir / "manifest.json", manifest)

    print(json.dumps({"status": "passed", "out": str(out), "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
