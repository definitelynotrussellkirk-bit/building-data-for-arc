#!/usr/bin/env python3
"""Reproducible finite sampler audit for the 91ba253f9945 native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

_HOME = Path(__file__).resolve().parent
_REPO = _HOME.parents[3]
_TASK_HOME = _HOME.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = _load("_audit_91ba253f9945_generator", _TASK_HOME / "generator.py")
prototype = _load("_audit_91ba253f9945_prototype", _HOME / "prototype.py")

_SOURCE_PATHS = (
    "generators/91ba253f9945/generator.py",
    "generators/91ba253f9945/tests/test_parametric_turn.py",
    "generators/91ba253f9945/workspace/parametric/adapter.py",
    "generators/91ba253f9945/workspace/parametric/adversarial_probe.py",
    "generators/91ba253f9945/workspace/parametric/promotion.json",
    "generators/91ba253f9945/workspace/parametric/prototype.py",
    "generators/91ba253f9945/workspace/parametric/sampler_audit.py",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def run(*, seeds: int = 32, base_seeds: int = 64) -> dict[str, Any]:
    if type(seeds) is not int or not 1 <= seeds <= 512:
        raise ValueError("seeds must be an exact integer in [1, 512]")
    if type(base_seeds) is not int or not 1 <= base_seeds <= 512:
        raise ValueError("base_seeds must be an exact integer in [1, 512]")

    shapes: set[tuple[int, int]] = set()
    base_draws = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(base_seeds):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            errors = generator.self_check(grid, difficulty=difficulty)
            if errors:
                raise AssertionError(f"base self_check failed for {difficulty=}, {seed=}: {errors}")
            shapes.add((len(grid), len(grid[0])))
            base_draws += 1

    stress = generator.generate(
        91,
        0,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        marker_count=7,
        decoy_count=18,
        source_basis=7,
        target_basis=0,
    )
    if generator.self_check(stress, difficulty="hard"):
        raise AssertionError("30x30 base stress override failed self_check")

    demo_counts = tuple(range(prototype.MIN_DEMOS, prototype.MAX_DEMOS + 1))
    episode_count = 0
    single_query_stability_cases = 0
    claimed_pairs = 0
    nonzero_counts: list[int] = []
    query_shapes: set[tuple[int, int]] = set()
    unique_motifs = set()

    for seed in range(seeds):
        for demos in demo_counts:
            episodes = {}
            for turn in prototype.TURNS:
                full = prototype.generate(seed, {"turn": turn}, demos, prototype.MAX_QUERIES)
                if demos == 3:
                    one = prototype.generate(seed, {"turn": turn}, demos, prototype.MIN_QUERIES)
                    if full["train"] != one["train"] or full["test"][0] != one["test"][0]:
                        raise AssertionError(f"single-query first item drifted for {seed=}, {demos=}, {turn=}")
                    single_query_stability_cases += 1
                encoded = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(full)]
                if len(encoded) != len(set(encoded)):
                    raise AssertionError(f"duplicate input for {seed=}, {demos=}, {turn=}")
                motifs = [prototype.extract_intermediate(grid) for grid in _inputs(full)]
                if len(motifs) != len(set(motifs)):
                    raise AssertionError(f"marker motif reuse for {seed=}, {demos=}, {turn=}")
                for split in ("train", "test"):
                    for pair in full[split]:
                        if pair["output"] != prototype.apply_rule(pair["input"], turn):
                            raise AssertionError(f"Python label mismatch for {seed=}, {demos=}, {turn=}")
                        nonzero_counts.append(sum(value != 0 for row in pair["input"] for value in row))
                episodes[turn] = full
                episode_count += 1
                claimed_pairs += len(full["train"]) + len(full["test"])

            left = episodes["counterclockwise"]
            right = episodes["clockwise"]
            if _inputs(left) != _inputs(right):
                raise AssertionError(f"matched inputs drifted for {seed=}, {demos=}")
            for split in ("train", "test"):
                if any(a["output"] == b["output"] for a, b in zip(left[split], right[split])):
                    raise AssertionError(f"settings collapsed on a pair for {seed=}, {demos=}, {split=}")
            if demos == prototype.MAX_DEMOS:
                motifs = [prototype.extract_intermediate(grid) for grid in _inputs(left)]
                unique_motifs.update(motifs)
                query_shapes.update((len(pair["input"]), len(pair["input"][0])) for pair in left["test"])

    expected_unique_motifs = seeds * (prototype.MAX_DEMOS + prototype.MAX_QUERIES)
    if len(unique_motifs) != expected_unique_motifs:
        raise AssertionError(
            f"expected {expected_unique_motifs} unique fresh motifs, got {len(unique_motifs)}"
        )

    return {
        "schema": "arcpuzzles-task-sampler-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed",
        "base_draws": base_draws,
        "base_distinct_shapes": len(shapes),
        "base_shape_bounds": [list(min(shapes)), list(max(shapes))],
        "stress_override": {
            "shape": [len(stress), len(stress[0])],
            "marker_count": 7,
            "decoy_count": 18,
            "source_basis": 7,
            "target_basis": 0,
        },
        "seeds": seeds,
        "demo_counts": list(demo_counts),
        "query_counts": [prototype.MIN_QUERIES, prototype.MAX_QUERIES],
        "parametric_episodes": episode_count,
        "single_query_stability_cases": single_query_stability_cases,
        "claimed_pairs_checked": claimed_pairs,
        "query_shapes": [list(shape) for shape in sorted(query_shapes)],
        "unique_marker_motifs": len(unique_motifs),
        "expected_unique_marker_motifs": expected_unique_motifs,
        "nonzero_input_cells": {"min": min(nonzero_counts), "max": max(nonzero_counts)},
        "checks": [
            "base self_check",
            "matched inputs",
            "all inputs distinct",
            "all marker motifs distinct within an episode",
            "fresh marker motifs across retained seeds",
            "Python label parity",
            "settings differ on every pair",
            "single-query first item stable",
            "30x30 stress override",
        ],
        "source_sha256": {path: _sha(_REPO / path) for path in _SOURCE_PATHS},
        "limits": "finite deterministic audit; protected Racket is performed separately by authoring preflight",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--base-seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run(seeds=args.seeds, base_seeds=args.base_seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
