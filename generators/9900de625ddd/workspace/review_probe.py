#!/usr/bin/env python3
"""Source-bound lesson review using the public Catalog.generate/apply APIs.

Run from the packet root, after the generator is final::

    python3 run_with_racket.py python3 generators/9900de625ddd/workspace/review_probe.py \
        --out ../checks/probe-final --lessons 100 --cycle-lessons 20

No Python implementation of the target rule supplies expected outputs. The
selected canonical Racket rule labels both the canonical inputs and generated
episodes. Rival rules are read dynamically from the selected generator.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "9900de625ddd"
BANDS = ("easy", "medium", "hard")
DECLARATIONS = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")


def digest(value: Any) -> str:
    """Hash a compact JSON representation, including nested grid lists."""
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                     sort_keys=True).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def selected_canonical(repo: Path) -> tuple[dict, str]:
    path = repo / "shared/data/canonical/puzzles.jsonl"
    matches = []
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append((row, hashlib.sha256(line.encode()).hexdigest()))
    if len(matches) != 1:
        raise ValueError(f"Expected one selected canonical row; found {len(matches)}")
    return matches[0]


def load_selected_generator(repo: Path):
    # These are the public portable helper package and the public Catalog API.
    # No private runner helpers are imported or called by this probe.
    for source in (repo / "src", repo / "shared/runtime"):
        if str(source) not in sys.path:
            sys.path.insert(0, str(source))
    path = repo / "generators" / TASK_ID / "generator.py"
    captured_source = path.read_bytes()
    spec = importlib.util.spec_from_file_location("selected_generator_review", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    # Compile the exact hashed bytes, avoiding stale .pyc files and the race
    # between importing a module and separately reading its source identity.
    exec(compile(captured_source, str(path), "exec"), module.__dict__)
    module.__review_source_sha256 = hashlib.sha256(captured_source).hexdigest()
    return module


def declared_rules(module) -> dict[str, dict]:
    """Preserve both declarations, including differing same-name callables."""
    result = {}
    for group in DECLARATIONS:
        mapping = getattr(module, group, None)
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError(f"{group} must be a nonempty dictionary")
        for name, function in sorted(mapping.items()):
            if not isinstance(name, str) or not name or not callable(function):
                raise ValueError(f"Invalid {group} declaration: {name!r}")
            key = f"{group}.{name}"
            result[key] = {"declaration": group, "name": name, "function": function}
    return result


def call_rule(function, pair: dict) -> dict:
    """Keep a real disagreement separate from exceptions and input mutation."""
    argument = deepcopy(pair["input"])
    result = {"agrees": None, "output": None, "error": None, "mutated_input": False}
    try:
        output = function(argument)
        if hasattr(output, "tolist"):
            output = output.tolist()
        if isinstance(output, tuple):
            output = [list(row) for row in output]
        if (not isinstance(output, list) or not output or
                any(not isinstance(row, list) or not row for row in output) or
                len({len(row) for row in output}) != 1 or
                any(type(value) is not int or not 0 <= value <= 9
                    for row in output for value in row)):
            raise ValueError("rival returned a malformed grid")
        result["output"] = output
        result["agrees"] = output == pair["output"]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["mutated_input"] = argument != pair["input"]
    if result["mutated_input"]:
        result["agrees"] = None
        result["error"] = result["error"] or "rival mutated its input"
    return result


def canonical_fits(rules: dict, pairs: list[dict]) -> dict:
    result = {}
    for key, declaration in rules.items():
        evaluations = [call_rule(declaration["function"], pair) for pair in pairs]
        result[key] = {
            "declaration": declaration["declaration"], "name": declaration["name"],
            "usable_pairs": len(pairs),
            "matching_pairs": sum(item["agrees"] is True for item in evaluations),
            "disagreement_pairs": [index for index, item in enumerate(evaluations)
                                   if item["agrees"] is False],
            "exceptions": [{"pair_index": index, "error": item["error"]}
                           for index, item in enumerate(evaluations) if item["error"]],
            "fits_every_usable_pair": bool(pairs) and all(
                item["agrees"] is True for item in evaluations),
        }
    return result


def lesson_status(evaluations: list[dict], n_train: int) -> str:
    demos, queries = evaluations[:n_train], evaluations[n_train:]
    if any(item["agrees"] is False for item in demos):
        return "refuted_by_demo"
    if any(item["error"] for item in demos):
        return "demo_error"
    if any(item["error"] for item in queries):
        return "query_error"
    if any(item["agrees"] is False for item in queries):
        return "query_discriminates"
    return "survived_all"


def assess_lesson(module, rules: dict, episode: dict, band: str, run_name: str,
                  witnesses: dict) -> dict:
    demos, queries = episode["train"], episode["test"]
    pairs = demos + queries
    sample_indices = episode["sample_indices"]
    if len(sample_indices) != len(pairs):
        raise ValueError("Public episode sample_indices do not match pair count")
    record = {
        "run": run_name, "band": band, "seed": episode["seed"],
        "episode_index": episode["episode_index"],
        "requested_sample_index": episode["sample_index"],
        "accepted_sample_indices": sample_indices,
        "rejections": episode["rejections"],
        "n_train": len(demos), "n_test": len(queries),
        "generator_sha256": episode["provenance"]["generator_sha256"],
        "catalog_rule_hash": episode["provenance"]["catalog_rule_hash"],
        "executed_rule_hash": episode["executed_rule_hash"],
        "input_sha256": [digest(pair["input"]) for pair in pairs],
        "output_sha256": [digest(pair["output"]) for pair in pairs],
        "rivals": {}, "errors": [], "schedule_profile_errors": [],
    }
    profile = getattr(module, "schedule_profile", None)
    if callable(profile):
        record["schedule_profiles"] = []
        for index in sample_indices:
            try:
                record["schedule_profiles"].append(profile(episode["seed"], index, difficulty=band))
            except Exception as exc:
                record["schedule_profiles"].append(None)
                record["schedule_profile_errors"].append(
                    {"sample_index": index, "error": f"{type(exc).__name__}: {exc}"})
    for key, declaration in rules.items():
        evaluations = [call_rule(declaration["function"], pair) for pair in pairs]
        status = lesson_status(evaluations, len(demos))
        disagreeing = [index for index, item in enumerate(evaluations)
                       if item["agrees"] is False]
        failures = [{"pair_index": index, "sample_index": sample_indices[index],
                     "error": item["error"]}
                    for index, item in enumerate(evaluations) if item["error"]]
        record["rivals"][key] = {"status": status, "disagreement_pair_indices": disagreeing,
                                  "exceptions": failures}
        for failure in failures:
            record["errors"].append({"rival": key, **failure})
        if disagreeing and key not in witnesses:
            index = disagreeing[0]
            witnesses[key] = {
                "band": band, "run": run_name, "seed": episode["seed"],
                "sample_index": sample_indices[index],
                "split": "train" if index < len(demos) else "test",
                "input": pairs[index]["input"], "racket_output": pairs[index]["output"],
                "rival_output": evaluations[index]["output"],
                "input_sha256": record["input_sha256"][index],
                "output_sha256": record["output_sha256"][index],
                "provenance": episode["provenance"],
            }
    hook = getattr(module, "lesson_identifiable", None)
    if not callable(hook):
        record["hook"] = {"reasons": None, "error": "missing lesson_identifiable"}
    else:
        argument_demos, argument_query = deepcopy(demos), deepcopy(queries[0])
        try:
            reasons = hook(argument_demos, argument_query)
            if not isinstance(reasons, list) or any(not isinstance(item, str) for item in reasons):
                raise TypeError("lesson_identifiable must return a list of reason strings")
            if argument_demos != demos or argument_query != queries[0]:
                raise ValueError("lesson_identifiable mutated its input")
            record["hook"] = {"reasons": reasons, "error": None}
        except Exception as exc:
            record["hook"] = {"reasons": None, "error": f"{type(exc).__name__}: {exc}"}
    harmful = [key for key, item in record["rivals"].items()
               if item["status"] == "query_discriminates"]
    survivors = [key for key, item in record["rivals"].items()
                 if item["status"] in {"survived_all", "query_discriminates", "query_error"}]
    record["demo_survivors"] = survivors
    record["query_discriminating_survivors"] = harmful
    record["hook_claims_identifiable_but_query_rival_survives"] = (
        record["hook"]["reasons"] == [] and bool(harmful))
    record["hook_rejects_without_query_discriminating_declared_rival"] = (
        bool(record["hook"]["reasons"]) and not harmful)
    return record


def summarize(records: list[dict]) -> dict:
    input_hashes = [value for item in records for value in item["input_sha256"]]
    demo_hashes = [value for item in records
                   for value in item["input_sha256"][:item["n_train"]]]
    query_hashes = [value for item in records
                    for value in item["input_sha256"][item["n_train"]:]]
    accepted = {(item["band"], item["seed"], index) for item in records
                for index in item["accepted_sample_indices"]}
    rejected = {(item["band"], item["seed"], rejection["sample_index"])
                for item in records for rejection in item["rejections"]}
    rival_keys = sorted({key for item in records for key in item["rivals"]})
    result = {
        "complete_lessons": len(records), "pair_exposures": len(input_hashes),
        "demonstration_pair_exposures": len(demo_hashes), "query_pair_exposures": len(query_hashes),
        "distinct_inputs": len(set(input_hashes)), "distinct_demo_inputs": len(set(demo_hashes)),
        "distinct_query_inputs": len(set(query_hashes)),
        "unique_accepted_draw_coordinates": len(accepted),
        "unique_attempted_draw_coordinates": len(accepted | rejected),
        "accepted_draw_exposures": len(input_hashes),
        "rejected_draw_exposures": sum(len(item["rejections"]) for item in records),
        "seed_min": min((item["seed"] for item in records), default=None),
        "seed_max": max((item["seed"] for item in records), default=None),
        "accepted_sample_index_min": min((coord[2] for coord in accepted), default=None),
        "accepted_sample_index_max": max((coord[2] for coord in accepted), default=None),
        "lessons_with_all_declared_rivals_refuted_by_demos": sum(
            all(value["status"] == "refuted_by_demo" for value in item["rivals"].values())
            for item in records),
        "lessons_with_query_discriminating_survivor": sum(
            bool(item["query_discriminating_survivors"]) for item in records),
        "rival_exception_exposures": sum(len(item["errors"]) for item in records),
        "schedule_profile_exception_exposures": sum(len(item["schedule_profile_errors"]) for item in records),
        "hook_errors": sum(item["hook"]["error"] is not None for item in records),
        "hook_identifiable": sum(item["hook"]["reasons"] == [] for item in records),
        "hook_optimistic_disagreements": sum(
            item["hook_claims_identifiable_but_query_rival_survives"] for item in records),
        "hook_conservative_rejections": sum(
            item["hook_rejects_without_query_discriminating_declared_rival"] for item in records),
        "accepted_schedule_profile_exposures": dict(sorted(Counter(
            str(profile) for item in records for profile in item.get("schedule_profiles", [])
            if profile is not None).items())),
        "demonstration_schedule_profile_exposures": dict(sorted(Counter(
            str(profile) for item in records
            for profile in item.get("schedule_profiles", [])[:item["n_train"]]
            if profile is not None).items())),
        "rivals": {},
    }
    for key in rival_keys:
        statuses = Counter(item["rivals"][key]["status"] for item in records)
        distinct_disagreements = {item["input_sha256"][index] for item in records
                                  for index in item["rivals"][key]["disagreement_pair_indices"]}
        result["rivals"][key] = {
            "lesson_status_counts": dict(sorted(statuses.items())),
            "genuine_disagreement_pair_exposures": sum(
                len(item["rivals"][key]["disagreement_pair_indices"]) for item in records),
            "distinct_disagreement_inputs": len(distinct_disagreements),
            "exception_exposures": sum(len(item["rivals"][key]["exceptions"]) for item in records),
        }
    return result


def source_identity(repo: Path, module, row: dict, row_hash: str) -> dict:
    paths = {"generator": repo / "generators" / TASK_ID / "generator.py",
             "probe": Path(__file__).resolve(),
             "catalog_api": repo / "src/arcpuzzles/catalog.py",
             "runtime_api": repo / "src/arcpuzzles/runtime.py",
             "worker": repo / "src/arcpuzzles/worker.py",
             "runner": repo / "shared/runtime/puzzle_generators/runner.py"}
    return {
        "generator_version": getattr(module, "VERSION", None),
        "loaded_generator_sha256": module.__review_source_sha256,
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "file_sha256": {name: file_digest(path) for name, path in paths.items()},
        "selected_canonical_jsonl_row_sha256": row_hash,
        "canonical_program_exact_text_sha256": hashlib.sha256(
            row["program_solution"].encode()).hexdigest(),
        "canonical_program_whitespace_normalized_sha256": hashlib.sha256(
            " ".join(row["program_solution"].split()).encode()).hexdigest(),
    }


def run(args) -> tuple[dict, int]:
    repo = args.repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("report.json", "episodes.jsonl")):
        raise FileExistsError("Use a new evidence directory; earlier runs are retained")
    module = load_selected_generator(repo)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import GenerationFailure

    rules = declared_rules(module)
    canonical, canonical_row_hash = selected_canonical(repo)
    source = source_identity(repo, module, canonical, canonical_row_hash)
    expected_hash = source["file_sha256"]["generator"]
    if source["loaded_generator_sha256"] != expected_hash:
        raise ValueError("Generator source changed after captured-byte module loading")
    if args.expected_generator_sha256 and args.expected_generator_sha256 != expected_hash:
        raise ValueError("Current generator differs from --expected-generator-sha256")
    catalog = Catalog(repo)
    description = catalog.describe(TASK_ID)
    if description["generator_sha256"] != expected_hash:
        raise ValueError("Catalog generator identity differs from selected source bytes")
    canonical_pairs = [pair for split in ("train", "test") for pair in canonical.get(split, [])
                       if pair.get("input") is not None and pair.get("output") is not None]
    if len(canonical_pairs) != 5:
        raise ValueError(f"Expected 5 usable canonical pairs; found {len(canonical_pairs)}")
    print("Labeling five canonical inputs with public Catalog.apply", flush=True)
    canonical_receipt = catalog.apply(TASK_ID, [pair["input"] for pair in canonical_pairs],
                                      reference="canonical", timeout=args.timeout)
    write_json(out / "canonical-apply.json", canonical_receipt)
    failures = []
    if (canonical_receipt["generator_sha256"] != expected_hash or
            not canonical_receipt["rule_hash_matches_catalog"]):
        failures.append("canonical apply authority/source identity mismatch")
    canonical_label_checks = []
    for index, (pair, item) in enumerate(zip(canonical_pairs, canonical_receipt["results"], strict=True)):
        matched = item["error"] is None and item["output"] == pair["output"]
        canonical_label_checks.append({"pair_index": index, "matches_stored_output": matched,
                                       "error": item["error"], "input_sha256": item["input_sha256"],
                                       "output_sha256": item["output_sha256"]})
        if not matched:
            failures.append(f"canonical pair {index}: authoritative label mismatch or exception")
    fits = canonical_fits(rules, canonical_pairs)
    for key, item in fits.items():
        if item["declaration"] == "CANONICAL_SHORTCUTS" and not item["fits_every_usable_pair"]:
            failures.append(f"{key}: claimed canonical shortcut fails a usable pair")

    period = getattr(module, "SCHEDULE_PERIOD", None)
    declared_profiles = getattr(module, "SCHEDULE_PROFILES", None)
    profile = getattr(module, "schedule_profile", None)
    schedule = {"declared_period": period, "declared_profiles": declared_profiles,
                "periodicity_comparisons": 0, "periodicity_errors": [], "cyclic_starts_tested": []}
    if period is not None and (type(period) is not int or period < 1):
        raise ValueError("SCHEDULE_PERIOD must be a positive integer")
    if period is not None and period <= args.max_cycle_period and callable(profile):
        starts = list(range(period))
        for band in BANDS:
            for seed in range(args.seed_start, args.seed_start + args.lessons):
                for index in range(args.sample_index, args.sample_index + 2 * period):
                    try:
                        first = profile(seed, index, difficulty=band)
                        repeated = profile(seed, index + period, difficulty=band)
                        schedule["periodicity_comparisons"] += 1
                        if first != repeated:
                            schedule["periodicity_errors"].append(
                                {"band": band, "seed": seed, "sample_index": index,
                                 "first": first, "after_period": repeated})
                    except Exception as exc:
                        schedule["periodicity_errors"].append(
                            {"band": band, "seed": seed, "sample_index": index,
                             "error": f"{type(exc).__name__}: {exc}"})
    else:
        starts = [0]
        schedule["cyclic_sweep_limitation"] = (
            "No small declared period and callable schedule; only requested base start measured")
    if schedule["periodicity_errors"]:
        failures.append("declared schedule periodicity mismatches or exceptions")
    witnesses, records, runs = {}, [], []
    with (out / "episodes.jsonl").open("w") as stream:
        for offset in starts:
            start = args.sample_index + offset
            count = args.lessons if offset == 0 else args.cycle_lessons
            schedule["cyclic_starts_tested"].append(start)
            for band in BANDS:
                name = f"{band}-start-{start}"
                options = {"count": count, "seed": args.seed_start, "difficulty": band,
                           "n_train": args.n_train, "n_test": 1, "sample_index": start,
                           "allow_unapproved": True, "reference": "canonical", "timeout": args.timeout}
                print(f"Catalog.generate: {name}, {count} complete lessons requested", flush=True)
                materialize_error = None
                try:
                    episodes = catalog.generate(TASK_ID, **options)
                except GenerationFailure as exc:
                    episodes = exc.partial_episodes
                    materialize_error = {"type": type(exc).__name__, "message": str(exc), "run": exc.run}
                    failures.append(f"{name}: only {len(episodes)}/{count} episodes completed")
                if len(episodes) != count and materialize_error is None:
                    failures.append(f"{name}: public API returned {len(episodes)}/{count} episodes")
                run_records = []
                for episode in episodes:
                    if (episode["provenance"]["generator_sha256"] != expected_hash or
                            episode["executed_rule_hash"] != description["rule_hash"] or
                            episode["provenance"]["catalog_rule_hash"] != description["rule_hash"]):
                        raise ValueError(f"{name}: generated episode identity mismatch")
                    if len(episode["train"]) != args.n_train or len(episode["test"]) != 1:
                        raise ValueError(f"{name}: incomplete public episode")
                    record = assess_lesson(module, rules, episode, band, name, witnesses)
                    run_records.append(record)
                    records.append(record)
                    stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                    stream.flush()
                runs.append({"name": name, "api": "Catalog.generate", "options": options,
                             "requested": count, "materialization_error": materialize_error,
                             "summary": summarize(run_records)})
                print(f"Completed {name}: {len(run_records)} lessons", flush=True)
    totals = summarize(records)
    for band in BANDS:
        base_count = sum(item["run"] == f"{band}-start-{args.sample_index}" for item in records)
        if base_count < args.lessons:
            failures.append(f"{band}: {base_count}/{args.lessons} base lessons complete")
    for field in ("rival_exception_exposures", "schedule_profile_exception_exposures",
                  "hook_errors", "hook_optimistic_disagreements",
                  "lessons_with_query_discriminating_survivor"):
        if totals[field]:
            failures.append(f"{field}: {totals[field]}")
    for key, item in fits.items():
        if item["declaration"] == "CANONICAL_SHORTCUTS" and key not in witnesses:
            failures.append(f"{key}: no genuine generated disagreement")
    unchanged = source_identity(repo, module, *selected_canonical(repo)) == source
    if not unchanged:
        failures.append("selected source or probe changed while measuring")
    write_json(out / "witnesses.json", {"source": source, "witnesses": witnesses})
    report = {
        "schema": "9900de625ddd-independent-lesson-probe-v1", "task_id": TASK_ID,
        "phase": args.phase, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "source": source, "source_unchanged_during_measurement": unchanged,
        "catalog_rule_hash": description["rule_hash"],
        "declared_rules": {key: {k: value for k, value in item.items() if k != "function"}
                           for key, item in rules.items()},
        "canonical": {"usable_pairs": len(canonical_pairs), "train_pairs": len(canonical["train"]),
                      "test_pairs": len(canonical["test"]), "label_checks": canonical_label_checks,
                      "rival_fit": fits},
        "sampler": {
            "api": "arcpuzzles.Catalog.generate", "n_train": args.n_train, "n_test": 1,
            "seed_policy": "API seed = seed_start + episode_index within each batch",
            "sample_policy": "API tries sequential indices from sample_index; invalid or duplicate pairs are rejected, with at most5*(n_train+n_test) attempts per episode",
            "base_lessons_per_band": args.lessons, "extra_lessons_per_cyclic_start_per_band": args.cycle_lessons,
            "overrides": {}, "same_seed_reused_across_bands_and_cyclic_starts": True,
            "counter_meaning": "Pair exposures include reused inputs in overlapping lesson windows; distinct_inputs deduplicates grid content globally within the summarized population. Draw coordinates include band, seed and accepted sample_index.",
        },
        "schedule": schedule, "runs": runs, "totals": totals,
        "per_band": {band: summarize([item for item in records if item["band"] == band]) for band in BANDS},
        "limitations": [
            "Finite declared competitors and finite source-bound samples do not establish universal rule induction.",
            "The guarantee measured here concerns default difficulty draws; exact overrides are not sampled.",
            "Nonzero individual disagreement frequency does not establish demonstration-level teaching; complete-lesson status is scored separately.",
            "A rival that survives demos but agrees with the query is reported as survived_all; it is not a query-answer disagreement.",
            "Hook rejections without a query-discriminating declared rival are reported as conservative, not automatically treated as a bug.",
            f"Measured {len(starts)} starting offsets for declared period {period!r}; see cyclic_sweep_limitation if present. Periodicity comparisons and start coverage use the recorded finite seed ranges.",
        ],
        "failures": failures, "verdict": "PASS" if not failures else "FAIL",
        "evidence": {name: {"sha256": file_digest(out / name), "bytes": (out / name).stat().st_size}
                     for name in ("canonical-apply.json", "episodes.jsonl", "witnesses.json")},
    }
    write_json(out / "report.json", report)
    write_json(out / "report.sha256.json", {"report.json": file_digest(out / "report.json")})
    print(json.dumps({"verdict": report["verdict"], "complete_lessons": totals["complete_lessons"],
                      "distinct_inputs": totals["distinct_inputs"], "failures": failures,
                      "report": str(out / "report.json")}, sort_keys=True), flush=True)
    return report, 0 if not failures else 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", default="final")
    parser.add_argument("--lessons", type=int, default=100)
    parser.add_argument("--cycle-lessons", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--max-cycle-period", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--expected-generator-sha256")
    args = parser.parse_args(argv)
    if args.lessons < 1 or args.cycle_lessons < 1 or args.n_train < 1 or args.sample_index < 0:
        parser.error("positive lesson/demo counts and a nonnegative sample index are required")
    return args


if __name__ == "__main__":
    raise SystemExit(run(parse_args())[1])
