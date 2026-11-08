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
from reviewer_support import canonical_path, find_root

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_hash(source: str) -> str:
    return _sha256_bytes(" ".join(source.split()).encode())


def _canonical_program(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program missing")


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must use one `(rule! EXPR)` form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


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
    programs = {setting: prototype.program_for(setting) for setting in prototype.SETTING_IDS}
    if _normalized_hash(programs[prototype.DEFAULT_SETTING]) != _normalized_hash(canonical):
        raise SystemExit("default setting no longer matches the canonical program")
    if len({_normalized_hash(source) for source in programs.values()}) != len(programs):
        raise SystemExit("two declared settings materialize the same Racket program")

    episodes = {
        setting: prototype.build_episode(args.seed, setting=setting, n_train=3, n_test=1)
        for setting in prototype.SETTING_IDS
    }
    for setting, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"{setting} episode invalid: {errors}")

    checks: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        for setting, episode in episodes.items():
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs: dict[str, Any] = {}
                    for candidate, source in programs.items():
                        racket_output = bridge.eval_text(_application(source, pair["input"]))
                        python_output = prototype.apply_python(pair["input"], candidate)
                        if racket_output != python_output:
                            raise SystemExit(
                                f"Racket/Python mismatch for {setting} {split}[{index}] "
                                f"under candidate {candidate}"
                            )
                        outputs[candidate] = racket_output
                    selected_output = outputs[setting]
                    if selected_output != pair["output"]:
                        raise SystemExit(f"selected label mismatch for {setting} {split}[{index}]")
                    checks.append(
                        {
                            "episode_setting": setting,
                            "episode_parameters": prototype.parameters_for(setting),
                            "split": split,
                            "pair_index": index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "outputs": outputs,
                            "all_settings_distinct": len(
                                {tuple(tuple(row) for row in output) for output in outputs.values()}
                            )
                            == len(outputs),
                        }
                    )
    finally:
        bridge.shutdown()

    train_checks = [row for row in checks if row["split"] == "train"]
    if not train_checks or not all(row["all_settings_distinct"] for row in train_checks):
        raise SystemExit("not every retained demonstration distinguishes all settings")

    generator_sha = next(iter(episodes.values()))["generator_sha256"]
    if any(episode["generator_sha256"] != generator_sha for episode in episodes.values()):
        raise SystemExit("episodes used different generator bytes")

    exact = checks[0]
    selected = exact["episode_setting"]
    rival = next(setting for setting in prototype.SETTING_IDS if setting != selected)
    exact_disagreement = {
        "episode_setting": selected,
        "rival_setting": rival,
        "sampling": exact["sampling"],
        "input": exact["input"],
        "selected_output": exact["outputs"][selected],
        "rival_output": exact["outputs"][rival],
    }

    source_paths = {
        "prototype.py": HERE / "prototype.py",
        "verify.py": Path(__file__).resolve(),
    }
    report = {
        "schema": "8d7d1364cf11-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed prototype; not selected canonical execution",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameters": {
            "anchor_mode": {
                "allowed_values": list(prototype.PARAMETERS["anchor_mode"]),
                "default": "matching_cell",
                "meaning": "align the matching source cell or the template bounding-box origin to each productive dot",
            },
            "canvas_mode": {
                "allowed_values": list(prototype.PARAMETERS["canvas_mode"]),
                "default": "clear",
                "meaning": "start from an all-4 canvas or preserve the input before stamping",
            },
            "chosen_once_per_episode": True,
            "input_constraints": (
                "generated episodes use three uniquely anchored templates, two productive dots per template, "
                "and retained inputs for which all four settings yield distinct outputs"
            ),
        },
        "setting_ids": list(prototype.SETTING_IDS),
        "default_setting": prototype.DEFAULT_SETTING,
        "programs": {
            setting: {
                "parameters": prototype.parameters_for(setting),
                "source": source,
                "sha256": _sha256_bytes(source.encode()),
                "normalized_sha256": _normalized_hash(source),
            }
            for setting, source in programs.items()
        },
        "canonical_program_normalized_sha256": _normalized_hash(canonical),
        "generator_sha256": generator_sha,
        "prototype_source_sha256": {
            name: _sha256_bytes(path.read_bytes()) for name, path in source_paths.items()
        },
        "racket_runtime": runtime_identity,
        "episode_errors": {
            setting: prototype.episode_errors(episode) for setting, episode in episodes.items()
        },
        "counts": {
            "settings": len(episodes),
            "train_pairs_per_setting": 3,
            "test_pairs_per_setting": 1,
            "episode_pairs": len(checks),
            "racket_executions": len(checks) * len(programs),
            "pairwise_distinguishing_train_pairs": sum(
                row["all_settings_distinct"] for row in train_checks
            ),
            "train_pairs": len(train_checks),
        },
        "exact_disagreement": exact_disagreement,
        "checks": checks,
        "limitations": [
            "This is a task-local prototype and is not wired into production generation or approval metadata.",
            "Evidence covers the four declared settings at one retained seed, not every possible input.",
            "Finite demonstrations eliminate the three declared parameter rivals, not every imaginable rule.",
        ],
    }

    out_path = Path(args.out)
    _write_json(out_path, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "schema": "8d7d1364cf11-parametric-materialization-v1",
            "seed": args.seed,
            "generator_sha256": generator_sha,
            "files": {},
        }
        for setting, episode in episodes.items():
            files = {
                f"{setting}.rkt": programs[setting] + "\n",
                f"{setting}-episode.json": json.dumps(episode, indent=2, sort_keys=True) + "\n",
                f"{setting}-public.json": json.dumps(
                    prototype.public_challenge(episode), indent=2, sort_keys=True
                )
                + "\n",
            }
            for name, body in files.items():
                path = artifact_dir / name
                path.write_text(body, encoding="utf-8")
                manifest["files"][name] = {
                    "sha256": _sha256_bytes(body.encode()),
                    "bytes": len(body.encode()),
                }
        _write_json(artifact_dir / "manifest.json", manifest)

    print(json.dumps({"status": "passed", "out": str(out_path), "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
