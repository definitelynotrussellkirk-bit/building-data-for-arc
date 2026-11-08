#!/usr/bin/env python3
"""Reproducible semantic lesson probe for dc0a7662670b.

This intentionally consumes the generator's *declared* shortcut/rival maps
instead of maintaining a second hand-copied list.  It verifies that canonical
shortcuts really fit every canonical pair, then rotates every short cyclic
start through complete generated lessons and reports any rival that survives
all demonstrations.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs, find_root

try:
    from puzzle_generators.per_puzzle.dc0a7662670b import generator as gen
except ModuleNotFoundError:
    # Direct source checkout: the package shim exists only in portable snapshots.
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("dc0a7662670b_generator", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {generator_path}")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

TASK_ID = "dc0a7662670b"
BANDS = ("easy", "medium", "hard")


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _pair(seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _declared_rivals() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}
    for attribute in (
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "SEMANTIC_RIVALS",
    ):
        for name, function in getattr(gen, attribute, {}).items():
            prior = rivals.get(name)
            if prior is not None and prior is not function:
                raise ValueError(
                    f"rival name {name!r} is bound to different callables"
                )
            rivals[name] = function
    return rivals


def run_probe(*, per_band: int = 100, cyclic_starts: int = 8) -> dict[str, Any]:
    """Return a JSON-serializable semantic coverage report.

    ``per_band`` controls independent lesson seeds per difficulty band.
    ``cyclic_starts`` checks starts ``0..cyclic_starts-1`` for every seed, so
    every query rotation of the four-profile schedule is exercised when the
    value is at least four.
    """
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(cyclic_starts) is not int or cyclic_starts < 1:
        raise ValueError("cyclic_starts must be a positive integer")

    errors: list[str] = []
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    rivals = _declared_rivals()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))

    for name, shortcut in shortcuts.items():
        mismatches = [
            index
            for index, pair in enumerate(pairs)
            if shortcut(pair["input"]) != pair["output"]
        ]
        if mismatches:
            errors.append(
                f"declared canonical shortcut {name!r} mismatches pair(s) "
                + ",".join(map(str, mismatches))
            )

    profiles_seen: set[str] = set()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    survivor_counts: dict[str, int] = {}
    windows_checked = 0
    expected_profiles = set(gen.SCHEDULE_PROFILES)

    for band_index, band in enumerate(BANDS):
        for lesson_index in range(per_band):
            seed = 1_000_000 + band_index * 100_000 + lesson_index
            for start in range(cyclic_starts):
                demos = [
                    _pair(seed, start + offset, band)
                    for offset in range(gen.EXAMPLES_NEEDED)
                ]
                query = _pair(seed, start + gen.EXAMPLES_NEEDED, band)
                windows_checked += 1

                observed = {
                    gen.observe_overrides(pair["input"])["shape_profile"]
                    for pair in demos
                }
                profiles_seen.update(observed)
                if observed != expected_profiles:
                    errors.append(
                        f"{band} seed={seed} start={start}: profiles "
                        f"{sorted(observed)} != {sorted(expected_profiles)}"
                    )

                for pair in demos + [query]:
                    unique_inputs.add(_grid_key(pair["input"]))

                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    errors.append(
                        f"{band} seed={seed} start={start}: " + "; ".join(reasons)
                    )

                for name, rival in rivals.items():
                    try:
                        fits = all(
                            rival(pair["input"]) == pair["output"]
                            for pair in demos
                        )
                    except Exception as exc:  # diagnostic, never hide a rival crash
                        errors.append(
                            f"{band} seed={seed} start={start}: rival {name!r} "
                            f"raised {type(exc).__name__}: {exc}"
                        )
                        continue
                    if fits:
                        survivor_counts[name] = survivor_counts.get(name, 0) + 1

    generator_path = Path(gen.__file__).resolve()
    return {
        "schema": "dc0a7662670b-semantic-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "sampler": {
            "bands": list(BANDS),
            "lesson_seeds_per_band": per_band,
            "cyclic_starts_per_seed": cyclic_starts,
            "examples_per_lesson": gen.EXAMPLES_NEEDED,
            "seed_formula": "1000000 + band_index*100000 + lesson_index",
        },
        "canonical_pairs_checked": len(pairs),
        "canonical_shortcuts_checked": len(shortcuts),
        "declared_rivals_checked": sorted(rivals),
        "cyclic_windows_checked": windows_checked,
        "unique_inputs_checked": len(unique_inputs),
        "profiles_seen": sorted(profiles_seen),
        "surviving_rivals": dict(sorted(survivor_counts.items())),
        "errors": errors,
        "status": "pass" if not errors and not survivor_counts else "fail",
        "limits": (
            "Finite declared-rival testing over the task's constructive domain; "
            "this does not prove universal induction or cover undeclared rivals."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--cyclic-starts", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_probe(
        per_band=args.per_band,
        cyclic_starts=args.cyclic_starts,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
