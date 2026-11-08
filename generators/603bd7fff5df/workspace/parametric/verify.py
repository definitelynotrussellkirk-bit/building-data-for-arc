#!/usr/bin/env python3
"""Execute every proposed halo-depth Racket program and retain evidence."""
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
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = _canonical_program(root)
    programs = {depth: prototype.program_for(depth) for depth in prototype.HALO_DEPTHS}
    if _normalized_hash(programs[prototype.DEFAULT_HALO_DEPTH]) != _normalized_hash(canonical):
        raise SystemExit("default halo depth no longer matches the canonical program")
    if len({_normalized_hash(source) for source in programs.values()}) != len(programs):
        raise SystemExit("two declared halo depths materialize the same Racket program")

    episodes = {
        depth: prototype.build_episode(args.seed, halo_depth=depth, n_train=3, n_test=1)
        for depth in prototype.HALO_DEPTHS
    }
    for depth, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"halo_depth={depth} episode invalid: {errors}")

    checks: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        for selected_depth, episode in episodes.items():
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs: dict[str, Any] = {}
                    for candidate_depth, source in programs.items():
                        racket_output = bridge.eval_text(_application(source, pair["input"]))
                        python_output = prototype.apply_python(pair["input"], candidate_depth)
                        if racket_output != python_output:
                            raise SystemExit(
                                f"Racket/Python mismatch for halo_depth={selected_depth} "
                                f"{split}[{index}] under candidate {candidate_depth}"
                            )
                        outputs[str(candidate_depth)] = racket_output
                    selected_output = outputs[str(selected_depth)]
                    if selected_output != pair["output"]:
                        raise SystemExit(
                            f"selected label mismatch for halo_depth={selected_depth} {split}[{index}]"
                        )
                    checks.append(
                        {
                            "episode_halo_depth": selected_depth,
                            "split": split,
                            "pair_index": index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "outputs": outputs,
                            "all_depths_distinct": len(
                                {tuple(tuple(row) for row in output) for output in outputs.values()}
                            )
                            == len(outputs),
                        }
                    )
    finally:
        bridge.shutdown()

    train_checks = [row for row in checks if row["split"] == "train"]
    if not train_checks or not all(row["all_depths_distinct"] for row in train_checks):
        raise SystemExit("not every retained demonstration distinguishes all halo depths")

    generator_sha = next(iter(episodes.values()))["generator_sha256"]
    if any(episode["generator_sha256"] != generator_sha for episode in episodes.values()):
        raise SystemExit("episodes used different generator bytes")

    exact = train_checks[0]
    selected = exact["episode_halo_depth"]
    rival = next(depth for depth in prototype.HALO_DEPTHS if depth != selected)
    exact_disagreement = {
        "episode_halo_depth": selected,
        "rival_halo_depth": rival,
        "sampling": exact["sampling"],
        "input": exact["input"],
        "selected_output": exact["outputs"][str(selected)],
        "rival_output": exact["outputs"][str(rival)],
    }

    source_paths = {
        "prototype.py": HERE / "prototype.py",
        "verify.py": Path(__file__).resolve(),
    }
    report = {
        "schema": "603bd7fff5df-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; not selected canonical execution",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": "halo_depth",
            "allowed_values": list(prototype.HALO_DEPTHS),
            "default": prototype.DEFAULT_HALO_DEPTH,
            "meaning": "number of rows retained above and below the gray-marker bounding box",
            "chosen_once_per_episode": True,
            "input_constraints": (
                "every retained input has at least two rows above and below the gray bbox, "
                "canonical one-row halo evidence, and added blue evidence in the two-row halo"
            ),
        },
        "programs": {
            str(depth): {
                "source": source,
                "sha256": _sha256_bytes(source.encode()),
                "normalized_sha256": _normalized_hash(source),
            }
            for depth, source in programs.items()
        },
        "canonical_program_normalized_sha256": _normalized_hash(canonical),
        "generator_sha256": generator_sha,
        "prototype_source_sha256": {
            name: _sha256_bytes(path.read_bytes()) for name, path in source_paths.items()
        },
        "racket_runtime": runtime_identity,
        "episode_errors": {
            str(depth): prototype.episode_errors(episode) for depth, episode in episodes.items()
        },
        "counts": {
            "settings": len(episodes),
            "train_pairs_per_setting": 3,
            "test_pairs_per_setting": 1,
            "episode_pairs": len(checks),
            "racket_executions": len(checks) * len(programs),
            "pairwise_distinguishing_train_pairs": sum(
                row["all_depths_distinct"] for row in train_checks
            ),
            "train_pairs": len(train_checks),
        },
        "exact_disagreement": exact_disagreement,
        "checks": checks,
        "limitations": [
            "This is a task-local prototype and is not wired into production generation or approval metadata.",
            "Evidence covers three declared depths at one retained seed, not every lawful input.",
            "Output dimensions make the bounded depth alternatives easy to identify; this tests rule variation, not resistance to all imaginable shortcuts.",
            "Finite demonstrations eliminate the two declared parameter rivals, not every possible crop rule.",
        ],
    }

    out_path = Path(args.out)
    _write_json(out_path, report)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "schema": "603bd7fff5df-parametric-materialization-v1",
            "seed": args.seed,
            "generator_sha256": generator_sha,
            "files": {},
        }
        for depth, episode in episodes.items():
            stem = f"halo-depth-{depth}"
            files = {
                f"{stem}.rkt": programs[depth] + "\n",
                f"{stem}-episode.json": json.dumps(episode, indent=2, sort_keys=True) + "\n",
                f"{stem}-public.json": json.dumps(
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
