#!/usr/bin/env python3
"""Fast source-bound curriculum probe for 5751039becb2.

This complements the shared Racket-backed lesson census.  It enumerates every
cyclic start of the four-slot schedule, uses an independent Python oracle (not
``generator.rule_mirror``) to label examples, dynamically reads all declared
lesson competitors, and reports any competitor that fits a complete demo
window.  It is intended for rapid authoring/debugging; the selected Racket rule
and shared battery remain the final authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Sequence

TASK_ID = "5751039becb2"
BANDS = ("easy", "medium", "hard")
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _load_generator():
    explicit = os.environ.get("GENERATOR_UNDER_TEST")
    candidates = [Path(explicit)] if explicit else []
    candidates.append(Path(__file__).resolve().parents[1] / "generator.py")
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location(
                f"curriculum_probe_{TASK_ID}", path
            )
            if spec is None or spec.loader is None:
                raise RuntimeError(f"cannot load generator from {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def independent_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Transcribe the local diagonal rule without using production helpers."""
    h, w = len(grid), len(grid[0])
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == value
                for dr, dc in _DIAGONALS
            ):
                output[r][c] = value
    return output


def _grid_hash(grid: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_hash(generator: Any) -> str | None:
    filename = getattr(generator, "__file__", None)
    if not filename:
        return None
    path = Path(filename)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def run(*, per_band: int = 100, seed: int = 5751039, generator=None) -> dict[str, Any]:
    """Audit non-overlapping lesson windows with all cyclic start residues."""
    if per_band < 1:
        raise ValueError("per_band must be positive")
    gen = generator or _load_generator()
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    profiles = tuple(getattr(gen, "SCHEDULE_PROFILES", ()))
    period = len(profiles)
    if period < 1:
        raise ValueError("generator has no SCHEDULE_PROFILES")
    n_demos = int(getattr(gen, "EXAMPLES_NEEDED", 3))

    rival_survivals = {name: 0 for name in competitors}
    witness_hits = {
        band: {name: 0 for name in witnesses}
        for band in BANDS
    }
    cyclic_starts_by_band: dict[str, set[int]] = {band: set() for band in BANDS}
    unidentifiable: list[dict[str, Any]] = []
    oracle_mismatches: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()

    for band_index, band in enumerate(BANDS):
        band_seed = seed + band_index * 1_000_003
        for lesson_index in range(per_band):
            # period+1 is coprime to period, so starts cycle through every
            # residue while adjacent lesson windows do not overlap.
            start = lesson_index * (period + 1)
            cyclic_starts_by_band[band].add(start % period)
            episode = []
            for offset in range(n_demos + 1):
                sample_index = start + offset
                grid = gen.generate(
                    band_seed,
                    sample_index,
                    difficulty=band,
                )
                expected = independent_output(grid)
                unique_inputs.add(_grid_hash(grid))
                if gen.rule_mirror(grid) != expected:
                    oracle_mismatches.append(
                        {
                            "band": band,
                            "lesson": lesson_index,
                            "sample_index": sample_index,
                        }
                    )
                for name, predicate in witnesses.items():
                    if predicate(grid):
                        witness_hits[band][name] += 1
                episode.append({"input": grid, "output": expected})

            demos, query = episode[:n_demos], episode[-1]
            reasons = list(gen.lesson_identifiable(demos, query))
            if reasons:
                unidentifiable.append(
                    {
                        "band": band,
                        "lesson": lesson_index,
                        "start": start,
                        "reasons": reasons,
                    }
                )
            for name, rival in competitors.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    rival_survivals[name] += 1

    lessons_total = per_band * len(BANDS)
    return {
        "schema": "5751039becb2-curriculum-probe/1",
        "task_id": TASK_ID,
        "generator_sha256": _source_hash(gen),
        "seed": seed,
        "per_band": per_band,
        "bands": list(BANDS),
        "period": period,
        "profiles": list(profiles),
        "n_demos": n_demos,
        "lessons_total": lessons_total,
        "unique_inputs": len(unique_inputs),
        "cyclic_starts_by_band": {
            band: sorted(starts) for band, starts in cyclic_starts_by_band.items()
        },
        "witness_hits": witness_hits,
        "rival_survivals": rival_survivals,
        "unidentifiable_lessons": len(unidentifiable),
        "unidentifiable_examples": unidentifiable[:10],
        "oracle_mismatches": len(oracle_mismatches),
        "oracle_mismatch_examples": oracle_mismatches[:10],
        "status": (
            "PASS"
            if not unidentifiable
            and not oracle_mismatches
            and not any(rival_survivals.values())
            else "FAIL"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=5751039)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(per_band=args.per_band, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
