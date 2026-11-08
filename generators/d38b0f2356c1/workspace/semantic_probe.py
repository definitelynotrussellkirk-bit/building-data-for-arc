"""Source-bound lesson audit for d38b0f2356c1.

The probe enumerates the generator's executable witness/rival declarations rather
than maintaining a second rival-name list.  It measures a deterministic sample of
three-demo lessons; it is evidence about that sample, not universal induction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK = "d38b0f2356c1"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def load_generator(path: Path | None = None):
    source = (path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("d38b0f2356c1_probe_target", source)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise RuntimeError(f"canonical task {TASK} is absent from {path}")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _grid_hash(grid) -> str:
    encoded = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_hash(module) -> str:
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


def audit(module, lessons_per_band: int = 100) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")

    shortcuts = dict(module.CANONICAL_SHORTCUTS)
    competitors = dict(module.LESSON_COMPETITORS)
    witnesses = dict(module.SEMANTIC_WITNESSES)
    demo_count = int(module.EXAMPLES_NEEDED)
    cycle = len(module.SCHEDULE_PROFILES)
    if cycle < 1:
        raise ValueError("SCHEDULE_PROFILES must be nonempty")

    canonical_results = {}
    pairs = canonical_pairs()
    for name, rival in sorted(shortcuts.items()):
        mismatches = [
            index
            for index, pair in enumerate(pairs)
            if rival(pair["input"]) != pair["output"]
        ]
        canonical_results[name] = {
            "pairs_checked": len(pairs),
            "fit_count": len(pairs) - len(mismatches),
            "mismatch_pair_indices": mismatches,
        }

    bands: dict[str, Any] = {}
    all_input_hashes: set[str] = set()
    for band in ("easy", "medium", "hard"):
        input_hashes: set[str] = set()
        cyclic_starts = Counter()
        witness_inputs = Counter()
        witness_lessons = Counter()
        schedule_profiles = Counter()
        competitor_stats = {
            name: {
                "lessons_refuted": 0,
                "demo_disagreements": 0,
                "query_disagreements": 0,
                "all_input_disagreements": 0,
            }
            for name in sorted(competitors)
        }
        self_check_failures = []
        strict_failures = []
        identifiability_failures = []
        nondeterministic = []

        for lesson_index in range(lessons_per_band):
            seed = 1009 + lesson_index
            start = lesson_index % cycle
            cyclic_starts[str(start)] += 1
            grids = []
            for offset in range(demo_count + 1):
                sample_index = start + offset
                grid = module.generate(seed, sample_index, difficulty=band)
                replay = module.generate(seed, sample_index, difficulty=band)
                if replay != grid:
                    nondeterministic.append(
                        {"lesson": lesson_index, "offset": offset, "seed": seed,
                         "sample_index": sample_index}
                    )
                grids.append(grid)
                digest = _grid_hash(grid)
                input_hashes.add(digest)
                all_input_hashes.add(digest)
                schedule_profiles[module.schedule_profile(seed, sample_index, band)] += 1
                issues = module.self_check(grid)
                if issues:
                    self_check_failures.append(
                        {"lesson": lesson_index, "offset": offset, "issues": issues}
                    )
                strict_issues = module.strict_canonical_like(grid)
                if strict_issues:
                    strict_failures.append(
                        {"lesson": lesson_index, "offset": offset,
                         "issues": strict_issues}
                    )
                for witness_name, predicate in sorted(witnesses.items()):
                    if predicate(grid):
                        witness_inputs[witness_name] += 1

            outputs = [module._intended_output(grid) for grid in grids]
            demos = [
                {"input": grids[index], "output": outputs[index]}
                for index in range(demo_count)
            ]
            query = {"input": grids[-1], "output": outputs[-1]}
            lesson_issues = module.lesson_identifiable(demos, query)
            if lesson_issues:
                identifiability_failures.append(
                    {"lesson": lesson_index, "issues": lesson_issues}
                )

            for witness_name, predicate in sorted(witnesses.items()):
                if any(predicate(pair["input"]) for pair in demos):
                    witness_lessons[witness_name] += 1

            for name, rival in sorted(competitors.items()):
                demo_disagreements = sum(
                    rival(pair["input"]) != pair["output"] for pair in demos
                )
                query_disagreement = rival(query["input"]) != query["output"]
                stats = competitor_stats[name]
                stats["lessons_refuted"] += demo_disagreements > 0
                stats["demo_disagreements"] += demo_disagreements
                stats["query_disagreements"] += query_disagreement
                stats["all_input_disagreements"] += (
                    demo_disagreements + query_disagreement
                )

        bands[band] = {
            "lessons": lessons_per_band,
            "generated_inputs": lessons_per_band * (demo_count + 1),
            "distinct_inputs": len(input_hashes),
            "cyclic_starts": dict(sorted(cyclic_starts.items())),
            "schedule_profile_inputs": dict(sorted(schedule_profiles.items())),
            "witness_input_hits": {
                name: witness_inputs[name] for name in sorted(witnesses)
            },
            "witness_lesson_hits": {
                name: witness_lessons[name] for name in sorted(witnesses)
            },
            "competitors": competitor_stats,
            "self_check_failures": len(self_check_failures),
            "self_check_failure_examples": self_check_failures[:5],
            "strict_profile_failures": len(strict_failures),
            "strict_profile_failure_examples": strict_failures[:5],
            "lesson_identifiability_failures": len(identifiability_failures),
            "lesson_identifiability_failure_examples": identifiability_failures[:5],
            "nondeterministic_replays": len(nondeterministic),
            "nondeterministic_examples": nondeterministic[:5],
        }

    canonical_ok = all(
        result["fit_count"] == result["pairs_checked"]
        for result in canonical_results.values()
    )
    bands_ok = all(
        stats["self_check_failures"] == 0
        and stats["strict_profile_failures"] == 0
        and stats["lesson_identifiability_failures"] == 0
        and stats["nondeterministic_replays"] == 0
        and all(
            rival_stats["lessons_refuted"] == lessons_per_band
            for rival_stats in stats["competitors"].values()
        )
        for stats in bands.values()
    )

    return {
        "schema": "d38b0f2356c1-semantic-probe-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": _source_hash(module),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "lessons_per_band": lessons_per_band,
        "canonical_shortcuts": sorted(shortcuts),
        "lesson_competitors": sorted(competitors),
        "semantic_witnesses": sorted(witnesses),
        "canonical_shortcut_results": canonical_results,
        "bands": bands,
        "distinct_inputs_across_bands": len(all_input_hashes),
        "lesson_policy": {
            "demo_count": demo_count,
            "query_count": 1,
            "seed": "1009 + lesson_index",
            "cyclic_start": f"lesson_index modulo {cycle}",
            "sample_indices": "cyclic_start through cyclic_start + demo_count",
            "difficulty_bands": ["easy", "medium", "hard"],
            "overlapping_within_seed": True,
        },
        "domain_limits": [
            "Only the declared generator domain and executable declared rivals are measured.",
            "The sample uses deterministic crossed seed/index schedules; it is not an IID estimate.",
            "Passing these finite lessons does not establish universal induction or learner success.",
            "Python oracle parity is separately bound by canonical tests and the repository Racket gates.",
        ],
        "passed": canonical_ok and bands_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    module = load_generator(args.generator)
    report = audit(module, lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {
        "passed": report["passed"],
        "generator_sha256": report["generator_sha256"],
        "lessons_per_band": report["lessons_per_band"],
        "distinct_inputs_across_bands": report["distinct_inputs_across_bands"],
        "bands": {
            band: {
                "distinct_inputs": stats["distinct_inputs"],
                "lesson_identifiability_failures": stats["lesson_identifiability_failures"],
                "competitors": stats["competitors"],
            }
            for band, stats in report["bands"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
