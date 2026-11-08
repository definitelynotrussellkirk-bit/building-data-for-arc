#!/usr/bin/env python3
"""Source-bound lesson probe for generator 17de34436a9f.

The generic semantic gate checks marginal witness frequency and a small lesson
sample.  This probe exercises complete four-demonstration lessons, all cyclic
starts of the declared schedule, and every rival declared by the generator.
It intentionally derives rival names from the final module instead of copying a
hard-coded list, so future edits cannot silently escape the audit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "17de34436a9f"
HERE = Path(__file__).resolve()
TASK_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
GENERATOR_PATH = TASK_ROOT / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return _sha256_bytes(payload)


def _canonical_row() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [pair for split in ("train", "test") for pair in row[split]]


def _computed_rule_hash(program: str) -> str:
    normalized = " ".join(program.split())
    return _sha256_bytes(normalized.encode())[:12]


def _safe_apply(fn, grid: list[list[int]]) -> tuple[list[list[int]] | None, str | None]:
    try:
        return fn(grid), None
    except Exception as exc:  # fail loudly in the report, not by omission
        return None, f"{type(exc).__name__}: {exc}"


def run_probe(lessons_per_band: int = 100) -> dict[str, Any]:
    if lessons_per_band < len(GEN.SCHEDULE_PROFILES):
        raise ValueError(
            f"lessons_per_band must be at least {len(GEN.SCHEDULE_PROFILES)} "
            "to cover every cyclic schedule start"
        )

    canonical_row = _canonical_row()
    canonical_pairs = _canonical_pairs(canonical_row)
    computed_rule_hash = _computed_rule_hash(canonical_row["program_solution"])

    canonical_mirror_mismatches = []
    for index, pair in enumerate(canonical_pairs):
        actual, error = _safe_apply(GEN.rule_mirror, pair["input"])
        if error or actual != pair["output"]:
            canonical_mirror_mismatches.append(
                {"pair_index": index, "error": error, "actual": actual}
            )

    shortcut_checks: dict[str, Any] = {}
    for name, shortcut in sorted(GEN.CANONICAL_SHORTCUTS.items()):
        fits = 0
        errors = []
        for index, pair in enumerate(canonical_pairs):
            actual, error = _safe_apply(shortcut, pair["input"])
            if error:
                errors.append({"pair_index": index, "error": error})
            elif actual == pair["output"]:
                fits += 1
        shortcut_checks[name] = {
            "canonical_pairs": len(canonical_pairs),
            "canonical_fits": fits,
            "errors": errors,
        }

    report: dict[str, Any] = {
        "schema": "17de34436a9f_lesson_probe/1",
        "task_id": TASK_ID,
        "status": "PASS",
        "source_binding": {
            "generator_sha256": _sha256_bytes(GENERATOR_PATH.read_bytes()),
            "probe_sha256": _sha256_bytes(HERE.read_bytes()),
            "generator_version": GEN.VERSION,
            "declared_rule_hash": GEN.RULE_HASH,
            "computed_rule_hash": computed_rule_hash,
            "canonical_path": str(CANONICAL_PATH.relative_to(REPO_ROOT)),
            "canonical_pairs": len(canonical_pairs),
        },
        "declared_domain": {
            "axes": GEN.AXES,
            "schedule_profiles": list(GEN.SCHEDULE_PROFILES),
            "examples_needed": GEN.EXAMPLES_NEEDED,
            "witnesses": sorted(GEN.SEMANTIC_WITNESSES),
            "competitors": sorted(GEN.LESSON_COMPETITORS),
            "canonical_shortcuts": sorted(GEN.CANONICAL_SHORTCUTS),
        },
        "sampler": {
            "lessons_per_band": lessons_per_band,
            "seed_rule": "0x17DE000 + lesson_index",
            "cyclic_start_rule": "lesson_index % len(SCHEDULE_PROFILES)",
            "sample_indices": "start..start+4 (4 demos + 1 query)",
            "outputs": "generator.rule_mirror; canonical parity checked here; Racket parity is checked by the authoritative semantic/rule-smoke gates",
        },
        "canonical_mirror_mismatches": canonical_mirror_mismatches,
        "canonical_shortcut_checks": shortcut_checks,
        "bands": {},
        "limitations": [
            "This is a finite curriculum audit, not a claim of universal induction.",
            "High-volume outputs use the task-local Python mirror; final authoritative battery evidence independently checks Python/Racket parity.",
        ],
        "failures": [],
    }

    if computed_rule_hash != GEN.RULE_HASH:
        report["failures"].append(
            f"declared RULE_HASH {GEN.RULE_HASH} != computed {computed_rule_hash}"
        )
    if canonical_mirror_mismatches:
        report["failures"].append("Python mirror mismatches canonical outputs")
    for name, result in shortcut_checks.items():
        if result["errors"] or result["canonical_fits"] != len(canonical_pairs):
            report["failures"].append(
                f"declared canonical shortcut {name!r} does not fit every canonical pair"
            )

    schedule_len = len(GEN.SCHEDULE_PROFILES)
    expected_starts = list(range(schedule_len))

    for band in BANDS:
        input_hashes: set[str] = set()
        lesson_hashes: set[str] = set()
        cyclic_starts: set[int] = set()
        profile_counts: Counter[str] = Counter()
        witness_firings: Counter[str] = Counter(
            {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        )
        witness_lessons: Counter[str] = Counter(
            {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        )
        competitor_survivors: Counter[str] = Counter(
            {name: 0 for name in GEN.LESSON_COMPETITORS}
        )
        query_changing_survivors: Counter[str] = Counter(
            {name: 0 for name in GEN.LESSON_COMPETITORS}
        )
        shortcut_disagreements: Counter[str] = Counter(
            {name: 0 for name in GEN.CANONICAL_SHORTCUTS}
        )
        strict_hits = 0
        self_check_failures = []
        strict_failures = []
        identifiability_failures = []
        rival_errors = []

        for lesson_index in range(lessons_per_band):
            seed = 0x17DE000 + lesson_index
            start = lesson_index % schedule_len
            cyclic_starts.add(start)
            pairs = []
            lesson_input_hashes = []

            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(seed, sample_index, difficulty=band)
                errors = GEN.self_check(grid, difficulty=band)
                if errors:
                    self_check_failures.append(
                        {
                            "lesson_index": lesson_index,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                strict_errors = GEN.strict_canonical_like(grid)
                if strict_errors:
                    strict_failures.append(
                        {
                            "lesson_index": lesson_index,
                            "sample_index": sample_index,
                            "errors": strict_errors,
                        }
                    )
                else:
                    strict_hits += 1

                output = GEN.rule_mirror(grid)
                pairs.append({"input": grid, "output": output})
                digest = _grid_hash(grid)
                input_hashes.add(digest)
                lesson_input_hashes.append(digest)
                profile_counts[
                    str(GEN.schedule_profile(seed, sample_index, band))
                ] += 1

                for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    try:
                        if predicate(grid):
                            witness_firings[witness_name] += 1
                    except Exception as exc:
                        rival_errors.append(
                            {
                                "kind": "witness",
                                "name": witness_name,
                                "lesson_index": lesson_index,
                                "sample_index": sample_index,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )

                for shortcut_name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
                    rival_output, error = _safe_apply(shortcut, grid)
                    if error:
                        rival_errors.append(
                            {
                                "kind": "shortcut",
                                "name": shortcut_name,
                                "lesson_index": lesson_index,
                                "sample_index": sample_index,
                                "error": error,
                            }
                        )
                    elif rival_output != output:
                        shortcut_disagreements[shortcut_name] += 1

            lesson_hashes.add(_sha256_bytes("|".join(lesson_input_hashes).encode()))
            demos = pairs[: GEN.EXAMPLES_NEEDED]
            query = pairs[GEN.EXAMPLES_NEEDED]

            for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                try:
                    if any(predicate(pair["input"]) for pair in demos):
                        witness_lessons[witness_name] += 1
                except Exception as exc:
                    rival_errors.append(
                        {
                            "kind": "lesson_witness",
                            "name": witness_name,
                            "lesson_index": lesson_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

            for competitor_name, competitor in GEN.LESSON_COMPETITORS.items():
                try:
                    survives = all(
                        competitor(pair["input"]) == pair["output"] for pair in demos
                    )
                    if survives:
                        competitor_survivors[competitor_name] += 1
                        if competitor(query["input"]) != query["output"]:
                            query_changing_survivors[competitor_name] += 1
                except Exception as exc:
                    rival_errors.append(
                        {
                            "kind": "competitor",
                            "name": competitor_name,
                            "lesson_index": lesson_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

            reasons = GEN.lesson_identifiable(demos, query)
            if reasons:
                identifiability_failures.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "start": start,
                        "reasons": reasons,
                    }
                )

        band_report = {
            "lessons": lessons_per_band,
            "demos_per_lesson": GEN.EXAMPLES_NEEDED,
            "queries": lessons_per_band,
            "total_inputs": lessons_per_band * (GEN.EXAMPLES_NEEDED + 1),
            "unique_input_count": len(input_hashes),
            "unique_lesson_count": len(lesson_hashes),
            "cyclic_starts_checked": sorted(cyclic_starts),
            "schedule_profile_counts": dict(sorted(profile_counts.items())),
            "strict_hits": strict_hits,
            "strict_draws": lessons_per_band * (GEN.EXAMPLES_NEEDED + 1),
            "self_check_failures": self_check_failures,
            "strict_failures": strict_failures,
            "witness_firings": dict(sorted(witness_firings.items())),
            "witness_lessons": dict(sorted(witness_lessons.items())),
            "competitor_survivors": dict(sorted(competitor_survivors.items())),
            "competitor_query_changing_survivors": dict(
                sorted(query_changing_survivors.items())
            ),
            "canonical_shortcut_generated_disagreements": dict(
                sorted(shortcut_disagreements.items())
            ),
            "identifiability_failures": identifiability_failures,
            "rival_errors": rival_errors,
        }
        report["bands"][band] = band_report

        if sorted(cyclic_starts) != expected_starts:
            report["failures"].append(
                f"{band}: missing cyclic starts; got {sorted(cyclic_starts)}"
            )
        if self_check_failures or strict_failures or rival_errors:
            report["failures"].append(f"{band}: structural/strict/rival errors")
        if identifiability_failures:
            report["failures"].append(f"{band}: unidentifiable lessons")
        for witness_name, count in witness_lessons.items():
            if count != lessons_per_band:
                report["failures"].append(
                    f"{band}: witness {witness_name!r} present in only "
                    f"{count}/{lessons_per_band} complete lessons"
                )
        for competitor_name, count in query_changing_survivors.items():
            if count:
                report["failures"].append(
                    f"{band}: competitor {competitor_name!r} survives and changes "
                    f"{count} queries"
                )
        for shortcut_name, count in shortcut_disagreements.items():
            if count == 0:
                report["failures"].append(
                    f"{band}: no generated counterexample for canonical shortcut "
                    f"{shortcut_name!r}"
                )

    if report["failures"]:
        report["status"] = "FAIL"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(args.lessons_per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
