#!/usr/bin/env python3
"""Bounded learnability and public-projection audit for the native adapter."""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes


_HOME = Path(__file__).resolve().parent


def _load_adapter():
    path = _HOME / "adapter.py"
    name = "_arc_040bfb038c65_parametric_audit_adapter"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_ADAPTER = _load_adapter()
_GENERATOR = _ADAPTER._GENERATOR


def _paint(grid, cells):
    output = deepcopy(grid)
    for row, col in cells:
        output[row][col] = 8
    return output


def _largest_row_major(grid):
    objects = _GENERATOR._components(grid)
    size = max(map(len, objects))
    return _paint(grid, next(obj for obj in objects if len(obj) == size))


def _fixed_top_left(grid):
    objects = _GENERATOR._components(grid)
    return _paint(grid, min(objects, key=min))


def _fixed_bottom_right(grid):
    objects = _GENERATOR._components(grid)
    return _paint(grid, max(objects, key=min))


def _nearest_partner(grid):
    majorities, oddball = _GENERATOR._class_roles(grid)
    anchor = min(oddball)
    partner = min(
        majorities,
        key=lambda obj: abs(min(obj)[0] - anchor[0]) + abs(min(obj)[1] - anchor[1]),
    )
    return _paint(grid, partner)


def _rivals(target):
    common = {
        "largest_row_major": _largest_row_major,
        "fixed_top_left": _fixed_top_left,
        "fixed_bottom_right": _fixed_bottom_right,
    }
    if target == "outsider":
        return {**common, "farthest_partner": _ADAPTER._farthest_partner_output}
    return {
        **common,
        "nearest_partner": _nearest_partner,
        "outsider": _GENERATOR.rule_mirror,
    }


def _projection(episode):
    controller_bytes = public_challenge_bytes(episode)
    first_turn_challenge = {
        "train": episode["train"],
        "test": [episode["test"][0]],
    }
    first_turn_bytes = public_challenge_bytes(first_turn_challenge)
    controller = json.loads(controller_bytes)
    first_turn = json.loads(first_turn_bytes)
    return {
        "controller_query_count": len(controller["test"]),
        "first_turn_query_count": len(first_turn["test"]),
        "settings_visible": "settings" in controller or "settings" in first_turn,
        "program_visible": "program_solution" in controller or "program_solution" in first_turn,
        "query_outputs_visible": any("output" in pair for pair in controller["test"]),
        "future_queries_visible_on_first_turn": len(first_turn["test"]) != 1,
        "controller_sha256": hashlib.sha256(controller_bytes).hexdigest(),
        "first_turn_sha256": hashlib.sha256(first_turn_bytes).hexdigest(),
    }


def run_audit(*, seeds=(0, 17), demo_counts=(2, 3, 6)):
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    ambiguous = []
    checks = []
    episodes = 0
    rotations = 0
    projection = None
    for seed in seeds:
        for target in ("outsider", "farthest_partner"):
            for demos in demo_counts:
                episode = _ADAPTER.generate(seed, {"target": target}, demos, 4)
                episodes += 1
                rotations += len(episode["test"])
                if projection is None:
                    projection = _projection(episode)
                for name, rival in _rivals(target).items():
                    fits_demos = all(
                        rival(pair["input"]) == pair["output"]
                        for pair in episode["train"]
                    )
                    disagreements = [
                        index
                        for index, pair in enumerate(episode["test"])
                        if rival(pair["input"]) != pair["output"]
                    ]
                    row = {
                        "seed": seed,
                        "target": target,
                        "demos": demos,
                        "rival": name,
                        "fits_all_demos": fits_demos,
                        "query_disagreements": disagreements,
                    }
                    checks.append(row)
                    if fits_demos and disagreements:
                        ambiguous.append(row)
    assert projection is not None
    projection_ok = not any(
        projection[name]
        for name in (
            "settings_visible",
            "program_visible",
            "query_outputs_visible",
            "future_queries_visible_on_first_turn",
        )
    ) and projection["controller_query_count"] == 4 and projection["first_turn_query_count"] == 1
    return {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "status": "passed" if not ambiguous and projection_ok else "failed",
        "task_id": "040bfb038c65",
        "settings": ["outsider", "farthest_partner"],
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": episodes,
        "query_rotations_checked": rotations,
        "rival_checks": checks,
        "ambiguous_cases": ambiguous,
        "projection": projection,
        "limits": "Finite declared rivals and sampled seeds only; not a proof of unique induction.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_audit()
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
