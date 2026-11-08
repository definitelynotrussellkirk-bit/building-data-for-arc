#!/usr/bin/env python3
"""Source-bound curriculum probe for generator 5782a1f38509.

This tool audits the generator's *declared* competitors and shortcuts rather
than carrying a copied rival-name list.  It materializes non-overlapping
five-demo lessons with one held-out query, checks all cyclic schedule starts,
reports unique inputs/outputs, and records the exact generator source hash.

Run from the repository root:

    PYTHONPATH=shared/runtime:src python3 \
      generators/5782a1f38509/workspace/lesson_probe.py \
      --lessons-per-band 100 --out ../checks/final-lesson-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "5782a1f38509"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
GENERATOR_PATH = HOME / "generator.py"
BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"source_bound_generator_{TASK_ID}", GENERATOR_PATH
    )
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record() -> dict[str, Any]:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open() as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise RuntimeError(f"canonical record {TASK_ID} not found")


def _grid_hash(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _lesson_seed(band: str, lesson_index: int) -> int:
    payload = f"{TASK_ID}|lesson-probe-v1|{band}|{lesson_index}".encode()
    return int(hashlib.sha256(payload).hexdigest()[:16], 16)


def _survivors(generator, demos, query):
    target = generator.rule_mirror(query["input"])
    fit_demos = []
    query_changing = []
    answer_equivalent = []
    for name, rival in generator.LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            fit_demos.append(name)
            if rival(query["input"]) != target:
                query_changing.append(name)
            else:
                answer_equivalent.append(name)
    return {
        "fit_demos": sorted(fit_demos),
        "query_changing": sorted(query_changing),
        "answer_equivalent": sorted(answer_equivalent),
    }


def _materialize_lesson(generator, *, band: str, seed: int, start: int):
    demos = []
    profiles = []
    for offset in range(generator.EXAMPLES_NEEDED):
        sample_index = start + offset
        grid = generator.generate(seed, sample_index, difficulty=band)
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(
                f"self_check failed at band={band} seed={seed} "
                f"sample_index={sample_index}: {errors}"
            )
        demos.append({"input": grid, "output": generator.rule_mirror(grid)})
        profiles.append(generator.schedule_profile(seed, sample_index, band))
    query_index = start + generator.EXAMPLES_NEEDED
    query_grid = generator.generate(seed, query_index, difficulty=band)
    query_errors = generator.self_check(query_grid)
    if query_errors:
        raise AssertionError(
            f"query self_check failed at band={band} seed={seed} "
            f"sample_index={query_index}: {query_errors}"
        )
    query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
    return demos, query, profiles


def run_probe(*, lessons_per_band: int = 100) -> dict[str, Any]:
    if isinstance(lessons_per_band, bool) or not isinstance(lessons_per_band, int):
        raise ValueError("lessons_per_band must be an integer")
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")

    generator = _load_generator()
    canonical = _canonical_record()
    canonical_pairs = list(canonical["train"]) + [canonical["test"]]
    source_bytes = GENERATOR_PATH.read_bytes()

    shortcut_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs)
        for name, rival in sorted(generator.CANONICAL_SHORTCUTS.items())
    }

    cyclic_starts = []
    for start in range(len(generator.SCHEDULE_PROFILES)):
        seed = _lesson_seed("cyclic", start)
        demos, query, profiles = _materialize_lesson(
            generator, band="medium", seed=seed, start=start
        )
        survivors = _survivors(generator, demos, query)
        cyclic_starts.append(
            {
                "start_modulus": start,
                "profiles": profiles,
                "query_profile": generator.schedule_profile(
                    seed, start + generator.EXAMPLES_NEEDED, "medium"
                ),
                "survivors": survivors,
                "lesson_identifiable_reasons": generator.lesson_identifiable(demos, query),
            }
        )

    bands: dict[str, Any] = {}
    all_unique_inputs = set()
    all_unique_outputs = set()
    all_profile_counts = Counter()
    for band in BANDS:
        unique_inputs = set()
        unique_outputs = set()
        profile_counts = Counter()
        query_changing_survivors = Counter()
        demo_survivors = Counter()
        rival_disagreements = Counter()
        unidentifiable = []
        strict_draws = 0
        total_draws = 0

        for lesson_index in range(lessons_per_band):
            seed = _lesson_seed(band, lesson_index)
            start = lesson_index * LESSON_STRIDE
            demos, query, profiles = _materialize_lesson(
                generator, band=band, seed=seed, start=start
            )
            reasons = generator.lesson_identifiable(demos, query)
            survivors = _survivors(generator, demos, query)
            demo_survivors.update(survivors["fit_demos"])
            query_changing_survivors.update(survivors["query_changing"])
            if reasons or survivors["query_changing"]:
                unidentifiable.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "start_sample_index": start,
                        "reasons": reasons,
                        "survivors": survivors,
                    }
                )

            for profile in profiles:
                profile_counts[str(profile)] += 1
            profile_counts[
                str(generator.schedule_profile(
                    seed, start + generator.EXAMPLES_NEEDED, band
                ))
            ] += 1

            for pair in demos + [query]:
                grid = pair["input"]
                output = pair["output"]
                input_hash = _grid_hash(grid)
                output_hash = _grid_hash(output)
                unique_inputs.add(input_hash)
                unique_outputs.add(output_hash)
                all_unique_inputs.add(input_hash)
                all_unique_outputs.add(output_hash)
                total_draws += 1
                strict_draws += bool(generator.strict_canonical_like(grid))
                target = generator.rule_mirror(grid)
                for name, rival in generator.LESSON_COMPETITORS.items():
                    if rival(grid) != target:
                        rival_disagreements[name] += 1

        all_profile_counts.update(profile_counts)
        bands[band] = {
            "lessons": lessons_per_band,
            "demos_per_lesson": generator.EXAMPLES_NEEDED,
            "queries_per_lesson": 1,
            "draws": total_draws,
            "unique_inputs": len(unique_inputs),
            "unique_outputs": len(unique_outputs),
            "strict_canonical_like": strict_draws,
            "strict_fraction": strict_draws / total_draws,
            "profile_counts": dict(sorted(profile_counts.items())),
            "rival_disagreement_draws": dict(sorted(rival_disagreements.items())),
            "demo_survivors": dict(sorted(demo_survivors.items())),
            "query_changing_survivors": dict(sorted(query_changing_survivors.items())),
            "identifiable_lessons": lessons_per_band - len(unidentifiable),
            "unidentifiable_lessons": len(unidentifiable),
            "unidentifiable_examples": unidentifiable[:5],
        }

    failures = []
    if not all(shortcut_fit.values()):
        failures.append("a declared CANONICAL_SHORTCUT does not fit every canonical pair")
    for row in cyclic_starts:
        if row["survivors"]["query_changing"] or row["lesson_identifiable_reasons"]:
            failures.append(
                f"cyclic start {row['start_modulus']} leaves a query-changing competitor"
            )
    for band, stats in bands.items():
        if stats["unidentifiable_lessons"]:
            failures.append(
                f"{band}: {stats['unidentifiable_lessons']} unidentifiable lessons"
            )

    return {
        "schema": "arcpuzzles-source-bound-lesson-probe-v1",
        "task_id": TASK_ID,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "rule_hash": generator.RULE_HASH,
        "canonical_pair_count": len(canonical_pairs),
        "canonical_shortcuts_fit": shortcut_fit,
        "declared_competitors": sorted(generator.LESSON_COMPETITORS),
        "declared_schedule_profiles": list(generator.SCHEDULE_PROFILES),
        "axes": generator.AXES,
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "lesson_seed": "uint64(sha256(task|lesson-probe-v1|band|lesson_index)[:16])",
            "start_sample_index": "lesson_index * 11",
            "demos": "five consecutive indices start..start+4",
            "query": "start+5",
            "overlap": "none within or across lessons",
        },
        "cyclic_starts": cyclic_starts,
        "bands": bands,
        "pooled": {
            "lessons": lessons_per_band * len(BANDS),
            "draws": lessons_per_band * len(BANDS) * (generator.EXAMPLES_NEEDED + 1),
            "unique_inputs": len(all_unique_inputs),
            "unique_outputs": len(all_unique_outputs),
            "profile_counts": dict(sorted(all_profile_counts.items())),
        },
        "limitations": [
            "The probe eliminates only rivals declared by the generator; it does not prove universal rule induction.",
            "Outputs use the source-bound Python mirror; independent Racket parity is established by rule_smoke and authority checks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(
        f"{report['task_id']}: {report['status']} — "
        f"{report['pooled']['lessons']} lessons, "
        f"{report['pooled']['unique_inputs']}/{report['pooled']['draws']} unique inputs, "
        f"{report['pooled']['unique_outputs']} unique outputs"
    )
    for band, stats in report["bands"].items():
        print(
            f"  {band}: identifiable {stats['identifiable_lessons']}/{stats['lessons']}, "
            f"unique inputs {stats['unique_inputs']}/{stats['draws']}, "
            f"strict {stats['strict_canonical_like']}/{stats['draws']}"
        )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
