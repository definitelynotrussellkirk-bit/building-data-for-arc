#!/usr/bin/env python3
"""Standalone curriculum audit for task 3adf11522bf5.

Run from the task workspace or point --generator at a selected copy.  This tool
uses the independent reference_probe oracle and emits machine-readable evidence;
it never reads canonical labels or the Racket source.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reference_probe import observed, reference_output


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("curriculum_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def audit(generator_path: Path, *, seed: int, per_band: int, windows: int) -> dict[str, Any]:
    gen = _load(generator_path)
    errors: list[str] = []
    bands: dict[str, Any] = {}
    for difficulty in ("easy", "medium", "hard"):
        shapes: Counter[str] = Counter()
        colors: Counter[str] = Counter()
        profiles: Counter[str] = Counter()
        witnesses: Counter[str] = Counter()
        rival_disagreements: Counter[str] = Counter()
        for index in range(per_band):
            grid = gen.generate(seed, index, difficulty=difficulty)
            if grid != gen.generate(seed, index, difficulty=difficulty):
                errors.append(f"nondeterministic draw: {difficulty} index={index}")
            validation = gen.strict_canonical_like(grid)
            if validation:
                errors.append(f"strict rejection: {difficulty} index={index}: {validation}")
            obs = observed(grid)
            shapes[f"{obs['grid_h']}x{obs['grid_w']}"] += 1
            colors[str(obs["obstacle_color"])] += 1
            profiles[str(obs["scene_profile"])] += 1
            intended = reference_output(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                witnesses[name] += 1
                for rival_name in gen.WITNESS_RIVALS[name]:
                    if gen.SEMANTIC_RIVALS[rival_name](grid) != intended:
                        rival_disagreements[rival_name] += 1
                    else:
                        errors.append(
                            f"false witness claim: {difficulty} index={index} "
                            f"{name}->{rival_name}"
                        )
        bands[difficulty] = {
            "draws": per_band,
            "shapes": dict(sorted(shapes.items())),
            "colors": dict(sorted(colors.items())),
            "profiles": dict(sorted(profiles.items())),
            "witnesses": dict(sorted(witnesses.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
        }

    rotations = 0
    for difficulty in ("easy", "medium", "hard"):
        for start in range(windows):
            lesson = []
            for index in range(start, start + 5):
                grid = gen.generate(seed + 1, index, difficulty=difficulty)
                lesson.append({"input": grid, "output": reference_output(grid)})
            for query_index in range(5):
                rotations += 1
                demos = [pair for i, pair in enumerate(lesson) if i != query_index]
                query = lesson[query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    errors.append(
                        f"unidentifiable {difficulty} start={start} query={query_index}: {reasons}"
                    )
                for name, rival in gen.LESSON_COMPETITORS.items():
                    fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                    if fits and rival(query["input"]) != query["output"]:
                        errors.append(
                            f"competitor survived demos: {difficulty} start={start} "
                            f"query={query_index} rival={name}"
                        )

    return {
        "schema": "3adf11522bf5-curriculum-probe-v1",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seed": seed,
        "per_band": per_band,
        "windows_per_band": windows,
        "rotations_checked": rotations,
        "bands": bands,
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--seed", type=int, default=2401)
    parser.add_argument("--per-band", type=int, default=80)
    parser.add_argument("--windows", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(
        args.generator.resolve(), seed=args.seed, per_band=args.per_band, windows=args.windows
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
