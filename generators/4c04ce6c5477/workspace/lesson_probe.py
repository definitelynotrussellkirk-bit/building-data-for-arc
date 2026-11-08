#!/usr/bin/env python3
"""Racket-backed curriculum census for generator 4c04ce6c5477.

The probe uses the public ``arcpuzzles.runtime.generate`` path, which snapshots
this checkout, executes the selected canonical Racket authority, and attaches
source hashes to every episode.  It measures complete 3-demo/1-query lessons,
not isolated generator draws.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import generate

from reference_probe import analyze, height_output, load_generator

TASK_ID = "4c04ce6c5477"
BANDS = ("easy", "medium", "hard")
BASE_SEEDS = {"easy": 420_000, "medium": 430_000, "hard": 440_000}
N_DEMOS = 3
N_QUERIES = 1


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _empty_rival_counts(names: list[str]) -> dict[str, int]:
    return {name: 0 for name in names}


def _score_band(generator, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    rival_names = sorted(generator.LESSON_COMPETITORS)
    pair_disagreements = _empty_rival_counts(rival_names)
    demo_disagreements = _empty_rival_counts(rival_names)
    query_disagreements = _empty_rival_counts(rival_names)
    survivors_after_demos = _empty_rival_counts(rival_names)
    query_disagreement_survivors = _empty_rival_counts(rival_names)

    unique_inputs: set[str] = set()
    dimensions: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    palette_sizes: Counter[str] = Counter()
    sample_indices: Counter[str] = Counter()
    generator_hashes: Counter[str] = Counter()
    rule_hashes: Counter[str] = Counter()
    executed_rule_hashes: Counter[str] = Counter()
    generator_versions: Counter[str] = Counter()
    lesson_hook_findings: list[dict[str, Any]] = []
    oracle_mismatches: list[dict[str, Any]] = []
    replay_examples: list[dict[str, Any]] = []
    pair_count = 0
    rejection_count = 0

    for episode in episodes:
        demos = episode["train"]
        query = episode["test"][0]
        pairs = [*demos, query]
        pair_count += len(pairs)
        rejection_count += len(episode.get("rejections", []))
        generator_versions[str(episode.get("generator_version"))] += 1
        provenance = episode["provenance"]
        generator_hashes[provenance["generator_sha256"]] += 1
        rule_hashes[provenance["catalog_rule_hash"]] += 1
        executed_rule_hashes[episode["executed_rule_hash"]] += 1
        for sample_index in episode.get("sample_indices", []):
            sample_indices[str(sample_index)] += 1

        if len(replay_examples) < 3:
            replay_examples.append(
                {
                    "episode_index": episode["episode_index"],
                    "seed": episode["seed"],
                    "sample_index": episode["sample_index"],
                    "accepted_sample_indices": episode.get("sample_indices", []),
                }
            )

        findings = list(generator.lesson_identifiable(demos, query) or [])
        if findings:
            lesson_hook_findings.append(
                {
                    "episode_index": episode["episode_index"],
                    "seed": episode["seed"],
                    "findings": findings,
                }
            )

        for pair_index, pair in enumerate(pairs):
            grid = pair["input"]
            unique_inputs.add(_grid_hash(grid))
            facts = analyze(grid)
            dimensions[f"{facts['height']}x{facts['width']}"] += 1
            object_counts[str(len(facts["components"]))] += 1
            palette_sizes[str(len({obj['color'] for obj in facts['components']}) + 1)] += 1
            if height_output(grid) != pair["output"]:
                oracle_mismatches.append(
                    {
                        "episode_index": episode["episode_index"],
                        "pair_index": pair_index,
                        "seed": episode["seed"],
                    }
                )
            for name, rival in generator.LESSON_COMPETITORS.items():
                pair_disagreements[name] += int(rival(grid) != pair["output"])

        for name, rival in generator.LESSON_COMPETITORS.items():
            demo_misses = sum(rival(pair["input"]) != pair["output"] for pair in demos)
            query_miss = rival(query["input"]) != query["output"]
            demo_disagreements[name] += demo_misses
            query_disagreements[name] += int(query_miss)
            survived = demo_misses == 0
            survivors_after_demos[name] += int(survived)
            query_disagreement_survivors[name] += int(survived and query_miss)

    return {
        "lessons": len(episodes),
        "demos_per_lesson": N_DEMOS,
        "queries_per_lesson": N_QUERIES,
        "pairs_seen": pair_count,
        "unique_inputs": len(unique_inputs),
        "duplicate_input_occurrences": pair_count - len(unique_inputs),
        "rejections": rejection_count,
        "dimension_counts": dict(sorted(dimensions.items())),
        "object_count_histogram": dict(sorted(object_counts.items())),
        "palette_size_histogram_including_background": dict(sorted(palette_sizes.items())),
        "accepted_sample_index_histogram": dict(sorted(sample_indices.items(), key=lambda item: int(item[0]))),
        "rival_pair_disagreements": pair_disagreements,
        "rival_demo_disagreements": demo_disagreements,
        "rival_query_disagreements": query_disagreements,
        "rival_survivors_after_all_demos": survivors_after_demos,
        "rival_query_disagreement_survivors": query_disagreement_survivors,
        "lesson_identifiable_failures": lesson_hook_findings,
        "independent_height_oracle_mismatches": oracle_mismatches,
        "generator_sha256_counts": dict(generator_hashes),
        "catalog_rule_hash_counts": dict(rule_hashes),
        "executed_rule_hash_counts": dict(executed_rule_hashes),
        "generator_version_counts": dict(generator_versions),
        "replay_examples": replay_examples,
    }


def run_census(*, lessons_per_band: int) -> dict[str, Any]:
    if lessons_per_band < 100:
        raise ValueError("lessons_per_band must be at least 100 for review evidence")

    probe_path = Path(__file__).resolve()
    task_root = probe_path.parents[1]
    repo_root = probe_path.parents[3]
    generator_path = task_root / "generator.py"
    reference_probe_path = probe_path.with_name("reference_probe.py")
    canonical_path = repo_root / "shared/data/canonical/puzzles.jsonl"

    generator = load_generator(generator_path)
    catalog = Catalog(repo_root)
    catalog_row = catalog.describe(TASK_ID)
    generator_sha = _sha256(generator_path)
    if catalog_row["generator_sha256"] != generator_sha:
        raise RuntimeError("catalog generator hash does not match the reviewed source")

    bands: dict[str, Any] = {}
    for band in BANDS:
        episodes = generate(
            catalog,
            TASK_ID,
            count=lessons_per_band,
            seed=BASE_SEEDS[band],
            difficulty=band,
            n_train=N_DEMOS,
            n_test=N_QUERIES,
            sample_index=0,
            overrides={},
            allow_unapproved=True,
            timeout=1200,
            reference="canonical",
        )
        bands[band] = _score_band(generator, episodes)

    problems: list[str] = []
    for band, stats in bands.items():
        if stats["lessons"] != lessons_per_band:
            problems.append(f"{band}: materialized {stats['lessons']}/{lessons_per_band} lessons")
        if stats["rejections"]:
            problems.append(f"{band}: {stats['rejections']} generation rejections")
        if stats["lesson_identifiable_failures"]:
            problems.append(f"{band}: lesson_identifiable reported surviving rivals")
        if stats["independent_height_oracle_mismatches"]:
            problems.append(f"{band}: independent height oracle disagreed with Racket")
        if any(stats["rival_survivors_after_all_demos"].values()):
            problems.append(f"{band}: at least one declared rival survived all demos")
        if set(stats["generator_sha256_counts"]) != {generator_sha}:
            problems.append(f"{band}: episode provenance used another generator hash")
        if set(stats["executed_rule_hash_counts"]) != {generator.RULE_HASH}:
            problems.append(f"{band}: executed rule hash differs from RULE_HASH")

    return {
        "schema": "4c04ce6c5477-racket-lesson-census-v1",
        "task_id": TASK_ID,
        "passed": not problems,
        "problems": problems,
        "source_binding": {
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha,
            "generator_version": str(generator.VERSION),
            "declared_rule_hash": str(generator.RULE_HASH),
            "catalog_rule_hash": str(catalog_row["rule_hash"]),
            "canonical_path": str(canonical_path),
            "canonical_ledger_sha256": _sha256(canonical_path),
            "reference_probe_path": str(reference_probe_path),
            "reference_probe_sha256": _sha256(reference_probe_path),
            "lesson_probe_path": str(probe_path),
            "lesson_probe_sha256": _sha256(probe_path),
        },
        "sampler": {
            "entrypoint": "arcpuzzles.runtime.generate",
            "runtime_behavior": "snapshots current catalog sources, runs canonical Racket authority in an isolated worker",
            "lessons_per_band": lessons_per_band,
            "difficulty_bands": list(BANDS),
            "base_seeds": BASE_SEEDS,
            "episode_seed_policy": "base seed + episode_index",
            "lesson_sample_index_start": 0,
            "pair_sample_policy": "accepted sequential sample indices beginning at 0 within each episode",
            "demos_per_lesson": N_DEMOS,
            "queries_per_lesson": N_QUERIES,
            "reference": "canonical",
            "overrides": {},
            "cyclic_schedule": None,
        },
        "domain_limits": {
            "axes": _jsonable(generator.AXES),
            "background": 0,
            "non_background_colors": "distinct sample without replacement from 1..9",
            "object_count": "2..5 isolated four-connected monochrome objects",
            "bbox_heights": "distinct; consecutive within each generated input",
            "grid_height": "7..16",
            "grid_width": "10..18",
        },
        "declared_rivals": sorted(generator.LESSON_COMPETITORS),
        "bands": bands,
        "claim_scope": (
            "Finite source-bound census over the listed seeds and public runtime sampler; "
            "it verifies the declared rivals only and is not universal induction."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    report = run_census(lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "problems": report["problems"],
        "generator_sha256": report["source_binding"]["generator_sha256"],
        "bands": {
            name: {
                "lessons": row["lessons"],
                "pairs_seen": row["pairs_seen"],
                "unique_inputs": row["unique_inputs"],
                "survivors": row["rival_survivors_after_all_demos"],
            }
            for name, row in report["bands"].items()
        },
    }, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
