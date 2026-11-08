#!/usr/bin/env python3
"""Source-bound whole-lesson census for ARC task 4c26a1072222.

The production runner constructs four demonstrations and one query from one
seed, starting at a requested sample index and advancing until it has five
unique valid pairs.  This probe mirrors that assembly policy without importing
private runner helpers, obtains outputs from the generator's pinned Python rule
mirror, and reads the generator's actual shortcut/rival/witness declarations.
Independent Racket parity is established by the repository rule-smoke and
semantic-contract gates; this tool focuses on teaching support and diversity.
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

TASK_ID = "4c26a1072222"
BANDS = ("easy", "medium", "hard")
PAIR_COUNT = 5


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _pair_hash(pair: dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(pair).encode("utf-8")).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(_stable_json(grid).encode("utf-8")).hexdigest()


def _load_module(path: Path):
    name = f"lesson_probe_{TASK_ID}_{_sha256(path)[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs(path: Path) -> list[dict[str, Any]]:
    pairs: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row.get("test") or []
            if isinstance(test, dict):
                test = [test]
            for pair in [*(row.get("train") or []), *test]:
                if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                    continue
                pairs.setdefault(_pair_hash(pair), pair)
    if not pairs:
        raise KeyError(f"no usable canonical pairs found for {TASK_ID} in {path}")
    return list(pairs.values())


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _assemble_lesson(
    generator: Any,
    *,
    seed: int,
    band: str,
    start: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Mirror runner.run_one's sequential, valid, unique-pair assembly."""
    pairs: list[dict[str, Any]] = []
    pair_hashes: set[str] = set()
    sample_indices: list[int] = []
    rejection_counts: Counter[str] = Counter()
    sample_index = start
    max_attempts = PAIR_COUNT * 5
    attempts = 0
    while len(pairs) < PAIR_COUNT and attempts < max_attempts:
        attempts += 1
        grid = generator.generate(seed, sample_index, difficulty=band)
        findings = list(generator.self_check(grid, difficulty=band) or [])
        if findings:
            rejection_counts["self_check"] += 1
            sample_index += 1
            continue
        output = generator.rule_mirror(grid)
        pair = {"input": grid, "output": output}
        digest = _pair_hash(pair)
        if digest in pair_hashes:
            rejection_counts["duplicate_pair"] += 1
            sample_index += 1
            continue
        pair_hashes.add(digest)
        pairs.append(pair)
        sample_indices.append(sample_index)
        sample_index += 1
    if len(pairs) != PAIR_COUNT:
        raise AssertionError(
            f"under-production at band={band} seed={seed} start={start}: "
            f"{len(pairs)}/{PAIR_COUNT} pairs after {attempts} attempts"
        )
    return pairs[:-1], pairs[-1], {
        "attempts": attempts,
        "sample_indices": sample_indices,
        "rejections": dict(rejection_counts),
    }


def _empty_counts(mapping: dict[str, Callable]) -> dict[str, int]:
    return {name: 0 for name in mapping}


