#!/usr/bin/env python3
"""Source-bound curriculum qualification for generator 7fc158ab7b70.

This probe intentionally discovers rivals and witnesses from the generator's
live declarations.  It checks every cyclic three-demo window in a deterministic
lesson sampler and records unique inputs, observed axes, joint size/palette
coverage, witness frequency, and rival disagreements for later review.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "7fc158ab7b70"
BANDS = ("easy", "medium", "hard")
REPO = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "shared/data/canonical/puzzles.jsonl").exists()
)
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"qualification_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def source_sha256() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def _grid_key(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _canonical_row() -> dict[str, Any]:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _canonical_shortcut_results() -> dict[str, bool]:
    row = _canonical_row()
    pairs = list(row.get("train", ())) + list(row.get("test", ()))
    results: dict[str, bool] = {}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        fits = True
        usable = 0
        for pair in pairs:
            if GEN.self_check(pair["input"]):
                continue
            usable += 1
            try:
                fits = fits and rival(pair["input"]) == pair["output"]
            except Exception:
                fits = False
        results[name] = usable > 0 and fits
    return results


def run_probe(*, lessons_per_band: int = 100, base_seed: int = 71000) -> dict[str, Any]:
    if type(lessons_per_band) is not int or lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be a positive int")
    if type(base_seed) is not int:
        raise TypeError("base_seed must be int")

    competitors = dict(GEN.LESSON_COMPETITORS)
    witnesses = dict(GEN.SEMANTIC_WITNESSES)
    canonical_fits = _canonical_shortcut_results()
    bands: dict[str, Any] = {}

    for band_index, band in enumerate(BANDS):
        input_hashes: set[str] = set()
        observed: dict[str, Counter[str]] = {
            axis: Counter() for axis in GEN.AXES
        }
        rival_disagreements = Counter({name: 0 for name in competitors})
        witness_hits = Counter({name: 0 for name in witnesses})
        identifiable = 0
        failures: list[dict[str, Any]] = []
        start_residues: set[int] = set()
        size_uniqueness_counts: Counter[tuple[int, bool]] = Counter()

        for lesson_index in range(lessons_per_band):
            # One deterministic seed per lesson plus consecutive sample indices
            # matches the normal lesson builder and exercises every cyclic start.
            seed = base_seed + band_index * 100_000 + lesson_index
            start = lesson_index
            start_residues.add(start % GEN.EXAMPLES_NEEDED)
            pairs: list[dict[str, Any]] = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(
                    seed,
                    start + offset,
                    difficulty=band,
                )
                errors = GEN.self_check(grid, difficulty=band)
                if errors:
                    failures.append(
                        {
                            "lesson_index": lesson_index,
                            "sample_index": start + offset,
                            "kind": "self_check",
                            "errors": errors,
                        }
                    )
                input_hashes.add(_grid_key(grid))
                axes = GEN.observe_overrides(grid)
                for axis, value in axes.items():
                    observed[axis][json.dumps(value, sort_keys=True)] += 1
                size_uniqueness_counts[(
                    int(axes["grid_n"]), bool(axes["unique_colors"])
                )] += 1
                expected = GEN.rule_mirror(grid)
                for name, rival in competitors.items():
                    if rival(grid) != expected:
                        rival_disagreements[name] += 1
                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_hits[name] += 1
                pairs.append({"input": grid, "output": expected})

            demos = pairs[: GEN.EXAMPLES_NEEDED]
            query = pairs[GEN.EXAMPLES_NEEDED]
            reasons = GEN.lesson_identifiable(demos, query)
            if reasons:
                failures.append(
                    {
                        "lesson_index": lesson_index,
                        "sample_indices": [start, start + GEN.EXAMPLES_NEEDED],
                        "kind": "lesson_identifiable",
                        "reasons": reasons,
                    }
                )
            else:
                identifiable += 1

            for name, rival in competitors.items():
                if not any(rival(demo["input"]) != demo["output"] for demo in demos):
                    failures.append(
                        {
                            "lesson_index": lesson_index,
                            "kind": "unrefuted_rival",
                            "rival": name,
                        }
                    )

        expected_size_uniqueness = {
            (grid_n, unique_colors)
            for grid_n in (3, 4, 5)
            for unique_colors in (False, True)
        }
        observed_size_uniqueness = set(size_uniqueness_counts)
        joint_coverage = {
            "expected": [
                {"grid_n": grid_n, "unique_colors": unique_colors}
                for grid_n, unique_colors in sorted(expected_size_uniqueness)
            ],
            "observed": [
                {
                    "grid_n": grid_n,
                    "unique_colors": unique_colors,
                    "count": size_uniqueness_counts[(grid_n, unique_colors)],
                }
                for grid_n, unique_colors in sorted(observed_size_uniqueness)
            ],
            "missing": [
                {"grid_n": grid_n, "unique_colors": unique_colors}
                for grid_n, unique_colors in sorted(
                    expected_size_uniqueness - observed_size_uniqueness
                )
            ],
        }

        bands[band] = {
            "seed_formula": (
                f"{base_seed} + band_index*100000 + lesson_index"
            ),
            "lesson_start_indices": [0, lessons_per_band - 1],
            "lessons_checked": lessons_per_band,
            "pairs_generated": lessons_per_band * (GEN.EXAMPLES_NEEDED + 1),
            "unique_inputs": len(input_hashes),
            "identifiable_lessons": identifiable,
            "cyclic_start_residues": sorted(start_residues),
            "rival_disagreements_across_pairs": dict(rival_disagreements),
            "witness_hits_across_pairs": dict(witness_hits),
            "observed_axes": {
                axis: dict(sorted(counts.items()))
                for axis, counts in observed.items()
            },
            "grid_n_x_unique_colors": joint_coverage,
            "failures": failures,
        }

    return {
        "schema": "generator-distribution-qualification-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": source_sha256(),
        "rule_hash": GEN.RULE_HASH,
        "examples_needed": GEN.EXAMPLES_NEEDED,
        "lessons_per_band": lessons_per_band,
        "total_lessons": lessons_per_band * len(BANDS),
        "total_generated_pairs": (
            lessons_per_band * len(BANDS) * (GEN.EXAMPLES_NEEDED + 1)
        ),
        "lesson_assembly": {
            "policy": (
                "For each lesson, use one deterministic seed and four consecutive "
                "sample indices; first three are demonstrations, fourth is query."
            ),
            "start_index_formula": "lesson_index",
            "cyclic_start_residues": sorted(
                {index % GEN.EXAMPLES_NEEDED for index in range(lessons_per_band)}
            ),
        },
        "declared_competitors": sorted(competitors),
        "declared_witnesses": sorted(witnesses),
        "canonical_shortcuts_fit_canonical": canonical_fits,
        "bands": bands,
    }


def _is_success(report: dict[str, Any]) -> bool:
    if not all(report["canonical_shortcuts_fit_canonical"].values()):
        return False
    return all(
        band["identifiable_lessons"] == band["lessons_checked"]
        and not band["grid_n_x_unique_colors"]["missing"]
        and not band["failures"]
        for band in report["bands"].values()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--base-seed", type=int, default=71000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_probe(
        lessons_per_band=args.lessons_per_band,
        base_seed=args.base_seed,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
        print(args.out)
    return 0 if _is_success(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
