#!/usr/bin/env python3
"""Measure whether one advertised generator axis has any observable effect."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(repo: Path, task_id: str):
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    path = repo / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_axis_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--task", required=True)
    parser.add_argument("--axis", required=True)
    parser.add_argument("--left", required=True, help="JSON value")
    parser.add_argument("--right", required=True, help="JSON value")
    parser.add_argument("--pairs-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs_per_band < 1:
        parser.error("--pairs-per-band must be positive")

    repo = args.repo.resolve()
    module, generator_path = _load(repo, args.task)
    left_value: Any = json.loads(args.left)
    right_value: Any = json.loads(args.right)
    left_override = {args.axis: left_value}
    right_override = {args.axis: right_value}

    identical = 0
    total = 0
    errors: list[dict[str, Any]] = []
    first: dict[str, Any] | None = None
    for difficulty in ("easy", "medium", "hard"):
        for index in range(args.pairs_per_band):
            seed = f"audit-ignored-axis-v1:{args.task}:{difficulty}:{index}"
            try:
                left_grid = module.generate(
                    seed, index, difficulty=difficulty, **left_override
                )
                right_grid = module.generate(
                    seed, index, difficulty=difficulty, **right_override
                )
                same = left_grid == right_grid
                total += 1
                identical += int(same)
                if first is None:
                    first = {
                        "seed": seed,
                        "sample_index": index,
                        "difficulty": difficulty,
                        "left_input": left_grid,
                        "right_input": right_grid,
                        "left_self_check_errors": list(module.self_check(left_grid)),
                        "right_self_check_errors": list(module.self_check(right_grid)),
                    }
                if not same:
                    errors.append(
                        {
                            "seed": seed,
                            "sample_index": index,
                            "difficulty": difficulty,
                            "kind": "outputs_differ",
                        }
                    )
            except Exception as exc:
                errors.append(
                    {
                        "seed": seed,
                        "sample_index": index,
                        "difficulty": difficulty,
                        "kind": "exception",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    assert first is not None
    report = {
        "schema": "arcpuzzles-audit-ignored-axis-v1",
        "task_id": args.task,
        "generator_path": str(generator_path.relative_to(repo)),
        "generator_sha256": _sha(generator_path),
        "axis": args.axis,
        "left_overrides": left_override,
        "right_overrides": right_override,
        "seed_scheme": f"audit-ignored-axis-v1:{args.task}:<difficulty>:<index>",
        "difficulties": ["easy", "medium", "hard"],
        "indices_per_difficulty": args.pairs_per_band,
        "total_pairs": total,
        "byte_identical_pairs": identical,
        "errors": errors,
        "first_exact_example": first,
        "conclusion": (
            f"advertised axis {args.axis!r} had no observable effect in all sampled pairs"
            if identical == total and not errors
            else "mixed"
        ),
        "command": [
            "python3",
            "../checks/audit/ignored_axis_probe.py",
            "--repo",
            ".",
            "--task",
            args.task,
            "--axis",
            args.axis,
            "--left",
            args.left,
            "--right",
            args.right,
            "--pairs-per-band",
            str(args.pairs_per_band),
            "--out",
            str(args.out),
        ],
        "cwd": "repo",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "task_id": args.task,
                "axis": args.axis,
                "total_pairs": total,
                "byte_identical_pairs": identical,
                "errors": len(errors),
            },
            sort_keys=True,
        )
    )
    return 0 if identical == total and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
