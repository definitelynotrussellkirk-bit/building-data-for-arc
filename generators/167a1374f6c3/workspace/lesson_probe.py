#!/usr/bin/env python3
"""Source-bound semantic census for generator 167a1374f6c3.

The probe intentionally imports the assigned ``generator.py`` by exact file
path, iterates the declarations actually exported by that source, and records
its SHA-256 beside every census.  It is evidence about the sampled lessons, not
a claim that arbitrary learners must infer the intended rule.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = TASK_HOME / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME_PATH = REPO_ROOT / "shared" / "runtime"

sys.path.insert(0, str(RUNTIME_PATH))
_SPEC = importlib.util.spec_from_file_location(
    f"lesson_probe_generator_{TASK_HOME.name}", GENERATOR_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _canonical_task() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise RuntimeError(f"canonical task {GEN.TASK_ID} not found in {CANONICAL_PATH}")


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        "input": copy.deepcopy(grid),
        "output": GEN._authority_output(grid),
    }


def _axis_summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for axis in GEN.AXES:
        values = [row[axis] for row in observations]
        unique = sorted(set(values), key=lambda value: (str(type(value)), repr(value)))
        entry: dict[str, Any] = {
            "unique_count": len(unique),
            "values": unique if len(unique) <= 20 else unique[:20],
            "values_truncated": len(unique) > 20,
        }
        if values and all(type(value) is int for value in values):
            entry["minimum"] = min(values)
            entry["maximum"] = max(values)
        summary[axis] = entry
    return summary


def _canonical_shortcut_report(canonical: dict[str, Any]) -> dict[str, Any]:
    pairs = list(canonical.get("train", [])) + list(canonical.get("test", []))
    report: dict[str, Any] = {}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        matches: list[bool] = []
        errors: list[dict[str, str | int]] = []
        for index, pair in enumerate(pairs):
            try:
                matches.append(shortcut(pair["input"]) == pair["output"])
            except Exception as exc:  # evidence should preserve failures
                matches.append(False)
                errors.append(
                    {
                        "pair_index": index,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        report[name] = {
            "usable_pairs": len(pairs),
            "matching_pairs": sum(matches),
            "fits_all_pairs": bool(pairs) and all(matches),
            "mismatching_pair_indexes": [
                index for index, matched in enumerate(matches) if not matched
            ],
            "errors": errors,
        }
    return report


def run_probe(*, lessons_per_band: int = 100, seed_base: int = 16_713_744) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    canonical = _canonical_task()
    generator_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    schedule_modulus = len(GEN.SCHEDULE_PROFILES)
    examples_needed = int(GEN.EXAMPLES_NEEDED)
    if schedule_modulus < 1:
        raise ValueError("generator exposes no schedule profiles")

    report: dict[str, Any] = {
        "task_id": GEN.TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
        "generator_sha256": generator_sha,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "lessons_per_band": lessons_per_band,
        "seed_base": seed_base,
        "domain_limits": copy.deepcopy(GEN.AXES),
        "schedule_profiles": list(GEN.SCHEDULE_PROFILES),
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "lesson_assembly": (
                f"{examples_needed} consecutive demos followed by one query"
            ),
            "cyclic_start_modulus": schedule_modulus,
            "start_formula": "lesson_index % cyclic_start_modulus",
            "seed_formula": (
                "seed_base + band_index*1000000 + lesson_index"
            ),
            "sample_index_formula": (
                "start, ..., start+EXAMPLES_NEEDED for each lesson"
            ),
            "generated_examples_per_lesson": examples_needed + 1,
            "declared_competitor_source": "GEN.LESSON_COMPETITORS",
            "declared_shortcut_source": "GEN.CANONICAL_SHORTCUTS",
        },
        "canonical_shortcuts": _canonical_shortcut_report(canonical),
        "bands": {},
        "claim_scope": (
            "Finite source-bound census only; this does not prove universal "
            "induction by arbitrary solvers."
        ),
    }

    for band_index, band in enumerate(("easy", "medium", "hard")):
        input_hashes: set[str] = set()
        output_hashes: set[str] = set()
        observations: list[dict[str, Any]] = []
        start_counts: Counter[int] = Counter()
        profile_counts: Counter[str] = Counter()
        reasons_counter: Counter[str] = Counter()
        identifiable = 0
        ambiguous = 0
        competitor_stats = {
            name: {
                "example_disagreements": 0,
                "lessons_with_demo_disagreement": 0,
                "lessons_fitting_all_demos": 0,
                "lessons_changing_query": 0,
                "ambiguous_survivor_lessons": 0,
                "exceptions": [],
            }
            for name in GEN.LESSON_COMPETITORS
        }

        for lesson_index in range(lessons_per_band):
            seed = seed_base + band_index * 1_000_000 + lesson_index
            start = lesson_index % schedule_modulus
            start_counts[start] += 1
            grids = [
                GEN.generate(seed, start + offset, difficulty=band)
                for offset in range(examples_needed + 1)
            ]
            pairs = [_pair(grid) for grid in grids]
            demos, query = pairs[:-1], pairs[-1]

            for offset, pair in enumerate(pairs):
                input_hashes.add(_json_hash(pair["input"]))
                output_hashes.add(_json_hash(pair["output"]))
                observations.append(GEN.observe_overrides(pair["input"]))
                profile_counts[
                    GEN.schedule_profile(seed, start + offset, difficulty=band)
                ] += 1

            reasons = GEN.lesson_identifiable(demos, query)
            if reasons:
                ambiguous += 1
                reasons_counter.update(reasons)
            else:
                identifiable += 1

            for name, competitor in GEN.LESSON_COMPETITORS.items():
                stats = competitor_stats[name]
                demo_matches: list[bool] = []
                query_matches = False
                try:
                    for demo in demos:
                        match = competitor(demo["input"]) == demo["output"]
                        demo_matches.append(match)
                        if not match:
                            stats["example_disagreements"] += 1
                    query_matches = competitor(query["input"]) == query["output"]
                    if not query_matches:
                        stats["example_disagreements"] += 1
                except Exception as exc:
                    stats["exceptions"].append(
                        {
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "start": start,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

                if not all(demo_matches):
                    stats["lessons_with_demo_disagreement"] += 1
                else:
                    stats["lessons_fitting_all_demos"] += 1
                if not query_matches:
                    stats["lessons_changing_query"] += 1
                if all(demo_matches) and not query_matches:
                    stats["ambiguous_survivor_lessons"] += 1

        generated_examples = lessons_per_band * (examples_needed + 1)
        report["bands"][band] = {
            "lessons": lessons_per_band,
            "generated_examples": generated_examples,
            "unique_inputs": len(input_hashes),
            "unique_outputs": len(output_hashes),
            "unique_input_fraction": len(input_hashes) / generated_examples,
            "unique_output_fraction": len(output_hashes) / generated_examples,
            "identifiable_lessons": identifiable,
            "ambiguous_lessons": ambiguous,
            "identifiability_reasons": dict(sorted(reasons_counter.items())),
            "cyclic_start_counts": {
                str(key): value for key, value in sorted(start_counts.items())
            },
            "schedule_profile_counts": dict(sorted(profile_counts.items())),
            "observed_axes": _axis_summary(observations),
            "competitors": competitor_stats,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=16_713_744)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(
        lessons_per_band=args.lessons_per_band,
        seed_base=args.seed_base,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": report["task_id"],
        "generator_sha256": report["generator_sha256"],
        "lessons_per_band": report["lessons_per_band"],
        "bands": {
            band: {
                "identifiable": data["identifiable_lessons"],
                "ambiguous": data["ambiguous_lessons"],
                "unique_inputs": data["unique_inputs"],
            }
            for band, data in report["bands"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