def _score_lessons(
    generator: Any,
    *,
    band: str,
    seed_start: int,
    lesson_count: int,
    starts: list[int],
) -> dict[str, Any]:
    competitors = dict(generator.LESSON_COMPETITORS)
    witnesses = dict(generator.SEMANTIC_WITNESSES)
    if not competitors or not all(callable(fn) for fn in competitors.values()):
        raise TypeError("LESSON_COMPETITORS must be a non-empty callable mapping")
    if not witnesses or not all(callable(fn) for fn in witnesses.values()):
        raise TypeError("SEMANTIC_WITNESSES must be a non-empty callable mapping")

    unique_inputs: set[str] = set()
    unique_pairs: set[str] = set()
    dimensions: Counter[str] = Counter()
    palettes: Counter[str] = Counter()
    band_counts: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    transform_counts: Counter[str] = Counter()
    source_color_counts: Counter[str] = Counter()
    witness_pair_hits = _empty_counts(witnesses)
    witness_lesson_hits = _empty_counts(witnesses)
    demo_disagreements = _empty_counts(competitors)
    query_disagreements = _empty_counts(competitors)
    lessons_eliminating = _empty_counts(competitors)
    survivors_after_demos = _empty_counts(competitors)
    query_disagreement_survivors = _empty_counts(competitors)
    identifiable_failures: list[dict[str, Any]] = []
    attempts = 0
    sampled_indices: Counter[str] = Counter()
    rejection_counts: Counter[str] = Counter()
    lessons = 0
    pair_count = 0

    for ordinal in range(lesson_count):
        seed = seed_start + ordinal
        for start in starts:
            demos, query, assembly = _assemble_lesson(
                generator, seed=seed, band=band, start=start
            )
            lessons += 1
            attempts += int(assembly["attempts"])
            for index in assembly["sample_indices"]:
                sampled_indices[str(index)] += 1
            rejection_counts.update(assembly["rejections"])
            all_pairs = [*demos, query]
            pair_count += len(all_pairs)

            lesson_witnesses = {name: False for name in witnesses}
            for pair in all_pairs:
                grid = pair["input"]
                unique_inputs.add(_grid_hash(grid))
                unique_pairs.add(_pair_hash(pair))
                dimensions[f"{len(grid)}x{len(grid[0])}"] += 1
                palette_size = len({cell for row in grid for cell in row})
                palettes[str(palette_size)] += 1
                signature = generator.semantic_signature(grid)
                band_counts[str(signature["n_bands"])] += 1
                profile_counts[str(generator.schedule_profile(seed, assembly["sample_indices"][all_pairs.index(pair)], band))] += 1
                for name in signature["transforms"]:
                    transform_counts[str(name)] += 1
                for count in signature["source_color_counts"]:
                    source_color_counts[str(count)] += 1
                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_pair_hits[name] += 1
                        lesson_witnesses[name] = True
            for name, hit in lesson_witnesses.items():
                witness_lesson_hits[name] += int(hit)

            for name, competitor in competitors.items():
                demo_misses = sum(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                )
                query_miss = competitor(query["input"]) != query["output"]
                demo_disagreements[name] += demo_misses
                query_disagreements[name] += int(query_miss)
                eliminated = demo_misses > 0
                lessons_eliminating[name] += int(eliminated)
                survives = not eliminated
                survivors_after_demos[name] += int(survives)
                query_disagreement_survivors[name] += int(survives and query_miss)

            findings = list(generator.lesson_identifiable(demos, query) or [])
            if findings:
                identifiable_failures.append(
                    {
                        "seed": seed,
                        "start": start,
                        "findings": findings,
                        "sample_indices": assembly["sample_indices"],
                    }
                )

    return {
        "lessons": lessons,
        "pairs_seen": pair_count,
        "unique_inputs": len(unique_inputs),
        "duplicate_input_occurrences": pair_count - len(unique_inputs),
        "unique_pairs": len(unique_pairs),
        "duplicate_pair_occurrences": pair_count - len(unique_pairs),
        "generator_attempts": attempts,
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "sample_index_counts": dict(sorted(sampled_indices.items(), key=lambda item: int(item[0]))),
        "dimension_counts": dict(sorted(dimensions.items())),
        "palette_size_counts": dict(sorted(palettes.items())),
        "n_band_counts": dict(sorted(band_counts.items())),
        "schedule_profile_counts": dict(sorted(profile_counts.items())),
        "transform_occurrences": dict(sorted(transform_counts.items())),
        "source_color_count_occurrences": dict(sorted(source_color_counts.items())),
        "witness_pair_hits": witness_pair_hits,
        "witness_lesson_hits": witness_lesson_hits,
        "demo_disagreements": demo_disagreements,
        "query_disagreements": query_disagreements,
        "lessons_eliminating_rival": lessons_eliminating,
        "survivors_after_demos": survivors_after_demos,
        "query_disagreement_survivors": query_disagreement_survivors,
        "lesson_identifiable_failures": identifiable_failures,
    }


