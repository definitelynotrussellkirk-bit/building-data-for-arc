#!/usr/bin/env python3
"""Bounded deterministic stress check for the direction-parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "ffcd7510821d_stress_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load direction-parametric marker rotation prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def run(seeds: int = 256) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 10_000:
        raise ValueError("seeds must be an exact integer in 1..10000")
    scene_count = 0
    episode_count = 0
    max_shape = [0, 0]
    public_ids: set[str] = set()
    direction_contrasts = 0
    for seed in range(seeds):
        inputs = [prototype.build_input(seed, slot) for slot in range(len(prototype.PROFILES))]
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
        if len(encoded) != len(set(encoded)):
            raise RuntimeError(f"duplicate input at seed {seed}")
        scene_count += len(inputs)
        for grid in inputs:
            max_shape[0] = max(max_shape[0], len(grid))
            max_shape[1] = max(max_shape[1], len(grid[0]))

        full = {}
        for direction in prototype.DIRECTIONS:
            for demos in (2, 6):
                episode = prototype.generate_episode(
                    seed,
                    direction=direction,
                    demos=demos,
                    queries=4,
                )
                audit = prototype.audit_episode(episode)
                if (
                    audit["setting_survivors"] != [direction]
                    or audit["ambiguous_query_changers"]
                    or audit["surviving_equivalent_rivals"]
                ):
                    raise RuntimeError(f"shortcut audit failed at seed {seed}: {audit}")
                visible = prototype.public_challenge(episode)
                public_id = hashlib.sha256(public_challenge_bytes(visible)).hexdigest()
                if public_id in public_ids:
                    raise RuntimeError(f"duplicate visible challenge: {public_id}")
                public_ids.add(public_id)
                episode_count += 1
                if demos == 6:
                    full[direction] = episode
        left = full["clockwise"]
        right = full["counterclockwise"]
        if [p["input"] for p in left["train"] + left["test"]] != [
            p["input"] for p in right["train"] + right["test"]
        ]:
            raise RuntimeError(f"setting-dependent input sampling at seed {seed}")
        if not any(
            a["output"] != b["output"]
            for a, b in zip(left["train"], right["train"])
        ):
            raise RuntimeError(f"directions do not contrast at seed {seed}")
        direction_contrasts += 1

    return {
        "schema": "ffcd7510821d-direction-stress-v1",
        "status": "passed",
        "seeds": seeds,
        "scenes": scene_count,
        "episodes": episode_count,
        "public_challenges": len(public_ids),
        "direction_contrasts": direction_contrasts,
        "max_shape": max_shape,
        "demo_counts": [2, 6],
        "queries": 4,
        "limits": (
            "Deterministic seeds 0..N-1; finite declared rivals and structural "
            "checks only. Protected Racket qualification is separate."
        ),
    }


def write_report(path: Path, report: dict) -> Path:
    path = Path(path)
    raw = (
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != raw:
        raise FileExistsError(f"refusing to replace differing report: {path}")
    path.write_bytes(raw)
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=256)
    parser.add_argument("--out", required=True, type=Path)
    options = parser.parse_args(argv)
    try:
        report = run(options.seeds)
        write_report(options.out, report)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
