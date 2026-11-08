#!/usr/bin/env python3
"""Exhaustive profile-level audit of the ordered main-diagonal curriculum.

Run from the packet through run_with_racket.py, for its portable import paths::

    python3 run_with_racket.py python3 \
      generators/57488f2a7c15/workspace/schedule_contract.py \
      --out ../checks/schedule-profile-contract.json

Despite that wrapper, this script never generates a grid, reads canonical
answers, or executes Racket. It checks schedule_profile only. Realized input
features are checked separately by test_schedule_profiles.py; authoritative
labels and actual accepted sample indices belong to the production census.

Each of the six context-conditioned rivals preserves every original cell and
always completes lower sources. It conditionally omits completion of upper
sources. All five canonical inputs have only lower incomplete sources, so
these rivals fit their canonical labels. That premise was checked during the
authoring review; the script does not remeasure canonical label agreement.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "57488f2a7c15"
PERIOD = 18
CONTEXTS = ("shared", "unique", "none")
TRIANGLES = ("lower", "mixed", "upper")
BANDS = ("easy", "medium", "hard")
RIVAL_NAMES = tuple(
    f"{operation}_{context}"
    for operation in ("lower_only_in", "full_only_in")
    for context in CONTEXTS
)
BOUND = {
    "scope": "all cyclic starts and all single-query holdouts; finite context rivals",
    "claim": "Six-pair universal rotation safety is incompatible with all nine joint profiles.",
    "argument": [
        "For each context, lower_only_in_CONTEXT disagrees precisely on an incomplete upper source in that context.",
        "A six-pair window containing exactly one such witness becomes ambiguous when that witness is the query.",
        "In a cyclic schedule with positive support, its six-window witness counts cannot reach zero: moving from positive counts to zero changes by at most one and would first pass through the forbidden count one.",
        "Therefore every six-pair window must contain at least two upper-source witnesses in each of the three disjoint contexts.",
        "Those six witnesses occupy every position, leaving no lower-only profile; full joint support, including canonical lower-only inputs, is impossible.",
    ],
    "consequence": "Use five ordered demonstrations and report arbitrary query rotations as diagnostic, or change the lesson-size/support contract.",
    "limitation": "This concerns the named rivals and every cyclic window, not every imaginable inference rule or arbitrary non-cyclic lesson assembly.",
}


def split_profile(profile):
    if not isinstance(profile, str):
        raise ValueError(f"Expected triangle:context string, got {profile!r}")
    fields = profile.split(":")
    if len(fields) != 2 or fields[0] not in TRIANGLES or fields[1] not in CONTEXTS:
        raise ValueError(f"Unknown semantic profile {profile!r}")
    return tuple(fields)


def witness_flags(profile):
    triangle, context = split_profile(profile)
    upper = triangle != "lower"
    return {
        "upper_incomplete_source": upper,
        "lower_incomplete_source": triangle != "upper",
        "shared_diagonal_source_color": context == "shared",
        "unique_diagonal_color": context == "unique",
        "no_diagonal": context == "none",
        "upper_shared": upper and context == "shared",
        "upper_unique": upper and context == "unique",
        "upper_none": upper and context == "none",
    }


def rival_disagrees(rival, profile):
    """Symbolic disagreement with lawful completion, not a grid prediction."""
    triangle, context = split_profile(profile)
    if triangle == "lower":
        return False
    if rival.startswith("lower_only_in_"):
        return context == rival.removeprefix("lower_only_in_")
    if rival.startswith("full_only_in_"):
        return context != rival.removeprefix("full_only_in_")
    raise ValueError(f"Unknown profile rival {rival!r}")


def score_context_lessons(profiles, n_demos):
    """Enumerate every cyclic start and every query holdout symbolically."""
    if not profiles or type(n_demos) is not int or n_demos < 1:
        raise ValueError("Need nonempty profiles and a positive demo count")
    for profile in profiles:
        split_profile(profile)
    period = len(profiles)
    witness_names = tuple(witness_flags(profiles[0]))
    production_minima = {name: n_demos for name in witness_names}
    rotation_minima = dict(production_minima)
    production_counts = {name: 0 for name in RIVAL_NAMES}
    rotation_counts = dict(production_counts)
    first_production = {}
    first_rotation = {}
    windows = []
    for start in range(period):
        window = [profiles[(start + offset) % period] for offset in range(n_demos + 1)]
        flags = [witness_flags(profile) for profile in window]
        demo_counts = {name: sum(row[name] for row in flags[:n_demos]) for name in witness_names}
        production_minima = {name: min(production_minima[name], demo_counts[name]) for name in witness_names}
        windows.append({"start": start, "demonstrations": window[:n_demos],
                        "query": window[n_demos], "demo_witness_counts": demo_counts})
        for query_index in range(n_demos + 1):
            demo_indices = [i for i in range(n_demos + 1) if i != query_index]
            for name in witness_names:
                rotation_minima[name] = min(rotation_minima[name], sum(flags[i][name] for i in demo_indices))
            for name in RIVAL_NAMES:
                ambiguous = (rival_disagrees(name, window[query_index]) and
                             not any(rival_disagrees(name, window[i]) for i in demo_indices))
                if not ambiguous:
                    continue
                witness = {"start": start, "query_index": query_index,
                           "demo_indices": demo_indices,
                           "demonstrations": [window[i] for i in demo_indices],
                           "query": window[query_index], "rival": name}
                rotation_counts[name] += 1
                first_rotation.setdefault(name, witness)
                if query_index == n_demos:
                    production_counts[name] += 1
                    first_production.setdefault(name, witness)
    return {
        "period": period,
        "n_demonstrations": n_demos,
        "starts_checked": period,
        "query_holdouts_checked": period * (n_demos + 1),
        "production_demo_witness_minima": production_minima,
        "rotation_demo_witness_minima": rotation_minima,
        "production_ambiguities": production_counts,
        "rotation_ambiguities": rotation_counts,
        "first_production_counterexamples": first_production,
        "first_rotation_counterexamples": first_rotation,
        "windows": windows,
    }


def analyze_schedule(generator, *, seed=0, difficulty=None, period=PERIOD):
    n_demos = generator.EXAMPLES_NEEDED
    profiles = [generator.schedule_profile(seed, i, difficulty=difficulty) for i in range(period)]
    second_period = [generator.schedule_profile(seed, i + period, difficulty=difficulty)
                     for i in range(period)]
    report = score_context_lessons(profiles, n_demos)
    counts = Counter(profiles)
    triangle_counts = Counter(split_profile(profile)[0] for profile in profiles)
    context_counts = Counter(split_profile(profile)[1] for profile in profiles)
    all_joint = {f"{triangle}:{context}" for triangle in TRIANGLES for context in CONTEXTS}
    independent = all(
        counts[f"{triangle}:{context}"] * period == triangle_counts[triangle] * context_counts[context]
        for triangle in TRIANGLES for context in CONTEXTS
    )
    failures = []
    if n_demos != 5:
        failures.append("This retained contract requires five ordered demonstrations.")
    if profiles != second_period:
        failures.append(f"Declared profiles did not repeat over the checked period {period}.")
    if set(counts) != all_joint:
        failures.append("Not all nine triangle/context combinations have support.")
    if not independent:
        failures.append("Triangle and diagonal-context frequencies are coupled over the period.")
    if any(value < 1 for value in report["production_demo_witness_minima"].values()):
        failures.append("At least one production window lacks a required semantic witness.")
    if any(report["production_ambiguities"].values()):
        failures.append("An identified context rival fits all demos and changes the production query.")
    report.update({
        "scope": "profile_only",
        "seed": seed,
        "difficulty": difficulty,
        "profiles": profiles,
        "joint_profile_counts": dict(sorted(counts.items())),
        "independent_joint_frequencies": independent,
        "period_repeated": profiles == second_period,
        "status": "production_profile_pass" if not failures else "production_profile_fail",
        "failures": failures,
        "rotation_status": ("diagnostic_ambiguity_found" if any(report["rotation_ambiguities"].values())
                            else "no_profile_ambiguity_found"),
    })
    return report


def rejected_period12_proposal():
    """Retain the superseded design counterexample, never label it baseline data."""
    triangles = ("lower", "mixed", "upper", "mixed")
    # The proposal's ordinary mode could be unique or none; unique is a lawful
    # concrete choice. Both are unshared and expose the same conditional flaw.
    contexts = ("shared", "shared", "unique")
    profiles = [f"{triangles[i % 4]}:{contexts[i % 3]}" for i in range(12)]
    report = score_context_lessons(profiles, 3)
    report["scope"] = "superseded_profile_proposal_not_generator_evidence"
    report["note"] = "Three-demo proposal; ordinary instantiated as unique. No generator snapshot or Racket labels were measured here."
    return report


def import_generator(source):
    spec = importlib.util.spec_from_file_location("symmetry_profile_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", help="Repeat for multiple family seeds; default 0 and 17")
    parser.add_argument("--band", choices=BANDS, action="append", help="Repeat for bands; default all three")
    parser.add_argument("--period", type=int, default=PERIOD)
    parser.add_argument("--out", type=Path, help="New JSON path; existing evidence is never overwritten")
    args = parser.parse_args()
    if args.period < 1:
        parser.error("--period must be positive")
    from reviewer_support import find_root
    root = find_root(__file__)
    candidates = (root / "generators" / TASK_ID / "generator.py",
                  root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    source = next(path for path in candidates if path.is_file())
    source_bytes = source.read_bytes()
    generator = import_generator(source)
    reports = [analyze_schedule(generator, seed=seed, difficulty=band, period=args.period)
               for seed in (args.seed or [0, 17]) for band in (args.band or list(BANDS))]
    if source.read_bytes() != source_bytes:
        raise RuntimeError("Generator source changed during the profile audit; run a fresh report")
    report = {
        "schema": "main-diagonal-profile-schedule-v1",
        "task_id": TASK_ID,
        "scope": "profile_only_not_authoritative_label_evidence",
        "generator_path": source.relative_to(root).as_posix(),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "generated_inputs_checked": 0,
        "racket_labels_checked": 0,
        "canonical_labels_checked": 0,
        "canonical_rival_fit_basis": "Authoring premise: all five canonical inputs have only lower incomplete sources. Canonical labels are not reread in this script.",
        "rivals": {name: {"semantics": ("Complete lower sources only in this context, otherwise complete all sources."
                                        if name.startswith("lower_only_in_") else
                                        "Complete all sources only in this context, otherwise complete lower sources only."),
                            "context": name.rsplit("_", 1)[1]} for name in RIVAL_NAMES},
        "status": ("production_profile_pass" if all(row["status"] == "production_profile_pass" for row in reports)
                   else "production_profile_fail"),
        "reports": reports,
        "rotation_impossibility_bound": BOUND,
        "superseded_period12_proposal": rejected_period12_proposal(),
    }
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(serialized, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
        print(json.dumps({"status": report["status"], "scope": report["scope"],
                          "out": str(args.out), "configurations": len(reports)}, sort_keys=True))
    return 0 if report["status"] == "production_profile_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
