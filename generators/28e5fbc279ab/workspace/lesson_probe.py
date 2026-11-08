#!/usr/bin/env python3
"""Source-bound lesson census over the generator's declared rivals.

The probe assembles every cyclic start in the three-profile schedule, labels all
examples through the unchanged Racket authority, and dynamically iterates
``LESSON_COMPETITORS`` and ``CANONICAL_SHORTCUTS`` from the loaded generator.
It distinguishes lesson references, generated slots, and unique input grids.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

TASK = "28e5fbc279ab"


def assess_lesson(generator, demos, query):
    """Assess one labeled 3-demo/1-query lesson against declared rivals."""
    rival_results = {}
    for name, rival in generator.LESSON_COMPETITORS.items():
        demo_outputs = [rival(pair["input"]) for pair in demos]
        demo_refuted = any(actual != pair["output"]
                           for actual, pair in zip(demo_outputs, demos))
        query_output = rival(query["input"])
        query_disagreement = query_output != query["output"]
        rival_results[name] = {
            "demo_refuted": demo_refuted,
            "query_disagreement": query_disagreement,
            "query_relevant_survival": (not demo_refuted) and query_disagreement,
        }
    reasons = generator.lesson_identifiable(
        demos, {"input": query["input"], "output": query["output"]}
    )
    return {
        "rivals": rival_results,
        "lesson_identifiable_reasons": list(reasons),
    }


def _parse_starts(text):
    try:
        starts = tuple(int(part.strip()) for part in text.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("starts must be comma-separated integers") from exc
    if not starts or any(value < 0 for value in starts):
        raise argparse.ArgumentTypeError("starts must contain nonnegative integers")
    if len(starts) != len(set(starts)):
        raise argparse.ArgumentTypeError("starts must be distinct")
    return starts


def _grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--phase", choices=("before", "intermediate", "final"), required=True)
    ap.add_argument("--seed-base", type=int, default=101)
    ap.add_argument("--seeds", type=int, default=40,
                    help="number of seeds; with starts 0,1,2 this gives 120 lessons per band")
    ap.add_argument("--starts", type=_parse_starts, default=(0, 1, 2),
                    help="comma-separated cyclic lesson starts")
    args = ap.parse_args()
    if args.seeds <= 0:
        ap.error("--seeds must be positive")

    runtime = args.runtime.resolve()
    sys.path.insert(0, str(runtime))
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, normalized_rule_hash

    bundle = runner._load_bundle(TASK)
    generator = bundle.generator_module
    bridge, rule_fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
    all_unique_inputs = set()
    failures = []
    counterexamples = {}
    bands = {}

    try:
        canonical = []
        canonical_shortcut_counts = {
            name: Counter(total=0, fits=0)
            for name in generator.CANONICAL_SHORTCUTS
        }
        for index, pair in enumerate(canonical_pairs(TASK)):
            actual = runner._apply_rule(bridge, rule_fn, pair["input"])
            shortcut_results = {}
            for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
                fits = shortcut(pair["input"]) == actual
                canonical_shortcut_counts[name]["total"] += 1
                canonical_shortcut_counts[name]["fits"] += int(fits)
                shortcut_results[name] = fits
            canonical.append({
                "index": index,
                "racket_matches_stored": actual == pair["output"],
                "self_check": generator.self_check(pair["input"]),
                "rule_mirror_matches_racket": (
                    not hasattr(generator, "rule_mirror")
                    or generator.rule_mirror(pair["input"]) == actual
                ),
                "canonical_shortcuts_fit": shortcut_results,
            })

        for band in ("easy", "medium", "hard"):
            counts = Counter()
            rival_counts = {
                name: Counter(
                    lessons=0,
                    demo_refuted=0,
                    query_disagreement=0,
                    query_relevant_survival=0,
                )
                for name in generator.LESSON_COMPETITORS
            }
            cache = {}
            band_unique_inputs = set()

            def example(seed, sample_index):
                key = (seed, sample_index)
                if key in cache:
                    return cache[key]
                counts["generated_slots"] += 1
                try:
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    messages = list(generator.self_check(grid))
                    output = runner._apply_rule(bridge, rule_fn, grid)
                    mirror_disagreement = (
                        hasattr(generator, "rule_mirror")
                        and generator.rule_mirror(grid) != output
                    )
                    record = {
                        "input": grid,
                        "output": output,
                        "self_check": messages,
                        "mirror_disagreement": mirror_disagreement,
                        "seed": seed,
                        "sample_index": sample_index,
                    }
                    counts["generated_completed"] += 1
                    counts["self_check_rejected"] += int(bool(messages))
                    counts["mirror_disagreement"] += int(mirror_disagreement)
                    serialized = _grid_key(grid)
                    band_unique_inputs.add(serialized)
                    all_unique_inputs.add(serialized)
                    if messages:
                        counterexamples.setdefault(
                            f"{band}:self_check_rejected", record
                        )
                    if mirror_disagreement:
                        counterexamples.setdefault(
                            f"{band}:mirror_disagreement", record
                        )
                except Exception as exc:  # retained as evidence, never silent
                    counts["generation_or_authority_errors"] += 1
                    record = None
                    failures.append({
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                cache[key] = record
                return record

            for seed in range(args.seed_base, args.seed_base + args.seeds):
                for start in args.starts:
                    counts["lesson_attempts"] += 1
                    records = [example(seed, start + offset) for offset in range(4)]
                    counts["draw_references"] += 4
                    if any(record is None for record in records):
                        counts["lesson_errors"] += 1
                        continue
                    demos = [
                        {"input": record["input"], "output": record["output"]}
                        for record in records[:3]
                    ]
                    query = {
                        "input": records[3]["input"],
                        "output": records[3]["output"],
                    }
                    assessment = assess_lesson(generator, demos, query)
                    counts["lessons_completed"] += 1
                    reasons = assessment["lesson_identifiable_reasons"]
                    counts["lesson_identifiable_rejected"] += int(bool(reasons))
                    if reasons:
                        counterexamples.setdefault(
                            f"{band}:lesson_identifiable_rejected",
                            {
                                "seed": seed,
                                "start": start,
                                "reasons": reasons,
                                "demos": demos,
                                "query": query,
                            },
                        )
                    for name, result in assessment["rivals"].items():
                        rival_counts[name]["lessons"] += 1
                        for metric, value in result.items():
                            rival_counts[name][metric] += int(value)
                        if result["query_relevant_survival"]:
                            counterexamples.setdefault(
                                f"{band}:surviving_rival:{name}",
                                {
                                    "seed": seed,
                                    "start": start,
                                    "rival": name,
                                    "demos": demos,
                                    "query": query,
                                },
                            )

            counts["unique_inputs"] = len(band_unique_inputs)
            bands[band] = {
                "counts": dict(counts),
                "rivals": {name: dict(values) for name, values in rival_counts.items()},
            }

    finally:
        bridge.shutdown()

    source_path = Path(generator.__file__)
    canonical_shortcuts = {
        name: dict(counts) for name, counts in canonical_shortcut_counts.items()
    }
    report = {
        "schema": "declared-lesson-rival-census-v1",
        "task_id": TASK,
        "phase": args.phase,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "rule_sha256": hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
        "rule_hash": normalized_rule_hash(bundle.rule_source),
        "runtime": str(runtime),
        "declared_domain": {
            "summary": getattr(generator, "SUMMARY", None),
            "invariants": list(getattr(generator, "INVARIANTS", ())),
            "axes": getattr(generator, "AXES", {}),
            "examples_needed": getattr(generator, "EXAMPLES_NEEDED", None),
            "schedule_profiles": list(getattr(generator, "SCHEDULE_PROFILES", ())),
            "lesson_competitors": list(generator.LESSON_COMPETITORS),
            "canonical_shortcuts": list(generator.CANONICAL_SHORTCUTS),
        },
        "sampler": {
            "difficulty_bands": ["easy", "medium", "hard"],
            "seed_inclusive": [args.seed_base, args.seed_base + args.seeds - 1],
            "seed_count": args.seeds,
            "cyclic_starts": list(args.starts),
            "lesson_policy": "three consecutive demonstrations plus the next consecutive query",
            "overrides": {},
            "lessons_per_band": args.seeds * len(args.starts),
            "draw_references_per_band": args.seeds * len(args.starts) * 4,
        },
        "bands": bands,
        "unique_inputs_all_bands": len(all_unique_inputs),
        "canonical": canonical,
        "canonical_shortcuts": canonical_shortcuts,
        "counterexamples": counterexamples,
        "failures": failures,
        "command": {
            "cwd": str(Path.cwd()),
            "argv": [sys.executable, *sys.argv],
        },
    }

    fatal = len(failures)
    if args.phase == "final":
        for canonical_pair in canonical:
            fatal += int(not canonical_pair["racket_matches_stored"])
            fatal += int(bool(canonical_pair["self_check"]))
            fatal += int(not canonical_pair["rule_mirror_matches_racket"])
            fatal += sum(not value for value in canonical_pair["canonical_shortcuts_fit"].values())
        for band_report in bands.values():
            counts = band_report["counts"]
            fatal += sum(counts.get(name, 0) for name in (
                "generation_or_authority_errors",
                "lesson_errors",
                "self_check_rejected",
                "mirror_disagreement",
                "lesson_identifiable_rejected",
            ))
            for rival in band_report["rivals"].values():
                fatal += rival["lessons"] - rival["demo_refuted"]
                fatal += rival["query_relevant_survival"]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "phase": report["phase"],
        "source_sha256": report["source_sha256"],
        "sampler": report["sampler"],
        "bands": report["bands"],
        "unique_inputs_all_bands": report["unique_inputs_all_bands"],
        "canonical_shortcuts": report["canonical_shortcuts"],
        "failures": len(report["failures"]),
        "fatal": fatal,
    }, indent=2))
    return int(bool(fatal))


if __name__ == "__main__":
    raise SystemExit(main())
