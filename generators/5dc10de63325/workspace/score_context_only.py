#!/usr/bin/env python3
"""Score explicit output-only predictors on a complete retained lesson census.

This task-local tool recognizes the four positive cyan glyphs of 5dc10de63325.
It consumes accepted pairs and their retained labels, imports no generator, and
executes neither generation nor Racket. JSON and gzip-compressed JSON are read.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


TASK_ID = "5dc10de63325"
GLYPH_ROWS = {
    1: ("00000", "08008", "00000", "00000", "08008"),
    2: ("00000", "88088", "00000", "00000", "88088"),
    3: ("08008", "88088", "00000", "08008", "88088"),
    4: ("88088", "88088", "00000", "88088", "88088"),
}
GLYPHS = {q: [[int(v) for v in row] for row in rows] for q, rows in GLYPH_ROWS.items()}
GLYPH_IDS = {tuple(map(tuple, grid)): q for q, grid in GLYPHS.items()}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@lru_cache(maxsize=1)
def shared_validator():
    """Find the existing validator in this script's own library/runtime tree."""
    for parent in Path(__file__).resolve().parents:
        for relative in ("shared/tools/lesson_census.py", "scripts/lesson_census.py"):
            path = parent / relative
            if path.is_file():
                spec = importlib.util.spec_from_file_location("_context_only_census_validation", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if callable(getattr(module, "validate_retained_census", None)):
                    return module, path
    raise ValueError("Cannot find the shared retained-census validator in this script's tree")


def glyph_id(grid):
    if (type(grid) is not list or len(grid) != 5
            or any(type(row) is not list or len(row) != 5
                   or any(type(v) is not int for v in row) for row in grid)):
        raise ValueError("Output is not one of the four fixed cyan glyphs")
    try:
        return GLYPH_IDS[tuple(map(tuple, grid))]
    except KeyError:
        raise ValueError("Output is not one of the four fixed cyan glyphs") from None


def predictions(demos):
    """Receive demonstration output IDs only; never receive input grids."""
    freq = Counter(demos)
    missing = [q for q in range(1, 5) if not freq[q]]
    low_once = [q for q in (1, 2, 3) if freq[q] == 1]
    minimum_low = min(freq[q] for q in (1, 2, 3))
    rare_low = [q for q in (1, 2, 3) if freq[q] == minimum_low]
    order = list(dict.fromkeys(q for q in demos if q != 4))
    last_low = next((q for q in reversed(demos) if q != 4), None)
    next_low = order[(order.index(last_low) + 1) % 3] if len(order) == 3 and last_low is not None else None
    return {
        **{f"copy_demo_{i + 1}": q for i, q in enumerate(demos)},
        "modal_first_tie": max(demos, key=lambda q: freq[q]),
        "modal_lowest_q_tie": min(freq, key=lambda q: (-freq[q], q)),
        "only_missing_q_else_abstain": missing[0] if len(missing) == 1 else None,
        "seven_slot_histogram_complement": low_once[0] if low_once else 4,
        "rarest_low_q_else_q4_on_tie": rare_low[0] if len(rare_low) == 1 else 4,
        "least_seen_q_lowest_tie": min(range(1, 5), key=lambda q: (freq[q], q)),
        "follow_first_observed_low_cycle": next_low,
    }


def add_scores(target, demos, query):
    for name, prediction in predictions(demos).items():
        counts = target.setdefault(name, Counter())
        counts["episodes"] += 1
        counts["predicted"] += prediction is not None
        counts["correct"] += prediction == query


def finish_scores(raw):
    scores = {}
    for name, count in sorted(raw.items()):
        episodes, predicted, correct = count["episodes"], count["predicted"], count["correct"]
        scores[name] = {
            "episodes": episodes, "predicted": predicted, "abstained": episodes - predicted,
            "correct": correct, "wrong": predicted - correct,
            "accuracy_all_episodes": correct / episodes,
            "accuracy_when_predicted": correct / predicted if predicted else None,
        }
    return scores


def check_accepted_trace(instance, label):
    sampling = instance.get("sampling", {})
    if sampling.get("schema") != "arcpuzzles-pair-sampling-v1":
        raise ValueError(f"{label}: missing accepted-pair sampling metadata")
    tests = instance["test"]
    tests = tests if isinstance(tests, list) else [tests]
    pairs = instance["train"] + tests
    accepted = sampling.get("accepted_pairs")
    if not isinstance(accepted, list) or len(accepted) != len(pairs):
        raise ValueError(f"{label}: accepted-pair trace is incomplete")
    previous_index = None
    for position, (record, pair) in enumerate(zip(accepted, pairs)):
        expected_split = "train" if position < len(instance["train"]) else "test"
        expected_position = position if expected_split == "train" else 0
        index = record.get("sample_index")
        if (record.get("split") != expected_split or record.get("pair_index") != expected_position
                or record.get("input_sha256") != digest(pair["input"])
                or type(index) is not int or index < 0
                or (previous_index is not None and index <= previous_index)):
            raise ValueError(f"{label}: accepted-pair trace disagrees with retained pairs")
        previous_index = index
    return pairs


def score_census(census):
    validator, validator_path = shared_validator()
    task = validator.validate_retained_census(census)
    if task != TASK_ID:
        raise ValueError(f"This scorer supports only task {TASK_ID}, got {task}")
    source_hash = census.get("generator_sha256")
    if not isinstance(source_hash, str) or len(source_hash) != 64 or any(c not in "0123456789abcdef" for c in source_hash):
        raise ValueError("Retained generator SHA-256 is invalid")
    original, rotated, bands = {}, {}, {}
    accepted_pairs = 0
    input_hashes = set()
    for lesson in census["lessons"]:
        label = f"lesson {lesson['band']}:{lesson['index']}"
        pairs = check_accepted_trace(lesson["instance"], label)
        try:
            q = [glyph_id(pair["output"]) for pair in pairs]
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from None
        accepted_pairs += len(pairs)
        input_hashes.update(digest(pair["input"]) for pair in pairs)
        band = bands.setdefault(lesson["band"], {
            "lessons": 0, "accepted_pairs": 0, "original": {}, "rotated": {},
        })
        band["lessons"] += 1
        band["accepted_pairs"] += len(pairs)
        add_scores(original, q[:-1], q[-1])
        add_scores(band["original"], q[:-1], q[-1])
        for held in range(len(q)):
            demos = q[:held] + q[held + 1:]
            add_scores(rotated, demos, q[held])
            add_scores(band["rotated"], demos, q[held])
    original_scores, rotation_scores = finish_scores(original), finish_scores(rotated)
    perfect = lambda results: [name for name, row in results.items()
                               if row["correct"] == row["predicted"] == row["episodes"]]
    return {
        "schema": "cyan_accepted_context_scores_v1", "status": "complete", "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "declared_rule_hash": census.get("declared_rule_hash"),
        "rule_source_sha256": census.get("rule_source_sha256"),
        "rule_callable_sha256": census.get("rule_callable_sha256"),
        "source_census_status": census["status"],
        "source_authority": census["sampler"].get("authority"),
        "validation": {
            "shared_validator_sha256": hashlib.sha256(validator_path.read_bytes()).hexdigest(),
            "complete_census_and_retained_hashes": True,
            "accepted_pair_traces_checked": accepted_pairs,
            "all_outputs_recognized_exactly": True,
        },
        "population": {
            "accepted_lessons": len(census["lessons"]), "accepted_pairs": accepted_pairs,
            "unique_input_grids": len(input_hashes), "demonstrations_per_lesson": census["sampler"]["n_demos"],
            "original_queries": len(census["lessons"]), "rotated_queries_including_original": accepted_pairs,
            "source_retained_rotation_records": census["summary"]["rotations"],
            "rotation_recipe": "Hold out each already accepted pair once; preserve remaining order.",
            "new_generated_inputs": 0, "new_racket_executions": 0,
        },
        "predictor_scope": {
            "inputs_to_predictors": "Demonstration output glyph IDs only; no input grid, query label, seed, or sample index.",
            "generic_output_rules": "copy_demo_N and modal_first_tie",
            "task_specific_rules": "All remaining rules know the four fixed glyphs and their q1..q4 order; q4 is the full glyph.",
            "seven_slot_histogram_complement": "Choose the first q1..q3 occurring once, otherwise q4; retained as a diagnostic for the rejected seven-slot schedule.",
            "follow_first_observed_low_cycle": "Learn the first-occurrence order of q1..q3 and predict its successor after the last low glyph; abstain until all three appear.",
        },
        "original_query": original_scores, "query_rotations": rotation_scores,
        "perfect_predictors_in_sample": {"original_query": perfect(original_scores), "query_rotations": perfect(rotation_scores)},
        "per_band": {name: {
            "accepted_lessons": row["lessons"], "accepted_pairs": row["accepted_pairs"],
            "original_query": finish_scores(row["original"]), "query_rotations": finish_scores(row["rotated"]),
        } for name, row in sorted(bands.items())},
        "limits": [
            "These are scores on the accepted pairs in the supplied complete census, not raw generator windows.",
            "Retained labels are reused unchanged. Validation checks their format and internal bindings; it does not independently re-execute or authenticate the reference rule.",
            "Only the explicitly listed predictors are measured; absence of a perfect predictor is not universal identifiability or proof of shortcut freedom.",
            "Rotations reuse the same accepted bundles and are not independent draws or exhaustive seed/cyclic-window coverage.",
            "A completed report and high or low accuracy do not grant approval or training admission.",
        ],
    }


def read_census(path):
    encoded = path.read_bytes()
    plain = gzip.decompress(encoded) if encoded.startswith(b"\x1f\x8b") else encoded
    return json.loads(plain), {
        "path": str(path), "file_sha256": hashlib.sha256(encoded).hexdigest(),
        "json_bytes_sha256": hashlib.sha256(plain).hexdigest(),
        "compression": "gzip" if encoded.startswith(b"\x1f\x8b") else "none",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.input.resolve() == args.out.resolve():
        parser.error("Input and output paths must differ")
    if args.out.exists():
        parser.error("Use a new output path")
    try:
        census, input_info = read_census(args.input)
        report = score_census(census)
        report["input_census"] = input_info
        report["scorer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        exit_code = 0
    except Exception as exc:
        report = {"schema": "cyan_accepted_context_scores_v1", "status": "error",
                  "input_census": str(args.input), "errors": [f"{type(exc).__name__}: {exc}"]}
        exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    if exit_code:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps({
            "status": report["status"], "generator_sha256": report["generator_sha256"],
            "population": report["population"],
            "original_query_accuracy": {k: v["accuracy_all_episodes"] for k, v in report["original_query"].items()},
            "rotation_accuracy": {k: v["accuracy_all_episodes"] for k, v in report["query_rotations"].items()},
            "perfect_predictors_in_sample": report["perfect_predictors_in_sample"], "out": str(args.out),
        }, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
