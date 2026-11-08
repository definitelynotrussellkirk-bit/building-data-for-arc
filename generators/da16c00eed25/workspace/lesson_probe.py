#!/usr/bin/env python3
"""Source-bound lesson/rival census for da16c00eed25.

The probe builds four-demo/one-query lessons through the production runner and
selected Racket authority. It reads CANONICAL_SHORTCUTS and LESSON_COMPETITORS
from the generator itself, verifies every shortcut on every usable canonical
pair, samples at least 100 lessons per difficulty band, and exhausts every
cyclic schedule start. Exit 0 means these finite checks passed; it is not a
claim of universal induction.

Run from repo/:
  PYTHONPATH=shared/runtime python3 generators/da16c00eed25/workspace/lesson_probe.py \
      --lessons-per-band 100 --out ../checks/lesson_probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime

TASK_ID = "da16c00eed25"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11


def normalize_grid(grid: Any) -> list[list[int]]:
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(cell) for cell in row] for row in grid]
    return [list(row) for row in grid]


def grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def probe_seed(band: str, index: int) -> int:
    raw = f"{TASK_ID}|lesson-probe-v1|{band}|{index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & ((1 << 63) - 1)


def read_canonical_pairs() -> list[dict[str, list[list[int]]]]:
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") != TASK_ID:
                continue
            raw_pairs = list(record.get("train") or [])
            if isinstance(record.get("test"), dict):
                raw_pairs.append(record["test"])
            return [
                {
                    "input": normalize_grid(pair["input"]),
                    "output": normalize_grid(pair["output"]),
                }
                for pair in raw_pairs
                if isinstance(pair, dict) and "input" in pair and "output" in pair
            ]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def evaluate_lesson(gen: Any, lesson: dict[str, Any], competitors: dict[str, Any]) -> dict[str, Any]:
    demos = lesson["demos"]
    query = lesson["query"]
    details: dict[str, Any] = {}
    for name, rival in sorted(competitors.items()):
        disagreement_indexes = [
            i for i, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        details[name] = {
            "demo_disagreement_count": len(disagreement_indexes),
            "first_demo_disagreement": disagreement_indexes[0] if disagreement_indexes else None,
            "survives_all_demos": not disagreement_indexes,
            "query_disagrees": rival(query["input"]) != query["output"],
        }
    hook_errors = list(gen.lesson_identifiable(demos, query) or [])
    return {
        "all_competitors_refuted_by_demos": all(
            not row["survives_all_demos"] for row in details.values()
        ),
        "lesson_hook_errors": hook_errors,
        "competitors": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 100:
        parser.error("--lessons-per-band must be at least 100")

    generator_path = REPO_ROOT / f"generators/{TASK_ID}/generator.py"
    generator_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    probe_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    runtime_dir = tempfile.TemporaryDirectory(prefix="da16c00eed25-lesson-probe-")
    stage = Path(runtime_dir.name)
    runtime_manifest = prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
    sys.path.insert(0, str(stage))
    from puzzle_generators import runner

    bundle = runner._load_bundle(TASK_ID)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    gen = bundle.generator_module
    staged_generator = stage / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
    staged_generator_sha = hashlib.sha256(staged_generator.read_bytes()).hexdigest()
    if staged_generator_sha != generator_sha:
        raise RuntimeError(
            f"staged generator hash {staged_generator_sha} != source {generator_sha}"
        )
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    errors: list[str] = []

    if not shortcuts:
        errors.append("CANONICAL_SHORTCUTS is empty")
    if not competitors:
        errors.append("LESSON_COMPETITORS is empty")
    if set(shortcuts) != set(competitors):
        errors.append(
            "declaration mismatch: CANONICAL_SHORTCUTS="
            f"{sorted(shortcuts)} LESSON_COMPETITORS={sorted(competitors)}"
        )

    canonical = read_canonical_pairs()
    canonical_fit: dict[str, Any] = {}
    for name, rival in sorted(shortcuts.items()):
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical]
        fit = bool(matches) and all(matches)
        canonical_fit[name] = {
            "usable_pairs": len(matches),
            "matches": sum(matches),
            "fits_every_usable_pair": fit,
        }
        if not fit:
            errors.append(f"declared canonical shortcut {name!r} failed canonical fit")

    lessons: list[dict[str, Any]] = []
    materialization_errors: list[str] = []
    try:
        for band in BANDS:
            for index in range(args.lessons_per_band):
                seed = probe_seed(band, index)
                sample_index = index * LESSON_SAMPLE_STRIDE
                try:
                    instance = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=sample_index,
                        n_train=int(gen.EXAMPLES_NEEDED),
                        n_test=1,
                        difficulty=band,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                    )
                except Exception as exc:
                    materialization_errors.append(
                        f"band={band} index={index} seed={seed} sample_index={sample_index}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue
                lessons.append({
                    "band": band,
                    "index": index,
                    "seed": seed,
                    "sample_index": sample_index,
                    "replay": f"band={band} seed={seed} sample_index={sample_index}",
                    "demos": instance["train"],
                    "query": instance["test"][0],
                })

        lesson_counts = Counter(row["band"] for row in lessons)
        input_hashes: dict[str, set[str]] = defaultdict(set)
        all_input_hashes: set[str] = set()
        fully_refuting = Counter()
        hook_clean = Counter()
        competitor_refuted: dict[str, Counter[str]] = {band: Counter() for band in BANDS}
        witness_present: dict[str, Counter[str]] = {band: Counter() for band in BANDS}
        first_failures: list[dict[str, Any]] = []

        for lesson in lessons:
            band = lesson["band"]
            for pair in list(lesson["demos"]) + [lesson["query"]]:
                digest = grid_hash(pair["input"])
                input_hashes[band].add(digest)
                all_input_hashes.add(digest)
            result = evaluate_lesson(gen, lesson, competitors)
            if result["all_competitors_refuted_by_demos"]:
                fully_refuting[band] += 1
            if not result["lesson_hook_errors"]:
                hook_clean[band] += 1
            for name, detail in result["competitors"].items():
                if not detail["survives_all_demos"]:
                    competitor_refuted[band][name] += 1
            for name, predicate in sorted(witnesses.items()):
                if any(bool(predicate(pair["input"])) for pair in lesson["demos"]):
                    witness_present[band][name] += 1
            if (
                not result["all_competitors_refuted_by_demos"]
                or result["lesson_hook_errors"]
            ) and len(first_failures) < 5:
                first_failures.append({"replay": lesson["replay"], "result": result})

        per_band: dict[str, Any] = {}
        for band in BANDS:
            count = lesson_counts[band]
            per_band[band] = {
                "lessons": count,
                "grids": count * (int(gen.EXAMPLES_NEEDED) + 1),
                "unique_inputs": len(input_hashes[band]),
                "all_competitors_refuted_by_demos": fully_refuting[band],
                "lesson_identifiable_clean": hook_clean[band],
                "rival_refuted_lessons": dict(sorted(competitor_refuted[band].items())),
                "witness_present_in_demo_lessons": dict(sorted(witness_present[band].items())),
            }
            if count != args.lessons_per_band:
                errors.append(f"{band}: materialized {count}/{args.lessons_per_band} lessons")
            if fully_refuting[band] != count:
                errors.append(f"{band}: {fully_refuting[band]}/{count} lessons refuted every rival")
            if hook_clean[band] != count:
                errors.append(f"{band}: {hook_clean[band]}/{count} lessons passed lesson_identifiable")

        # Explicitly exhaust every schedule phase, again through runner+Racket.
        profiles = tuple(getattr(gen, "SCHEDULE_PROFILES", ()))
        cyclic_rows: list[dict[str, Any]] = []
        if not profiles:
            errors.append("SCHEDULE_PROFILES is missing or empty")
        else:
            for band in BANDS:
                for start in range(len(profiles)):
                    instance = runner.run_one(
                        TASK_ID,
                        seed=424242,
                        sample_index=start,
                        n_train=int(gen.EXAMPLES_NEEDED),
                        n_test=1,
                        difficulty=band,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                    )
                    lesson = {
                        "demos": instance["train"],
                        "query": instance["test"][0],
                    }
                    result = evaluate_lesson(gen, lesson, competitors)
                    row = {
                        "band": band,
                        "start": start,
                        "declared_profiles": [
                            gen.schedule_profile(424242, start + offset, difficulty=band)
                            for offset in range(int(gen.EXAMPLES_NEEDED))
                        ],
                        "all_competitors_refuted_by_demos": result["all_competitors_refuted_by_demos"],
                        "lesson_hook_errors": result["lesson_hook_errors"],
                    }
                    cyclic_rows.append(row)
                    if not row["all_competitors_refuted_by_demos"] or row["lesson_hook_errors"]:
                        errors.append(f"cyclic start failed: {row}")

        errors.extend(materialization_errors)
        report = {
            "schema": "da16c00eed25-lesson-rival-census-v1",
            "status": "PASS" if not errors else "FAIL",
            "task_id": TASK_ID,
            "generator_source": str(generator_path.relative_to(REPO_ROOT)),
            "generator_sha256": generator_sha,
            "probe_sha256": probe_sha,
            "staged_generator_sha256": staged_generator_sha,
            "runtime_manifest_file_count": len(runtime_manifest.get("files", [])),
            "rule_hash_declared": getattr(gen, "RULE_HASH", None),
            "scope": (
                "Finite source-bound census, not a proof of universal induction. "
                "All generated outputs came from the selected Racket authority."
            ),
            "domain_limits": {
                "axes": getattr(gen, "AXES", None),
                "invariants": getattr(gen, "INVARIANTS", None),
                "bands": list(BANDS),
            },
            "actual_sampler": {
                "entrypoint": "puzzle_generators.runner.run_one",
                "lesson_shape": f"{gen.EXAMPLES_NEEDED} demos + 1 query",
                "seed_policy": "sha256(task|lesson-probe-v1|band|index)[:8]",
                "sample_index_policy": f"index * {LESSON_SAMPLE_STRIDE}",
                "within_lesson_policy": "runner consumes consecutive accepted sample indexes",
                "difficulty_policy": "easy/medium/hard passed explicitly",
                "label_authority": "selected Racket rule",
            },
            "declarations_read_from_generator": {
                "canonical_shortcuts": sorted(shortcuts),
                "lesson_competitors": sorted(competitors),
                "semantic_witnesses": sorted(witnesses),
                "schedule_profiles": list(getattr(gen, "SCHEDULE_PROFILES", ())),
            },
            "canonical_shortcut_fit": canonical_fit,
            "census": {
                "lessons_requested": args.lessons_per_band * len(BANDS),
                "lessons_materialized": len(lessons),
                "grids": len(lessons) * (int(gen.EXAMPLES_NEEDED) + 1),
                "unique_inputs": len(all_input_hashes),
                "per_band": per_band,
                "first_failures": first_failures,
                "materialization_errors": materialization_errors[:5],
            },
            "cyclic_starts": {
                "seed": 424242,
                "starts_tested_per_band": list(range(len(profiles))),
                "rows": cyclic_rows,
            },
            "errors": errors,
        }
    finally:
        bridge.shutdown()
        runtime_dir.cleanup()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": generator_sha,
        "lessons": report["census"]["lessons_materialized"],
        "unique_inputs": report["census"]["unique_inputs"],
        "per_band": report["census"]["per_band"],
        "errors": errors,
        "out": str(args.out),
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
