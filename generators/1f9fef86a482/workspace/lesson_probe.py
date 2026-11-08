#!/usr/bin/env python3
"""Deep, source-bound curriculum probe for 1f9fef86a482.

Unlike the shared lesson census, this probe rotates every one of four consecutive
pairs into the query position.  It imports the generator's actual rival
registries, uses the independent oracle in ``reference_probe.py``, verifies all
claimed canonical shortcuts against every canonical pair, and records exact
seed/start policy plus unique-input counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reference_probe import authority_output, canonical_pairs, load_generator

BANDS = ("easy", "medium", "hard")


def _seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"task-local-cyclic:v1:1f9fef86a482:{band}:{index}".encode()
    ).digest()
    return int.from_bytes(digest[:4], "big")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_hash(module) -> str:
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


def _registries(module) -> dict[str, dict[str, Callable]]:
    out: dict[str, dict[str, Callable]] = {}
    for registry_name in (
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "SEMANTIC_RIVALS",
    ):
        registry = getattr(module, registry_name, {})
        if isinstance(registry, dict):
            out[registry_name] = {
                str(name): fn for name, fn in registry.items() if callable(fn)
            }
    return out


def run(per_band: int) -> dict[str, Any]:
    module = load_generator()
    registries = _registries(module)
    canonical = canonical_pairs()
    canonical_fit: dict[str, Any] = {}
    for name, rival in registries.get("CANONICAL_SHORTCUTS", {}).items():
        fits = sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        canonical_fit[name] = {
            "fits": fits,
            "pairs": len(canonical),
            "status": "fits_all" if fits == len(canonical) else "refuted",
        }

    report: dict[str, Any] = {
        "schema": "task-local-cyclic-lesson-probe-v1",
        "task_id": module.TASK_ID,
        "generator_version": module.VERSION,
        "generator_sha256": _source_hash(module),
        "per_band": per_band,
        "pairs_per_lesson": 4,
        "query_rotations_per_lesson": 4,
        "seed_recipe": "sha256('task-local-cyclic:v1:TASK:BAND:INDEX')[:4]",
        "start_recipe": "lesson index; pairs are consecutive start..start+3",
        "canonical_shortcut_fit": canonical_fit,
        "registries": {name: sorted(values) for name, values in registries.items()},
        "bands": {},
        "failures": [],
        "limits": [
            "Finite declared-rival check, not a proof of universal induction.",
            "The independent Python oracle is secondary to the canonical Racket authority.",
            "Rotations test four-pair blocks; larger or nonconsecutive episode assembly is outside scope.",
        ],
    }

    all_hashes: set[str] = set()
    total_rotations = 0
    bad_rotations = 0
    survivor_counts: dict[str, int] = {}
    for band in BANDS:
        band_hashes: set[str] = set()
        band_bad = 0
        for lesson_index in range(per_band):
            seed = _seed(band, lesson_index)
            start = lesson_index
            pairs = []
            for sample_index in range(start, start + 4):
                grid = module.generate(seed, sample_index, difficulty=band)
                pair = {"input": grid, "output": authority_output(grid)}
                pairs.append(pair)
                digest = _grid_hash(grid)
                band_hashes.add(digest)
                all_hashes.add(digest)

            for query_index in range(4):
                total_rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                hook_errors = module.lesson_identifiable(demos, query)
                survivors: list[str] = []
                for registry_name, registry in registries.items():
                    if registry_name == "CANONICAL_SHORTCUTS":
                        # It is useful to score these again, but keep namespace explicit.
                        pass
                    for rival_name, rival in registry.items():
                        if all(rival(demo["input"]) == demo["output"] for demo in demos):
                            label = f"{registry_name}:{rival_name}"
                            survivors.append(label)
                            survivor_counts[label] = survivor_counts.get(label, 0) + 1
                if hook_errors or survivors:
                    band_bad += 1
                    bad_rotations += 1
                    if len(report["failures"]) < 20:
                        report["failures"].append(
                            {
                                "band": band,
                                "lesson_index": lesson_index,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "hook_errors": hook_errors,
                                "surviving_rivals": survivors,
                                "input_hashes": [_grid_hash(pair["input"]) for pair in pairs],
                            }
                        )
        report["bands"][band] = {
            "lessons": per_band,
            "rotations": per_band * 4,
            "ambiguous_rotations": band_bad,
            "unique_inputs": len(band_hashes),
            "materialized_inputs": per_band * 4,
        }

    bad_shortcuts = [
        name for name, row in canonical_fit.items() if row["status"] != "fits_all"
    ]
    report["summary"] = {
        "lessons": per_band * len(BANDS),
        "rotations": total_rotations,
        "ambiguous_rotations": bad_rotations,
        "unique_inputs": len(all_hashes),
        "materialized_inputs": per_band * len(BANDS) * 4,
        "survivor_counts": survivor_counts,
        "canonical_shortcuts_not_fitting_all_pairs": bad_shortcuts,
    }
    report["status"] = (
        "pass" if bad_rotations == 0 and not bad_shortcuts else "fail"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band <= 0:
        parser.error("--per-band must be positive")
    report = run(args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"status={report['status']} out={args.out}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
