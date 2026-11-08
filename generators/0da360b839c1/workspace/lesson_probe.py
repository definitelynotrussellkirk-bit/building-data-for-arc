#!/usr/bin/env python3
"""Source-bound whole-lesson census for ARC task ``0da360b839c1``.

The repository runner assembles four demonstrations and one query from one seed
and consecutive sample indices.  The semantic gate pins lesson ``k`` in band
``b`` to a SHA-derived seed and start index ``11*k``.  This probe reproduces
that policy for 100 lessons per band by default and also checks every cyclic
start of the generator's four-profile schedule.

Outputs come from an independent Python transcription of the selected rule.
The retained repository rule-smoke and semantic-gate evidence supplies live
Racket parity.  Therefore this census supports finite claims about the declared
rival set and listed samples; it is not a universal induction claim.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

TASK_ID = "0da360b839c1"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_text(json.dumps(grid, separators=(",", ":")))


def _load_module(path: Path):
    name = f"lesson_probe_{TASK_ID}_{_sha256_file(path)[:12]}"
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


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return [*row.get("train", []), *test]


def canonical_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent transcription: blank, keep 9, point-reflect other colors."""
    anchors = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        raise ValueError(f"expected one 9 anchor, found {len(anchors)}")
    ar, ac = anchors[0]
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    out[ar][ac] = 9
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            nr, nc = 2 * ar - r, 2 * ac - c
            if 0 <= nr < height and 0 <= nc < width:
                out[nr][nc] = value
    return out


