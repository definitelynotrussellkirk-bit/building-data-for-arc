#!/usr/bin/env python3
"""Bounded curriculum evidence from literal glyphs and the live declarations.

This is a fast counts-derived oracle, calibrated against all canonical pairs.
It does not claim to execute Racket; the retained public semantic/lesson checks
provide that independent calibration. Run with ``--out checks/curriculum.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError:
    for parent in Path(__file__).resolve().parents:
        helper = parent / "shared/runtime/reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            break
    from reviewer_support import canonical_pairs, find_root


TASK_ID = "5dc10de63325"
GLYPH_ROWS = {
    1: ("00000", "08008", "00000", "00000", "08008"),
    2: ("00000", "88088", "00000", "00000", "88088"),
    3: ("08008", "88088", "00000", "08008", "88088"),
    4: ("88088", "88088", "00000", "88088", "88088"),
}
GLYPHS = {q: [[int(v) for v in row] for row in rows] for q, rows in GLYPH_ROWS.items()}


def cyan_count(grid):
    return sum(v == 8 for row in grid for v in row)


def independent_output(grid):
    count = cyan_count(grid)
    if not 4 <= count <= 19:
        raise ValueError(f"count {count} is outside the reviewed positive-glyph domain")
    return [row[:] for row in GLYPHS[count // 4]]


def load_generator():
    root = find_root(__file__)
    path = next(p for p in (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py",
    ) if p.is_file())
    data = path.read_bytes()
    spec = importlib.util.spec_from_file_location("cyan_curriculum_checked_generator", path)
    module = importlib.util.module_from_spec(spec)
    # Execute exactly the source bytes whose hash the report retains.
    exec(compile(data, str(path), "exec"), module.__dict__)
    return root, path, hashlib.sha256(data).hexdigest(), module


def declared_rivals(module):
    result = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        raw = getattr(module, namespace, {})
        if not isinstance(raw, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        for name, fn in raw.items():
            if not isinstance(name, str) or not callable(fn):
                raise TypeError(f"invalid {namespace} declaration: {name!r}")
            result[f"{namespace}:{name}"] = fn
    if not result:
        raise ValueError("no rivals were declared")
    return result


def context_predictions(demos):
    freq = Counter(demos)
    first_mode = max(demos, key=lambda q: freq[q])
    missing = [q for q in range(1, 5) if not freq[q]]
    low_once = [q for q in (1, 2, 3) if freq[q] == 1]
    low_min = min(freq[q] for q in (1, 2, 3))
    rare_low = [q for q in (1, 2, 3) if freq[q] == low_min]
    observed_low_order = list(dict.fromkeys(q for q in demos if q != 4))
    last_low = next((q for q in reversed(demos) if q != 4), None)
    next_low = None
    if len(observed_low_order) == 3 and last_low is not None:
        next_low = observed_low_order[(observed_low_order.index(last_low) + 1) % 3]
    return {
        **{f"copy_demo_{i + 1}": q for i, q in enumerate(demos)},
        "modal_first_tie": first_mode,
        "modal_lowest_q_tie": min(freq, key=lambda q: (-freq[q], q)),
        "only_missing_q_else_abstain": missing[0] if len(missing) == 1 else None,
        "seven_slot_histogram_complement": low_once[0] if low_once else 4,
        "rarest_low_q_else_q4_on_tie": rare_low[0] if len(rare_low) == 1 else 4,
        "least_seen_q_lowest_tie": min(range(1, 5), key=lambda q: (freq[q], q)),
        "follow_first_observed_low_cycle": next_low,
    }


def add_context(stats, demos, query):
    for name, prediction in context_predictions(demos).items():
        cell = stats.setdefault(name, Counter())
        cell["episodes"] += 1
        cell["predicted"] += prediction is not None
        cell["correct"] += prediction == query


def format_context(stats):
    return {name: {
        **dict(cell),
        "accuracy_all_episodes": cell["correct"] / cell["episodes"],
        "accuracy_when_predicted": cell["correct"] / cell["predicted"] if cell["predicted"] else None,
    } for name, cell in sorted(stats.items())}


def status(fits, held):
    if all(fit for i, fit in enumerate(fits) if i != held):
        return "survived_all" if fits[held] else "ambiguous"
    return "refuted"


def rejected_policy_report():
    policies = {
        "baseline_period4_with_default_three_demos": ([1, 2, 3, 4], 3),
        "rejected_period4_with_four_demos": ([1, 2, 3, 4], 4),
        "rejected_fixed_seven_pair_histogram": ([1, 2, 3, 1, 2, 3, 4], 6),
    }
    output = {}
    for name, (buckets, n_train) in policies.items():
        contexts = {}
        for start in range(len(buckets)):
            q = [buckets[(start + i) % len(buckets)] for i in range(n_train + 1)]
            add_context(contexts, q[:-1], q[-1])
        output[name] = {"period_buckets": buckets, "n_train": n_train,
                        "production_lessons": len(buckets), "context_only": format_context(contexts)}
    counts = [6, 12, 10, 16, 14, 4, 7, 8, 11, 17, 15, 5, 6, 13, 10, 18, 14, 9, 7, 19]
    rejected = {name: Counter() for name in ("q1_fill_order", "q2_fill_order")}
    for start in range(20):
        q = [counts[(start + i) % 20] // 4 for i in range(5)]
        for name, bad_q in (("q1_fill_order", 1), ("q2_fill_order", 2)):
            fits = [value != bad_q for value in q]
            rejected[name]["production_" + status(fits, 4)] += 1
            for held in range(5):
                rejected[name]["rotation_" + status(fits, held)] += 1
    output["rejected_twenty_count_four_demo_schedule"] = {
        "counts": counts, "production_lessons": 20, "single_holdouts_including_production": 100,
        "rivals": {name: dict(result) for name, result in rejected.items()},
    }
    return output


def run_probe(seeds=20, bands=("medium",)):
    root, source, source_hash, module = load_generator()
    pairs = canonical_pairs(TASK_ID, root=root)
    rivals = declared_rivals(module)
    calibration = [independent_output(pair["input"]) == pair["output"] for pair in pairs]
    if not all(calibration):
        raise AssertionError("literal glyph oracle disagrees with a canonical label")
    fits = {name: {"matches": sum(fn([row[:] for row in p["input"]]) == p["output"] for p in pairs),
                   "labeled_pairs": len(pairs)} for name, fn in rivals.items()}
    canonical_claims_valid = all(item["matches"] == len(pairs) for name, item in fits.items()
                                 if name.startswith("CANONICAL_SHORTCUTS:"))
    n_train = module.EXAMPLES_NEEDED
    window_size = n_train + 1
    rival_stats = {name: Counter() for name in rivals}
    context_production, context_rotations = {}, {}
    counts, profiles = Counter(), Counter()
    seed_reports = []
    violations, first_ambiguities = [], {}
    min_bucket_support = {q: window_size for q in (1, 2, 3)}
    min_rounding_support = window_size
    production_lessons = rotations = generated_inputs = 0
    for band in bands:
        for seed in range(seeds):
            entries, phase, direction = module._schedule(seed)
            period = len(entries)
            samples = []
            for index in range(period + n_train):
                grid = module.generate(seed, index, difficulty=band)
                errors = module.self_check(grid, difficulty=band)
                if errors:
                    violations.append({"kind": "self_check", "seed": seed, "index": index,
                                       "difficulty": band, "errors": errors})
                count = cyan_count(grid)
                output = independent_output(grid)
                profile = module.schedule_profile(seed, index, difficulty=band)
                if profile not in module.SCHEDULE_PROFILES:
                    violations.append({"kind": "undeclared_profile", "profile": profile})
                samples.append({"n": count, "q": count // 4,
                                "fits": {name: fn([row[:] for row in grid]) == output for name, fn in rivals.items()}})
                generated_inputs += 1
                if index < period:
                    counts[count] += 1
                    profiles[profile] += 1
            per_seed_context = {}
            for start in range(period):
                window = samples[start:start + window_size]
                q = [sample["q"] for sample in window]
                bucket_counts = Counter(q)
                rounding = sum(sample["n"] < 16 and sample["n"] % 4 >= 2 for sample in window)
                for bucket in (1, 2, 3):
                    min_bucket_support[bucket] = min(min_bucket_support[bucket], bucket_counts[bucket])
                min_rounding_support = min(min_rounding_support, rounding)
                if min(bucket_counts[bucket] for bucket in (1, 2, 3)) < 2 or rounding < 2:
                    violations.append({"kind": "insufficient_guard_examples", "seed": seed,
                                       "start": start, "difficulty": band,
                                       "counts": [sample["n"] for sample in window]})
                add_context(context_production, q[:-1], q[-1])
                add_context(per_seed_context, q[:-1], q[-1])
                production_lessons += 1
                for held in range(window_size):
                    add_context(context_rotations, q[:held] + q[held + 1:], q[held])
                    rotations += 1
                for name in rivals:
                    matched = [sample["fits"][name] for sample in window]
                    rival_stats[name]["production_" + status(matched, n_train)] += 1
                    for held in range(window_size):
                        result = status(matched, held)
                        rival_stats[name]["rotation_" + result] += 1
                        if result == "ambiguous":
                            first_ambiguities.setdefault(name, {
                                "seed": seed, "difficulty": band, "start": start,
                                "held_out": held, "counts": [sample["n"] for sample in window],
                            })
            seed_reports.append({"seed": seed, "difficulty": band, "cycle_length": period,
                                 "phase": phase, "direction": direction,
                                 "production_context": format_context(per_seed_context)})
    live_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    all_counts_reached = set(counts) == set(range(4, 20))
    report = {
        "schema": "cyan_count_curriculum_probe_v1", "task_id": TASK_ID,
        "generator_version": module.VERSION, "generator_sha256": source_hash,
        "live_source_matches_checked_bytes": source_hash == live_hash,
        "rule_hash_declared_by_generator": module.RULE_HASH,
        "oracle": "Four independent literal glyphs, selected by observed count(8)//4; no generated Racket labels executed by this probe.",
        "canonical_calibration": {"labeled_records": len(pairs), "matches": sum(calibration),
                                  "unique_pairs": len({json.dumps([p['input'], p['output']]) for p in pairs})},
        "canonical_rival_fit": fits, "all_declared_canonical_shortcuts_fit": canonical_claims_valid,
        "population": {"seeds": list(range(seeds)), "bands": list(bands), "n_train": n_train,
                       "n_query": 1, "start_policy": "Every actual cycle start for every seed and band; generate through the final window without recycling input arrays.",
                       "lesson_source": "Raw consecutive generator draws; the legacy production_* field names describe the final-position holdout of these raw windows.",
                       "materializer_applied": False,
                       "filters_applied": [],
                       "generated_inputs": generated_inputs, "production_lessons": production_lessons,
                       "single_holdouts_including_production": rotations,
                       "rotation_order": "Remove each query pair once; preserve all remaining demonstration positions in their original order."},
        "counts_in_first_cycles": dict(sorted(counts.items())),
        "all_counts_4_through_19_observed": all_counts_reached,
        "profiles_in_first_cycles": dict(sorted(profiles.items())),
        "minimum_original_window_support": {"buckets": min_bucket_support, "uncapped_rounding_counterexamples": min_rounding_support},
        "rival_scores": {name: dict(result) for name, result in rival_stats.items()},
        "first_ambiguities": first_ambiguities, "violations": violations[:20],
        "violation_count": len(violations), "production_context_only": format_context(context_production),
        "rotation_context_only": format_context(context_rotations),
        "per_seed": seed_reports, "rejected_alternatives": rejected_policy_report(),
        "limits": [
            "Finite named rivals and explicit context predictors do not prove universal identifiability.",
            "This probe applies neither duplicate removal nor identity filtering. Its raw-window scores must not be presented as accepted materializer-lesson scores.",
            "Every observed seed cycle is exhausted, but only the listed seeds and bands are measured.",
            "The canonical set has only counts 12 and 16; counts 4..11 and 17..19 and nonzero remainders are deliberate rule-supported extrapolations.",
            "Count-all-nonzero is answer-equivalent on the supported {0,8} domain; no color-decoy refutation is claimed.",
            "A fixed 6x6 crop is canonically compatible but is not a guaranteed-refuted curriculum rival; no universal crop-shortcut coverage is claimed.",
        ],
    }
    report["status"] = "PASS" if not violations and not first_ambiguities and canonical_claims_valid and all_counts_reached and source_hash == live_hash else "FAIL"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--bands", nargs="+", default=["medium"], choices=("easy", "medium", "hard"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_probe(args.seeds, tuple(args.bands))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    context = report["production_context_only"]
    print(json.dumps({"status": report["status"], "generator_sha256": report["generator_sha256"],
                      "population": report["population"], "minimum_support": report["minimum_original_window_support"],
                      "all_counts": report["all_counts_4_through_19_observed"],
                      "declared_rivals": len(report["rival_scores"]),
                      "ambiguities": len(report["first_ambiguities"]),
                      "context_accuracy": {name: item["accuracy_all_episodes"] for name, item in context.items()},
                      "report": str(args.out)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
