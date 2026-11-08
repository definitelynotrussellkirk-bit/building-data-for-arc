#!/usr/bin/env python3
"""Source-bound whole-lesson census for ARC task 01bb2cbe1309.

The production per-puzzle runner assembles one lesson from a single seed and
sequential sample indices: four demonstrations followed by one query, starting
at sample index zero.  This probe measures that exact sampler and, because the
generator has a four-state deterministic teaching schedule, every cyclic start
as well.  Rival functions are read from the generator's declarations rather
than copied into the probe.

The official output used here is an independent Python transcription of the
immutable local-window rule.  The repository rule-smoke and semantic gates are
responsible for cross-checking generated outputs against live Racket.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "01bb2cbe1309"
BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    encoded = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_module(path: Path):
    name = f"lesson_probe_{TASK_ID}_{_sha256(path)[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(f"{TASK_ID} is absent from {path}")


def canonical_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent transcription: read only the original input grid."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            top_left = grid[row][col]
            top_right = grid[row][col + 1]
            bottom_left = grid[row + 1][col]
            bottom_right = grid[row + 1][col + 1]
            if (
                top_left != 0
                and top_left == bottom_right
                and top_right == 0
                and bottom_left == 0
            ):
                out[row][col + 1] = top_left
                out[row + 1][col] = top_left
            elif (
                top_right != 0
                and top_right == bottom_left
                and top_left == 0
                and bottom_right == 0
            ):
                out[row][col] = top_right
                out[row + 1][col + 1] = top_right
    return out


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _empty_rival_counts(rivals: dict[str, Callable]) -> dict[str, int]:
    return {name: 0 for name in rivals}


def _lesson(
    generator: Any,
    *,
    seed: int,
    band: str,
    start: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    pair_count = int(generator.EXAMPLES_NEEDED) + 1
    pairs: list[dict[str, Any]] = []
    profiles: list[str] = []
    for offset in range(pair_count):
        sample_index = start + offset
        grid = generator.generate(seed, sample_index, difficulty=band)
        findings = list(generator.self_check(grid) or [])
        if findings:
            raise AssertionError(
                f"self_check failed at {band}/seed={seed}/index={sample_index}: "
                + "; ".join(findings)
            )
        observed = generator.observe_overrides(grid)
        profiles.append(str(observed["scene_profile"]))
        pairs.append({"input": grid, "output": canonical_oracle(grid)})
    return pairs[:-1], pairs[-1], profiles


def _score_lessons(
    generator: Any,
    *,
    band: str,
    seeds: range,
    starts: list[int],
) -> dict[str, Any]:
    competitors = dict(generator.LESSON_COMPETITORS)
    if not competitors or not all(callable(fn) for fn in competitors.values()):
        raise TypeError("LESSON_COMPETITORS must be a non-empty callable mapping")

    unique_inputs: set[str] = set()
    profile_counts: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()
    demo_disagreements = _empty_rival_counts(competitors)
    query_disagreements = _empty_rival_counts(competitors)
    survivors_after_demos = _empty_rival_counts(competitors)
    query_disagreement_survivors = _empty_rival_counts(competitors)
    lessons = 0
    pairs_seen = 0
    profile_sequences: Counter[str] = Counter()

    for seed in seeds:
        for start in starts:
            demos, query, profiles = _lesson(
                generator, seed=seed, band=band, start=start
            )
            lessons += 1
            all_pairs = [*demos, query]
            pairs_seen += len(all_pairs)
            profile_sequences["->".join(profiles)] += 1
            for pair, profile in zip(all_pairs, profiles):
                unique_inputs.add(_grid_sha256(pair["input"]))
                profile_counts[profile] += 1
                dimensions[f"{len(pair['input'])}x{len(pair['input'][0])}"] += 1

            for name, competitor in competitors.items():
                demo_misses = sum(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                )
                query_miss = competitor(query["input"]) != query["output"]
                demo_disagreements[name] += demo_misses
                query_disagreements[name] += int(query_miss)
                survives = demo_misses == 0
                survivors_after_demos[name] += int(survives)
                query_disagreement_survivors[name] += int(survives and query_miss)

            declared_findings = list(
                generator.lesson_identifiable(demos, query) or []
            )
            if declared_findings:
                raise AssertionError(
                    f"lesson_identifiable failed at {band}/seed={seed}/start={start}: "
                    + "; ".join(declared_findings)
                )

    return {
        "lessons": lessons,
        "pairs_seen": pairs_seen,
        "unique_inputs": len(unique_inputs),
        "duplicate_input_occurrences": pairs_seen - len(unique_inputs),
        "profile_counts": dict(sorted(profile_counts.items())),
        "dimension_counts": dict(sorted(dimensions.items())),
        "profile_sequences": dict(sorted(profile_sequences.items())),
        "demo_disagreements": demo_disagreements,
        "query_disagreements": query_disagreements,
        "survivors_after_demos": survivors_after_demos,
        "query_disagreement_survivors": query_disagreement_survivors,
    }


def run_census(
    *,
    generator_path: Path,
    canonical_path: Path,
    lessons_per_band: int = 100,
    seed_start: int = 0,
) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    generator_path = generator_path.resolve()
    canonical_path = canonical_path.resolve()

    repo_root = generator_path.parents[2]
    runtime_path = repo_root / "shared" / "runtime"
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))
    generator = _load_module(generator_path)
    if generator.TASK_ID != TASK_ID:
        raise ValueError(f"generator TASK_ID {generator.TASK_ID!r} != {TASK_ID!r}")

    canonical = _canonical_row(canonical_path)
    canonical_test = canonical.get("test", [])
    if isinstance(canonical_test, dict):
        canonical_test = [canonical_test]
    canonical_pairs = [*canonical.get("train", []), *canonical_test]
    oracle_matches = sum(
        canonical_oracle(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )
    if oracle_matches != len(canonical_pairs):
        raise AssertionError(
            f"independent oracle matches only {oracle_matches}/{len(canonical_pairs)} "
            "canonical pairs"
        )

    shortcut_fit: dict[str, Any] = {}
    for name, shortcut in dict(generator.CANONICAL_SHORTCUTS).items():
        fit = sum(
            shortcut(pair["input"]) == pair["output"]
            for pair in canonical_pairs
        )
        shortcut_fit[name] = {
            "fit_pairs": fit,
            "usable_canonical_pairs": len(canonical_pairs),
            "fits_all_usable_pairs": fit == len(canonical_pairs),
        }

    schedule = tuple(generator.SCHEDULE_PROFILES)
    cyclic_starts = list(range(len(schedule)))
    seeds = range(seed_start, seed_start + lessons_per_band)
    bands: dict[str, Any] = {}
    for band in BANDS:
        production = _score_lessons(
            generator, band=band, seeds=seeds, starts=[0]
        )
        cyclic = _score_lessons(
            generator, band=band, seeds=seeds, starts=cyclic_starts
        )
        bands[band] = {
            "seed_start": seed_start,
            "seed_stop_exclusive": seed_start + lessons_per_band,
            "seed_count": lessons_per_band,
            "production_lessons": production["lessons"],
            "production_pairs_seen": production["pairs_seen"],
            "production_unique_inputs": production["unique_inputs"],
            "production_duplicate_input_occurrences": production[
                "duplicate_input_occurrences"
            ],
            "production_profile_counts": production["profile_counts"],
            "production_dimension_counts": production["dimension_counts"],
            "production_profile_sequences": production["profile_sequences"],
            "production_demo_disagreements": production["demo_disagreements"],
            "production_query_disagreements": production["query_disagreements"],
            "production_survivors_after_demos": production[
                "survivors_after_demos"
            ],
            "production_query_disagreement_survivors": production[
                "query_disagreement_survivors"
            ],
            "cyclic_starts_seen": cyclic_starts,
            "cyclic_lessons": cyclic["lessons"],
            "cyclic_pairs_seen": cyclic["pairs_seen"],
            "cyclic_unique_inputs": cyclic["unique_inputs"],
            "cyclic_duplicate_input_occurrences": cyclic[
                "duplicate_input_occurrences"
            ],
            "cyclic_profile_counts": cyclic["profile_counts"],
            "cyclic_profile_sequences": cyclic["profile_sequences"],
            "cyclic_demo_disagreements": cyclic["demo_disagreements"],
            "cyclic_query_disagreements": cyclic["query_disagreements"],
            "cyclic_survivors_after_demos": cyclic[
                "survivors_after_demos"
            ],
            "cyclic_query_disagreement_survivors": cyclic[
                "query_disagreement_survivors"
            ],
        }

    probe_path = Path(__file__).resolve()
    return {
        "schema": "01bb2cbe1309-lesson-census-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(generator_path),
            "generator_sha256": _sha256(generator_path),
            "generator_version": str(generator.VERSION),
            "rule_hash": str(generator.RULE_HASH),
            "canonical_path": str(canonical_path),
            "canonical_ledger_sha256": _sha256(canonical_path),
            "probe_path": str(probe_path),
            "probe_sha256": _sha256(probe_path),
        },
        "oracle": {
            "kind": "independent Python transcription",
            "reads_original_input_only": True,
            "canonical_pairs_matched": oracle_matches,
            "canonical_pairs_total": len(canonical_pairs),
            "live_racket_cross_check": "external repository rule_smoke/semantic_gate evidence",
        },
        "sampler": {
            "production_source": "shared/runtime/puzzle_generators/runner.py::run_one/run_batch",
            "production_seed_policy": "seed_start + lesson ordinal",
            "production_sample_index_start": 0,
            "demo_count": int(generator.EXAMPLES_NEEDED),
            "query_count": 1,
            "sequential_sample_indices": True,
            "cyclic_starts": cyclic_starts,
            "schedule_profiles": list(schedule),
        },
        "domain": {
            "declared_axes": _jsonable(generator.AXES),
            "scene_profiles": list(generator.SCENE_PROFILES),
            "schedule_profiles": list(schedule),
            "canonical_shapes": _jsonable(generator._CANONICAL_SHAPES),
            "nonzero_color_domain": "two distinct colors sampled without replacement from 1..9",
            "component_domain": "2..8 separated local components; at most one named negative",
            "difficulty_bands": list(BANDS),
        },
        "declared_rivals": sorted(generator.LESSON_COMPETITORS),
        "declared_canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
        "canonical_shortcut_fit": shortcut_fit,
        "bands": bands,
        "claim_scope": (
            "Finite source-bound census only; it demonstrates the declared rival set "
            "on the listed seeds and cyclic starts, not universal rule induction."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    task_home = here.parent.parent
    repo_root = task_home.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=task_home / "generator.py",
    )
    parser.add_argument(
        "--canonical",
        type=Path,
        default=repo_root / "shared/data/canonical/puzzles.jsonl",
    )
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = run_census(
        generator_path=args.generator,
        canonical_path=args.canonical,
        lessons_per_band=args.lessons_per_band,
        seed_start=args.seed_start,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
