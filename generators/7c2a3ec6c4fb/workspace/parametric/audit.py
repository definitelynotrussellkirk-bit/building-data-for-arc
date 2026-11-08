"""Bounded authoring audit for the native 7c2a3ec6c4fb family.

This is a reusable pre-qualification check for future agents.  It verifies
seed determinism, setting-independent sampling, finite lesson identification,
query-prefix stability, output parity with the Python reference transform, and
the substantive 30x30 stress case.  Protected Racket authority remains the
native qualification command.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ADAPTER = HOME / "adapter.py"
SETTINGS = (
    {"crop_orientation": "as_found"},
    {"crop_orientation": "marker_to_top_left"},
)


def _load():
    name = "_audit_7c2a3ec6c4fb_" + hashlib.sha256(str(ADAPTER).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    if spec is None or spec.loader is None:
        raise ImportError(ADAPTER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 100:
        raise ValueError("seed_count must be an exact integer in 1..100")
    adapter = _load()
    jobs = []
    for seed in range(seed_count):
        episodes = [adapter.generate(seed, setting, 3, 4) for setting in SETTINGS]
        repeated = [adapter.generate(seed, setting, 3, 4) for setting in SETTINGS]
        assert episodes == repeated
        visible_inputs = [
            [pair["input"] for pair in episode["train"] + episode["test"]]
            for episode in episodes
        ]
        assert visible_inputs[0] == visible_inputs[1]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in visible_inputs[0]}) == 7
        for setting, episode in zip(SETTINGS, episodes):
            assert episode["certificate"]["surviving_settings"] == [setting]
            assert episode["certificate"]["ambiguous_rivals"] == []
            orientation = setting["crop_orientation"]
            assert all(
                pair["output"] == adapter.transform(pair["input"], orientation)
                for pair in episode["train"] + episode["test"]
            )
            prefix = adapter.generate(seed, setting, 3, 1)
            assert adapter.public_turn(prefix, 0) == adapter.public_turn(episode, 0)
            stress = episode["test"][-1]["input"]
            analysis = adapter.analyze(stress)
            jobs.append(
                {
                    "seed": seed,
                    "settings": setting,
                    "surviving_settings": episode["certificate"]["surviving_settings"],
                    "ambiguous_rivals": episode["certificate"]["ambiguous_rivals"],
                    "stress_shape": [len(stress), len(stress[0])],
                    "stress_nonzero_cells": sum(cell != 0 for row in stress for cell in row),
                    "stress_marker_corner": analysis["marker_corner"],
                    "stress_component_count": analysis["component_count"],
                }
            )
    return {
        "schema": "arcpuzzles-7c2a3ec6c4fb-self-audit-v1",
        "scope": f"{seed_count} seeds x 2 settings; 3 demonstrations; 4 prefix-stable queries; Python reference checks only",
        "jobs": jobs,
        "job_count": len(jobs),
        "ambiguous_job_count": sum(bool(job["ambiguous_rivals"]) for job in jobs),
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    report = build(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "jobs": report["job_count"],
                "ambiguous": report["ambiguous_job_count"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
