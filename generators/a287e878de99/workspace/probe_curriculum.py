#!/usr/bin/env python3
"""Source-bound curriculum probe for generator a287e878de99.

This is a reviewer utility, not production sampler code.  It independently
checks the intended degree-one labels, canonical shortcut fit, every requested
cyclic lesson start, each possible query rotation of a five-pair bundle, and a
small joint-override boundary matrix.  Pass ``--full-overrides`` to enumerate
the complete advertised Cartesian override space.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_a287e878de99_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def endpoint_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent oracle: retain gray cells with exactly one gray 4-neighbor."""
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in row] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            degree = sum(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == 5
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if degree == 1:
                output[row][col] = 5
    return output


def _override_values(full: bool) -> dict[str, tuple[Any, ...]]:
    if full:
        return {
            "grid_h": tuple(range(7, 16)),
            "grid_w": tuple(range(8, 18)),
            "component_count": tuple(range(2, 6)),
            "scene_pattern": ("path", "branch", "cycle", "singleton"),
        }
    return {
        "grid_h": (7, 15),
        "grid_w": (8, 17),
        "component_count": (2, 5),
        "scene_pattern": ("path", "branch", "cycle", "singleton"),
    }


def run_probe(*, starts: int, full_overrides: bool) -> dict[str, Any]:
    gen = _load_generator()
    generator_path = TASK_HOME / "generator.py"
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()

    canonical = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    canonical_failures: list[dict[str, Any]] = []
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for index, pair in enumerate(canonical):
            if rival(pair["input"]) != pair["output"]:
                canonical_failures.append({"rival": name, "pair": index})

    curriculum_failures: list[dict[str, Any]] = []
    checked_rotations = 0
    bands = ("easy", "medium", "hard")
    for band in bands:
        for start in range(starts):
            pairs = []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(0xA287E878, index, difficulty=band)
                output = endpoint_output(grid)
                if output != gen.rule_mirror(grid):
                    curriculum_failures.append(
                        {"band": band, "start": start, "index": index, "error": "oracle drift"}
                    )
                pairs.append({"input": grid, "output": output})
            for query_index in range(len(pairs)):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                checked_rotations += 1
                if reasons:
                    curriculum_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

    values = _override_values(full_overrides)
    override_failures: list[dict[str, Any]] = []
    checked_overrides = 0
    for band in (None, *bands):
        for height in values["grid_h"]:
            for width in values["grid_w"]:
                for count in values["component_count"]:
                    for scene in values["scene_pattern"]:
                        requested = {
                            "grid_h": height,
                            "grid_w": width,
                            "component_count": count,
                            "scene_pattern": scene,
                        }
                        checked_overrides += 1
                        try:
                            grid = gen.generate(
                                0x0B5E7E57,
                                checked_overrides,
                                difficulty=band,
                                **requested,
                            )
                            observed = gen.observe_overrides(grid)
                            if observed != requested:
                                override_failures.append(
                                    {"band": band, "requested": requested, "observed": observed}
                                )
                            if endpoint_output(grid) != gen.rule_mirror(grid):
                                override_failures.append(
                                    {"band": band, "requested": requested, "error": "oracle drift"}
                                )
                        except Exception as exc:  # evidence should preserve the exact failing request
                            override_failures.append(
                                {
                                    "band": band,
                                    "requested": requested,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )

    failures = canonical_failures + curriculum_failures + override_failures
    return {
        "schema": "a287e878de99-curriculum-probe-v1",
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "generator_sha256": generator_sha256,
        "declared_rule_hash": gen.RULE_HASH,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "bands": list(bands),
        "starts_per_band": starts,
        "checked_rotations": checked_rotations,
        "checked_overrides": checked_overrides,
        "full_overrides": full_overrides,
        "canonical_pairs": len(canonical),
        "canonical_rivals": sorted(gen.CANONICAL_SHORTCUTS),
        "canonical_failures": canonical_failures,
        "curriculum_failures": curriculum_failures,
        "override_failures": override_failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--full-overrides", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.starts < 1:
        parser.error("--starts must be positive")
    report = run_probe(starts=args.starts, full_overrides=args.full_overrides)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
