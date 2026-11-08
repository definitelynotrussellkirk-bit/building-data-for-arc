#!/usr/bin/env python3
"""Fast task-local qualification probe for generator 89c85768abe1.

This does not replace the source-bound Racket battery or lesson census.  It is a
cheap, reusable preflight for future edits: it checks lawful/default draws,
semantic witnesses, every two-demo schedule start, the exact-axis Cartesian
boundaries, malformed fixtures, replay determinism, and input diversity.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
GENERATOR_PATH = TASK_ROOT / "generator.py"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "qualification_generator_89c85768abe1", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    spec.loader.exec_module(module)
    return module


def _signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _pair(grid: list[list[int]], generator) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def qualify(draws_per_band: int = 40) -> dict[str, Any]:
    """Return a JSON-serializable report; ``status`` is ``pass`` or ``fail``."""
    if type(draws_per_band) is not int or draws_per_band < 2:
        raise ValueError("draws_per_band must be an integer >= 2")

    generator = _load_generator()
    bands = ["easy", "medium", "hard"]
    errors: list[str] = []
    signatures: set[tuple[tuple[int, ...], ...]] = set()
    witness_hits: Counter[str] = Counter()
    profile_hits: Counter[str] = Counter()
    lawful_draws = 0
    identifiable_windows = 0

    for band_index, band in enumerate(bands):
        for index in range(draws_per_band):
            seed = 890000 + band_index * 100000 + index
            grid = generator.generate(seed, index, difficulty=band)
            structural = generator.self_check(grid, difficulty=band)
            strict = generator.strict_canonical_like(grid)
            if structural:
                errors.append(f"{band} draw {index} self_check: {structural[:2]}")
            elif strict:
                errors.append(f"{band} draw {index} strict: {strict[:2]}")
            else:
                lawful_draws += 1
            signatures.add(_signature(grid))
            profile_hits[str(generator.schedule_profile(seed, index, band))] += 1
            for name, witness in generator.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_hits[name] += 1

            demos = []
            for demo_index in range(index, index + generator.EXAMPLES_NEEDED):
                demo_grid = generator.generate(seed, demo_index, difficulty=band)
                demos.append(_pair(demo_grid, generator))
            query_grid = generator.generate(
                seed, index + generator.EXAMPLES_NEEDED, difficulty=band
            )
            reasons = generator.lesson_identifiable(
                demos, _pair(query_grid, generator)
            )
            if reasons:
                errors.append(
                    f"{band} lesson start {index} unidentifiable: {reasons[:2]}"
                )
            else:
                identifiable_windows += 1

    override_cases = 0
    for band in bands:
        for sample_index in (0, 1):
            for height in (7, 14):
                for width in (9, 16):
                    for rectangles in (2, 3, 4):
                        requested = {
                            "grid_h": height,
                            "grid_w": width,
                            "rectangles": rectangles,
                        }
                        try:
                            grid = generator.generate(
                                881122,
                                sample_index,
                                difficulty=band,
                                **requested,
                            )
                            observed = generator.observe_overrides(grid)
                            structural = generator.self_check(grid, difficulty=band)
                        except Exception as exc:  # report, do not hide
                            errors.append(
                                f"override {band}/{sample_index}/{requested} raised "
                                f"{type(exc).__name__}: {exc}"
                            )
                            continue
                        override_cases += 1
                        if observed != requested:
                            errors.append(
                                f"override {band}/{sample_index} requested {requested}, "
                                f"observed {observed}"
                            )
                        if structural:
                            errors.append(
                                f"override {band}/{sample_index}/{requested} malformed: "
                                f"{structural[:2]}"
                            )

    mutation_fixtures_rejected = 0
    for name, grid in generator.mutation_fixtures():
        reasons = generator.self_check(grid)
        if reasons:
            mutation_fixtures_rejected += 1
        else:
            errors.append(f"mutation fixture {name!r} was accepted")

    random.seed(20261003)
    process_state = random.getstate()
    replay_a = generator.generate(777, 19, difficulty="hard")
    replay_b = generator.generate(777, 19, difficulty="hard")
    if random.getstate() != process_state:
        errors.append("generate mutated Python's process-global random state")
    if replay_a != replay_b:
        errors.append("same seed/sample replay was not deterministic")
    if replay_a is replay_b or any(a is b for a, b in zip(replay_a, replay_b)):
        errors.append("replay returned shared mutable grid storage")

    for name in generator.SEMANTIC_WITNESSES:
        if witness_hits[name] == 0:
            errors.append(f"semantic witness {name!r} never fired")
    for profile in generator.SCHEDULE_PROFILES:
        if profile_hits[str(profile)] == 0:
            errors.append(f"schedule profile {profile!r} never appeared")

    draws = len(bands) * draws_per_band
    report = {
        "schema": "89c85768abe1-local-qualification-v1",
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "bands": bands,
        "draws_per_band": draws_per_band,
        "draws": draws,
        "lawful_draws": lawful_draws,
        "unique_inputs": len(signatures),
        "identifiable_windows": identifiable_windows,
        "override_cases": override_cases,
        "mutation_fixtures_rejected": mutation_fixtures_rejected,
        "witness_hits": dict(witness_hits),
        "profile_hits": dict(profile_hits),
        "errors": errors,
        "limits": [
            "Python-only preflight; canonical Racket remains the authority.",
            "Checks declared rivals and finite draws, not universal induction.",
            "Use the source-bound battery and lesson-census for acceptance evidence.",
        ],
        "status": "pass" if not errors else "fail",
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=40)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = qualify(args.draws_per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
