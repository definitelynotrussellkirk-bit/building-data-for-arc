#!/usr/bin/env python3
"""Execute both proposed partition-axis settings with the pinned Racket runtime."""
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

RULE_DIR = HERE / "rules"


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def racket_callable(source: str) -> str:
    """Convert one `(rule! BODY)` source into a directly callable expression."""
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must use one `(rule! BODY)` form")
    body = stripped[len("(rule!") : -1].strip()
    if body.startswith("(lambda"):
        return body
    return f"(lambda (g) {body})"


def racket_grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def racket_application(source: str, grid: list[list[int]]) -> str:
    return f"({racket_callable(source)} {racket_grid_literal(grid)})"


def canonical_program(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program missing")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def retained_rule_path(axis: str) -> Path:
    return RULE_DIR / f"{axis}.rkt"


def verify_retained_rules(programs: dict[str, str]) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for axis, source in programs.items():
        path = retained_rule_path(axis)
        expected = source + "\n"
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            raise RuntimeError(f"retained Racket source does not match {axis}: {path}")
        receipts[axis] = {
            "path": str(path.relative_to(HERE)),
            "sha256": hashlib.sha256(source.encode()).hexdigest(),
            "normalized_sha256": normalized_hash(source),
            "source": source,
        }
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = canonical_program(root)
    programs = {axis: prototype.program_for(axis) for axis in prototype.ALLOWED_AXES}
    if normalized_hash(programs[prototype.DEFAULT_AXIS]) != normalized_hash(canonical):
        raise SystemExit("horizontal default no longer matches the canonical program")
    rule_receipts = verify_retained_rules(programs)

    episodes = {
        axis: prototype.build_episode(
            args.seed, partition_axis=axis, n_train=3, n_test=1
        )
        for axis in prototype.ALLOWED_AXES
    }
    for axis, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"{axis} episode invalid: {errors}")

    bridge = RacketBridge(timeout=30, max_calls_before_restart=64)
    checks: list[dict[str, Any]] = []
    try:
        runtime_identity = bridge.runtime_identity
        for axis, episode in episodes.items():
            alternative = prototype.other_axis(axis)
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    selected_racket = bridge.eval_text(
                        racket_application(programs[axis], pair["input"])
                    )
                    alternative_racket = bridge.eval_text(
                        racket_application(programs[alternative], pair["input"])
                    )
                    selected_python = prototype.apply_python(pair["input"], axis)
                    alternative_python = prototype.apply_python(
                        pair["input"], alternative
                    )
                    if selected_racket != pair["output"] or selected_racket != selected_python:
                        raise SystemExit(
                            f"selected Racket/Python mismatch for {axis} {split}[{pair_index}]"
                        )
                    if alternative_racket != alternative_python:
                        raise SystemExit(
                            f"alternative Racket/Python mismatch for {axis} {split}[{pair_index}]"
                        )
                    checks.append(
                        {
                            "setting": axis,
                            "alternative": alternative,
                            "split": split,
                            "pair_index": pair_index,
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
    if not all(row["settings_disagree"] for row in checks):
        raise SystemExit("a retained query does not distinguish the settings")

    generator_hashes = {episode["generator_sha256"] for episode in episodes.values()}
    if len(generator_hashes) != 1:
        raise SystemExit("episodes used different generator bytes")
    generator_sha256 = next(iter(generator_hashes))
    prototype_sha256 = hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest()

    report = {
        "schema": "df3c6021b715-parametric-axis-verification-v1",
        "status": "passed",
        "scope": "proposed prototype; not selected canonical execution",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_AXES),
            "canonical_default": prototype.DEFAULT_AXIS,
            "chosen_once_per_episode": True,
            "selection": "ALLOWED_AXES[seed % 2] when not explicitly pinned",
            "input_dependency": (
                "two distinct interior dots, one in each horizontal half and one in "
                "each vertical half, so both axis rules are lawful on the same input"
            ),
        },
        "programs": rule_receipts,
        "canonical_program_normalized_sha256": normalized_hash(canonical),
        "prototype_source_sha256": prototype_sha256,
        "generator_sha256": generator_sha256,
        "racket_runtime": runtime_identity,
        "episode_errors": {
            axis: prototype.episode_errors(episode)
            for axis, episode in episodes.items()
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
            "distinguishing_all_pairs": sum(
                row["settings_disagree"] for row in checks
            ),
        },
        "exact_disagreement": checks[0],
        "checks": checks,
        "limitations": [
            "Bounded evidence for two axis settings at one retained seed, not production approval.",
            "The selected canonical generator and Racket authority remain fixed to horizontal frames.",
            "Inputs are deliberately constrained to be lawful under both settings; broader parametric sampling is untested.",
            "The labelled demonstrations refute the declared alternative axis only; undeclared rivals are not exhausted.",
        ],
    }

    out_path = Path(args.out)
    write_json(out_path, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "schema": "df3c6021b715-parametric-axis-materialization-v1",
            "seed": args.seed,
            "generator_sha256": generator_sha256,
            "prototype_source_sha256": prototype_sha256,
            "files": {},
        }
        for axis, episode in episodes.items():
            files = {
                f"{axis}.rkt": programs[axis] + "\n",
                f"{axis}-episode.json": json.dumps(
                    episode, indent=2, sort_keys=True
                )
                + "\n",
                f"{axis}-public.json": json.dumps(
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
        write_json(artifact_dir / "manifest.json", manifest)

    print(
        json.dumps(
            {
                "status": "passed",
                "out": str(out_path),
                "counts": report["counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
