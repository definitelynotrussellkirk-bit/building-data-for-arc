#!/usr/bin/env python3
"""Compare valid generate() outputs between two source-bound generator files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


def _load(path: Path, name: str) -> tuple[Any, str]:
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    spec = importlib.util.spec_from_file_location(f"_{name}_{digest}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def _frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        parser.error("--out already exists; use a fresh evidence path")

    before, before_sha = _load(args.before.resolve(), "before")
    after, after_sha = _load(args.after.resolve(), "after")
    if tuple(before.SCENE_PROFILES) != tuple(after.SCENE_PROFILES):
        raise AssertionError("scene profile surface changed")

    mismatches: list[dict[str, Any]] = []
    cases = 0
    unique = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for profile_index, profile in enumerate(after.SCENE_PROFILES):
            for index in range(12):
                seed = 300_000 + 10_000 * profile_index + 100 * index
                sample_index = 17 * index + profile_index
                old = before.generate(
                    seed, sample_index, difficulty=difficulty, scene_profile=profile
                )
                new = after.generate(
                    seed, sample_index, difficulty=difficulty, scene_profile=profile
                )
                cases += 1
                unique.add(_frozen(new))
                if old != new:
                    mismatches.append(
                        {
                            "kind": "profile",
                            "difficulty": difficulty,
                            "profile": profile,
                            "seed": seed,
                            "sample_index": sample_index,
                        }
                    )
                if after.self_check(new):
                    raise AssertionError("after source produced an invalid profile draw")

        for index in range(100):
            seed = 700_000 + index
            sample_index = 31 * index
            old = before.generate(seed, sample_index, difficulty=difficulty)
            new = after.generate(seed, sample_index, difficulty=difficulty)
            cases += 1
            unique.add(_frozen(new))
            if old != new:
                mismatches.append(
                    {
                        "kind": "default",
                        "difficulty": difficulty,
                        "seed": seed,
                        "sample_index": sample_index,
                    }
                )
            if after.self_check(new):
                raise AssertionError("after source produced an invalid default draw")

    result = {
        "schema": "arc-generator-valid-output-stability-v1",
        "task_id": after.TASK_ID,
        "before": {"path": str(args.before), "sha256": before_sha},
        "after": {"path": str(args.after), "sha256": after_sha},
        "cases": cases,
        "unique_outputs": len(unique),
        "mismatches": mismatches,
        "valid_generate_outputs_byte_identical": not mismatches,
        "scope": (
            "All declared profiles across four difficulty arguments (12 draws each) "
            "plus 100 default draws per difficulty; invalid scalar calls are intentionally excluded."
        ),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