def _pinned_seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:lesson:{band}:{lesson_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _lesson(generator: Any, *, seed: int, band: str, start: int):
    pair_count = int(generator.EXAMPLES_NEEDED) + 1
    pairs: list[dict[str, Any]] = []
    profiles: list[str] = []
    witnesses: list[list[str]] = []
    for offset in range(pair_count):
        sample_index = start + offset
        grid = generator.generate(seed, sample_index, difficulty=band)
        findings = list(generator.self_check(copy.deepcopy(grid)) or [])
        if findings:
            raise AssertionError(
                f"self_check failed at {band}/seed={seed}/index={sample_index}: "
                + "; ".join(findings)
            )
        observed = generator.observe_overrides(grid)
        profiles.append(str(observed["layout_profile"]))
        witnesses.append([
            name for name, predicate in generator.SEMANTIC_WITNESSES.items()
            if predicate(copy.deepcopy(grid))
        ])
        pairs.append({"input": grid, "output": canonical_oracle(grid)})
    return pairs[:-1], pairs[-1], profiles, witnesses


def _empty_counts(rivals: dict[str, Callable]) -> dict[str, int]:
    return {name: 0 for name in rivals}


def _score_lessons(
    generator: Any,
    *,
    band: str,
    lesson_specs: Iterable[tuple[int, int]],
) -> dict[str, Any]:
    competitors = dict(generator.LESSON_COMPETITORS)
    if not competitors or not all(callable(fn) for fn in competitors.values()):
        raise TypeError("LESSON_COMPETITORS must be a non-empty callable mapping")

    unique_inputs: set[str] = set()
    profile_counts: Counter[str] = Counter()
    profile_sequences: Counter[str] = Counter()
    dimension_counts: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    demo_disagreements = _empty_counts(competitors)
    query_disagreements = _empty_counts(competitors)
    survivors_after_demos = _empty_counts(competitors)
    query_disagreement_survivors = _empty_counts(competitors)
    lessons = 0
    pairs_seen = 0
    unidentifiable = 0
    first_unidentifiable: dict[str, Any] | None = None

    for seed, start in lesson_specs:
        demos, query, profiles, pair_witnesses = _lesson(
            generator, seed=seed, band=band, start=start
        )
        lessons += 1
        all_pairs = [*demos, query]
        pairs_seen += len(all_pairs)
        profile_sequences["->".join(profiles)] += 1
        for pair, profile, names in zip(all_pairs, profiles, pair_witnesses):
            unique_inputs.add(_grid_sha256(pair["input"]))
            profile_counts[profile] += 1
            dimension_counts[f"{len(pair['input'])}x{len(pair['input'][0])}"] += 1
            witness_hits.update(names)

        for name, competitor in competitors.items():
            demo_misses = sum(
                competitor(copy.deepcopy(pair["input"])) != pair["output"]
                for pair in demos
            )
            query_miss = competitor(copy.deepcopy(query["input"])) != query["output"]
            demo_disagreements[name] += demo_misses
            query_disagreements[name] += int(query_miss)
            survives = demo_misses == 0
            survivors_after_demos[name] += int(survives)
            query_disagreement_survivors[name] += int(survives and query_miss)

        declared_findings = list(generator.lesson_identifiable(demos, query) or [])
        if declared_findings:
            unidentifiable += 1
            if first_unidentifiable is None:
                first_unidentifiable = {
                    "band": band,
                    "seed": seed,
                    "sample_index": start,
                    "reasons": declared_findings,
                }

    return {
        "lessons": lessons,
        "pairs_seen": pairs_seen,
        "unique_inputs": len(unique_inputs),
        "duplicate_input_occurrences": pairs_seen - len(unique_inputs),
        "unidentifiable": unidentifiable,
        "first_unidentifiable": first_unidentifiable,
        "profile_counts": dict(sorted(profile_counts.items())),
        "profile_sequences": dict(sorted(profile_sequences.items())),
        "dimension_counts": dict(sorted(dimension_counts.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
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

    canonical_row = _canonical_row(canonical_path)
    canonical_pairs = _canonical_pairs(canonical_row)
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
            shortcut(copy.deepcopy(pair["input"])) == pair["output"]
            for pair in canonical_pairs
        )
        shortcut_fit[name] = {
            "fit_pairs": fit,
            "usable_canonical_pairs": len(canonical_pairs),
            "fits_all_usable_pairs": fit == len(canonical_pairs),
        }

    schedule = tuple(generator.SCHEDULE_PROFILES)
    cyclic_starts = list(range(len(schedule)))
    bands: dict[str, Any] = {}
    for band in BANDS:
        pinned_specs = [
            (_pinned_seed(band, k), k * LESSON_SAMPLE_STRIDE)
            for k in range(lessons_per_band)
        ]
        cyclic_specs = [
            (_pinned_seed(band, k), start)
            for k in range(lessons_per_band)
            for start in cyclic_starts
        ]
        pinned = _score_lessons(generator, band=band, lesson_specs=pinned_specs)
        cyclic = _score_lessons(generator, band=band, lesson_specs=cyclic_specs)
        bands[band] = {
            "lesson_index_start": 0,
            "lesson_index_stop_exclusive": lessons_per_band,
            "seed_count": lessons_per_band,
            "pinned_lessons": pinned["lessons"],
            "pinned_pairs_seen": pinned["pairs_seen"],
            "pinned_unique_inputs": pinned["unique_inputs"],
            "pinned_duplicate_input_occurrences": pinned["duplicate_input_occurrences"],
            "pinned_unidentifiable": pinned["unidentifiable"],
            "pinned_first_unidentifiable": pinned["first_unidentifiable"],
            "pinned_profile_counts": pinned["profile_counts"],
            "pinned_profile_sequences": pinned["profile_sequences"],
            "pinned_dimension_counts": pinned["dimension_counts"],
            "pinned_witness_hits": pinned["witness_hits"],
            "pinned_demo_disagreements": pinned["demo_disagreements"],
            "pinned_query_disagreements": pinned["query_disagreements"],
            "pinned_survivors_after_demos": pinned["survivors_after_demos"],
            "pinned_query_disagreement_survivors": pinned[
                "query_disagreement_survivors"
            ],
            "cyclic_starts_seen": cyclic_starts,
            "cyclic_lessons": cyclic["lessons"],
            "cyclic_pairs_seen": cyclic["pairs_seen"],
            "cyclic_unique_inputs": cyclic["unique_inputs"],
            "cyclic_duplicate_input_occurrences": cyclic["duplicate_input_occurrences"],
            "cyclic_unidentifiable": cyclic["unidentifiable"],
            "cyclic_first_unidentifiable": cyclic["first_unidentifiable"],
            "cyclic_profile_counts": cyclic["profile_counts"],
            "cyclic_profile_sequences": cyclic["profile_sequences"],
            "cyclic_witness_hits": cyclic["witness_hits"],
            "cyclic_demo_disagreements": cyclic["demo_disagreements"],
            "cyclic_query_disagreements": cyclic["query_disagreements"],
            "cyclic_survivors_after_demos": cyclic["survivors_after_demos"],
            "cyclic_query_disagreement_survivors": cyclic[
                "query_disagreement_survivors"
            ],
        }

    probe_path = Path(__file__).resolve()
    return {
        "schema": "0da360b839c1-lesson-census-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(generator_path),
            "generator_sha256": _sha256_file(generator_path),
            "generator_version": str(generator.VERSION),
            "rule_hash": str(generator.RULE_HASH),
            "canonical_path": str(canonical_path),
            "canonical_ledger_sha256": _sha256_file(canonical_path),
            "probe_path": str(probe_path),
            "probe_sha256": _sha256_file(probe_path),
        },
        "oracle": {
            "kind": "independent Python transcription of selected point-reflection rule",
            "reads_original_input_only": True,
            "canonical_pairs_matched": oracle_matches,
            "canonical_pairs_total": len(canonical_pairs),
            "live_racket_cross_check": (
                "external retained repository rule_smoke and semantic_gate evidence"
            ),
        },
        "sampler": {
            "production_source": "shared/runtime/puzzle_generators/runner.py::run_one",
            "pinned_seed_policy": (
                "int(sha256('profile-floor:v1:TASK:lesson:BAND:k')[:12],16)"
            ),
            "pinned_sample_index_policy": f"{LESSON_SAMPLE_STRIDE}*k",
            "lesson_index_range": [0, lessons_per_band - 1],
            "demo_count": int(generator.EXAMPLES_NEEDED),
            "query_count": 1,
            "sequential_sample_indices": True,
            "cyclic_starts": cyclic_starts,
            "schedule_profiles": list(schedule),
        },
        "domain": {
            "declared_axes": _jsonable(generator.AXES),
            "schedule_profiles": list(schedule),
            "difficulty_bands": list(BANDS),
            "generator_self_check_required": True,
        },
        "declared_rivals": sorted(generator.LESSON_COMPETITORS),
        "declared_canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
        "canonical_shortcut_fit": shortcut_fit,
        "bands": bands,
        "claim_scope": (
            "Finite source-bound census of declared rivals on the listed pinned seeds "
            "and cyclic starts. It does not establish universal rule induction or model gains."
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
        default=repo_root / "shared" / "data" / "canonical" / "puzzles.jsonl",
    )
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = run_census(
        generator_path=args.generator,
        canonical_path=args.canonical,
        lessons_per_band=args.lessons_per_band,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
