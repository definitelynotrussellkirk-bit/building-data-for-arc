#!/usr/bin/env python3
"""Execute and retain Racket evidence for the occurrence-threshold prototype."""
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


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_hash(source: str) -> str:
    return _sha256(" ".join(source.split()).encode())


def _canonical_program(root: Path) -> str:
    values = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            values.append(row["program_solution"])
    if not values or len(set(values)) != 1:
        raise RuntimeError("canonical program missing or ambiguous")
    return values[0]


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must be one `(rule! EXPR)` form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261021)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = _canonical_program(root)
    programs = {
        minimum: prototype.program_for(minimum, root=root)
        for minimum in prototype.MINIMUM_OCCURRENCES
    }
    if programs[prototype.DEFAULT_MINIMUM_OCCURRENCES] != canonical:
        raise SystemExit("default threshold no longer equals the canonical authority")
    if len({_normalized_hash(source) for source in programs.values()}) != len(programs):
        raise SystemExit("declared settings materialize identical Racket programs")

    episodes = {
        minimum: prototype.build_episode(
            args.seed,
            minimum_occurrences=minimum,
            n_train=3,
            n_test=1,
            root=root,
        )
        for minimum in prototype.MINIMUM_OCCURRENCES
    }
    for minimum, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"minimum_occurrences={minimum} invalid: {errors}")

    checks: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        for selected, episode in episodes.items():
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs: dict[str, Any] = {}
                    for candidate, source in programs.items():
                        racket_output = bridge.eval_text(_application(source, pair["input"]))
                        python_output = prototype.apply_python(pair["input"], candidate)
                        if racket_output != python_output:
                            raise SystemExit(
                                f"Racket/Python mismatch: selected={selected} "
                                f"{split}[{index}] candidate={candidate}"
                            )
                        outputs[str(candidate)] = racket_output
                    if outputs[str(selected)] != pair["output"]:
                        raise SystemExit(
                            f"selected label mismatch: minimum={selected} {split}[{index}]"
                        )
                    checks.append(
                        {
                            "episode_minimum_occurrences": selected,
                            "split": split,
                            "pair_index": index,
                            "input": pair["input"],
                            "outputs": outputs,
                            "settings_distinct": outputs["2"] != outputs["3"],
                        }
                    )
    finally:
        bridge.shutdown()

    demonstrations = [row for row in checks if row["split"] == "train"]
    if not demonstrations or not all(row["settings_distinct"] for row in demonstrations):
        raise SystemExit("retained demonstrations do not distinguish both settings")

    source_paths = {"prototype.py": HERE / "prototype.py", "verify.py": Path(__file__).resolve()}
    witness = demonstrations[0]
    report = {
        "schema": "70c33a3391ac-parametric-verification-v1",
        "status": "passed",
        "scope": prototype.STATUS,
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": "minimum_occurrences",
            "allowed_values": list(prototype.MINIMUM_OCCURRENCES),
            "default": prototype.DEFAULT_MINIMUM_OCCURRENCES,
            "meaning": "minimum number of exact colored component-crop occurrences required",
            "chosen_once_per_episode": True,
            "input_constraints": (
                "each retained scene has one crop exactly twice later in canonical scan order, "
                "one different crop exactly three times earlier, and two unique distractors"
            ),
        },
        "programs": {
            str(minimum): {
                "source": source,
                "sha256": _sha256(source.encode()),
                "normalized_sha256": _normalized_hash(source),
            }
            for minimum, source in programs.items()
        },
        "canonical_program_sha256": _sha256(canonical.encode()),
        "canonical_program_normalized_sha256": _normalized_hash(canonical),
        "prototype_source_sha256": {
            name: _sha256(path.read_bytes()) for name, path in source_paths.items()
        },
        "racket_runtime": runtime_identity,
        "episode_errors": {
            str(minimum): prototype.episode_errors(episode)
            for minimum, episode in episodes.items()
        },
        "counts": {
            "settings": len(episodes),
            "train_pairs_per_setting": 3,
            "test_pairs_per_setting": 1,
            "episode_pairs": len(checks),
            "racket_executions": len(checks) * len(programs),
            "distinguishing_train_pairs": sum(row["settings_distinct"] for row in demonstrations),
            "train_pairs": len(demonstrations),
        },
        "exact_disagreement": {
            "input": witness["input"],
            "minimum_occurrences_2_output": witness["outputs"]["2"],
            "minimum_occurrences_3_output": witness["outputs"]["3"],
        },
        "checks": checks,
        "limitations": [
            "This is a proposed task-local prototype and is not wired into selected production generation or approval metadata.",
            "Evidence covers two settings at one retained seed, not every lawful component scene.",
            "The extended grammar intentionally contains two repeated crop classes; canonical production scenes continue to contain exactly one class repeated twice.",
            "Threshold two inherits the canonical first-qualifying reversed-scan tie break; the retained placement makes that choice explicit rather than claiming order invariance.",
            "Finite demonstrations distinguish the declared threshold rival, not every possible crop-selection rule.",
        ],
    }
    out_path = Path(args.out)
    _write_json(out_path, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        files: dict[str, str] = {}
        for minimum, episode in episodes.items():
            stem = f"minimum-occurrences-{minimum}"
            files[f"{stem}.rkt"] = programs[minimum] + "\n"
            files[f"{stem}-episode.json"] = json.dumps(episode, indent=2, sort_keys=True) + "\n"
            files[f"{stem}-public.json"] = json.dumps(
                prototype.public_challenge(episode), indent=2, sort_keys=True
            ) + "\n"
        manifest = {
            "schema": "70c33a3391ac-parametric-materialization-v1",
            "seed": args.seed,
            "files": {},
        }
        for name, body in files.items():
            path = artifact_dir / name
            path.write_text(body, encoding="utf-8")
            manifest["files"][name] = {
                "sha256": _sha256(body.encode()),
                "bytes": len(body.encode()),
            }
        _write_json(artifact_dir / "manifest.json", manifest)

    print(json.dumps({"status": "passed", "out": str(out_path), "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
