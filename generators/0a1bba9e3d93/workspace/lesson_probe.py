#!/usr/bin/env python3
"""Source-bound whole-lesson census for ARC task 0a1bba9e3d93.

The production per-puzzle runner starts at sample index zero, accepts four
training pairs plus one query pair, advances sample indices sequentially, and
skips rejected or duplicate pairs.  This probe reproduces those materialization
rules with an independent Python transcription of the immutable rule.  It also
checks every cyclic schedule start because the generator declares a four-state
teaching schedule.

The report is finite evidence for the named rivals on the listed seeds.  It is
not a claim of universal induction.  Live Racket agreement remains the job of
the repository rule-smoke and semantic-gate batteries.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

TASK_ID = "0a1bba9e3d93"
BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    blob = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _pair_sha256(pair: dict[str, Any]) -> str:
    blob = json.dumps(
        [pair["input"], pair["output"]], separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def _load(path: Path, prefix: str):
    name = f"{prefix}_{TASK_ID}_{_sha256(path)[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(f"{TASK_ID} absent from {path}")


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return [*row.get("train", []), *test]


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _materialize_lesson(
    generator: Any,
    oracle: Callable[[list[list[int]]], list[list[int]]],
    *,
    seed: int,
    band: str,
    start: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    needed = int(generator.EXAMPLES_NEEDED) + 1
    max_attempts = needed * 5
    sample_index = start
    attempts = 0
    pairs: list[dict[str, Any]] = []
    accepted_indices: list[int] = []
    profiles: list[str] = []
    rejections: Counter[str] = Counter()
    seen_pairs: set[str] = set()

    while len(pairs) < needed and attempts < max_attempts:
        attempts += 1
        try:
            grid = generator.generate(seed, sample_index, difficulty=band)
        except Exception as exc:
            rejections[f"generate:{type(exc).__name__}"] += 1
            sample_index += 1
            continue
        findings = list(generator.self_check(grid) or [])
        if findings:
            rejections["self_check"] += 1
            sample_index += 1
            continue
        try:
            output = oracle(grid)
        except Exception as exc:
            rejections[f"oracle:{type(exc).__name__}"] += 1
            sample_index += 1
            continue
        pair = {"input": grid, "output": output}
        pair_hash = _pair_sha256(pair)
        if pair_hash in seen_pairs:
            rejections["duplicate_pair"] += 1
            sample_index += 1
            continue
        seen_pairs.add(pair_hash)
        pairs.append(pair)
        accepted_indices.append(sample_index)
        profiles.append(generator.schedule_profile(seed, sample_index, band))
        sample_index += 1

    if len(pairs) != needed:
        raise RuntimeError(
            f"{band}/seed={seed}/start={start}: produced {len(pairs)}/{needed} "
            f"pairs after {attempts} attempts; rejections={dict(rejections)}"
        )
    metadata = {
        "attempts": attempts,
        "accepted_indices": accepted_indices,
        "profiles": profiles,
        "rejections": dict(rejections),
        "rejection_count": sum(rejections.values()),
    }
    return pairs[:-1], pairs[-1], metadata


def _empty_counts(competitors: dict[str, Callable]) -> dict[str, int]:
    return {name: 0 for name in competitors}


def _score(
    generator: Any,
    oracle: Callable[[list[list[int]]], list[list[int]]],
    *,
    band: str,
    seeds: range,
    starts: list[int],
) -> dict[str, Any]:
    competitors = dict(generator.LESSON_COMPETITORS)
    if not competitors or not all(callable(fn) for fn in competitors.values()):
        raise TypeError("LESSON_COMPETITORS must be a non-empty callable mapping")

    unique_inputs: set[str] = set()
    unique_pairs: set[str] = set()
    dimensions: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    profile_sequences: Counter[str] = Counter()
    accepted_index_sequences: Counter[str] = Counter()
    rejection_reasons: Counter[str] = Counter()
    demo_disagreements = _empty_counts(competitors)
    query_disagreements = _empty_counts(competitors)
    survivors_after_demos = _empty_counts(competitors)
    query_disagreement_survivors = _empty_counts(competitors)
    lessons = pairs_seen = rejection_count = 0

    for seed in seeds:
        for start in starts:
            demos, query, meta = _materialize_lesson(
                generator, oracle, seed=seed, band=band, start=start
            )
            lessons += 1
            all_pairs = [*demos, query]
            pairs_seen += len(all_pairs)
            rejection_count += meta["rejection_count"]
            rejection_reasons.update(meta["rejections"])
            profile_sequences["->".join(meta["profiles"])] += 1
            accepted_index_sequences["->".join(map(str, meta["accepted_indices"]))] += 1
            for pair, profile in zip(all_pairs, meta["profiles"]):
                unique_inputs.add(_grid_sha256(pair["input"]))
                unique_pairs.add(_pair_sha256(pair))
                profile_counts[str(profile)] += 1
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

            findings = list(generator.lesson_identifiable(demos, query) or [])
            if findings:
                raise AssertionError(
                    f"lesson_identifiable failed at {band}/seed={seed}/start={start}: "
                    + "; ".join(findings)
                )

    return {
        "lessons": lessons,
        "pairs_seen": pairs_seen,
        "unique_inputs": len(unique_inputs),
        "unique_pairs": len(unique_pairs),
        "duplicate_input_occurrences": pairs_seen - len(unique_inputs),
        "rejections": rejection_count,
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "profile_counts": dict(sorted(profile_counts.items())),
        "profile_sequences": dict(sorted(profile_sequences.items())),
        "accepted_index_sequences": dict(sorted(accepted_index_sequences.items())),
        "dimension_counts": dict(sorted(dimensions.items())),
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
    probe_path = Path(__file__).resolve()
    reference_path = probe_path.with_name("reference_probe.py")
    generator = _load(generator_path, "lesson_probe_generator")
    reference = _load(reference_path, "lesson_probe_reference")
    if generator.TASK_ID != TASK_ID:
        raise ValueError(f"generator TASK_ID {generator.TASK_ID!r} != {TASK_ID!r}")

    canonical_row = _canonical_row(canonical_path)
    canonical_pairs = _canonical_pairs(canonical_row)
    canonical_oracle_matches = sum(
        reference.oracle(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )
    if canonical_oracle_matches != len(canonical_pairs):
        raise AssertionError(
            f"independent oracle matches {canonical_oracle_matches}/"
            f"{len(canonical_pairs)} canonical pairs"
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
        production = _score(
            generator, reference.oracle, band=band, seeds=seeds, starts=[0]
        )
        cyclic = _score(
            generator,
            reference.oracle,
            band=band,
            seeds=seeds,
            starts=cyclic_starts,
        )
        bands[band] = {
            "seed_start": seed_start,
            "seed_stop_exclusive": seed_start + lessons_per_band,
            "seed_count": lessons_per_band,
            "production_lessons": production["lessons"],
            "production_pairs_seen": production["pairs_seen"],
            "production_unique_inputs": production["unique_inputs"],
            "production_unique_pairs": production["unique_pairs"],
            "production_duplicate_input_occurrences": production[
                "duplicate_input_occurrences"
            ],
            "production_rejections": production["rejections"],
            "production_rejection_reasons": production["rejection_reasons"],
            "production_profile_counts": production["profile_counts"],
            "production_profile_sequences": production["profile_sequences"],
            "production_accepted_index_sequences": production[
                "accepted_index_sequences"
            ],
            "production_dimension_counts": production["dimension_counts"],
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
            "cyclic_unique_pairs": cyclic["unique_pairs"],
            "cyclic_duplicate_input_occurrences": cyclic[
                "duplicate_input_occurrences"
            ],
            "cyclic_rejections": cyclic["rejections"],
            "cyclic_rejection_reasons": cyclic["rejection_reasons"],
            "cyclic_profile_counts": cyclic["profile_counts"],
            "cyclic_profile_sequences": cyclic["profile_sequences"],
            "cyclic_accepted_index_sequences": cyclic[
                "accepted_index_sequences"
            ],
            "cyclic_demo_disagreements": cyclic["demo_disagreements"],
            "cyclic_query_disagreements": cyclic["query_disagreements"],
            "cyclic_survivors_after_demos": cyclic["survivors_after_demos"],
            "cyclic_query_disagreement_survivors": cyclic[
                "query_disagreement_survivors"
            ],
        }

    return {
        "schema": "0a1bba9e3d93-lesson-census-v1",
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
            "reference_path": str(reference_path),
            "reference_sha256": _sha256(reference_path),
        },
        "oracle": {
            "kind": "independent Python transcription",
            "reads_original_input_only": True,
            "canonical_pairs_matched": canonical_oracle_matches,
            "canonical_pairs_total": len(canonical_pairs),
            "live_racket_cross_check": (
                "external repository rule_smoke and semantic_gate evidence"
            ),
        },
        "sampler": {
            "production_source": (
                "shared/runtime/puzzle_generators/runner.py::run_one/run_batch"
            ),
            "production_seed_policy": "seed_start + lesson ordinal",
            "production_sample_index_start": 0,
            "demo_count": int(generator.EXAMPLES_NEEDED),
            "query_count": 1,
            "sequential_sample_indices": True,
            "duplicate_pair_rejection": True,
            "max_attempts": "5 * (demo_count + query_count)",
            "cyclic_starts": cyclic_starts,
            "schedule_profiles": list(schedule),
        },
        "domain": {
            "declared_axes": _jsonable(generator.AXES),
            "difficulty_bands": list(BANDS),
            "panel_structure": "three equal panels plus two full color-8 separators",
            "foreground_domain": "two distinct colors sampled without replacement from 1..7,9",
            "shape_domain": "four linked 3-cell growth families; delta size 2",
            "limitations": (
                "finite linked morphology family; does not cover arbitrary connected "
                "polyomino growth or multi-color panel objects"
            ),
        },
        "declared_rivals": sorted(generator.LESSON_COMPETITORS),
        "declared_canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
        "canonical_shortcut_fit": shortcut_fit,
        "bands": bands,
        "claim_scope": (
            "Finite source-bound census over the listed seeds and cyclic starts; "
            "it demonstrates the declared rival set, not universal rule induction."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    task_home = here.parent.parent
    repo_root = task_home.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=task_home / "generator.py")
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
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