def run_probe(
    *,
    generator_path: Path,
    canonical_path: Path,
    lessons_per_band: int,
    seed_start: int,
    expected_generator_sha256: str | None,
) -> dict[str, Any]:
    if lessons_per_band < 100:
        raise ValueError("--lessons-per-band must be at least 100 for this review")
    generator_path = generator_path.resolve()
    canonical_path = canonical_path.resolve()
    generator_sha256 = _sha256(generator_path)
    if expected_generator_sha256 and generator_sha256 != expected_generator_sha256:
        raise ValueError(
            f"generator SHA-256 mismatch: expected {expected_generator_sha256}, "
            f"found {generator_sha256}"
        )

    repo_root = generator_path.parents[2]
    runtime = repo_root / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    generator = _load_module(generator_path)
    if generator.TASK_ID != TASK_ID:
        raise ValueError(f"loaded TASK_ID {generator.TASK_ID!r}, expected {TASK_ID!r}")
    if int(generator.EXAMPLES_NEEDED) != 4:
        raise ValueError("this probe's production assembly expects EXAMPLES_NEEDED == 4")

    canonical_pairs = _canonical_pairs(canonical_path)
    mirror_matches = sum(
        generator.rule_mirror(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )
    if mirror_matches != len(canonical_pairs):
        raise AssertionError(
            f"rule_mirror matches only {mirror_matches}/{len(canonical_pairs)} canonical pairs"
        )

    shortcuts = dict(generator.CANONICAL_SHORTCUTS)
    if not shortcuts or not all(callable(fn) for fn in shortcuts.values()):
        raise TypeError("CANONICAL_SHORTCUTS must be a non-empty callable mapping")
    shortcut_fit: dict[str, Any] = {}
    for name, shortcut in shortcuts.items():
        fits = sum(
            shortcut(pair["input"]) == pair["output"]
            for pair in canonical_pairs
        )
        shortcut_fit[name] = {
            "fit_pairs": fits,
            "usable_canonical_pairs": len(canonical_pairs),
            "fits_all_usable_pairs": fits == len(canonical_pairs),
        }
        if fits != len(canonical_pairs):
            raise AssertionError(
                f"declared canonical shortcut {name!r} fits only "
                f"{fits}/{len(canonical_pairs)} usable canonical pairs"
            )

    schedule = tuple(generator.SCHEDULE_PROFILES)
    if not schedule:
        raise ValueError("SCHEDULE_PROFILES must be non-empty")
    cyclic_starts = list(range(len(schedule)))
    bands: dict[str, Any] = {}
    failures: list[str] = []
    for band_index, band in enumerate(BANDS):
        band_seed_start = seed_start + band_index * lessons_per_band
        production = _score_lessons(
            generator,
            band=band,
            seed_start=band_seed_start,
            lesson_count=lessons_per_band,
            starts=[0],
        )
        cyclic = _score_lessons(
            generator,
            band=band,
            seed_start=band_seed_start,
            lesson_count=lessons_per_band,
            starts=cyclic_starts,
        )
        bands[band] = {
            "seed_start": band_seed_start,
            "seed_stop_exclusive": band_seed_start + lessons_per_band,
            "production": production,
            "cyclic_schedule_starts": cyclic_starts,
            "cyclic": cyclic,
        }
        for scope_name, scope in (("production", production), ("cyclic", cyclic)):
            if scope["lesson_identifiable_failures"]:
                failures.append(
                    f"{band}/{scope_name}: {len(scope['lesson_identifiable_failures'])} "
                    "lesson_identifiable failures"
                )
            for rival, survivors in scope["survivors_after_demos"].items():
                if survivors:
                    failures.append(
                        f"{band}/{scope_name}: rival {rival!r} survives "
                        f"{survivors}/{scope['lessons']} lessons"
                    )
            for witness, hits in scope["witness_lesson_hits"].items():
                if hits != scope["lessons"]:
                    failures.append(
                        f"{band}/{scope_name}: witness {witness!r} appears in "
                        f"{hits}/{scope['lessons']} lessons"
                    )

    observed_transforms = {
        name
        for band in bands.values()
        for name in band["cyclic"]["transform_occurrences"]
    }
    missing_transforms = sorted(set(generator.TRANSFORM_NAMES) - observed_transforms)
    if missing_transforms:
        failures.append(f"missing D4 transforms in cyclic census: {missing_transforms}")

    probe_path = Path(__file__).resolve()
    report = {
        "schema": "4c26a1072222-lesson-probe-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha256,
            "generator_version": str(generator.VERSION),
            "rule_hash": str(generator.RULE_HASH),
            "canonical_path": str(canonical_path),
            "canonical_sha256": _sha256(canonical_path),
            "probe_path": str(probe_path),
            "probe_sha256": _sha256(probe_path),
        },
        "oracle": {
            "kind": "generator.rule_mirror",
            "canonical_pairs_matched": mirror_matches,
            "canonical_pairs_total": len(canonical_pairs),
            "independent_live_racket_cross_check": (
                "external checks/after rule_smoke, semantic_gate, and authority_sync"
            ),
        },
        "sampler": {
            "mirrors": "shared/runtime/puzzle_generators/runner.py::run_one",
            "seed_policy": "seed_start + lesson ordinal",
            "production_sample_index_start": 0,
            "pair_policy": "four demos plus one query; sequential indices; reject invalid or duplicate pairs; max 25 attempts",
            "demo_count": 4,
            "query_count": 1,
            "cyclic_starts_tested": cyclic_starts,
            "schedule_profiles": list(schedule),
        },
        "domain_limits": {
            "declared_axes": _jsonable(generator.AXES),
            "difficulty_bands": list(BANDS),
            "input_width": 9,
            "input_heights": [8, 11],
            "nonzero_palette_size": 8,
            "bands_per_input": [3, 4],
            "source_colors_per_A_block": [2, 3],
            "D4_transforms": list(generator.TRANSFORM_NAMES),
            "claim_scope": (
                "Finite source-bound census of declared rivals and the listed seed ranges; "
                "not a universal claim about all possible solvers or induction."
            ),
        },
        "declarations": {
            "canonical_shortcuts": sorted(shortcuts),
            "lesson_competitors": sorted(generator.LESSON_COMPETITORS),
            "semantic_witnesses": sorted(generator.SEMANTIC_WITNESSES),
        },
        "canonical_shortcut_fit": shortcut_fit,
        "lessons_per_band": lessons_per_band,
        "bands": bands,
        "failures": failures,
        "passed": not failures,
    }
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    task_home = here.parent.parent
    repo_root = task_home.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=task_home / "generator.py")
    parser.add_argument(
        "--canonical",
        type=Path,
        default=repo_root / "shared" / "data" / "canonical" / "puzzles.jsonl",
    )
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-start", type=int, default=20261003)
    parser.add_argument("--expected-generator-sha256")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    try:
        report = run_probe(
            generator_path=args.generator,
            canonical_path=args.canonical,
            lessons_per_band=args.lessons_per_band,
            seed_start=args.seed_start,
            expected_generator_sha256=args.expected_generator_sha256,
        )
    except Exception as exc:
        print(f"lesson probe failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
